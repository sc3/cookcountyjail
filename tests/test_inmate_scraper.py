

from mock import Mock, call
from datetime import datetime
import gevent
from gevent.queue import Queue


from countyapi.management.scraper.inmates_scraper import InmatesScraper, CCJ_INMATE_DETAILS_URL

ONE_SECOND = 1


class Test_InmatesScraper:

    def test_create_if_exists_calls_http(self):
        http = Http_TestDouble(get_succeeds_always=True)
        inmates = Mock()
        monitor = Mock()
        inmate_scraper = InmatesScraper(http, inmates, InmateDetails_TestDouble, monitor)
        jail_ids = ['jail_id_%d' % id for id in range(1, 5)]
        expected_http_calls_args = []
        for jail_id in jail_ids:
            expected_http_calls_args.append(CCJ_INMATE_DETAILS_URL + jail_id)
            inmate_scraper.create_if_exists(jail_id)
        assert http.get_args_list() == expected_http_calls_args

    def test_create_if_exists_adds_inmates(self):
        http = Http_TestDouble()
        inmates = Mock()
        monitor = Mock()
        inmate_scraper = InmatesScraper(http, inmates, InmateDetails_TestDouble, monitor)
        jail_ids = ['jail_id_%d' % id for id in range(1, 5)]
        expected_inmate_details_calls_args = []
        for jail_id in jail_ids:
            if not http.bad_response_desired(jail_id):
                expected_inmate_details_calls_args.append(call(InmateDetails_TestDouble(jail_id)))
            inmate_scraper.create_if_exists(jail_id)
        assert inmates.add.call_args_list == expected_inmate_details_calls_args

    def test_create_if_exists_runs_in_parallel(self):
        http = Http_TestDouble(use_sleep=True)
        inmates = Inmates_TestDouble()
        monitor = Mock()
        inmate_scraper = InmatesScraper(http, inmates, InmateDetails_TestDouble, monitor)
        jail_ids = ['jail_id_%d' % j_id for j_id in range(1, 6)]
        expected_http_calls_args = []
        expected_inmate_details_calls_args = []
        for jail_id in jail_ids:
            expected_http_calls_args.append(CCJ_INMATE_DETAILS_URL + jail_id)
            if not http.bad_response_desired(jail_id):
                expected_inmate_details_calls_args.append(InmateDetails_TestDouble(jail_id))
        expected_inmate_details_calls_args.append(expected_inmate_details_calls_args.pop(0))
        inmate_create_if_msgs = []
        count = len(expected_inmate_details_calls_args)
        start_time = datetime.now()
        for jail_id in jail_ids:
            inmate_scraper.create_if_exists(jail_id)
        while count > 0:
            inmate_create_if_msgs.append(inmates.msg())
            count -= 1
        end_time = datetime.now()
        assert (end_time - start_time).seconds == ONE_SECOND # All processing should happen with a second
        assert inmates.msg_q_size() == 0  # make sure did not receive more messages than expected.
        assert http.get_args_list() == expected_http_calls_args
        assert inmate_create_if_msgs == expected_inmate_details_calls_args

    def test_finish(self):
        http = Http_TestDouble(use_sleep=True)
        inmates = Inmates_TestDouble()
        monitor = Mock()
        inmate_scraper = InmatesScraper(http, inmates, InmateDetails_TestDouble, monitor)
        inmate_scraper.finish()
        assert monitor.notify.call_args_list == [call(inmate_scraper.__class__, inmate_scraper.FINISHED_PROCESSING)]


class InmateDetails_TestDouble:

    def __init__(self, details):
        self._details = details

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__


class Http_TestDouble:

    def __init__(self, get_succeeds_always=False, use_sleep=False):
        self._get_succeeds_always = get_succeeds_always
        self._use_sleep = use_sleep
        self._get_args_list = []

    def bad_response_desired(self, arg):
        arg_vals = arg.split('_')
        return (int(arg_vals[2]) % 2) == 0

    def get(self, arg):
        self._get_args_list.append(arg)
        if self._use_sleep:
            sleep_interval = ONE_SECOND if self._first_jail_id(arg) else 0.5
            gevent.sleep(sleep_interval)
        if not self._get_succeeds_always and self.bad_response_desired(arg):
            return False, ''
        return 200, arg

    def get_args_list(self):
        return self._get_args_list

    def _first_jail_id(self, arg):
        arg_vals = arg.split('_')
        return int(arg_vals[2]) == 1


class Inmates_TestDouble:

    def __init__(self):
        self._messages = self._setup_messages_system()

    def add(self, msg):
        self._messages.put(msg)
        gevent.sleep(0)

    def msg(self):
        return self._messages.get()

    def msg_q_size(self):
        gevent.sleep(0)
        return self._messages.qsize()

    def _setup_messages_system(self):
        return Queue(0)
