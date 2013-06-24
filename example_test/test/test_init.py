import unittest, sys
sys.path.append("/vagrant/salt-test-runner")
from salttest import salttest

class TestInit(salttest.SaltTest):

  def testFileExists(self):
    self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()