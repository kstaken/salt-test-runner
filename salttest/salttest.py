import unittest
import docker
import os, sys, time, subprocess
import salt.client
import salt.key

class TestContext():
  def __init__(self, test_name, minion_config=None, top_state=None):
    self.test_name = test_name
    self.build_tag = test_name + '-' + str(os.getpid())
    self.docker_client = docker.Client()
    self.salt_client = salt.client.LocalClient()
    self.minion_config = minion_config
    self.top_state = top_state

  def build(self):        
    self._build_container()
    self._start_container()
    self._accept_keys()
    self._verify_minion()
    self._setup_states()
    
  def highstate(self):
    self.salt_client.cmd(self.build_tag, 'state.highstate')

  def destroy(self):
    # Cleanup
    output, error = subprocess.Popen(['/usr/bin/salt-key', '-y', '-d', self.build_tag], stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    
    self.docker_client.stop(self.container_id)
    self.docker_client.remove_image(self.build_tag)

  def _build_container(self):
    # Generate the docker build profile
    dockerfile = """FROM salt-minion
    MAINTAINER Kimbro Staken "kstaken@kstaken.com"

    CMD ["salt-minion"]

    RUN echo %s > /etc/salt/minion
    """

    minionconfig = '\"master: 172.16.42.1\\nid: %s\"' % self.build_tag
    
    # Build the container
    result = self.docker_client.build((dockerfile % minionconfig).split('\n'))
    self.image_id = result[0]

    # Tag the container with the test name
    self.docker_client.tag(self.image_id, self.build_tag)

  def _start_container(self):
    # Start the container
    self.container_id = self.docker_client.create_container(self.image_id, 'salt-minion', detach=True)['Id']
    self.docker_client.start(self.container_id)

  def _accept_keys(self):
    # Give the minion a chance to connect
    #time.sleep(5)
    command = ['/usr/bin/salt-key', '-l', 'un']
    output = ''
    while (self.build_tag not in output):
      output, error = subprocess.Popen(command, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    
    # Accept the minion keys
    output, error = subprocess.Popen(['/usr/bin/salt-key', '-y', '-a', self.build_tag], stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()

  def _verify_minion(self):
    # run a test ping
    max = 20
    while len(self.salt_client.cmd(self.build_tag, 'test.ping')) == 0 and max > 0:
      #print 'Waiting for minion to be available ' + str(max)
      max = max - 1
      time.sleep(1)

    if (len(self.salt_client.cmd(self.build_tag, 'test.ping')) == 0):
      print 'ERROR: Failed to ping the minion'
      sys.exit(1)
        
  def _setup_states(self):
    # Setup the salt tree.
    # link the test module into place
    try:
      os.remove('/srv/salt/' + self.test_name)
    except:
      True
    os.symlink(os.getcwd() + '/' + self.test_name + '/' + self.test_name, '/srv/salt/' + self.test_name)
    # replace top.sls
    os.remove('/srv/salt/top.sls')
    os.symlink(os.getcwd() + '/' + self.test_name + '/test/top.sls', '/srv/salt/top.sls')
