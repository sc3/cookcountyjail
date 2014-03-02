
from controller import Controller
from search_commands import SearchCommands
from inmates_scraper import InmatesScraper
from inmates import Inmates
from inmate import Inmate
from inmate_details import InmateDetails
from http import Http


class Scraper:

    def __init__(self, monitor):
        self._monitor = monitor

    def check_for_missing_inmates(self, start_date):
        self._debug('started check_for_missing_inmates')
        inmates = Inmates(Inmate, self._monitor)
        inmates_scraper = InmatesScraper(Http(), inmates, InmateDetails, self._monitor, workers_to_start=70)
        search_commands = SearchCommands(inmates_scraper, self._monitor)
        controller = Controller(self._monitor, search_commands, inmates_scraper, inmates)
        controller.find_missing_inmates(start_date)
        self._debug('waiting for check_for_missing_inmates processing to finish')
        controller.wait_for_finish()
        self._debug('finished check_for_missing_inmates')

    def _debug(self, msg):
        self._monitor.debug('Scraper: %s' % msg)

    def run(self):
        self._debug('started')
        inmates = Inmates(Inmate, self._monitor)
        inmates_scraper = InmatesScraper(Http(), inmates, InmateDetails, self._monitor)
        search_commands = SearchCommands(inmates_scraper, self._monitor)
        controller = Controller(self._monitor, search_commands, inmates_scraper, inmates)
        controller.run()
        self._debug('waiting for processing to finish')
        controller.wait_for_finish()
        self._debug('finished')
