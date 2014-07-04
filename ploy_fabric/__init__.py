from contextlib import contextmanager
import argparse
import inspect
import logging
import os
import sys


log = logging.getLogger('ploy_fabric')


notset = object()


def get_host_string(instance):
    return "{user}@{host}".format(
        user=instance.config.get('user', 'root'),
        host=instance.uid)


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


class DeprecationProxy:
    def __init__(self, wrapped, name, new_name):
        self.wrapped = wrapped
        self.name = name
        self.new_name = new_name
        self.seen = set()

    def __getattr__(self, name):
        caller_frame = inspect.currentframe().f_back
        info = inspect.getframeinfo(caller_frame)
        orig_name = self.__dict__['name']
        new_name = self.__dict__['new_name']
        seen = self.__dict__['seen']
        key = (info.filename, info.lineno)
        if key not in seen:
            seen.add(key)
            log.warning("Use of deprecated variable name '%s', use '%s' instead.\n%s:%s\n%s" % (
                orig_name, new_name, info.filename, info.lineno, ''.join(info.code_context)))
        return getattr(self.__dict__['wrapped'], name)


@contextmanager
def fabric_env(ctrl, instance):
    import fabric.state
    connections, env = fabric.state.connections, fabric.state.env
    orig = dict()
    orig['reject_unknown_hosts'] = env.get('reject_unknown_hosts', notset)
    env.reject_unknown_hosts = True
    orig['disable_known_hosts'] = env.get('disable_known_hosts', notset)
    env.disable_known_hosts = True
    orig['host_string'] = env.get('host_string', notset)
    env.host_string = get_host_string(instance)
    orig['known_hosts'] = env.get('known_hosts', notset)
    env.known_hosts = ctrl.known_hosts
    orig['instances'] = env.get('instances', notset)
    env.instances = ctrl.instances
    orig['instance'] = env.get('instance', notset)
    env.instance = instance
    orig['servers'] = env.get('servers', notset)
    env.servers = DeprecationProxy(ctrl.instances, 'servers', 'instances')
    orig['server'] = env.get('server', notset)
    env.server = DeprecationProxy(instance, 'server', 'instance')
    orig['config_base'] = env.get('config_base', notset)
    env.config_base = ctrl.config.path
    try:
        with cwd(os.path.dirname(get_fabfile(instance))):
            yield
    finally:
        if connections.opened(env.host_string):  # pragma: no cover
            connections[env.host_string].close()
        for key, value in orig.items():
            if value is notset:
                if key in env:
                    del env[key]
            else:
                env[key] = value


@contextmanager
def fabric_integration(ctrl, instance):
    from ploy_fabric import _fabric_integration
    # this needs to be done before any other fabric module import
    _fabric_integration.patch()

    orig_instances = _fabric_integration.instances
    orig_log = _fabric_integration.log
    _fabric_integration.instances = ctrl.instances
    _fabric_integration.log = log
    try:
        with fabric_env(ctrl, instance):
            yield
    finally:
        _fabric_integration.instances = orig_instances
        _fabric_integration.log = orig_log


class FabricCmd(object):
    """Run Fabric"""

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def __call__(self, argv, help):
        """Do stuff on the cluster (using fabric)"""
        parser = argparse.ArgumentParser(
            prog="%s do" % self.ctrl.progname,
            description=help,
            add_help=False,
        )
        instances = self.ctrl.get_instances(command='init_ssh_key')
        parser.add_argument("instance", nargs=1,
                            metavar="instance",
                            help="Name of the instance from the config.",
                            choices=list(instances))
        parser.add_argument("fabric_opts",
                            metavar="...", nargs=argparse.REMAINDER,
                            help="Fabric options")
        args = parser.parse_args(argv)

        instance = instances[args.instance[0]]
        with fabric_integration(self.ctrl, instance):
            from fabric.main import main
            from fabric.state import env
            fabfile = get_fabfile(instance)
            newargv = ['fab', '-H', env.host_string, '-r', '-D', '-f', fabfile]
            if args.fabric_opts:
                newargv = newargv + args.fabric_opts
            with sys_argv(newargv):
                main()


class DoCmd(object):
    """Run a specific Fabric task"""

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def get_completion(self):
        return sorted(self.ctrl.get_instances(command='do'))

    def __call__(self, argv, help):
        """Run a fabric task on an instance"""
        parser = argparse.ArgumentParser(
            prog="%s do" % self.ctrl.progname,
            description=help)
        instances = self.ctrl.get_instances(command='do')
        parser.add_argument("instance", nargs=1,
                            metavar="instance",
                            help="Name of the instance from the config.",
                            choices=list(instances))
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

        instance = instances[args.instance[0]]
        if args.list:
            print "Available commands:"
            print
            with callables(instance) as tasks:
                for name in sorted(tasks):
                    print "    %s" % name
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
        exec code in g, g
        new_style, classic, default = extract_tasks(g.items())
        callables = new_style if env.new_style_tasks else classic
        yield callables


def do(self, task, *args, **kwargs):
    with callables(self) as tasks:
        return tasks[task](*args, **kwargs)


def augment_instance(instance):
    if hasattr(instance, 'init_ssh_key') and not hasattr(instance, 'do'):
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
