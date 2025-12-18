#!/bin/bash


mkdir -p /opt/dbproxy/
touch /opt/dbproxy/event.log

docker run -d -v /opt/dbproxy/event.log:/opt/dbproxy/event.log -e PROXY_PORT=3306 -e TARGET_IP=10.50.122.100 -e TARGET_PORT=4000 --net host --name pot dbproxy:v1
