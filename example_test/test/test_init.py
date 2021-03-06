import unittest, sys
sys.path.append('.')
from salttest import salttest

class TestInit(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls._containers = salttest.TestContainers('containers.yml')
    cls._containers.build()
    cls._containers.setup_salt(config='module_test', top_sls='top.sls', module='../example_test')
    cls._containers.highstate()
    environment = cls._containers.save()
    
  @classmethod
  def tearDownClass(cls):
    cls._containers.destroy()

  def testName(self):
    context = self._containers.get('example_test')
    self.assertEquals(context.test_name, 'example_test')
    
  def testFileExists(self):
    context = self._containers.get('example_test')
    self.assertEquals(context.salt_client.cmd(context.build_tag, 'cmd.run', ['cat /tmp/test-file'])[context.build_tag], 'Just a test')

    context = self._containers.get('example_test2')
    self.assertEquals(context.salt_client.cmd(context.build_tag, 'cmd.run', ['cat /tmp/test-file'])[context.build_tag], 'Just a test')

if __name__ == '__main__':
    unittest.main()