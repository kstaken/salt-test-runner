salt-test-runner
================

Experimental salt stack module and state testing using Docker

Status: Basic multi-node environments and tests work in rudimentary fashion but I've decided to break out the docker container management into a separate project called dockermix. Currently salt states have problems with the minimal enironments of docker containers and you can't currently run init under docker. There is patch waiting merge. 

Provide a distributed test environment for salt stack modules and states that runs within a single VM.

Requires: Salt Stack & Docker 

Build a docker template with the salt-minion installed.

    docker build -t salt-minion-precise - < salttest/docker/salt-minion-precise.docker

That container can then be executed by running, but the tests will handle container setup automatically.
    
    docker run -d salt-minion

For test execution run as user that can run the salt command.

    python example_test/test/test_init.py
    
Limitations of testing with docker
==================================

Container based system doesn't have any control over the kernel and does not run standard OS init process in most cases. This will vary depending on the base container you start from but since docker is intended to run a single command per container the images tend to be light.

