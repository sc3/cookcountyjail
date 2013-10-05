#!/bin/bash

# set path to include /usr/local/bin so need programs are available
export PATH=$PATH:/usr/local/bin

# Indicate that Production Database is to be used
export CCJ_PRODUCTION=1

# bind in virtualev settings
source ${HOME}/.virtualenvs/cookcountyjail/bin/activate

echo "Cook County Jail scraper started at `date`"

#
# Parallel execution is limited by the number of database connections.
# For Postgres the default number is 20, however a number of these are
# reserved. Increasing the number of database connections allowed means
# the number of parallel processes can increase.
#
# Expermintation has found that 13 is the optimal amount for Postgres
# connections, however on the cookcountyjail.recoveredfactory.net as
# of 2013-07-25 when run with 13, 3 of the processes are starved, so 10
# is the maximum that can effectively
NUMBER_PARALLEL_PROCESSES=10
#
# The order of parallel execution affects the over all time here is a sample of
# the numer of records per Letter of the alphabet ordered from largest to smallest:
# S   1020
# M   989
# B   952
# W   930
# C   845
# H   795
# R   660
# J   632
# G   582
# P   485
# D   454
# L   450
# T   449
# A   399
# F   298
# K   194
# E   187
# N   148
# V   148
# O   145
# Y   41
# I   40
# Z   38
# Q   20
# U   19
# X   0
#
# Shortest execution time comes from executing the largest name groups first in order
# of largest to smallest.

for x in S M B W C H R J G P D L T A F K E N V O Y I Z Q U X;do
    echo "python /home/ubuntu/apps/cookcountyjail/manage.py scrape_inmates --search" $x
done  | parallel -j $NUMBER_PARALLEL_PROCESSES

# now check for any inmates entered into system yesterday but not in alphabetical listsing
python /home/ubuntu/apps/cookcountyjail/manage.py look_for_missing_inmates -y

# now find inamtes no longer in system and mark them as being discharged
python /home/ubuntu/apps/cookcountyjail/manage.py generate_search_for_discharged_inmates_cmds | parallel -j $NUMBER_PARALLEL_PROCESSES

echo "Cook County Jail scraper finished scrapping at `date`"

echo "Generating summaries - `date`"
python /home/ubuntu/apps/cookcountyjail/manage.py generate_summaries

echo "Priming the cache - `date`"
sudo -u www-data find /var/www/cache -type f -delete
time curl -v -L -G -s -o/dev/null -d "format=jsonp&callback=processJSONP&limit=0" http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate/
time curl -v -L -G -s -o/dev/null -d "format=csv&limit=0" http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate/
time curl -v -L -G -s -o/dev/null -d "format=json&limit=0" http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate/

echo "Cook County Jail scraper finished at `date`"

echo "Dumping database for `date`"
python /home/ubuntu/apps/cookcountyjail/manage.py dumpdata countyapi > $HOME/backup/cookcountyjail-$(date +%Y-%m-%d).json
ln -sf $HOME/backup/{cookcountyjail-$(date +%Y-%m-%d),latest}.json
