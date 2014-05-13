#!/bin/bash

http_code=''
sudo service cookcountyjail restart
echo `date`
while $http_code != "201";do
  http_code=`curl -o /dev/null --silent --head --write-out '%{http_code}\n' "http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=json&limit=0&booking_date__exact=2014-03-15"`
done
echo `date`
