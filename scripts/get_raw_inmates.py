"""
update_from_raw_inmates.py

When we run the scraper it saves all it's data in a file.
The file is in a directory structured as followed

/ - root
  ...
  /2013 - records for 2013
    01-01.csv - records for January 1st
    ...
    12-25.csv - records for December 25th
  /2014
    ... - records for 2014
  ...

So for everyday a new csv file is created in a directory
for it's corresponding year. We download these files
and update our database. The format is:

/<year>
  <MM>-<DD>.csv

More about the actual files at:
https://docs.google.com/document/d/1mgC8HLHHP4qvHR-jN6GQX04abiZkJp2mNffEicCIjuw/

"""


import csv, requests
from datetime import date

RAW_INMATES_ROOT = "http://cookcountyjail.recoveredfactory.net/raw_inmate_data/%s/%s-%s.csv"

def get_data(desired_date):
    """
    Gets the data for a date from the server.

    :param desired_date: a date instance
    :return: the raw content
    """
    # TODO: refactor, I'm sure we already do a lot of this

    year, month, day = desired_date.strftime('%Y-%m-%d').split('-')
    r = requests.get(RAW_INMATES_ROOT % (year, month, day))

    if r.status_code == requests.codes.ok:
        return r.content
    else:
        raise BaseException('Something went wrong while making '
                            'the request for %s-%s-%s' % (year, month, day))

def get_csv_data(desired_date):
    """
    A csv dict reader object from the date.

    :param desired_date: a date instance
    :return: csv reader with inmate data for desired date
    """
    return csv.DictReader(get_data(desired_date).split('\n'))



