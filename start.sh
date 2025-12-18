#!/bin/bash

echo "proxy_port: $PROXY_PORT"
echo "target_ip: $TARGET_IP"
echo "target_port: $TARGET_PORT"

/opt/dbproxy/main --proxy_port="$PROXY_PORT" --target_ip="$TARGET_IP" --target_port="$TARGET_PORT"
