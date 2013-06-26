import unittest
import docker
import os, sys, time, subprocess, yaml
import logging
import salttest
import salt.client
import salt.key

class TestContainers:
  def __init__(self, conf_file):
    self._setupLogging()

    if (not conf_file.startswith('/')):
      conf_file = os.path.join(os.path.dirname(sys.argv[0]), conf_file)

    data = open(conf_file, 'r')
    self.config = yaml.load(data)

    self.containers = {}

  def get(self, container):
    return self.containers[container]

  def build(self):
    for container in self.config['containers']:
      base = self.config['containers'][container]['base']
      ports = None
      if ('ports' in self.config['containers'][container]):
        ports = self.config['containers'][container]['ports']
        
      #BaseContainer(base)
      self.log.info('Building container: %s using base template %s', container, base)
      build = TestContext(container, base_image=base, ports=ports)
      build.build()

      self.containers[container] = build
      
  def destroy(self):
    for container in self.containers:
      self.log.info('Destroying container: %s', container)      
      self.containers[container].destroy()
      
  def highstate(self):
    for container in self.containers:
      self.log.info('Running highstate on container: %s', container)      
      self.containers[container].highstate()
    
  def dump(self):
    result = {}
    result['containers'] = {}
    for container in self.containers:
      origin = self.containers[container]
      output = result['containers'][container] = {}
      output['image_id'] = str(origin.image_id)
      output['container_id'] = str(origin.container_id)
      if (origin.ports):
        output['ports'] = {}
        for port in origin.ports:
          public_port = origin.docker_client.port(origin.container_id, str(port))
          output['ports'][port] = str(public_port)

      str(self.containers[container].container_id)

    # TODO, change the YAML Dumper used here to be safe
    return yaml.dump(result)

  def _setupLogging(self):
    self.log = logging.getLogger('salttest')
    self.log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)-10s %(message)s")
    filehandler = logging.FileHandler('salttest.txt', 'w')
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)
    self.log.addHandler(filehandler)

class TestContext:
  def __init__(self, test_name, base_image=None, minion_config=None, top_state=None, ports=None):
    self.log = logging.getLogger('salttest')

    self.test_name = test_name
    self.build_tag = test_name + '-' + str(os.getpid())
    self.docker_client = docker.Client()
    self.salt_client = salt.client.LocalClient()
    self.minion_config = minion_config
    self.top_state = top_state
    self.ports = ports
    self.base_image = 'salt-minion-precise'
    if (base_image):
      self.base_image = base_image

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
    output, error = subprocess.Popen(['salt-key', '-y', '-d', self.build_tag], stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    
    self.docker_client.stop(self.container_id)
    self.docker_client.remove_image(self.build_tag)

  def _build_container(self):
    # Generate the docker build profile
    dockerfile = """FROM %s
    MAINTAINER Kimbro Staken "kstaken@kstaken.com"

    CMD ["salt-minion"]

    RUN echo %s > /etc/salt/minion
    """

    minionconfig = '\"master: 172.16.42.1\\nid: %s\"' % self.build_tag
    
    self.log.info("Building container with minionconfig: %s", minionconfig)
    # Build the container
    result = self.docker_client.build((dockerfile % (self.base_image, minionconfig)).split('\n'))
    self.image_id = result[0]
    
    # Tag the container with the test name
    self.docker_client.tag(self.image_id, self.build_tag)
    self.log.info('Container registered with tag: %s', self.build_tag)      

  def _start_container(self):
    # Start the container
    self.container_id = self.docker_client.create_container(self.image_id, 'salt-minion', 
      detach=True, ports=self.ports, hostname=self.build_tag)['Id']
    self.docker_client.start(self.container_id)
    self.log.info('Container started: %s', self.build_tag)      

  def _accept_keys(self):
    # Give the minion a chance to connect
    #time.sleep(5)
    command = ['salt-key', '-l', 'un']
    output = ''
    while (self.build_tag not in output):
      output, error = subprocess.Popen(command, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    
    # Accept the minion keys
    subprocess.Popen(['salt-key', '-y', '-a', self.build_tag], stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    self.log.info('Salt Minion key accepted for: %s', self.build_tag)      

  def _verify_minion(self):
    # run a test ping
    max = 20
    while len(self.salt_client.cmd(self.build_tag, 'test.ping')) == 0 and max > 0:
      max = max - 1      
      self.log.info('Waiting for minion to respond to ping on: %s Will attempt %d more times', self.build_tag, max)      
      time.sleep(1)

    if (len(self.salt_client.cmd(self.build_tag, 'test.ping')) == 0):
      self.log.error('Failed to ping the minion for: %s', self.build_tag)
      sys.exit(1) # <--- this is problematic
      
    self.log.info('Minion for %s responded to ping', self.build_tag)
        
  def _setup_states(self):
    # Setup the salt tree.
    
    # TODO: get rid of these hard coded paths
    try:
      os.remove('/srv/salt/' + self.test_name)
    except:
      True

    state_path = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), '..', self.test_name)    
    os.symlink(state_path, '/srv/salt/' + self.test_name)

    # replace top.sls
    top_sls = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'top.sls')
    os.remove('/srv/salt/top.sls')
    os.symlink(top_sls, '/srv/salt/top.sls')

class BaseContainer:
  def __init__(self, container_name):
    self.log = logging.getLogger('salttest')
    self.log.info('Building base container: %s - This may take a while', container_name)      
    
    template = os.path.join(os.path.dirname(salttest.__file__), 'docker', container_name + '.docker')
    self.dockerfile = open(template, 'r').readlines()
    self.docker_client = docker.Client()
    self.container_name = container_name
    print self.dockerfile
    #sys.exit(1)
    self.build()

  def build(self):
    # Build the container
    result = self.docker_client.build(self.dockerfile)
    self.image_id = result[0]

    # Tag the container with the test name
    self.docker_client.tag(self.image_id, self.container_name)
    self.log.info('Base container registered with tag: %s', self.container_name)      

  def destroy(self):
    self.log.info('Cleaning up base container: %s', self.container_name)      
    self.docker_client.remove_image(self.container_name)
