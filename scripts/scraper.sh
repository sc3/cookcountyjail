#!/bin/bash

echo "Cook County Jail API v1.0 scraper v2.0 started at `date`"

# set path to include /usr/local/bin so needed programs are available
export PATH=$PATH:/usr/local/bin

# Indicate that Production Database is to be used
export CCJ_PRODUCTION=1

# bind in virtualev settings
source ${HOME}/.virtualenvs/cookcountyjail/bin/activate

MANAGE='python '${HOME}'/apps/cookcountyjail/manage.py'
INMATE_API='http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate/'
DB_BACKUPS_DIR=${HOME}/website/1.0/db_backups
DB_BACKUP_FILE=cookcountyjail-$(date +%Y-%m-%d).json

SCRAPER_OPTIONS=--verbose

${MANAGE} ng_scraper ${SCRAPER_OPTIONS}

echo "Cook County Jail scraper finished scrapping at `date`"

echo "Generating summaries - `date`"
${MANAGE} generate_summaries

echo "Priming the cache - `date`"
sudo -u www-data find /var/www/cache -type f -delete
time curl -v -L -G -s -o/dev/null -d "format=jsonp&callback=processJSONP&limit=0" ${INMATE_API}
time curl -v -L -G -s -o/dev/null -d "format=csv&limit=0" ${INMATE_API}
time curl -v -L -G -s -o/dev/null -d "format=json&limit=0" ${INMATE_API}

echo "Dumping database for `date`"
${MANAGE} dumpdata countyapi > ${DB_BACKUPS_DIR}/${DB_BACKUP_FILE}
(cd ${DB_BACKUPS_DIR} && gzip ${DB_BACKUP_FILE} && ln -sf ${DB_BACKUP_FILE}.gz latest.json.gz)

echo "Restart gunicorn servers for better user experience."
sudo service cookcountyjail restart

echo "Cook County Jail scraper V1.0 finished at `date`"
