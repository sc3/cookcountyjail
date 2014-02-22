
import gevent
from gevent.queue import JoinableQueue

from throwable_commands_queue import ThrowawayCommandsQueue

WORKERS_TO_START = 70

CCJ_INMATE_DETAILS_URL = 'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='


class InmatesScraper:

    FINISHED_PROCESSING = 'Finished Processing'

    def __init__(self, http, inmates, inmate_details, monitor, workers_to_start=WORKERS_TO_START):
        self._http = http
        self._inmates = inmates
        self._inmate_details = inmate_details
        self._monitor = monitor
        self._workers_to_start = workers_to_start
        self._read_commands_q, self._workers = self._setup_command_system()
        self._write_commands_q = self._read_commands_q

    def create_if_exists(self, arg):
        self._write_commands_q.put((self._create_if_exists, arg))
        gevent.sleep(0)

    def _create_if_exists(self, arg):
        worked, value = self._http.get(CCJ_INMATE_DETAILS_URL + arg)
        if worked:
            self._inmates.add(self._inmate_details(arg))

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

    def _setup_command_system(self):
        return (JoinableQueue(0), [gevent.spawn(self._process_commands) for x in range(self._workers_to_start)])

    def _wait_for_scrapping_to_finish(self):
        self._read_commands_q.join()
        self._monitor.notify(self.__class__, self.FINISHED_PROCESSING)
