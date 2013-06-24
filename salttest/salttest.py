import unittest
import docker
import os, sys, time
import salt.client
import salt.key
from subprocess import call
from subprocess import Popen

class SaltTest(unittest.TestCase):
  def setUp(self):
    # Generate the docker build profile
    dockerfile = """FROM salt-minion
    MAINTAINER Kimbro Staken "kstaken@kstaken.com"

    CMD ["salt-minion"]

    RUN echo %s > /etc/salt/minion
    """

    self.build_tag = "test-name-" + str(os.getpid())

    minionconfig = "\"master: 172.16.42.1\\nid: %s\"" % self.build_tag

    self.docker_client = docker.Client()

    # Build the container
    result = self.docker_client.build((dockerfile % minionconfig).split('\n'))
    image_id = result[0]

    self.docker_client.tag(image_id, self.build_tag)

    # Start the container
    self.container_id = self.docker_client.create_container(image_id, "salt-minion", detach=True)['Id']
    self.docker_client.start(self.container_id)

    # Give the minion a chance to connect
    time.sleep(5)

    # Accept the minion keys
    ret = call(["/usr/bin/salt-key", "-y", "-a", self.build_tag])

    # run a test ping
    self.salt_client = salt.client.LocalClient()
    max = 20
    while len(self.salt_client.cmd(self.build_tag, 'test.ping')) == 0 and max > 0:
      #print "Waiting for minion to be available " + str(max)
      max = max - 1
      time.sleep(1)

    if (len(self.salt_client.cmd(self.build_tag, 'test.ping')) == 0):
      print "ERROR: Failed to ping the minion"
      sys.exit(1)
    #else:
      #print "Minion is reachable"

  def testPing(self):
    self.assertNotEqual(len(self.salt_client.cmd(self.build_tag, 'test.ping')), 0)

  def tearDown(self):
    # Cleanup
    ret = call(["/usr/bin/salt-key", "-y", "-d", self.build_tag])

    self.docker_client.stop(self.container_id)
    self.docker_client.remove_image(self.build_tag)

if __name__ == '__main__':
    unittest.main()