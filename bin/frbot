#!/bin/bash

# specify "`pwd`/logs" when running on local
LOG_DIR=/var/log

docker stop frbot > /dev/null 2>&1

docker rm frbot > /dev/null 2>&1

docker run \
  -d \
  -v $LOG_DIR:/home/root/logs \
  -e TZ=Asia/Tokyo \
  --name frbot \
  bybit-frbot:latest
