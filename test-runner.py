#!/usr/bin/env python

import docker
import os

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

# Accept the minion keys

# run a test ping