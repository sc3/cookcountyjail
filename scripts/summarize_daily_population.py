#
# Fetches the Daily Poulation values for a date
# and summarizes population changes for it.
#

import requests
from json import loads
from ccj.models.daily_population import DailyPopulation
from ccj.config import get_dpc_path


class SummarizeDailyPopulation:
    def _booked_males_as(self, response):
        return len(loads(response.text)['objects'])

    def date(self, date):
        race = 'AS'
        gender = 'M'
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        get_cmd = '%s?format=json&limit=0&race=%s&gender=%s&booking_date=%s' % \
            (county_inmate_api, race, gender, date)
        response = requests.get(get_cmd)
        assert response.status_code == 200
        dpc = DailyPopulation(get_dpc_path())
        with dpc.writer() as f:
            f.store({'date': date,
                     'booked_males_as': self._booked_males_as(response)})
