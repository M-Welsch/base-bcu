#!/bin/bash

docker build -t max/rsync_daemon rsync_daemon
docker build -t max/nginx nginx_router
docker build -t max/testfile_generator testfile_generator
docker pull corpusops/sshd

