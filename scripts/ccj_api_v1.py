#
# Used to extract information from Cook Count Jail at Recovered Factory via the 1.0 API
#

import sys
import requests
from datetime import datetime
from json import loads
from copy import copy


#
# The field booking_date is date field and is matched by booking_date__exact
# The field discharge_date_earliest is a datetime value. To match it the start and end times of
# the day are calculated and then discharge_date_earliest__gte and
# discharge_date_earliest__lte are used to match against the respective times.
#

COOK_COUNTY_URL = 'http://cookcountyjail.recoveredfactory.net'
COOK_COUNTY_INMATE_API = '%s/api/1.0/countyinmate' % COOK_COUNTY_URL
BOOKING_DATE_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__exact=%%s' % COOK_COUNTY_INMATE_API
LEFT_DATE_URL_TEMPLATE = \
    '%s?format=json&limit=0&discharge_date_earliest__gte=%%s&discharge_date_earliest__lte=%%s' % COOK_COUNTY_INMATE_API
NOT_DISCHARGED_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__lte=%%s&discharge_date_earliest__isnull=True' %\
    COOK_COUNTY_INMATE_API
DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE = \
    '%s?format=json&limit=0&booking_date__lt=%%s&discharge_date_earliest__gte=%%s' % COOK_COUNTY_INMATE_API


# All inmates housing history - housinghistory/?inmate=2013-0120138
# Housing location info - housinglocation/?housing_location=C%20SHIPMENT&format=json
# All housing history changes for a day - housinghistory/?format=json&limit=0&housing_date_discovered__exact=2013-12-10

DATE_FORMAT = '%Y-%m-%d'
OBJECTS = 'objects'


class CcjApiV1:

    def __init__(self):
        self._booked_inmates = {}
        self._left_inmates = {}

    def booked_inmates(self, start_of_day):
        if start_of_day not in self._booked_inmates:
            booked_inmates_cmd = BOOKING_DATE_URL_TEMPLATE % start_of_day
            self._booked_inmates[start_of_day] = self._fetch_json_data(booked_inmates_cmd)
        return self._booked_inmates[start_of_day]

    def booked_left(self, date_to_fetch):
        start_of_day = self._convert_to_beginning_of_day(date_to_fetch)
        end_of_day = self._convert_to_end_of_day(date_to_fetch)
        inmates = copy(self.booked_inmates(start_of_day))
        left_inmates = self.left_inmates(start_of_day, end_of_day)
        inmates.extend(left_inmates)
        return inmates

    @staticmethod
    def _convert_to_beginning_of_day(starting_date):
        starting_date_time = datetime.strptime(starting_date, DATE_FORMAT)
        return starting_date_time.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    @staticmethod
    def _convert_to_end_of_day(ending_date):
        ending_date_time = datetime.strptime(ending_date, DATE_FORMAT)
        return ending_date_time.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    def _discharged_inmates(self, starting_date_time):
        discharged_on_or_after_start_date_command = \
            DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE % (starting_date_time, starting_date_time)
        return self._fetch_json_data(discharged_on_or_after_start_date_command)

    def _fetch_json_data(self, url_to_fetch):
        try:
            the_response = requests.get(url_to_fetch)
            if the_response.status_code != 200:
                print 'failed to fetch {0}, got status code {1}'.format(
                        url_to_fetch, the_response.status_code)
                return []

        except requests.ConnectionError:
            _, exc_value, _ = sys.exc_info()
            print exc_value
            sys.exit(1)
        ccj_data = loads(the_response.text)
        return self._parse_json(ccj_data[OBJECTS])

    def left_inmates(self, start_of_day, end_of_day):
        if start_of_day not in self._left_inmates:
            left_inmates_cmd = LEFT_DATE_URL_TEMPLATE % (start_of_day, end_of_day)
            self._left_inmates[start_of_day] = self._fetch_json_data(left_inmates_cmd)
        return self._left_inmates[start_of_day]

    def _not_discharged_inmates(self, starting_date_time):
        not_discharged_cmd = NOT_DISCHARGED_URL_TEMPLATE % starting_date_time
        return self._fetch_json_data(not_discharged_cmd)

    def _parse_json(self, obj):
        if isinstance(obj, dict):
            new_obj = {}
            for key, value in obj.iteritems():
                key = str(key)
                new_obj[key] = self._parse_json(value)
        elif isinstance(obj, list):
            new_obj = []
            for value in obj:
                new_obj.append(self._parse_json(value))
        elif isinstance(obj, unicode):
            new_obj = str(obj)
        else:
            new_obj = obj
        return new_obj

    def start_population_data(self, starting_date):
        starting_date_time = self._convert_to_beginning_of_day(starting_date)
        inmates = copy(self._not_discharged_inmates(starting_date_time))
        discharged_data = self._discharged_inmates(starting_date_time)
        inmates.extend(discharged_data)
        return inmates
