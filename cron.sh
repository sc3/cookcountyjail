#!/bin/bash

echo "Cook County Jail scraper controller started at `date`"

LOG_FILE_SUFFIX=cookcountyjail-scraper-$(date +%Y-%m-%d).log
V1_LOG_FILE=v1-${LOG_FILE_SUFFX}
V2_LOG_FILE=v2-${LOG_FILE_SUFFX}

echo "Starting V1.0 Cook County Jail scraper at `date`"
'${HOME}'/apps/cookcountyjail/scripts/scraper.sh 2>&1 > '${HOME}'/logs/${V1_LOG_FILE}

echo "Starting V2.0 Cook County Jail scraper at `date`"
'${HOME}'/website/2.0/websites/active/scripts/scraper.sh 2>&1 > '${HOME}'/logs/${V2_LOG_FILE}

echo "Cook County Jail scraper controller finished at `date`"
