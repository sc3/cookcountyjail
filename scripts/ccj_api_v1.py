#
# Used to extract information from Cook Count Jail at Recovered Factory via the 1.0 API
#

import requests
from datetime import datetime, timedelta
from json import loads
from copy import copy

#
# The fields booking_date and discharge_date_earliest both contains a datetime value. However,
# the time component of booking_value is always 00:00:00, where as for discharge_date_earliest
# the time component is set to some time during the day. This means that matching an exact date
# with tastypie requires two different approaches: for booking_date use booking_date__exact,
# for discharge_date_earliest use discharge_date_earliest__gt the day before and
# discharge_date_earliest__lt the day after.
#

COOK_COUNTY_URL = 'http://cookcountyjail.recoveredfactory.net'
COOK_COUNTY_INMATE_API = '%s/api/1.0/countyinmate' % COOK_COUNTY_URL
BOOKING_DATE_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__exact=%%s' % COOK_COUNTY_INMATE_API
LEFT_DATE_URL_TEMPLATE = \
    '%s?format=json&limit=0&discharge_date_earliest__gte=%%s&discharge_date_earliest__lte=%%s' % COOK_COUNTY_INMATE_API
NOT_DISCHARGED_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__lte=%%s&discharge_date_earliest__isnull=True' %\
    COOK_COUNTY_INMATE_API
DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE  = \
    '%s?format=json&limit=0&booking_date__lt=%%s&discharge_date_earliest__gte=%%s' % COOK_COUNTY_INMATE_API

DATE_FORMAT = '%Y-%m-%d'
OBJECTS = 'objects'


class CcjApiV1:

    def __init__(self):
        pass

    def booked_left(self, date_to_fetch):
        start_of_day = self._convert_to_beginning_of_day(date_to_fetch)
        booked_inmates_cmd = BOOKING_DATE_URL_TEMPLATE % start_of_day
        booked_inmates_response = requests.get(booked_inmates_cmd)
        assert booked_inmates_response.status_code == 200
        left_inmates_cmd = LEFT_DATE_URL_TEMPLATE % (start_of_day, self._convert_to_end_of_day(date_to_fetch))
        left_inmates_response = requests.get(left_inmates_cmd)
        assert left_inmates_response.status_code == 200
        booked_inmates = loads(booked_inmates_response.text)
        inmates = self._parseJSON(copy(booked_inmates['objects']))
        left_inmates = loads(left_inmates_response.text)
        inmates.extend(self._parseJSON(left_inmates['objects']))
        return inmates

    def _convert_to_beginning_of_day(self, starting_date):
        starting_date_time = datetime.strptime(starting_date, DATE_FORMAT)
        return starting_date_time.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    def _convert_to_end_of_day(self, ending_date):
        end_of_day = datetime.strptime(ending_date, DATE_FORMAT)
        return end_of_day.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    def _parseJSON(self, obj):
        if isinstance(obj, dict):
            newobj = {}
            for key, value in obj.iteritems():
                key = str(key)
                newobj[key] = self._parseJSON(value)
        elif isinstance(obj, list):
            newobj = []
            for value in obj:
                newobj.append(self._parseJSON(value))
        elif isinstance(obj, unicode):
            newobj = str(obj)
        else:
            newobj = obj
        return newobj

    def start_population_data(self, starting_date):
        starting_date_time = self._convert_to_beginning_of_day(starting_date)
        not_discharged_cmd = NOT_DISCHARGED_URL_TEMPLATE % starting_date_time
        not_discharged_response = requests.get(not_discharged_cmd)
        assert not_discharged_response.status_code == 200
        discharged_on_or_after_start_date_command = \
            DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE % (starting_date_time, starting_date_time)
        discharged_response = requests.get(discharged_on_or_after_start_date_command)
        assert discharged_response.status_code == 200
        inmates = self._parseJSON(copy(loads(not_discharged_response.text)[OBJECTS]))
        discharged_data = self._parseJSON(loads(discharged_response.text)[OBJECTS])
        inmates.extend(discharged_data)
        return inmates
