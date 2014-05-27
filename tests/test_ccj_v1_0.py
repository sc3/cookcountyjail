
import httpretty
from random import randint
from helpers import STARTING_DATE, discharged_null_inmate_records, discharged_on_or_after_start_date_inmate_records
from json import dumps
from copy import copy

from scripts.ccj_api_v1 import CcjApiV1, BOOKING_DATE_URL_TEMPLATE, LEFT_DATE_URL_TEMPLATE, COOK_COUNTY_INMATE_API, \
    NOT_DISCHARGED_URL_TEMPLATE, DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE, convert_to_beginning_of_day, \
    convert_to_end_of_day


class TestCcjV1:

    @httpretty.activate
    def test_booked_left(self):
        start_of_day = STARTING_DATE
        end_of_day = STARTING_DATE
        booked_cmd = BOOKING_DATE_URL_TEMPLATE % start_of_day
        expected_booked_value = [{'booked_val': 'booked value is %d' % randint(0, 25)}]
        left_cmd = LEFT_DATE_URL_TEMPLATE % (convert_to_beginning_of_day(start_of_day),
                                             convert_to_end_of_day(end_of_day))
        expected_left_cmd = [{'left_val': 'left value is %d' % randint(0, 25)}]

        expected = copy(expected_booked_value)
        expected.extend(expected_left_cmd)

        ccj_api_requests = {}

        def fulfill_ccj_api_request(_, uri, headers):
            assert uri == booked_cmd or uri == left_cmd
            if uri == booked_cmd:
                ccj_api_requests['booked_cmd'] = True
                response = {
                    'objects': expected_booked_value
                }
            else:
                ccj_api_requests['left_cmd'] = True
                response = {
                    'objects': expected_left_cmd
                }
            return 200, headers, dumps(response)

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_INMATE_API,
                               body=fulfill_ccj_api_request)

        booked_left = CcjApiV1().booked_left(STARTING_DATE)

        assert ccj_api_requests['booked_cmd'] and ccj_api_requests['left_cmd']
        assert booked_left == expected


    @httpretty.activate
    def test_build_starting_population_count(self):
        starting_date = (STARTING_DATE)
        not_discharged_command = NOT_DISCHARGED_URL_TEMPLATE % starting_date
        discharged_on_or_after_start_date_command = \
            DISCHARGED_ON_OR_AFTER_STARTING_DATE_URL_TEMPLATE % (starting_date,
                                                                 convert_to_beginning_of_day(starting_date))
        book_not_null_inmate_records = discharged_null_inmate_records(randint(15, 31))
        discharged_on_or_after_start_date_records = \
            discharged_on_or_after_start_date_inmate_records(randint(21, 37))
        expected = book_not_null_inmate_records + discharged_on_or_after_start_date_records

        cook_county_get_count = {}

        def fulfill_county_api_request(_, uri, headers):
            assert uri == not_discharged_command or uri == discharged_on_or_after_start_date_command
            if uri == not_discharged_command:
                cook_county_get_count['not_discharged_cmd'] = True
                response = {
                    'meta': {'total_count': len(book_not_null_inmate_records)},
                    'objects': book_not_null_inmate_records
                }
            else:
                cook_county_get_count['discharged_on_or_after_start_date_command'] = True
                response = {
                    'meta': {'total_count': len(discharged_on_or_after_start_date_records)},
                    'objects': discharged_on_or_after_start_date_records
                }

            return 200, headers, dumps(response)

        httpretty.register_uri(httpretty.GET, COOK_COUNTY_INMATE_API,
                               body=fulfill_county_api_request)

        booked_left = CcjApiV1().start_population_data(STARTING_DATE)

        last_request = httpretty.last_request()
        assert last_request.method == "GET"
        assert cook_county_get_count['not_discharged_cmd'] and \
            cook_county_get_count['discharged_on_or_after_start_date_command']
        assert booked_left == expected
