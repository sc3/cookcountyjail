
import gevent
from countyapi.management.scraper.controller import Controller


class TestController:

    def run_controller(self, controller):
        def _run():
            controller.run()
        gevent.spawn(_run)
        gevent.sleep(0.001)

    def test_controller_can_be_stopped(self):
        controller = Controller(None)
        assert not controller.is_running
        assert controller.heartbeat_count == 0
        self.run_controller(controller)
        assert controller.is_running
        gevent.sleep(3.5)
        controller.stop()
        assert not controller.is_running
        assert controller.heartbeat_count == 4
