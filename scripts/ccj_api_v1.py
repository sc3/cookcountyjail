#
# Used to extract information from Cook Count Jail at Recovered Factory via the 1.0 API
#

import requests
from json import loads
from copy import copy

COOK_COUNTY_URL = 'http://cookcountyjail.recoveredfactory.net'
COOK_COUNTY_INMATE_API = '%s/api/1.0/countyinmate' % COOK_COUNTY_URL
BOOKING_DATE_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__exact=%%s' % COOK_COUNTY_INMATE_API
LEFT_DATE_URL_TEMPLATE = '%s?format=json&limit=0&discharge_date_earliest__exact=%%s' % COOK_COUNTY_INMATE_API
NOT_DISCHARGED_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__lt=%%s&discharge_date_earliest__isnull=True' %\
    COOK_COUNTY_INMATE_API
DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE  = \
    '%s?format=json&limit=0&booking_date__lt=%%s&discharge_date_earliest__gte=%%s' % COOK_COUNTY_INMATE_API

class CcjApiV1:

    def __init__(self):
        pass

    def booked_left(self, date_to_fetch):
        booked_inmates_cmd = BOOKING_DATE_URL_TEMPLATE % date_to_fetch
        booked_inmates_response = requests.get(booked_inmates_cmd)
        assert booked_inmates_response.status_code == 200
        left_inmates_cmd = LEFT_DATE_URL_TEMPLATE % date_to_fetch
        left_inmates_response = requests.get(left_inmates_cmd)
        assert left_inmates_response.status_code == 200
        return self._parseJSON(loads(booked_inmates_response.text) + loads(left_inmates_response.text))

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
        discharged_on_or_after_start_date_command = \
            DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE % (starting_date, starting_date)
        discharged_response = requests.get(discharged_on_or_after_start_date_command)
        assert discharged_response.status_code == 200
        not_discharged_response = loads(not_discharged_response.text)
        inmates = self._parseJSON(copy(not_discharged_response['objects']))
        discharged_response = self._parseJSON(loads(discharged_response.content))
        inmates.extend(discharged_response['objects'])
        return inmates
