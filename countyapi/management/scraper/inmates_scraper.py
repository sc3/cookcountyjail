
import gevent
from gevent.queue import Queue

WORKERS_TO_START = 70

CCJ_INMATE_DETAILS_URL = 'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='


class InmatesScraper:

    def __init__(self, http, inmates, inmate_details, workers_to_start=WORKERS_TO_START):
        self._http = http
        self._inmates = inmates
        self._inmate_details = inmate_details
        self._workers_to_start = workers_to_start
        self._workers = []
        self._commands = self._setup_command_system()

    def create_if_exists(self, arg):
        self._commands.put((self._create_if_exists, arg))
        gevent.sleep(0)

    def _create_if_exists(self, arg):
        worked, value = self._http.get(CCJ_INMATE_DETAILS_URL + arg)
        if worked:
            self._inmates.add(self._inmate_details(arg))

    def _process_commands(self):
        while True:
            func, args = self._commands.get()
            func(args)

    def _setup_command_system(self):
        commands = Queue(0)
        self._workers = [gevent.spawn(self._process_commands) for x in range(self._workers_to_start)]
        return commands
