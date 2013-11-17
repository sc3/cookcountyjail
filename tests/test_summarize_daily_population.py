import httpretty
from json import dumps
from random import randint
from scripts.summarize_daily_population \
    import SummarizeDailyPopulation
from ccj.app import app
from ccj.models.daily_population import DailyPopulation as DPC
from helper import safe_remove_file


class Test_SummarizeDailyPopulation:

    def setup_method(self, method):
        self._tmp_file = app.config['DPC_PATH']
        safe_remove_file(self._tmp_file)
        self.dpc = DPC(self._tmp_file)

    def teardown_method(self, method):
        safe_remove_file(self._tmp_file)

    @httpretty.activate
    def test_summarize_dpc_for_Aian_males_booked(self):
        race = 'AS'
        date = '2013-06-01'
        gender = 'M'
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        ccj_get_Asian_males_data_url = \
            '%s?format=json&limit=0&race=%s&gender=%s&booking_date__exact=%s' % \
            (county_inmate_api, race, gender, date)
        number_of_asians_booked = randint(0, 17)
        expected = [{'date': date, 'booked_males_as': '%d' % number_of_asians_booked}]

        def get_request(method, uri, headers):
            assert uri == ccj_get_Asian_males_data_url
            response = {
                'meta': {},
                'objects': [{} for x in range(0, number_of_asians_booked)]
            }
            return (200, headers, dumps(response))

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=get_request)

        SummarizeDailyPopulation().date(date)

        last_request = httpretty.last_request()
        assert last_request.method == "GET"
        assert self.dpc.query() == expected
