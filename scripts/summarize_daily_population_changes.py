#
# Fetches the Daily Poulation values for a date
# and summarizes population changes for it.
#

import requests
from json import loads
from ccj.models.daily_population_changes import DailyPopulationChanges
from ccj.config import get_dpc_path


class SummarizeDailyPopulationChanges:
    def _booked_males_as(self, response):
        return len(loads(response.text)['objects'])

    def date(self, date):
        race = 'AS'
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        get_cmd = '%s?format=json&limit=0&race=%s&booking_date__exact=%s' % \
            (county_inmate_api, race, date)
        response = requests.get(get_cmd)
        dpc = DailyPopulationChanges(get_dpc_path())
        with dpc.writer() as f:
            f.store({'date': date,
                     'booked_males_as': self._booked_males_as(response)})
