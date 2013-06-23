salt-test-runner
================

Experimental salt stack module and state testing using Docker

Status: basic container running with salt-minion under docker

Provide a distributed test environment for salt stack modules and states that runs within a single VM.

Requires: Salt Stack & Docker 

Build a docker template with the salt-minion installed.

    docker build -t salt-minion - < salt-minion.docker

Container can then be executed by running
    
    docker run -d salt-minion

For test execution run

    python test-runner.py
    
Limitations of testing with docker
==================================

Container based system doesn't have any control over the kernel and does not run standard OS init process in most cases. This will vary depending on the base container you start from but since docker is intended to run a single command per container the images tend to be light.

