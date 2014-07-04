from mock import MagicMock, patch
from ploy import Controller
import logging
import os
import pytest


def caplog_messages(caplog, level=logging.INFO):
    return [
        x.message
        for x in caplog.records()
        if x.levelno >= level]


class TestDoCommand:
    @pytest.fixture(autouse=True)
    def setup_ctrl(self, ployconf, tempdir):
        self.directory = ployconf.directory
        self.tempdir = tempdir
        self.ctrl = Controller(ployconf.directory)
        self.ctrl.configfile = ployconf.path
        self._write_config = ployconf.fill

    def testCallWithNoArguments(self):
        self._write_config('')
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'do'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert 'usage: ploy do' in output
        assert 'too few arguments' in output

    def testCallWithNonExistingInstance(self):
        self._write_config('')
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'do', 'foo'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert 'usage: ploy do' in output
        assert "argument instance: invalid choice: 'foo'" in output

    def testCallWithExistingInstanceButTooViewArguments(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        self._write_config('\n'.join([
            '[dummy-instance:foo]']))
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'do', 'foo'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert 'one of the arguments' in output

    def testCallWithMissingFabfileDeclaration(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        self._write_config('\n'.join([
            '[dummy-instance:foo]']))
        with patch('ploy_fabric.log') as LogMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithExistingInstance(self, monkeypatch):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'from fabric.api import run',
                'def something():',
                '    run("something")']))
        open_session_mock = MagicMock()
        open_session_mock().recv.return_value = ''
        open_session_mock().recv_stderr.return_value = ''
        open_session_mock().exit_status_ready.return_value = True
        open_session_mock().recv_exit_status.return_value = 0
        monkeypatch.setattr(
            ploy.tests.dummy_plugin.MockTransport, 'open_session',
            open_session_mock, raising=False)
        self.ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        assert open_session_mock().recv.called is True
        from fabric.state import env
        assert 'instances' not in env

    def testListTasks(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'def something():',
                '    pass']))
        with patch('sys.stdout') as StdOutMock:
            self.ctrl(['./bin/ploy', 'do', 'foo', '-l'])
        output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
        assert 'Available commands' in output
        assert 'something' in output

    def testCallWithTaskArg(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'from fabric.api import run',
                'def something(fooarg):',
                '    print fooarg']))
        with patch('sys.stdout') as StdOutMock:
            self.ctrl(['./bin/ploy', 'do', 'foo', 'something', 'bararg'])
        output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
        assert 'bararg' in output

    def testCallWithTaskKwArg(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'from fabric.api import run',
                'def something(fooarg="foo"):',
                '    print fooarg']))
        with patch('sys.stdout') as StdOutMock:
            self.ctrl(['./bin/ploy', 'do', 'foo', 'something', 'fooarg=bararg'])
        output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
        assert 'bararg' in output

    def testDeprecation(self, caplog):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'from fabric.api import env',
                'def something(fooarg="foo"):',
                '    print env.servers',
                '    print env.server']))
        self.ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        servers_msg, server_msg = [x.splitlines() for x in caplog_messages(caplog, level=logging.WARN)]
        assert servers_msg[0] == "Use of deprecated variable name 'servers', use 'instances' instead."
        parts = servers_msg[1].rsplit(':', 1)
        assert parts[0].endswith('etc/fabfile.py')
        assert parts[1] == '3'
        assert servers_msg[2] == "    print env.servers"
        assert server_msg[0] == "Use of deprecated variable name 'server', use 'instance' instead."
        parts = server_msg[1].rsplit(':', 1)
        assert parts[0].endswith('etc/fabfile.py')
        assert parts[1] == '4'
        assert server_msg[2] == "    print env.server"


class TestFabCommand:
    @pytest.fixture(autouse=True)
    def setup_ctrl(self, ployconf, tempdir):
        self.directory = ployconf.directory
        self.tempdir = tempdir
        self.ctrl = Controller(ployconf.directory)
        self.ctrl.configfile = ployconf.path
        self._write_config = ployconf.fill

    def testCallWithNoArguments(self):
        self._write_config('')
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'fab'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert 'usage: ploy do' in output
        assert 'too few arguments' in output

    def testCallWithNonExistingInstance(self):
        self._write_config('')
        with patch('sys.stderr') as StdErrMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'fab', 'foo'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        assert 'usage: ploy do' in output
        assert "argument instance: invalid choice: 'foo'" in output

    def testCallWithExistingInstanceButTooViewArguments(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        self._write_config('\n'.join([
            '[dummy-instance:foo]']))
        with patch('ploy_fabric.log') as LogMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'fab', 'foo'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithMissingFabfileDeclaration(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        self._write_config('\n'.join([
            '[dummy-instance:foo]']))
        with patch('ploy_fabric.log') as LogMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'fab', 'foo', 'something'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithExistingInstance(self, monkeypatch):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'from fabric.api import run',
                'def something():',
                '    run("something")']))
        open_session_mock = MagicMock()
        open_session_mock().recv.return_value = ''
        open_session_mock().recv_stderr.return_value = ''
        open_session_mock().exit_status_ready.return_value = True
        open_session_mock().recv_exit_status.return_value = 0
        monkeypatch.setattr(
            ploy.tests.dummy_plugin.MockTransport, 'open_session',
            open_session_mock, raising=False)
        with pytest.raises(SystemExit) as e:
            self.ctrl(['./bin/ploy', 'fab', 'foo', 'something'])
        assert open_session_mock().recv.called is True
        assert e.value.code == 0
        from fabric.state import env
        assert 'instances' not in env

    def testListTasks(self):
        import ploy_fabric
        import ploy.tests.dummy_plugin
        self.ctrl.plugins = {
            'dummy': ploy.tests.dummy_plugin.plugin,
            'fabric': ploy_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'def something():',
                '    pass']))
        with patch('sys.stdout') as StdOutMock:
            self.ctrl(['./bin/ploy', 'do', 'foo', '-l'])
        output = "".join(x[0][0] for x in StdOutMock.write.call_args_list)
        assert 'Available commands' in output
        assert 'something' in output
