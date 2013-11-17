import httpretty
from json import dumps
from random import randint
from scripts.summarize_daily_population \
    import SummarizeDailyPopulation
from ccj.app import app
from ccj.models.daily_population import DailyPopulation as DPC
import datetime
from tempfile import mkdtemp
from shutil import rmtree


class Test_SummarizeDailyPopulation:

    def setup_method(self, method):
        app.testing = True
        self._tmp_dir = mkdtemp(dir='/tmp')
        app.config['DPC_DIR_PATH'] = self._tmp_dir
        self.dpc = DPC(self._tmp_dir)
        self.sdp = SummarizeDailyPopulation()

    def teardown_method(self, method):
         rmtree(self._tmp_dir)

    def test_serialize_to_males_booked_as(self):
        s = self.sdp.serialize('M', 'booked', 'AS')
        assert s == 'males_booked_as'

    @httpretty.activate
    def test_fetch_count(self):
        gender = 'M'
        status = 'booked'
        race = 'AS'
        date = '2013-06-01'
        ccj_get_Asian_males_data_url = \
            '%s&booking_date__exact=%s&gender=%s&race=%s' % \
            (self.sdp.inmate_api, date, gender, race)
        number_of_asians_booked = randint(0, 17)

        def get_request(method, uri, headers):
            assert uri == ccj_get_Asian_males_data_url
            response = {
                'meta': {'total_count': number_of_asians_booked},
                'objects': []
            }
            return (200, headers, dumps(response))

        httpretty.register_uri(httpretty.GET, self.sdp.inmate_api,
                               body=get_request)

        assert self.sdp.fetch_count(date, gender, status, race) == number_of_asians_booked

    @httpretty.activate
    def test_summarize_males_booked_as(self):
        """ Integration test """

        number_of_asians_booked = randint(0, 17)

        def get_request(method, uri, headers):
            response = {
                'meta': {'total_count': number_of_asians_booked},
                'objects': []
            }
            return (200, headers, dumps(response))

        httpretty.register_uri(httpretty.GET, self.sdp.inmate_api,
                               body=get_request)

        date = str(datetime.date(2013, 7, 21))
        self.sdp.summarize(date)
        data = self.dpc.query() 

        assert data[0]['males_booked_as'] == str(number_of_asians_booked)
