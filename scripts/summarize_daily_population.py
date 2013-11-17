#
# Fetches the Daily Poulation values for a date
# and summarizes population changes for it.
#

import requests
from json import loads
from ccj.models.daily_population import DailyPopulation
from ccj.config import get_dpc_path


class SummarizeDailyPopulation:

    def __init__(self):
        self.inmate_api = 'http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=json&limit=1'
        self.qualities = {
            'M': 'males',
            'AS': 'as',
            'booked': 'booked'
        }

    def count(self, response):
        return loads(response.text)['meta']['total_count']


    def fetch_count(self, date, gender, status, race):
        get_url = self.inmate_api

        if status == 'booked':
            get_url += '&booking_date__exact=%s' % date

        # have to use gte and lte to get left, because the discharge
        # date object is never exactly what you want
        # if status == 'left':
        #    get_url += '&discharge_date_earliest__gte=%s' % date
        #    get_url += '&discharge_date_earliest__lte=%s' % date + 1

        get_url += '&gender=%s&race=%s' % (gender, race)

        response = requests.get(get_url)
        assert response.status_code == 200
        return self.count(response)


    def write_counts(self, data):
        dpc = DailyPopulation(get_dpc_path())
        with dpc.writer() as f:
            f.store(data)


    def serialize(self, gender, status, race):
        return (self.qualities[gender] + '_' 
                + self.qualities[status] + '_'
                + self.qualities[race])


    def summarize(self, date):
        data = {
            'date': date
        }
        gender = 'M'
        status = 'booked'
        race = 'AS'
        c = self.fetch_count(date, gender, status, race)
        s = self.serialize(gender, status, race)
        data[s] = c
        self.write_counts(data)

