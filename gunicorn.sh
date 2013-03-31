#!/bin/bash
set -e
PROJECT_DIR=/home/ubuntu/apps/cookcountyjail
LOGFILE=/home/ubuntu/logs/cookcountyjail.log
LOGDIR=$(dirname $LOGFILE)
export CCJ_PRODUCTION=1
NUM_WORKERS=2

USER=ubuntu
GROUP=ubuntu
cd $PROJECT_DIR
source /home/ubuntu/.virtualenvs/cookcountyjail/bin/activate
exec gunicorn_django -w $NUM_WORKERS \
    --user=$USER --group=$GROUP --log-level=debug \
    --log-file=$LOGFILE 2>>$LOGFILE
