
import gevent
from countyapi.management.scraper.controller import Controller
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import HEARTBEAT_INTERVAL


class TestController:

    def run_controller(self, controller):
        def _run():
            controller.run()
        gevent.spawn(_run)
        gevent.sleep(0.001)

    def test_controller_can_be_stopped(self):
        monitor = Monitor(None)
        controller = Controller(None, monitor)
        assert not controller.is_running
        assert controller.heartbeat_count == 0
        self.run_controller(controller)
        assert controller.is_running
        gevent.sleep(4.1)
        monitor.notify(self.__class__, controller.stop_command())
        gevent.sleep(HEARTBEAT_INTERVAL + 0.1)
        assert not controller.is_running
        assert controller.heartbeat_count == 4
