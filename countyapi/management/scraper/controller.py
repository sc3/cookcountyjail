
import gevent
from heartbeat import Heartbeat


class Controller:

    STOP_COMMAND = 'Controller_Halt'

    def __init__(self, monitor, search_commands, inmate_scraper, inmates):
        self._monitor = monitor
        self._search_commands = search_commands
        self._inmate_scraper = inmate_scraper
        self._inmates = inmates
        self.heartbeat_count = 0
        self.is_running = False
        self._worker = []

    def _debug(self, msg):
        self._monitor.debug('Controller: %s' % msg)

    def run(self):
        if not self.is_running:
            self._worker = [gevent.spawn(self._run)]
            gevent.sleep(0)

    def _run(self):
        self.is_running = True
        self._debug('started')
        self.heartbeat_count = 0
        heartbeat = Heartbeat(self._monitor)
        heartbeat_class = heartbeat.__class__
        self._search_commands.find_inmates()
        keep_running = True
        while keep_running:
            notifier, msg = self._monitor.notification()
            if notifier == heartbeat_class:
                self.heartbeat_count += 1
            else:
                self._debug('hb count %d, from %s, received - %s' % (self.heartbeat_count, notifier, msg))
                if msg == self.STOP_COMMAND:
                    keep_running = False
                elif notifier == self._search_commands.__class__:
                    self._inmate_scraper.finish()
                elif notifier == self._inmate_scraper.__class__:
                    self._inmates.finish()
                elif notifier == self._inmates.__class__:
                    keep_running = False
        self.is_running = False
        self._debug('stopped')

    def stop_command(self):
        return self.STOP_COMMAND

    def wait_for_finish(self):
        gevent.joinall(self._worker)
