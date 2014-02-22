
import gevent
from mock import Mock, call

from countyapi.management.scraper.controller import Controller
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import HEARTBEAT_INTERVAL
from countyapi.management.scraper.search_commands import SearchCommands

TIME_PADDING = 0.1


class TestController:


    def setup_method(self, method):
        self._monitor = Monitor(None)
        self._mock_manager = Mock()
        self._search = self._mock_manager.search
        self._inmate_scraper = self._mock_manager.inmate_scraper

    def stop_controller(self, controller):
        self._monitor.notify(self.__class__, controller.stop_command())
        gevent.sleep(TIME_PADDING)
        assert not controller.is_running

    def test_controller_can_be_stopped(self):
        controller = Controller(None, self._monitor, self._search, self._inmate_scraper)
        assert not controller.is_running
        assert controller.heartbeat_count == 0
        run_controller(controller)
        assert controller.is_running
        expected_num_heartbeats = 2
        gevent.sleep(HEARTBEAT_INTERVAL * expected_num_heartbeats + TIME_PADDING)
        self.stop_controller(controller)
        assert controller.heartbeat_count == expected_num_heartbeats

    def test_starts_search_for_new_inmates(self):
        controller = Controller(None, self._monitor, self._search, self._inmate_scraper)
        run_controller(controller)
        gevent.sleep(TIME_PADDING)
        self._monitor.notify(self._inmate_scraper.__class__, SearchCommands.FINISHED_FIND_INMATES)
        self.stop_controller(controller)
        assert self._search.find_inmates.call_args_list == [call()]
        assert self._inmate_scraper.finish.call_args_list == [call()]
        assert self._mock_manager.mock_calls == [call.search.find_inmates(), call.inmate_scraper.finish()]


def run_controller(controller):
    """
    Runs the controller in a greenlet as this is a blocking call
    @type controller: Controller
    @return: void
    """
    def _run():
        controller.run()
    gevent.spawn(_run)
    gevent.sleep(0.001)
