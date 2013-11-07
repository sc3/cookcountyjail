#!/usr/bin/env python

#
# This catches up the summary for Daily Population
#

from datetime import date, datetime, timedelta
from json import loads
import requests
from summarize_daily_population import SummarizeDailyPopulation


def last_date_summarized():
    cook_county_url = 'http://cookcountyjail.recoveredfactory.net/api/2.0'
    daily_population = 'daily_population'
    response = requests.get('%s/%s' % (cook_county_url,
                                       daily_population))
    if response.status_code == 200:
        dpc = loads(response.text)
        if dpc != []:
            return datetime.strptime(dpc[-1]['Date'], '%Y-%m-%d').date()
    return start_date()


def start_date():
    """
    July 21st, 2013 is when the fetch of inmate data was fixed
    so this is start date of when summarized values are good.
    """
    return date(2013, 7, 21)


def main():
    sdpc = SummarizeDailyPopulation()
    date_to_fetch = last_date_summarized()
    one_day = timedelta(1)
    yesterday = date.today() - one_day
    while date_to_fetch <= yesterday:
        sdpc.date(str(date_to_fetch))
        date_to_fetch += one_day

if __name__ == '__main__':
    main()
