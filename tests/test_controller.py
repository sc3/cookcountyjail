
import gevent
from mock import Mock, call
from datetime import date, timedelta

from countyapi.management.scraper.controller import Controller
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import HEARTBEAT_INTERVAL
from countyapi.management.scraper.search_commands import SearchCommands
from countyapi.management.scraper.inmates_scraper import InmatesScraper
from countyapi.management.scraper.inmates import Inmates


NUM_DAYS_MISSING_INMATES = 3
TIMEDELTA_MISSING_INMATES = timedelta(NUM_DAYS_MISSING_INMATES)
TIME_PADDING = 0.1


class TestController:

    def setup_method(self, method):
        self._monitor = Monitor(Mock())
        self._search = Mock()
        self._inmate_scraper = Mock()

    def send_notification(self, obj_instance, msg):
        self._monitor.notify(obj_instance.__class__, msg)
        gevent.sleep(TIME_PADDING)

    def stop_controller(self, controller):
        self._monitor.notify(self.__class__, controller.stop_command())
        gevent.sleep(TIME_PADDING)
        assert not controller.is_running

    def test_controller_can_be_stopped(self):
        inmates = Mock()
        controller = Controller(self._monitor, self._search, self._inmate_scraper, inmates)
        assert not controller.is_running
        assert controller.heartbeat_count == 0
        run_controller(controller)
        assert controller.is_running
        expected_num_heartbeats = 2
        gevent.sleep(HEARTBEAT_INTERVAL * expected_num_heartbeats + TIME_PADDING)
        self.stop_controller(controller)
        assert controller.heartbeat_count == expected_num_heartbeats

    def test_scraping(self):
        """
        This tests the normal operating loop of the scraper. It makes sure that it orchestrates
        the sequence correctly and that no operation is missing. Basically the scraper needs
        to do the following:
            - initiate check of active inmates
            - search for new inmates over the last 5 days or so
            - initiate check if inmates have really been discharged from the last few days
            - once search command generation is finished, tell inmate_scraper to signal when finished
            - once inmate_scraper is finished, tell inmates to signal when it finishes
            - once inmates is finished halt processing
        This test makes sure that the above happens in that order
        """
        inmates = Mock()
        controller = Controller(self._monitor, self._search, self._inmate_scraper, inmates)
        run_controller(controller)
        assert inmates.active_inmates_ids.call_args_list == [call(controller.inmates_response_q)]
        active_jail_ids = [2, 78]
        send_response(controller, active_jail_ids)
        assert self._search.update_inmates_status.call_args_list == [call(active_jail_ids)]
        self.send_notification(self._search, SearchCommands.FINISHED_UPDATE_INMATES_STATUS)
        assert self._search.find_inmates.call_args_list == [call()]
        self.send_notification(self._search, SearchCommands.FINISHED_FIND_INMATES)
        assert inmates.recently_discharged_inmates_ids.call_args_list == [call(controller.inmates_response_q)]
        send_response(controller, active_jail_ids)
        assert self._search.check_if_really_discharged.call_args_list == [call(active_jail_ids)]
        self.send_notification(self._search, SearchCommands.FINISHED_CHECK_OF_RECENTLY_DISCHARGED_INMATES)
        assert self._inmate_scraper.finish.call_args_list == [call()]
        self.send_notification(self._inmate_scraper, InmatesScraper.FINISHED_PROCESSING)
        assert inmates.finish.call_args_list == [call()]
        self.send_notification(inmates, Inmates.FINISHED_PROCESSING)
        assert not controller.is_running

    def test_search_missing_inmates(self):
        inmates = Mock()
        controller = Controller(self._monitor, self._search, self._inmate_scraper, inmates)
        start_date = date.today() - TIMEDELTA_MISSING_INMATES
        controller_missing_inmates(controller, start_date)
        assert inmates.known_inmates_ids_starting_with.call_args_list == [call(controller.inmates_response_q,
                                                                               start_date)]
        known_inmate_ids = []
        send_response(controller, known_inmate_ids)
        assert self._search.find_inmates.call_args_list == [call([], start_date=start_date)]
        self.send_notification(self._search, SearchCommands.FINISHED_FIND_INMATES)
        assert self._inmate_scraper.finish.call_args_list == [call()]
        self.send_notification(self._inmate_scraper, InmatesScraper.FINISHED_PROCESSING)
        assert inmates.finish.call_args_list == [call()]
        self.send_notification(inmates, Inmates.FINISHED_PROCESSING)
        assert not controller.is_running


def controller_missing_inmates(controller, start_date):
    """
    Runs the controller in a greenlet as this is a blocking call
    @type controller: Controller
    @return: void
    """
    controller.find_missing_inmates(start_date)
    gevent.sleep(0.001)


def run_controller(controller):
    """
    Runs the controller in a greenlet as this is a blocking call
    @type controller: Controller
    @return: void
    """
    controller.run()
    gevent.sleep(0.001)


def send_response(controller, response_msg):
    controller.inmates_response_q.put(response_msg)
    gevent.sleep(TIME_PADDING)
