#
# Tests the program that generates the Starting POpulation Counts
#

import httpretty
from json import dumps

# select count(*) from countyapi_countyinmate
#   where booking_date < '2013-07-21' and
#   (discharge_date_earliest is null or
#    discharge_date_earliest >= '2013-07-21');

STARTING_DATE = '2013-07-22'


class Test_StartingPopulationCounts:

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    @httpretty.activate
    def test_build_starting_population_count(self):
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        not_discharged_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__equal=null' % \
            (county_inmate_api, STARTING_DATE)
        discharged_after_start_date_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__gte=%s' % \
            (county_inmate_api, STARTING_DATE)
        number_of_asians_booked = randint(0, 17)
        expected = [{'date': date, 'booked_males_as': '%d' % number_of_asians_booked}]

        def get_no_discharged_command_request(method, uri, headers):
            assert uri == not_discharged_command
            response = {
                'meta': {},
                'objects': [{} for x in range(0, number_of_asians_booked)]
            }
            return (200, headers, dumps(response))

        def get_discharged_after_start_date_command_request(method, uri, headers):
            assert uri == discharged_after_start_date_command
            response = {
                'meta': {},
                'objects': [{} for x in range(0, number_of_asians_booked)]
            }
            return (200, headers, dumps(response))

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=get_no_discharged_command_request)

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=get_discharged_after_start_date_command_request)

        SummarizeDailyPopulation().buld_starting_population(STARTING_DATE)

        last_request = httpretty.last_request()
        assert last_request.method == "GET"
        assert self.dpc.query() == expected
