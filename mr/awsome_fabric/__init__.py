from contextlib import contextmanager
import argparse
import logging
import os
import sys


log = logging.getLogger('mr.awsome.fabric')


class StdFilter(object):
    def __init__(self, org):
        self.org = org
        self.flush = self.org.flush

    def isatty(self):
        return False

    def write(self, msg):
        import fabric.state
        lines = msg.split('\n')
        prefix = '[%s] ' % fabric.state.env.host_string
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                lines[index] = line[len(prefix):]
        self.org.write('\n'.join(lines))


@contextmanager
def std_filters():
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    if not isinstance(sys.stdout, StdFilter):
        sys.stdout = StdFilter(sys.stdout)
    if not isinstance(sys.stderr, StdFilter):
        sys.stderr = StdFilter(sys.stderr)
    yield
    sys.stdout = old_stdout
    sys.stderr = old_stderr


class FabricDoCmd(object):
    """Run Fabric"""

    def __init__(self, aws):
        self.aws = aws

    def __call__(self, argv, help):
        """Do stuff on the cluster (using fabric)"""
        parser = argparse.ArgumentParser(
            prog="aws do",
            description=help,
            add_help=False,
        )
        instances = self.aws.get_instances(command='init_ssh_key')
        parser.add_argument("server", nargs=1,
                            metavar="instance",
                            help="Name of the instance or server from the config.",
                            choices=list(instances))
        parser.add_argument("...", nargs=argparse.REMAINDER,
                            help="Fabric options")
        parser.parse_args(argv[:1])
        old_sys_argv = sys.argv
        old_cwd = os.getcwd()

        from mr.awsome_fabric import fabric_integration
        # this needs to be done before any other fabric module import
        fabric_integration.patch()

        import fabric.state
        import fabric.main

        hoststr = None
        try:
            fabric_integration.instances = self.aws.instances
            fabric_integration.log = log
            hoststr = argv[0]
            server = instances[hoststr]
            if 'user' in server.config:
                hoststr = '%s@%s' % (server.config['user'], hoststr)
            # prepare the connection
            fabric.state.env.reject_unknown_hosts = True
            fabric.state.env.disable_known_hosts = True

            fabfile = server.config.get('fabfile')
            if fabfile is None:
                log.error("No fabfile declared.")
                sys.exit(1)
            newargv = ['fab', '-H', hoststr, '-r', '-D']
            if fabfile is not None:
                newargv = newargv + ['-f', fabfile]
            sys.argv = newargv + argv[1:]

            # setup environment
            os.chdir(os.path.dirname(fabfile))
            fabric.state.env.servers = self.aws.instances
            fabric.state.env.server = server
            known_hosts = self.aws.known_hosts
            fabric.state.env.known_hosts = known_hosts
            fabric.state.env.config_base = self.aws.config.path

            with std_filters():
                fabric.main.main()
        finally:
            if fabric.state.connections.opened(hoststr):  # pragma: no cover
                fabric.state.connections[hoststr].close()
            sys.argv = old_sys_argv
            os.chdir(old_cwd)


def do(self, task, *args, **kwargs):
    from mr.awsome_fabric import fabric_integration
    # this needs to be done before any other fabric module import
    fabric_integration.patch()
    orig_instances = fabric_integration.instances
    orig_log = fabric_integration.log
    fabric_integration.instances = self.master.aws.instances
    fabric_integration.log = log

    from fabric.main import extract_tasks
    from fabric.state import env
    env.reject_unknown_hosts = True
    env.disable_known_hosts = True
    env.known_hosts = self.master.known_hosts
    env.server = self

    fabfile = self.config['fabfile']
    with open(fabfile) as f:
        source = f.read()
    code = compile(source, fabfile, 'exec')
    g = {
        '__file__': fabfile}
    exec code in g, g
    new_style, classic, default = extract_tasks(g.items())
    callables = new_style if env.new_style_tasks else classic
    orig_host_string = env.host_string
    env.host_string = "{}@{}".format(
        self.config.get('user', 'root'),
        self.id)
    with std_filters():
        result = callables[task](*args, **kwargs)
    fabric_integration.instances = orig_instances
    fabric_integration.log = orig_log
    del env['reject_unknown_hosts']
    del env['disable_known_hosts']
    env.host_string = orig_host_string
    return result


def augment_instance(instance):
    if not hasattr(instance, 'do'):
        instance.do = do.__get__(instance, instance.__class__)


def get_commands(aws):
    return [
        ('do', FabricDoCmd(aws))]


def get_massagers():
    from mr.awsome.config import PathMassager
    return [PathMassager(None, 'fabfile')]


plugin = dict(
    augment_instance=augment_instance,
    get_commands=get_commands,
    get_massagers=get_massagers)
