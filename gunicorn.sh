#!/bin/bash
set -e
PROJECT_DIR=/home/ubuntu/website/2.0/websites/active
LOGFILE=/home/ubuntu/logs/cookcountyjail-v2.0.log
LOGDIR=$(dirname $LOGFILE)
export CCJ_PRODUCTION=1
export CACHE_TTL=86400
NUM_WORKERS=4
TIMEOUT=240
USER=ubuntu
GROUP=ubuntu
cd $PROJECT_DIR
source /home/ubuntu/.virtualenvs/cookcountyjail_2.0-dev/bin/activate
gunicorn -w $NUM_WORKERS -b 127.0.0.1:8080 \
 --log-level=debug --user=$USER --group=$GROUP \
 --timeout=$TIMEOUT --log-file=$LOGFILE \
 ccj.app:app 2>>$LOGFILE
