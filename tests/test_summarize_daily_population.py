import httpretty
from json import dumps
from random import randint
from scripts.summarize_daily_population \
    import SummarizeDailyPopulation
from ccj.app import app
from ccj.models.daily_population import DailyPopulation as DPC
from .helper import safe_remove_file


class Test_SummarizeDailyPopulation:

    def setup_method(self, method):
        self._tmp_file = app.config['DPC_PATH']
        safe_remove_file(self._tmp_file)
        self.dpc = DPC(self._tmp_file)
        self.sdp = SummarizeDailyPopulation()


    def teardown_method(self, method):
        safe_remove_file(self._tmp_file)


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

        self.sdp.fetch_count(date, gender, status, race)

    def test_serialize(self):
        s = self.sdp.serialize('M', 'booked', 'AS')
        assert s == 'males_booked_as'

    # def test_summarize_males_booked_as(self):
    #     now = datetime.today()
    #     num_days_ago = timedelta(1 if now.hour >= 11 else 2)
    #     date_str = str(now.date() - num_days_ago)
    #     self.sdp.summarize(date_str)

