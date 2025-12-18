#!/bin/bash


repo="dbproxy"
tag="v1"

docker rmi ${repo}:${tag}

docker build -t ${repo}:${tag} .

