#!/usr/bin/env python

import docker
import os, sys, time
import salt.client
import salt.key
from subprocess import call
from subprocess import Popen

# Verify user can connect to salt

# Generate the docker build profile
dockerfile = """FROM salt-minion
MAINTAINER Kimbro Staken "kstaken@kstaken.com"

CMD ["salt-minion"]

RUN echo %s > /etc/salt/minion
"""

build_tag = "test-name-" + str(os.getpid())

minionconfig = "\"master: 172.16.42.1\\nid: %s\"" % build_tag

docker_client = docker.Client()

# Build the container
result = docker_client.build((dockerfile % minionconfig).split('\n'))
image_id = result[0]

docker_client.tag(image_id, build_tag)

# Start the container
container_id = docker_client.create_container(image_id, "salt-minion", detach=True)['Id']
docker_client.start(container_id)

# Give the minion a chance to connect
time.sleep(5)

# Accept the minion keys
ret = call(["/usr/bin/salt-key", "-y", "-a", build_tag])

# run a test ping
salt_client = salt.client.LocalClient()
max = 20
while len(salt_client.cmd(build_tag, 'test.ping')) == 0 and max > 0:
  print "Waiting for minion to be available " + str(max)
  max = max - 1
  time.sleep(1)

if (len(salt_client.cmd(build_tag, 'test.ping')) == 0):
  print "ERROR: Failed to ping the minion"
  sys.exit(1)
else:
  print "Minion is reachable"

# Cleanup
ret = call(["/usr/bin/salt-key", "-y", "-d", build_tag])

docker_client.stop(container_id)
docker_client.remove_image(build_tag)
