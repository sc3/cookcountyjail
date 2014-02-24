
import gevent
from gevent.queue import Queue

from heartbeat import Heartbeat
from search_commands import SearchCommands


class Controller:

    _CONTROLLER_NOTIFY_MSG_TEMPLATE = 'Controller: %s'
    _RECEIVED_ACTIVE_IDS_COMMAND = _CONTROLLER_NOTIFY_MSG_TEMPLATE % 'Received active ids'
    _START_COMMAND = _CONTROLLER_NOTIFY_MSG_TEMPLATE % 'Start'
    STOP_COMMAND = _CONTROLLER_NOTIFY_MSG_TEMPLATE % 'Halt'

    def __init__(self, monitor, search_commands, inmate_scraper, inmates):
        self._monitor = monitor
        self._search_commands = search_commands
        self._inmate_scraper = inmate_scraper
        self._inmates = inmates
        self.heartbeat_count = 0
        self.is_running = False
        self._worker = []
        self.active_ids_response_q = Queue(None)
        self._fetch_active_inmates_worker = []
        self._active_ids = []

    def _active_inmates(self):
        self._inmates.active_inmates_ids(self.active_ids_response_q)
        self._fetch_active_inmates_worker = [gevent.spawn(self._retrieve_active_inmates)]
        gevent.sleep(0)

    def _debug(self, msg):
        self._monitor.debug('Controller: %s' % msg)

    def _retrieve_active_inmates(self):
        self._active_ids = self.active_ids_response_q.get()
        self._monitor.notify(self.__class__, self._RECEIVED_ACTIVE_IDS_COMMAND)
        gevent.sleep(0)

    def run(self):
        if not self.is_running:
            self._monitor.notify(self.__class__, self._START_COMMAND)
            self._worker = [gevent.spawn(self._run)]
            gevent.sleep(0)

    def _run(self):
        self.is_running = True
        self._debug('started')
        self.heartbeat_count = 0
        heartbeat = Heartbeat(self._monitor)
        heartbeat_class = heartbeat.__class__
        keep_running = True
        while keep_running:
            notifier, msg = self._monitor.notification()
            if notifier == heartbeat_class:
                self.heartbeat_count += 1
            else:
                self._debug('hb count %d, from %s, received - %s' % (self.heartbeat_count,
                                                                     str(notifier).split('.')[-1],
                                                                     msg))
                if msg == self.STOP_COMMAND:
                    keep_running = False
                elif notifier == self._search_commands.__class__:
                    status = SearchCommands.FINISHED_UPDATE_INMATES_STATUS
                    if msg == status:
                        self._search_commands.find_inmates()
                    elif msg == SearchCommands.FINISHED_FIND_INMATES:
                        self._inmate_scraper.finish()
                    else:
                        self._monitor.debug(self._CONTROLLER_NOTIFY_MSG_TEMPLATE %
                                            ('Unknown notification from %s, received - %s' % (notifier, msg)))
                elif notifier == self._inmate_scraper.__class__:
                    self._inmates.finish()
                elif notifier == self._inmates.__class__:
                    keep_running = False
                elif notifier == self.__class__:
                    if msg == self._START_COMMAND:
                        self._active_inmates()
                    elif msg == self._RECEIVED_ACTIVE_IDS_COMMAND:
                        self._search_commands.update_inmates_status(self._active_ids)
                else:
                    self._monitor.debug(self._CONTROLLER_NOTIFY_MSG_TEMPLATE %
                                        ('Unknown notification from %s, received - %s' % (notifier, msg)))
        self.is_running = False
        self._debug('stopped')

    def stop_command(self):
        return self.STOP_COMMAND

    def wait_for_finish(self):
        gevent.joinall(self._worker)
