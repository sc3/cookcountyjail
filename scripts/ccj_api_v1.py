#
# Used to extract information from Cook Count Jail at Recovered Factory via the 1.0 API
#

import requests
from json import loads

COOK_COUNTY_URL = 'http://cookcountyjail.recoveredfactory.net'
COOK_COUNTY_INMATE_API = '%s/api/1.0/countyinmate' % COOK_COUNTY_URL
BOOKING_DATE_URL_TEMPLATE = '%s?format=json&limit=0&booking_date__exact=%%s' % COOK_COUNTY_INMATE_API
LEFT_DATE_URL_TEMPLATE = '%s?format=json&limit=0&discharge_date_earliest__exact=%%s' % COOK_COUNTY_INMATE_API


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
        return loads(booked_inmates_response.text) + loads(left_inmates_response.text)
