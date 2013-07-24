#!/bin/bash

# set path to include /usr/local/bin so need programs are available
export PATH=PATH:/usr/local/bin

# Indicate that Production Database is to be used
export CCJ_PRODUCTION=1

echo "Cook County Jail scraper started at `date`"

#
# Parallel execution is limited by the number of database connections.
# For Postgres the default number is 20, however a number of these are reserved.
# Expermintation has found that 13 is optimal amount. Increasing the number of
# connections allowed means the number of parallel processes can increase.
NUMBER_PARALLEL_PROCESSES=13
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
python /home/ubuntu/apps/cookcountyjail/manage.py discharge_inmates
echo "Cook County Jail scraper finished at `date`"
echo "Restarting nginx at `date`"
sudo service nginx restart
