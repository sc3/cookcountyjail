
import gevent
from gevent.queue import JoinableQueue

from throwable_commands_queue import ThrowawayCommandsQueue

WORKERS_TO_START = 70

CCJ_INMATE_DETAILS_URL = 'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='


class InmatesScraper:

    FINISHED_PROCESSING = 'InmatesScraper finished processing'

    def __init__(self, http, inmates, inmate_details_class, monitor, workers_to_start=WORKERS_TO_START):
        self._http = http
        self._inmates = inmates
        self._inmate_details_class = inmate_details_class
        self._monitor = monitor
        self._workers_to_start = workers_to_start
        self._read_commands_q, self._workers = self._setup_command_system()
        self._write_commands_q = self._read_commands_q

    def create_if_exists(self, arg):
        self._put(self._create_if_exists, arg)

    def _create_if_exists(self, jail_id):
        outcome = 'did not find'
        self._debug('check for new inmate %s' % jail_id)
        worked, inmate_details_in_html = self._http.get(CCJ_INMATE_DETAILS_URL + jail_id)
        if worked:
            self._inmates.add(self._inmate_details_class(inmate_details_in_html))
            outcome = 'found'
        self._debug('%s new inmate %s' % (outcome, jail_id))

    def _debug(self, msg):
        self._monitor.debug('InmatesScraper: %s' % msg)

    def finish(self):
        self._prevent_new_requests_from_being_processed()
        gevent.spawn(self._wait_for_scrapping_to_finish)
        gevent.sleep(0)

    def _prevent_new_requests_from_being_processed(self):
        self._write_commands_q = ThrowawayCommandsQueue()

    def _process_commands(self):
        while True:
            try:
                func, args = self._read_commands_q.get()
                func(args)
            finally:
                self._read_commands_q.task_done()

    def _put(self, method, args):
        self._write_commands_q.put((method, args))
        gevent.sleep(0)

    def _setup_command_system(self):
        return JoinableQueue(None), [gevent.spawn(self._process_commands) for x in range(self._workers_to_start)]

    def update_inmate_status(self, inmate_id):
        self._put(self._update_inmate_status, inmate_id)

    def _update_inmate_status(self, inmate_id):
        status_msg_template = '%%s inmate %s' % inmate_id
        self._debug(status_msg_template % 'starting update')
        worked, inmate_details_in_html = self._http.get(CCJ_INMATE_DETAILS_URL + inmate_id)
        if worked:
            self._inmates.update(self._inmate_details_class(inmate_details_in_html))
            status = 'updated'
        else:
            self._inmates.discharge(inmate_id)
            status = 'discharged'
        self._debug(status_msg_template % status)

    def _wait_for_scrapping_to_finish(self):
        self._debug('started waiting for scraping inmates to finish')
        self._read_commands_q.join()
        self._monitor.notify(self.__class__, self.FINISHED_PROCESSING)
        self._debug('finished waiting for scraping inmates to finish')
