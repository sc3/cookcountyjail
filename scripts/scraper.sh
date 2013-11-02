#!/bin/bash

#
# This runs the scapper job for the 2.0 API.
# This is intended to be called as a cron job.
#

echo "Cook County Jail 2.0 API scraper started at `date`"

# set path to include /usr/local/bin so need programs are available
export PATH=$PATH:/usr/local/bin

# Indicate that Production Database is to be used
export CCJ_PRODUCTION=1

# bind in virtualev settings
source ${HOME}/.virtualenvs/cookcountyjail/bin/activate

PATH_TO_2_0_WEBSITE_SCRIPTS=${HOME}/website/2.0/websites/activate/scripts

cd ${PATH_TO_2_0_WEBSITE_SCRIPTS}
./scraper.py

echo "Cook County Jail 2.0 API scraper finished at `date`"
