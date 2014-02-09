
import gevent
from countyapi.management.scraper.monitor import Monitor
from countyapi.management.scraper.heartbeat import Heartbeat


class Controller:

    def __init__(self, log):
        self.heartbeat_count = 0
        self.is_running = False
        self._keep_running = True
        self._log = log

    def run(self):
        monitor = None
        heartbeat = None

        def _run():
            self.is_running = True
            while self._keep_running:
                monitor.notification()
                self.heartbeat_count += 1
            self.is_running = False
        monitor = Monitor(self._log)
        heartbeat = Heartbeat(monitor)
        gevent.spawn(_run)
        gevent.sleep(0)

    def stop(self):
        self._keep_running = False
        gevent.sleep(1.1)
