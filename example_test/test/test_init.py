import unittest, sys
sys.path.append("/vagrant/salt-test-runner")
from salttest import salttest

class TestInit(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls._context = salttest.TestContext("example_test")
    cls._context.build()
    
  @classmethod
  def tearDownClass(cls):
    cls._context.destroy()

  #def setUp(self):
    #self.context = salttest.TestContext("example_test")
   # self.context.build()

  #def tearDown(self):
  #  self.context.destroy()

  def testFileExists(self):
    self.assertEquals(TestInit._context.test_name, "example_test")

if __name__ == '__main__':
    unittest.main()