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
    '%s?format=json&limit=0&discharge_date_earliest__gt=%%s&discharge_date_earliest__lt=%%s' % COOK_COUNTY_INMATE_API
NOT_DISCHARGED_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__lte=%%s&discharge_date_earliest__isnull=True' %\
    COOK_COUNTY_INMATE_API
DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE  = \
    '%s?format=json&limit=0&booking_date__lt=%%s&discharge_date_earliest__gt=%%s' % COOK_COUNTY_INMATE_API

class CcjApiV1:

    def __init__(self):
        pass

    def booked_left(self, date_to_fetch):
        booked_inmates_cmd = BOOKING_DATE_URL_TEMPLATE % date_to_fetch
        booked_inmates_response = requests.get(booked_inmates_cmd)
        assert booked_inmates_response.status_code == 200
        day_before = str(datetime.strptime(date_to_fetch, '%Y-%m-%d').date() - timedelta(1))
        day_after = str(datetime.strptime(date_to_fetch, '%Y-%m-%d').date() + timedelta(1))
        left_inmates_cmd = LEFT_DATE_URL_TEMPLATE % (day_before, day_after)
        left_inmates_response = requests.get(left_inmates_cmd)
        assert left_inmates_response.status_code == 200
        booked_inmates = loads(booked_inmates_response.text)
        inmates = self._parseJSON(copy(booked_inmates['objects']))
        left_inmates = loads(left_inmates_response.text)
        inmates.extend(self._parseJSON(left_inmates['objects']))
        return inmates

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
        not_discharged_cmd = NOT_DISCHARGED_URL_TEMPLATE % starting_date
        not_discharged_response = requests.get(not_discharged_cmd)
        assert not_discharged_response.status_code == 200
        day_before = str(datetime.strptime(starting_date, '%Y-%m-%d').date() - timedelta(1))
        discharged_on_or_after_start_date_command = \
            DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE % (starting_date, day_before)
        discharged_response = requests.get(discharged_on_or_after_start_date_command)
        assert discharged_response.status_code == 200
        not_discharged_response = loads(not_discharged_response.text)
        inmates = self._parseJSON(copy(not_discharged_response['objects']))
        discharged_response = self._parseJSON(loads(discharged_response.content))
        inmates.extend(discharged_response['objects'])
        return inmates
