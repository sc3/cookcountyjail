
import httpretty
from random import randint
from helpers import STARTING_DATE
from json import dumps

from scripts.ccj_api_v1 import CcjApiV1, BOOKING_DATE_URL_TEMPLATE, LEFT_DATE_URL_TEMPLATE, COOK_COUNTY_INMATE_API


class Test_CcjV1:

    @httpretty.activate
    def test_booked_left(self):
        booked_cmd = BOOKING_DATE_URL_TEMPLATE % STARTING_DATE
        expected_booked_value = ['booked value is %d' % randint(0, 25)]
        left_cmd = LEFT_DATE_URL_TEMPLATE % STARTING_DATE
        expected_left_cmd = ['left value is %d' % randint(0, 25)]

        expected = expected_booked_value + expected_left_cmd

        ccj_api_requests = {}
        def fulfill_ccj_api_request(method, uri, headers):
            assert uri == booked_cmd or uri == left_cmd
            if uri == booked_cmd:
                ccj_api_requests['booked_cmd'] = True
                response = expected_booked_value
            else:
                ccj_api_requests['left_cmd'] = True
                response = expected_left_cmd
            return 200, headers, dumps(response)

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_INMATE_API,
                               body=fulfill_ccj_api_request)

        booked_left = CcjApiV1().booked_left(STARTING_DATE)

        assert ccj_api_requests['booked_cmd'] and ccj_api_requests['left_cmd']
        assert booked_left == expected
