#!/bin/bash

LOG_DIR=/var/log
TZ=Asia/Tokyo
IMAGE_NAME=bybit-fr-bot
CONTAINER_NAME=$IMAGE_NAME

docker stop $CONTAINER_NAME > /dev/null 2>&1

docker rm $CONTAINER_NAME > /dev/null 2>&1

docker run \
  -d \
  -v $LOG_DIR:/home/root/logs \
  -e TZ=$TZ \
  --name $CONTAINER_NAME \
  $IMAGE_NAME:latest
