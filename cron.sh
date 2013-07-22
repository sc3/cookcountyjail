#!/bin/bash
export CCJ_PRODUCTION=1
echo "Cook County Jail scraper started at `date`"
source /home/ubuntu/.virtualenvs/cookcountyjail/bin/activate
python /home/ubuntu/apps/cookcountyjail/manage.py scrape_inmates -d
echo "Cook County Jail scraper finished at `date`"
echo "Restarting nginx at `date`"
sudo service nginx restart
curl --header "clear-cache: 1" http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=json&limit=0
curl --header "clear-cache: 1" http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=csv&limit=0
curl --header "clear-cache: 1" http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=jsonp&limit=0&callback=processJSONP