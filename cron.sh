#!/bin/bash
export CCJ_PRODUCTION=1
echo "Cook County Jail scraper started at `date`"
source /home/ubuntu/.virtualenvs/cookcountyjail/bin/activate
python /home/ubuntu/apps/cookcountyjail/manage.py scrape_inmates -d
echo "Cook County Jail scraper finished at `date`"
echo "Restarting nginx at `date`"
sudo service nginx restart
