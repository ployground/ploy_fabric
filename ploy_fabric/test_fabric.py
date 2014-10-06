from mock import MagicMock, patch
from ploy import Controller
import logging
import pytest


def caplog_messages(caplog, level=logging.INFO):
    return [
        x.message
        for x in caplog.records()
        if x.levelno >= level]


@pytest.fixture
def ctrl(ployconf):
    import ploy_fabric
    import ploy.tests.dummy_plugin
    ctrl = Controller(ployconf.directory)
    ctrl.plugins = {
        'dummy': ploy.tests.dummy_plugin.plugin,
        'fabric': ploy_fabric.plugin}
    ctrl.configfile = ployconf.path
    return ctrl


@pytest.yield_fixture
def fabfile(tempdir):
    import sys
    sys.modules.pop('foo', None)
    yield tempdir['etc/foo.py']
    sys.modules.pop('foo', None)


@pytest.mark.parametrize("cmd_name", ['fab', 'do'])
@pytest.fixture(params=['do', 'fab'])
def cmd(request):
    return request.param


@pytest.fixture
def open_session_mock(monkeypatch):
    import ploy.tests.dummy_plugin
    open_session_mock = MagicMock()
    open_session_mock().recv.return_value = ''
    open_session_mock().recv_stderr.return_value = ''
    open_session_mock().exit_status_ready.return_value = True
    open_session_mock().recv_exit_status.return_value = 0
    monkeypatch.setattr(
        ploy.tests.dummy_plugin.MockTransport, 'open_session',
        open_session_mock, raising=False)
    return open_session_mock


class TestDoCommand:
    def testCallWithExistingInstanceButTooViewArguments(self, ctrl, fabfile, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile.path])
        fabfile.fill([
            'from fabric.api import run',
            'def something():',
            '    run("something")'])
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                ctrl(['./bin/ploy', 'do', 'foo'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert 'one of the arguments' in output

    def testCallWithMissingFabfileDeclaration(self, ctrl, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]'])
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert "invalid choice: 'foo' (choose from )" in output

    def testCallWithExistingInstance(self, ctrl, fabfile, open_session_mock, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile.path])
        fabfile.fill([
            'from fabric.api import run',
            'def something():',
            '    run("something")'])
        ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        assert open_session_mock().recv.called is True
        from fabric.state import env
        assert 'instances' not in env

    def testCallWithTaskArg(self, ctrl, fabfile, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile.path])
        fabfile.fill([
            'from fabric.api import run',
            'def something(fooarg):',
            '    print fooarg'])
        with patch('sys.stdout') as StdOutMock:
            ctrl(['./bin/ploy', 'do', 'foo', 'something', 'bararg'])
        output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
        assert 'bararg' in output

    def testCallWithTaskKwArg(self, ctrl, fabfile, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile.path])
        fabfile.fill([
            'from fabric.api import run',
            'def something(fooarg="foo"):',
            '    print fooarg'])
        with patch('sys.stdout') as StdOutMock:
            ctrl(['./bin/ploy', 'do', 'foo', 'something', 'fooarg=bararg'])
        output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
        assert 'bararg' in output

    def testDeprecation(self, caplog, ctrl, fabfile, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile.path])
        fabfile.fill([
            'from fabric.api import env',
            'def something(fooarg="foo"):',
            '    print env.servers',
            '    print env.server'])
        ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        servers_msg, server_msg = [x.splitlines() for x in caplog_messages(caplog, level=logging.WARN)]
        assert servers_msg[0] == "Use of deprecated variable name 'servers', use 'instances' instead."
        parts = servers_msg[1].rsplit(':', 1)
        assert parts[0].endswith('etc/foo.py')
        assert parts[1] == '3'
        assert servers_msg[2] == "    print env.servers"
        assert server_msg[0] == "Use of deprecated variable name 'server', use 'instance' instead."
        parts = server_msg[1].rsplit(':', 1)
        assert parts[0].endswith('etc/foo.py')
        assert parts[1] == '4'
        assert server_msg[2] == "    print env.server"


class TestFabCommand:
    def testCallWithExistingInstanceButTooViewArguments(self, ctrl, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]'])
        with patch('ploy_fabric.log') as LogMock:
            with pytest.raises(SystemExit):
                ctrl(['./bin/ploy', 'fab', 'foo'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithMissingFabfileDeclaration(self, ctrl, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]'])
        with patch('ploy_fabric.log') as LogMock:
            with pytest.raises(SystemExit):
                ctrl(['./bin/ploy', 'fab', 'foo', 'something'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithExistingInstance(self, ctrl, fabfile, open_session_mock, ployconf):
        ployconf.fill([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile.path])
        fabfile.fill([
            'from fabric.api import run',
            'def something():',
            '    run("something")'])
        with pytest.raises(SystemExit) as e:
            ctrl(['./bin/ploy', 'fab', 'foo', 'something'])
        assert open_session_mock().recv.called is True
        assert e.value.code == 0
        from fabric.state import env
        assert 'instances' not in env


def test_call_with_no_arguments(cmd, ctrl, ployconf):
    ployconf.fill('')
    with patch('sys.stderr') as StdErrMock:
        with pytest.raises(SystemExit):
            ctrl(['./bin/ploy', cmd])
    output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
    assert 'usage: ploy %s' % cmd in output
    assert 'too few arguments' in output


def test_call_with_non_existing_instance(cmd, ctrl, ployconf):
    ployconf.fill('')
    with patch('sys.stderr') as StdErrMock:
        with pytest.raises(SystemExit):
            ctrl(['./bin/ploy', cmd, 'foo'])
    output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
    assert 'usage: ploy %s' % cmd in output
    assert "argument instance: invalid choice: 'foo'" in output


def test_list_tasks(cmd, ctrl, fabfile, ployconf):
    ployconf.fill([
        '[dummy-instance:foo]',
        'host = localhost',
        'fabfile = %s' % fabfile.path])
    fabfile.fill([
        'def something():',
        '    pass',
        '',
        'def something_else():',
        '    pass',
        ''])
    with patch('sys.stdout') as StdOutMock:
        StdOutMock.isatty.return_value = False
        try:
            ctrl(['./bin/ploy', cmd, 'foo', '-l'])
        except SystemExit as e:
            assert e.code == 0
    output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
    assert 'Available commands' in output
    assert 'something' in output
    assert 'something_else' in output


def test_env_overwrite_from_config(caplog, cmd, ctrl, fabfile, ployconf):
    ployconf.fill([
        '[dummy-instance:foo]',
        'host = localhost',
        'fabfile = %s' % fabfile.path,
        'fabric-ham = egg',
        'fabric-shell = fooshell'])
    fabfile.fill([
        'from fabric.api import env',
        'def something():',
        '    print "ham", env.ham',
        '    print "shell", env.shell'])
    with patch('sys.stdout') as StdOutMock:
        StdOutMock.isatty.return_value = False
        try:
            ctrl(['./bin/ploy', cmd, 'foo', 'something'])
        except SystemExit as e:
            assert e.code == 0
    output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
    assert "ham egg\n" in output
    assert "shell fooshell\n" in output
    if cmd == 'fab':
        msgs = [x for x in caplog_messages(caplog, level=logging.WARN)]
        assert msgs == [
            'Removed fab command line option -D/--disable-known-hosts because of overwrite for instance dummy-instance:foo.',
            'Removed fab command line option -r/--reject-unknown-hosts because of overwrite for instance dummy-instance:foo.',
            'Removed fab command line option -s/--shell because of overwrite for instance dummy-instance:foo.']
