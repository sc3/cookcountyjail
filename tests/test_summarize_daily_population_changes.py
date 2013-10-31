import httpretty
from json import dumps
from random import randint
from scripts.summarize_daily_population_changes \
    import SummarizeDailyPopulationChanges


class Test_SummarizeDailyPopulationChanges:

    @httpretty.activate
    def test_summarize_dpc_for_Aian_males_booked(self):
        race = 'AS'
        date = '2013-06-01'
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        ccj_get_Asian_males_data_url = \
            '%s?format=json&limit=0&race=%s&booking_date__exact=%s' % \
            (county_inmate_api, race, date)
        daily_population_changes_url = \
            '%s/api/2.0/daily_population_changes' % cook_county_url
        number_of_asians_booked = randint(0, 17)

        def get_request(method, uri, headers):
            assert uri == ccj_get_Asian_males_data_url
            response = {
                'meta': {},
                'objects': [{} for x in range(0, number_of_asians_booked)]
            }
            return (200, headers, dumps(response))

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=get_request)

        httpretty.register_uri(httpretty.POST, daily_population_changes_url,
                               body='{}')

        SummarizeDailyPopulationChanges().date(date)

        last_request = httpretty.last_request()
        assert last_request.method == "POST"
        assert last_request.parsed_body == \
            {'date': [date], 'booked_males_as': ['%d' % number_of_asians_booked]}
