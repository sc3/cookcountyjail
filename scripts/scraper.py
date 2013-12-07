#
# Warning:
# ========
#   The python version available on the cookcountyjail.recoveredfactory.net
#   machine does not set load paths correctly so for the time being:
#      1) Do not add #! to this file.
#      2) invoke this from parent directory like this:
#             python scripts.scraper
#
# This scrapes the Cook County Jail website populating the 2.0 API
# system with the results of the scrapping.
#
# This is expected to run after the existing 1.0 API scraper has run,
# so the target date is 11am. If it runs at that time or later in the
# day then it fetches the summarized date from yesterday, otherwise it
# fetches the info from the day before yesterday.
#
# It also is able to play catchup. It does this by fetching the last
# population. If there was none, then it builds the starting population.
# If the last population date is not the day before this ran, then it
# fetches all of the days up to and including the day before the current
# run day.
#
# If the last population was the day before the day it is run it does not
# run.
#


from datetime import date, datetime, timedelta
from ccj.models.daily_population import DailyPopulation
from ccj.config import get_dpc_dir
from scripts.ccj_api_v1 import CcjApiV1
from scripts.summarize_daily_population import SummarizeDailyPopulation

ONE_DAY = timedelta(1)
STARTING_DATE = '2013-07-22'


class Scraper:

    def __init__(self, ccj_api, dpc, sdp, population_starting_date):
        self._ccj_api = ccj_api
        self._dpc = dpc
        self._sdp = sdp
        self._population_starting_date = population_starting_date

    def _last_population_date(self):
        return datetime.strptime(self._dpc.previous_population()['date'], '%Y-%m-%d').date()

    @staticmethod
    def _next_day(a_date):
        return a_date + ONE_DAY

    def run(self):
        if self._dpc.has_no_starting_population():
            self._starting_population()
        last_population_date = self._last_population_date()
        yesterday = self._yesterday()
        while yesterday != last_population_date:
            last_population_date = self._next_day(last_population_date)
            next_day = str(last_population_date)
            booked_left = self._ccj_api.booked_left(next_day)
            population_changes = self._sdp.summarize(next_day, booked_left)
            with self._dpc.writer() as f:
                f.store(population_changes)

    def _starting_population(self):
        day_before_starting_date = str(datetime.strptime(self._population_starting_date, '%Y-%m-%d').date() - ONE_DAY)
        starting_population_data = self._ccj_api.start_population_data(self._population_starting_date)
        starting_population_counts = self._sdp.calculate_starting_population(starting_population_data,
                                                                             day_before_starting_date)
        self._dpc.store_starting_population(starting_population_counts)

    @staticmethod
    def _yesterday():
        return date.today() - timedelta(1)


if __name__ == '__main__':
    start_time = datetime.today()
    ccj_api = CcjApiV1()
    dpc = DailyPopulation(get_dpc_dir())
    sdp = SummarizeDailyPopulation()
    scraper = Scraper(ccj_api, dpc, sdp, STARTING_DATE)
    scraper.run()
    print 'Scraper ran for %s' % str(datetime.today() - start_time)
