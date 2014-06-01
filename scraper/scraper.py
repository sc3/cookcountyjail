
from controller import Controller
from search_commands import SearchCommands
from inmates_scraper import InmatesScraper
from inmates import Inmates
from countyapi.inmate import Inmate
from inmate_details import InmateDetails
from http import Http
from raw_inmate_data import RawInmateData


class Scraper:

    def __init__(self, monitor):
        self.__monitor = monitor

    def check_for_missing_inmates(self, start_date):
        self._debug('started check_for_missing_inmates')
        raw_inmate_data = RawInmateData(None, None, self.__monitor)
        inmates = Inmates(Inmate, raw_inmate_data, self.__monitor)
        inmates_scraper = InmatesScraper(Http(), inmates, InmateDetails, self.__monitor, workers_to_start=70)
        search_commands = SearchCommands(inmates_scraper, self.__monitor)
        controller = Controller(self.__monitor, search_commands, inmates_scraper, inmates)
        controller.find_missing_inmates(start_date)
        self._debug('waiting for check_for_missing_inmates processing to finish')
        controller.wait_for_finish()
        self._debug('finished check_for_missing_inmates')

    def _debug(self, msg):
        self.__monitor.debug('Scraper: %s' % msg)

    def run(self, snap_shot_date, feature_controls):
        self._debug('started')
        raw_inmate_data = RawInmateData(snap_shot_date, feature_controls, self.__monitor)
        inmates = Inmates(Inmate, raw_inmate_data, self.__monitor)
        inmates_scraper = InmatesScraper(Http(), inmates, InmateDetails, self.__monitor)
        search_commands = SearchCommands(inmates_scraper, self.__monitor)
        controller = Controller(self.__monitor, search_commands, inmates_scraper, inmates)
        controller.run()
        self._debug('waiting for processing to finish')
        controller.wait_for_finish()
        raw_inmate_data.finish()
        self._debug('finished')
