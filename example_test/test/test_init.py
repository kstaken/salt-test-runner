import unittest, sys
sys.path.append(".")
from salttest import salttest

class TestInit(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls._context = salttest.TestContext("example_test")
    cls._context.build()
    cls._context.highstate()
    
  @classmethod
  def tearDownClass(cls):
    cls._context.destroy()

  #def setUp(self):
    #self.context = salttest.TestContext("example_test")
   # self.context.build()

  #def tearDown(self):
  #  self.context.destroy()

  def testName(self):
    self.assertEquals(TestInit._context.test_name, "example_test")
    
  def testFileExists(self):
    context = TestInit._context
    self.assertEquals(context.salt_client.cmd(context.build_tag, "cmd.run", ["cat /tmp/test-file"])[context.build_tag], "Just a test")

if __name__ == '__main__':
    unittest.main()