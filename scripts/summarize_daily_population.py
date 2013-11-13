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


    def count(self, response):
        return loads(response.text)['meta']['total_count']


    def fetch_count(self, date, gender, status, race):
        get_cmd='%s&race=%s&gender=%s&booking_date__exact=%s' % \
            (self.inmate_api, race, gender, date)
        response = requests.get(get_cmd)
        assert response.status_code == 200
        return self.count(response)


    def write_counts(self, data):
        dpc = DailyPopulation(get_dpc_path())
        with dpc.writer() as f:
            f.store(data)