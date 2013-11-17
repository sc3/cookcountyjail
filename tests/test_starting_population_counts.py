#
# Tests the program that generates the Starting Population Counts
#

import httpretty
from json import dumps
from random import randint
from scripts.summarize_daily_population \
    import SummarizeDailyPopulation
from helpers import discharged_null_inmate_records, discharged_on_or_after_start_date_inmate_records, \
    count_population, expected_starting_population, STARTING_DATE

# select count(*) from countyapi_countyinmate
#   where booking_date < '2013-07-22' and
#   (discharge_date_earliest is null or
#    discharge_date_earliest >= '2013-07-21');


class TestStartingPopulationCounts:

    @httpretty.activate
    def test_build_starting_population_count(self):
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        not_discharged_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__isnull=True' % \
            (county_inmate_api, STARTING_DATE)
        discharged_after_start_date_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__gte=%s' % \
            (county_inmate_api, STARTING_DATE, STARTING_DATE)
        book_not_null_inmate_records = discharged_null_inmate_records(STARTING_DATE, randint(15, 31))
        discharged_on_or_after_start_date_records = \
            discharged_on_or_after_start_date_inmate_records(STARTING_DATE, randint(21, 37))
        inmates = book_not_null_inmate_records + discharged_on_or_after_start_date_records
        population_counts = count_population(inmates)
        expected = expected_starting_population(population_counts)

        cook_county_get_count = {}

        def fulfill_countyapi_request(method, uri, headers):
            assert uri == not_discharged_command or uri == discharged_after_start_date_command
            if uri == not_discharged_command:
                cook_county_get_count['not_discharged_cmd'] = True
                response = {
                    'meta': {'total_count': len(book_not_null_inmate_records)},
                    'objects': book_not_null_inmate_records
                }
            else:
                cook_county_get_count['discharged_after_start_date_command'] = True
                response = {
                    'meta': {'total_count': len(discharged_on_or_after_start_date_records)},
                    'objects': discharged_on_or_after_start_date_records
                }

            return 200, headers, dumps(response)

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=fulfill_countyapi_request)

        starting_population = SummarizeDailyPopulation().build_starting_population()

        last_request = httpretty.last_request()
        assert last_request.method == "GET"
        assert len(cook_county_get_count) == 2
        assert starting_population == expected
