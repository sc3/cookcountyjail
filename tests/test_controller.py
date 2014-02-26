
import gevent
from mock import Mock, call
from datetime import date, timedelta

from countyapi.management.scraper.controller import Controller
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import HEARTBEAT_INTERVAL
from countyapi.management.scraper.search_commands import SearchCommands, MAX_INMATE_NUMBER
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
        gevent.sleep(0)

    def stop_controller(self, controller):
        self._monitor.notify(self.__class__, controller.stop_command())
        gevent.sleep(TIME_PADDING)
        assert not controller.is_running

    # def test_controller_can_be_stopped(self):
    #     inmates = Mock()
    #     controller = Controller(self._monitor, self._search, self._inmate_scraper, inmates)
    #     assert not controller.is_running
    #     assert controller.heartbeat_count == 0
    #     run_controller(controller)
    #     assert controller.is_running
    #     expected_num_heartbeats = 2
    #     gevent.sleep(HEARTBEAT_INTERVAL * expected_num_heartbeats + TIME_PADDING)
    #     self.stop_controller(controller)
    #     assert controller.heartbeat_count == expected_num_heartbeats
    #
    # def test_updates_and_searches_new_inmates(self):
    #     inmates = Mock()
    #     controller = Controller(self._monitor, self._search, self._inmate_scraper, inmates)
    #     run_controller(controller)
    #     assert inmates.active_inmates_ids.call_args_list == [call(controller.inmates_response_q)]
    #     active_jail_ids = [2, 78]
    #     controller.inmates_response_q.put(active_jail_ids)
    #     gevent.sleep(TIME_PADDING)
    #     assert self._search.update_inmates_status.call_args_list == [call(active_jail_ids)]
    #     self.send_notification(self._search, SearchCommands.FINISHED_UPDATE_INMATES_STATUS)
    #     assert self._search.find_inmates.call_args_list == [call()]
    #     self.send_notification(self._search, SearchCommands.FINISHED_FIND_INMATES)
    #     assert self._inmate_scraper.finish.call_args_list == [call()]
    #     self.send_notification(self._inmate_scraper, InmatesScraper.FINISHED_PROCESSING)
    #     assert inmates.finish.call_args_list == [call()]
    #     self.send_notification(inmates, Inmates.FINISHED_PROCESSING)
    #     assert not controller.is_running

    def test_search_missing_inmates(self):
        inmates = Mock()
        controller = Controller(self._monitor, self._search, self._inmate_scraper, inmates)
        start_date = date.today() - TIMEDELTA_MISSING_INMATES
        controller_missing_inmates(controller, start_date)
        assert inmates.known_inmates_ids_starting_with.call_args_list == [call(controller.inmates_response_q,
                                                                               start_date)]
        known_inmate_ids = []
        controller.inmates_response_q.put(known_inmate_ids)
        gevent.sleep(TIME_PADDING)
        assert self._search.find_inmates.call_args_list == [call([], start_date=start_date)]
        self.send_notification(self._search, SearchCommands.FINISHED_FIND_INMATES)
        assert self._inmate_scraper.finish.call_args_list == [call()]
        self.send_notification(self._inmate_scraper, InmatesScraper.FINISHED_PROCESSING)
        assert inmates.finish.call_args_list == [call()]
        self.send_notification(inmates, Inmates.FINISHED_PROCESSING)
        assert not controller.is_running


def run_controller(controller):
    """
    Runs the controller in a greenlet as this is a blocking call
    @type controller: Controller
    @return: void
    """
    controller.run()
    gevent.sleep(0.001)


def controller_missing_inmates(controller, start_date):
    """
    Runs the controller in a greenlet as this is a blocking call
    @type controller: Controller
    @return: void
    """
    controller.find_missing_inmates(start_date)
    gevent.sleep(0.001)
