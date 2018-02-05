from __future__ import print_function, unicode_literals
from contextlib import contextmanager
from functools import wraps
import argparse
import logging
import os
import sys


log = logging.getLogger('ploy_fabric')


notset = object()


def get_host_string(instance, user=None):
    return "{user}@{host}".format(
        user=instance.config.get('user', user or 'root'),
        host=instance.uid)


class context:
    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        if args:
            self(args)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import fabric.state
            with fabric.state.env.instance.fabric(user=self.user):
                return func(*args, **kwargs)
        return wrapper


@contextmanager
def instance_context(instance, user=None):
    with fabric_env(instance.master.ctrl, instance) as env:
        env.host_string = get_host_string(instance, user=user)
        yield


def has_fabfile(instance):
    fabfile = instance.config.get('fabfile')
    if fabfile is None:
        return False
    if not os.path.exists(fabfile):
        return False
    return True


def get_fabfile(instance):
    fabfile = instance.config.get('fabfile')
    if fabfile is None:
        log.error("No fabfile declared.")
        sys.exit(1)
    if not os.path.exists(fabfile):
        log.error("The fabfile at '%s' is missing." % fabfile)
        sys.exit(1)
    return fabfile


@contextmanager
def sys_argv(newargv):
    orig_sys_argv = sys.argv
    sys.argv = newargv
    try:
        yield
    finally:
        sys.argv = orig_sys_argv


@contextmanager
def cwd(path):
    orig_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(orig_cwd)


def get_fabric_env_settings(ctrl, instance):
    env = dict(
        reject_unknown_hosts=True,
        disable_known_hosts=True,
        host_string=get_host_string(instance),
        known_hosts=ctrl.known_hosts,
        instances=ctrl.instances,
        instance=instance,
        config_base=ctrl.config.path)
    for k, v in instance.config.items():
        if not k.startswith('fabric-'):
            continue
        env[k[7:]] = v
    return env


@contextmanager
def fabric_env(ctrl, instance, fabcmd=False):
    import fabric.state
    env, env_options = fabric.state.env, fabric.state.env_options
    orig = dict()
    orig_options = list(env_options)
    for k, v in get_fabric_env_settings(ctrl, instance).items():
        orig[k] = env.get(k, notset)
        env[k] = v
    new_options = []
    for option in env_options:
        if option.dest not in orig:
            new_options.append(option)
        elif fabcmd:
            log.warn("Removed fab command line option %s because of overwrite for instance %s." % (option, instance.config_id))
    env_options[:] = new_options
    try:
        yield env
    finally:
        for key, value in orig.items():
            if value is notset:
                if key in env:
                    del env[key]
            else:
                env[key] = value
        env_options[:] = orig_options


@contextmanager
def fabric_connections(ctrl, instance, fabcmd=False):
    import fabric.state
    original_connections = set(fabric.state.connections)
    try:
        with fabric_env(ctrl, instance, fabcmd=fabcmd):
            yield
    finally:
        for connection in set(fabric.state.connections) - original_connections:
            log.debug("Closing connection to '%s' after Fabric call." % connection)
            del fabric.state.connections[connection]


@contextmanager
def fabric_integration(ctrl, instance, fabcmd=False):
    from ploy_fabric import _fabric_integration
    # this needs to be done before any other fabric module import
    _fabric_integration.patch()

    with cwd(os.path.dirname(get_fabfile(instance))):
        with fabric_connections(ctrl, instance, fabcmd=fabcmd):
            yield


class FabricCmd(object):
    """Run Fabric"""

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def __call__(self, argv, help):
        """Do stuff on the cluster (using fabric)"""
        from ploy.common import sorted_choices
        parser = argparse.ArgumentParser(
            prog="%s fab" % self.ctrl.progname,
            description=help,
            add_help=False,
        )
        instances = self.ctrl.get_instances(command='init_ssh_key')
        parser.add_argument("instance", nargs=1,
                            metavar="instance",
                            help="Name of the instance from the config.",
                            type=str,
                            choices=sorted_choices(instances))
        parser.add_argument("fabric_opts",
                            metavar="...", nargs=argparse.REMAINDER,
                            help="Fabric options")
        args = parser.parse_args(argv)

        instance = instances[args.instance[0]]
        with fabric_integration(self.ctrl, instance, fabcmd=True):
            from fabric.main import main
            fabfile = get_fabfile(instance)
            newargv = ['fab', '-f', fabfile]
            if args.fabric_opts:
                newargv = newargv + args.fabric_opts
            with sys_argv(newargv):
                main()


class DoCmd(object):
    """Run a specific Fabric task"""

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def get_completion(self):
        from ploy.common import sorted_choices
        instances = set()
        for instance in self.ctrl.get_instances(command='do'):
            if self.ctrl.instances[instance].has_fabfile():
                instances.add(instance)
        return sorted_choices(instances)

    def __call__(self, argv, help):
        """Run a fabric task on an instance"""
        parser = argparse.ArgumentParser(
            prog="%s do" % self.ctrl.progname,
            description=help)
        parser.add_argument("instance", nargs=1,
                            metavar="instance",
                            help="Name of the instance from the config.",
                            type=str,
                            choices=self.get_completion())
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("task", nargs='?',
                           help="The task to run.")
        group.add_argument("-l", "--list",
                           action='store_true',
                           help="List available tasks.")
        parser.add_argument("task_args",
                            metavar="arg|key=value", nargs="*",
                            help="Arguments for the task.")
        args = parser.parse_args(argv)

        instance = self.ctrl.instances[args.instance[0]]
        if args.list:
            print("Available commands:")
            print()
            with callables(instance) as tasks:
                for name in sorted(tasks):
                    print("    %s" % name)
                return
        task_args = []
        task_kwargs = {}
        for arg in args.task_args:
            parts = arg.split('=', 1)
            if len(parts) == 1:
                task_args.append(arg)
            else:
                task_kwargs[parts[0]] = parts[1]
        instance.do(args.task, *task_args, **task_kwargs)


exec_ = __builtins__.get('exec')
if exec_ is None:
    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")


@contextmanager
def callables(instance):
    with fabric_integration(instance.master.ctrl, instance):
        from fabric.main import extract_tasks
        from fabric.state import env

        fabfile = get_fabfile(instance)
        with open(fabfile) as f:
            source = f.read()
        code = compile(source, fabfile, 'exec')
        g = {'__file__': fabfile}
        exec_(code, g, g)
        new_style, classic, default = extract_tasks(g.items())
        callables = new_style if env.new_style_tasks else classic
        yield callables


def do(self, task, *args, **kwargs):
    with callables(self) as tasks:
        return tasks[task](*args, **kwargs)


def augment_instance(instance):
    if not hasattr(instance, 'init_ssh_key'):
        return
    if not hasattr(instance, 'fabric'):
        instance.fabric = instance_context.__get__(instance, instance.__class__)
    if not hasattr(instance, 'has_fabfile'):
        instance.has_fabfile = has_fabfile.__get__(instance, instance.__class__)
    if not hasattr(instance, 'do'):
        instance.do = do.__get__(instance, instance.__class__)


def get_commands(ctrl):
    return [
        ('fab', FabricCmd(ctrl)),
        ('do', DoCmd(ctrl))]


def get_massagers():
    from ploy.config import PathMassager
    return [PathMassager(None, 'fabfile')]


plugin = dict(
    augment_instance=augment_instance,
    get_commands=get_commands,
    get_massagers=get_massagers)
