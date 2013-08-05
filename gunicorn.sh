#!/bin/bash
set -e
PROJECT_DIR=/home/ubuntu/apps/cookcountyjail
LOGFILE=/home/ubuntu/logs/cookcountyjail.log
LOGDIR=$(dirname $LOGFILE)
export CCJ_PRODUCTION=1
export CACHE_TTL=86400
NUM_WORKERS=4
TIMEOUT=240

USER=ubuntu
GROUP=ubuntu
cd $PROJECT_DIR
source /home/ubuntu/.virtualenvs/cookcountyjail/bin/activate
exec gunicorn_django -w $NUM_WORKERS \
    --user=$USER --group=$GROUP --log-level=debug \
    --timeout=$TIMEOUT --log-file=$LOGFILE 2>>$LOGFILE
