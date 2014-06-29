from mock import patch
from ploy import Controller
import os
import pytest


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
        with patch('ploy_fabric.log') as LogMock:
            with pytest.raises(SystemExit):
                self.ctrl(['./bin/ploy', 'do', 'foo'])
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
                self.ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithExistingInstance(self):
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
                '    print "something"']))
        from ploy_fabric import fabric_integration
        # this needs to be done before any other fabric module import
        fabric_integration.patch()
        with patch('fabric.main.main') as FabricMainMock:
            self.ctrl(['./bin/ploy', 'do', 'foo', 'something'])
        FabricMainMock.assert_called_with()
