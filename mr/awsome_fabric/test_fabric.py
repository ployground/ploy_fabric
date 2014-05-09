from mock import patch
from mr.awsome import AWS
from unittest2 import TestCase
import os
import shutil
import tempfile


class DoCommandTests(TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.aws = AWS(self.directory)

    def tearDown(self):
        shutil.rmtree(self.directory)
        del self.directory

    def _write_config(self, content):
        with open(os.path.join(self.directory, 'aws.conf'), 'w') as f:
            f.write(content)

    def testCallWithNoArguments(self):
        self._write_config('')
        with patch('sys.stderr') as StdErrMock:
            with self.assertRaises(SystemExit):
                self.aws(['./bin/aws', 'do'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        self.assertIn('usage: aws do', output)
        self.assertIn('too few arguments', output)

    def testCallWithNonExistingInstance(self):
        self._write_config('')
        with patch('sys.stderr') as StdErrMock:
            with self.assertRaises(SystemExit):
                self.aws(['./bin/aws', 'do', 'foo'])
        output = "".join(x[0][0] for x in StdErrMock.write.call_args_list)
        self.assertIn('usage: aws do', output)
        self.assertIn("argument instance: invalid choice: 'foo'", output)

    def testCallWithExistingInstanceButTooViewArguments(self):
        import mr.awsome_fabric
        import mr.awsome.tests.dummy_plugin
        self.aws.plugins = {
            'dummy': mr.awsome.tests.dummy_plugin.plugin,
            'fabric': mr.awsome_fabric.plugin}
        self._write_config('\n'.join([
            '[dummy-instance:foo]']))
        with patch('mr.awsome_fabric.log') as LogMock:
            with self.assertRaises(SystemExit):
                self.aws(['./bin/aws', 'do', 'foo'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithMissingFabfileDeclaration(self):
        import mr.awsome_fabric
        import mr.awsome.tests.dummy_plugin
        self.aws.plugins = {
            'dummy': mr.awsome.tests.dummy_plugin.plugin,
            'fabric': mr.awsome_fabric.plugin}
        self._write_config('\n'.join([
            '[dummy-instance:foo]']))
        with patch('mr.awsome_fabric.log') as LogMock:
            with self.assertRaises(SystemExit):
                self.aws(['./bin/aws', 'do', 'foo', 'something'])
        LogMock.error.assert_called_with('No fabfile declared.')

    def testCallWithExistingInstance(self):
        import mr.awsome_fabric
        import mr.awsome.tests.dummy_plugin
        self.aws.plugins = {
            'dummy': mr.awsome.tests.dummy_plugin.plugin,
            'fabric': mr.awsome_fabric.plugin}
        fabfile = os.path.join(self.directory, 'fabfile.py')
        self._write_config('\n'.join([
            '[dummy-instance:foo]',
            'host = localhost',
            'fabfile = %s' % fabfile]))
        with open(fabfile, 'w') as f:
            f.write('\n'.join([
                'def something():',
                '    print "something"']))
        from mr.awsome_fabric import fabric_integration
        # this needs to be done before any other fabric module import
        fabric_integration.patch()
        with patch('fabric.main.main') as FabricMainMock:
            self.aws(['./bin/aws', 'do', 'foo', 'something'])
        FabricMainMock.assert_called_with()
