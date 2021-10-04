#!/bin/bash

LOG_DIR=/var/log
TZ=Asia/Tokyo
IMAGER_NAME=bybit-fr-bot
CONTAINER_NAME=$IMAGE_NAME

docker stop frbot > /dev/null 2>&1

docker rm frbot > /dev/null 2>&1

docker run \
  -d \
  -v $LOG_DIR:/home/root/logs \
  -e TZ=$TZ \
  --name $CONTAINER_NAME \
  $IMAGER_NAME:latest
