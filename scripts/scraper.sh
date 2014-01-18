#!/bin/bash

echo "Cook County Jail scraper v1.0 started at `date`"

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

#
# Parallel execution is limited by the number of database connections.
# For Postgres the default number is 20, however a number of these are
# reserved. Increasing the number of database connections allowed means
# the number of parallel processes can increase.
#
# Initial experimentation found that 13 is the optimal amount for Postgres
# connections, however on the cookcountyjail.recoveredfactory.net as
# of 2013-07-25 when run with 13, 3 of the processes are starved, so 10
# is the maximum that can effectively
NUMBER_PARALLEL_PROCESSES=10

# now find inmates no longer in system and mark them as being discharged
${MANAGE} generate_search_for_discharged_inmates_cmds | parallel -j $NUMBER_PARALLEL_PROCESSES

# Check for any inmates entered into system yesterday
${MANAGE} generate_searches_for_missing_inmates -y | parallel -j $NUMBER_PARALLEL_PROCESSES

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

echo "Cook County Jail scraper V1.0 finished at `date`"
