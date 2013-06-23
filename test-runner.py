#!/usr/bin/env python

import docker
import os, sys, time
import salt.client
import salt.key
from subprocess import call
from subprocess import Popen

# Generate the docker build profile
dockerfile = """FROM salt-minion
MAINTAINER Kimbro Staken "kstaken@kstaken.com"

CMD ["salt-minion"]

RUN echo %s > /etc/salt/minion
"""

build_tag = "test-name-" + str(os.getpid())

minionconfig = "\"master: 172.16.42.1\\nid: %s\"" % build_tag

client = docker.Client()

# Build the container
result = client.build((dockerfile % minionconfig).split('\n'))
image_id = result[0]

client.tag(image_id, build_tag)

# Start the container
result = client.create_container(image_id, "salt-minion", detach=True)
client.start(result['Id'])

# Give the minion a chance to connect
time.sleep(5)

# Accept the minion keys
ret = call(["/usr/local/bin/salt-key", "-y", "-a", build_tag])
print ret
#print call(["salt", build_tag, "test.ping"])

# run a test ping
client = salt.client.LocalClient()
max = 20
while len(client.cmd(build_tag, 'test.ping')) == 0 and max > 0:
  print "Waiting for minion to be available " + str(max)
  max = max - 1
  time.sleep(1)

print client.cmd(build_tag, 'test.ping')