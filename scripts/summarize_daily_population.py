#
# Fetches the Daily Population values for a date
# and summarizes population changes for it.
#

import requests
from datetime import datetime, timedelta
from json import loads
from ccj.models.daily_population import DailyPopulation
from ccj.app import app
from copy import copy

STARTING_DATE = '2013-07-22'
DAY_BEFORE = str(datetime.strptime(STARTING_DATE, '%Y-%m-%d').date() - timedelta(1))

COOK_COUNTY_URL = 'http://cookcountyjail.recoveredfactory.net'
COOK_COUNTY_INMATE_API = '%s/api/1.0/countyinmate' % COOK_COUNTY_URL

RACE_COUNTS = {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0}
RACE_MAP = {'A': 'AS', 'AS': 'AS', 'B': 'BK', 'BK': 'BK', 'IN': 'IN', 'LB': 'LT', 'LT': 'LT', 'LW': 'LT', 'W': 'WH',
            'WH': 'WH'}


class SummarizeDailyPopulation:

    def __init__(self):
        self.inmate_api = 'http://cookcountyjail.recoveredfactory.net/api/1.0/countyinmate?format=json&limit=1'
        self.qualities = {
            'M': 'males',
            'AS': 'as',
            'booked': 'booked'
        }

    @staticmethod
    def _booked_males_as(response):
        return len(loads(response.text)['objects'])

    def build_starting_population(self):
        get_cmd = '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__isnull=True' % \
                  (COOK_COUNTY_INMATE_API, STARTING_DATE)
        not_discharged_response = requests.get(get_cmd)
        assert not_discharged_response.status_code == 200
        not_discharged_response = loads(not_discharged_response.content)
        discharged_after_start_date_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__gte=%s' % \
            (COOK_COUNTY_INMATE_API, STARTING_DATE, STARTING_DATE)
        discharged_response = requests.get(discharged_after_start_date_command)
        assert discharged_response.status_code == 200
        discharged_response = loads(discharged_response.content)
        inmates = copy(not_discharged_response['objects'])
        inmates.extend(discharged_response['objects'])
        population_counts = self._population_counts(inmates)
        return [
            {
                'date': DAY_BEFORE,
                'population': population_counts['population_females'] + population_counts['population_males'],
                'population_females': population_counts['population_females'],
                'population_females_as': population_counts['F']['AS'],
                'population_females_bk': population_counts['F']['BK'],
                'population_females_in': population_counts['F']['IN'],
                'population_females_lt': population_counts['F']['LT'],
                'population_females_un': population_counts['F']['UN'],
                'population_females_wh': population_counts['F']['WH'],
                'population_males': population_counts['population_males'],
                'population_males_as': population_counts['M']['AS'],
                'population_males_bk': population_counts['M']['BK'],
                'population_males_in': population_counts['M']['IN'],
                'population_males_lt': population_counts['M']['LT'],
                'population_males_un': population_counts['M']['UN'],
                'population_males_wh': population_counts['M']['WH'],
            }
        ]

    def count(self, response):
        return loads(response.text)['meta']['total_count']

    def date(self, date):
        race = 'AS'
        gender = 'M'
        get_cmd = '%s?format=json&limit=0&race=%s&gender=%s&booking_date__exact=%s' % \
                  (COOK_COUNTY_INMATE_API, race, gender, date)
        response = requests.get(get_cmd)
        assert response.status_code == 200
        return self.count(response)

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
        dpc = DailyPopulation(app.config['DPC_DIR_PATH'])
        with dpc.writer() as f:
            f.store(data)

    @staticmethod
    def _population_counts(inmates):
        counts = {'F': copy(RACE_COUNTS), 'M': copy(RACE_COUNTS), 'population_females': 0, 'population_males': 0}
        for inmate in inmates:
            race = inmate['race']
            race = RACE_MAP[race] if race in RACE_MAP else 'UN'
            counts[inmate['gender']][race] += 1
            population_field_name = 'population_females' if inmate['gender'] == 'F' else 'population_males'
            counts[population_field_name] += 1
        return counts

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
