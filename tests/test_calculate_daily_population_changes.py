import httpretty
import requests
from json import dumps, loads
import pdb


class CalculateDailyPopulationChanges:
    def date(self, date):
        race = 'AS'
        date = '2013-06-01'
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        get_cmd = '%s?format=json&limit=0&race=%s&booking_date__exact=%s' % \
            (county_inmate_api, race, date)
        response = requests.get(get_cmd)
        daily_population_changes_url = \
            '%s/api/2.0/daily_population_changes' % cook_county_url
        requests.post(daily_population_changes_url, data={'date': date, 'booked_males_as': 0})


class Test_CalculateDailyPopulationChanges:

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    @httpretty.activate
    def test_calculate_dpc_for_specified_date(self):
        race = 'AS'
        date = '2013-06-01'
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        get_cmd = '%s?format=json&limit=0&race=%s&booking_date__exact=%s' % \
            (county_inmate_api, race, date)

        def get_request(method, uri, headers):
            assert uri == get_cmd
            response = {
                'meta': {},
                'objects': []
            }
            return (200, headers, dumps(response))

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=get_request)

        daily_population_changes_url = \
            '%s/api/2.0/daily_population_changes' % cook_county_url
        httpretty.register_uri(httpretty.POST, daily_population_changes_url,
                               body='{}')

        CalculateDailyPopulationChanges().date(date)

        last_request = httpretty.last_request()
        assert last_request.method == "POST"
        assert last_request.parsed_body == \
            {'date': [date], 'booked_males_as': ['0']}
