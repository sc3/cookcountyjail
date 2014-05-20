from datetime import date

import gevent
from gevent.queue import Queue

from heartbeat import Heartbeat

from search_commands import SearchCommands
from utils import ONE_DAY


NEW_INMATE_SEARCH_WINDOW_SIZE = 5


class Controller:

    _CONTROLLER_NOTIFY_MSG_TEMPLATE = 'Controller: %s'
    _RECEIVED_ACTIVE_IDS_COMMAND = _CONTROLLER_NOTIFY_MSG_TEMPLATE % 'Received active ids'
    _RECEIVED_KNOWN_INMATES_COMMAND = _CONTROLLER_NOTIFY_MSG_TEMPLATE % 'Received known inmates ids'
    _RECEIVED_RECENTLY_DISCHARGED_INMATES_IDS_COMMAND = \
        _CONTROLLER_NOTIFY_MSG_TEMPLATE % 'Received recently discharged inmates ids'
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
        self.inmates_response_q = Queue(None)
        self._inmates_worker = []
        self._inmates_response = []
        self._start_date_missing_inmates = None
        self._active_inmate_ids = []
        self._today = date.today()

    def _active_inmates(self):
        self._inmates.active_inmates_ids(self.inmates_response_q)
        self._retrieve_inmates_response(self._RECEIVED_ACTIVE_IDS_COMMAND)

    def _debug(self, msg):
        self._monitor.debug('Controller: %s' % msg)

    def _end_index_active_inmate_ids_in_search_window(self):
        end_date = (self._today - ONE_DAY * (NEW_INMATE_SEARCH_WINDOW_SIZE + 2)).strftime('%Y-%m%d')
        for i in range(len(self._active_inmate_ids)):
            if end_date >= self._active_inmate_ids[i][0:9]:
                return i
        return len(self._active_inmate_ids)

    def find_missing_inmates(self, start_date):
        if not self.is_running:
            self._start_date_missing_inmates = start_date
            self._worker = [gevent.spawn(self._find_missing_inmates)]
            self._notify(self._START_COMMAND)

    def _find_missing_inmates(self):
        self.is_running = True
        self._debug('find_missing_inmates started')
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
                    if msg == SearchCommands.FINISHED_FIND_INMATES:
                        self._debug('inmates scraper finish')
                        self._inmate_scraper.finish()
                    else:
                        self._debug('Unknown notification from %s, received - %s' % (notifier, msg))
                elif notifier == self._inmate_scraper.__class__:
                    self._debug('inmates finish')
                    self._inmates.finish()
                elif notifier == self._inmates.__class__:
                    keep_running = False
                elif notifier == self.__class__:
                    if msg == self._START_COMMAND:
                        self._debug('find known inmates')
                        self._known_inmates()
                    elif msg == self._RECEIVED_KNOWN_INMATES_COMMAND:
                        self._debug('find missing inmates')
                        self._search_commands.find_inmates(exclude_list=self._inmates_response,
                                                           start_date=self._start_date_missing_inmates)
                else:
                    self._debug('Unknown notification from %s, received - %s' % (notifier, msg))
        self._start_date_missing_inmates = None
        self.is_running = False
        self._debug('find_missing_inmates stopped')

    def _find_new_inmates(self):
        end_index = self._end_index_active_inmate_ids_in_search_window()
        self._search_commands.find_inmates(exclude_list=self._active_inmate_ids[0:end_index],
                                           start_date=self._today - ONE_DAY * (NEW_INMATE_SEARCH_WINDOW_SIZE + 1))

    def _known_inmates(self):
        self._inmates.known_inmates_ids_starting_with(self.inmates_response_q, self._start_date_missing_inmates)
        self._retrieve_inmates_response(self._RECEIVED_KNOWN_INMATES_COMMAND)

    def _notify(self, notification_msg):
        self._monitor.notify(self.__class__, notification_msg)

    def _recently_discharged_inmates_ids(self):
        self._inmates.recently_discharged_inmates_ids(self.inmates_response_q)
        self._retrieve_inmates_response(self._RECEIVED_RECENTLY_DISCHARGED_INMATES_IDS_COMMAND)

    def _retrieve_inmates_response(self, received_notification_msg):
        def _get_response_msg():
            self._retrieve_inmates_response_1(received_notification_msg)
        self._inmates_worker = [gevent.spawn(_get_response_msg)]
        gevent.sleep(0)

    def _retrieve_inmates_response_1(self, received_notification_msg):
        self._inmates_response = self.inmates_response_q.get()
        self._notify(received_notification_msg)

    def run(self):
        if not self.is_running:
            self._worker = [gevent.spawn(self._run)]
            self._notify(self._START_COMMAND)

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
                    if msg == SearchCommands.FINISHED_UPDATE_INMATES_STATUS:
                        self._debug('initiate search for new inmates')
                        self._find_new_inmates()
                    elif msg == SearchCommands.FINISHED_FIND_INMATES:
                        self._debug('fetch recently discharged inmate ids')
                        self._recently_discharged_inmates_ids()
                    elif msg == SearchCommands.FINISHED_CHECK_OF_RECENTLY_DISCHARGED_INMATES:
                        self._debug('initiate inmates scraper finish')
                        self._inmate_scraper.finish()
                    else:
                        self._debug('Unknown notification from %s, received - %s' % (notifier, msg))
                elif notifier == self._inmate_scraper.__class__:
                    self._debug('inmates finish')
                    self._inmates.finish()
                elif notifier == self._inmates.__class__:
                    keep_running = False
                elif notifier == self.__class__:
                    if msg == self._START_COMMAND:
                        self._debug('find active inmates')
                        self._active_inmates()
                    elif msg == self._RECEIVED_ACTIVE_IDS_COMMAND:
                        self._debug('update inmates status')
                        self._active_inmate_ids = self._inmates_response
                        self._search_commands.update_inmates_status(self._inmates_response)
                    elif msg == self._RECEIVED_RECENTLY_DISCHARGED_INMATES_IDS_COMMAND:
                        self._debug('initiate confirmation search of recently discharged inmates')
                        self._search_commands.check_if_really_discharged(self._inmates_response)
                else:
                    self._debug('Unknown notification from %s, received - %s' % (notifier, msg))
        self.is_running = False
        self._debug('stopped')

    def stop_command(self):
        return self.STOP_COMMAND

    def wait_for_finish(self):
        gevent.joinall(self._worker)
