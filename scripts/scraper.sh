#!/bin/bash

echo "Cook County Jail API v1.0 scraper v2.0 started at `date`"

# set path to include /usr/local/bin so needed programs are available
export PATH=$PATH:/usr/local/bin

# Indicate that Production Database is to be used
export CCJ_PRODUCTION=1

# Specify the location of django settings 
export DJANGO_SETTINGS_MODULE=countyapi.settings

# Set some constants
PROJECT_DIR=${HOME}'/apps/cookcountyjail'
SCRIPTS_DIR=${PROJECT_DIR}'/scripts'
MANAGE='python '${PROJECT_DIR}'/manage.py'
INMATE_API='http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate/'
DB_BACKUPS_DIR=${HOME}/website/1.0/db_backups
DB_BACKUP_FILE=cookcountyjail-$(date +%Y-%m-%d).json
SCRAPER_OPTIONS='--verbose'
export CCJ_RAW_INMATE_DATA_BUILD_DIR=${HOME}'/website/scraper/raw_inmate_data'

# Bind in virtualenv settings
source ${HOME}/.virtualenvs/cookcountyjail/bin/activate

# Actually run the scraper
python ${SCRIPTS_DIR}/ng_scraper.py ${SCRAPER_OPTIONS}

echo "Cook County Jail scraper finished scraping at `date`"

# TODO: port the audit_db command to v2
AUDIT_RESULT=$(${MANAGE} audit_db)
echo ${AUDIT_RESULT} 

# TODO: fix this broken notification code
# If problems found, send notification
# echo ${AUDIT_RESULT} | grep -q 'in_jail'
# if [ $? -eq 0 ];then
#     echo ${AUDIT_RESULT} | python ${HOME}/apps/cookcountyjail/scripts/notify.py
# fi

# TODO: take this out, or replace it with v2 summaries
echo "Generating summaries - `date`"
${MANAGE} generate_summaries

echo "Priming the cache - `date`"
sudo -u www-data find /var/www/cache -type f -delete
time curl -v -L -G -s -o/dev/null -d "format=jsonp&callback=processJSONP&limit=0" ${INMATE_API}
time curl -v -L -G -s -o/dev/null -d "format=csv&limit=0" ${INMATE_API}
time curl -v -L -G -s -o/dev/null -d "format=json&limit=0" ${INMATE_API}

# TODO: port the dumpdata command
echo "Dumping database for `date`"
${MANAGE} dumpdata countyapi > ${DB_BACKUPS_DIR}/${DB_BACKUP_FILE}
(cd ${DB_BACKUPS_DIR} && gzip ${DB_BACKUP_FILE} && ln -sf ${DB_BACKUP_FILE}.gz latest.json.gz)

echo "Restart gunicorn servers for better user experience."
sudo service cookcountyjail restart

# now wait until server is back up and running before terminating the scraper
http_code='0'
while [ "$http_code" != "301" ];do
  http_code=`curl -o /dev/null --silent --head --write-out '%{http_code}\n' "http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=json&limit=0&booking_date__exact=2014-03-15"`
done

echo "Cook County Jail scraper V1.0 finished at `date`"
