
from datetime import date, timedelta
from mock import Mock
from random import randint

from scripts.scraper import Scraper


ONE_DAY = timedelta(1)


class Test_Scraper:

    def setup_method(self, method):
        # initialize date values
        self._today = date.today()
        self._two_days_ago = str(self._today - ONE_DAY * 2)
        self._yesterday = str(self._today - ONE_DAY)

        # now setup needed mock objects that are injected into Scraper object
        self.ccj_api = Mock()
        self.dpc = Mock()
        self.sdp = Mock()
        dpc_writer =  Mock()
        self.dpc_writer = dpc_writer

        class CsvWriterStub:
            """
            This class is needed to handle the with semantics of the object
            the DailyPopulation.writer method returns.
            This implementation returns a mock version of that object so that
            the values it receives can be validated
            """
            def __enter__(self):
                return dpc_writer
            def __exit__(self, type, value, traceback):
                pass

        self.csv_writer = CsvWriterStub

        # Create scraper object with mocked objects
        self.scraper = Scraper(self.ccj_api, self.dpc, self.sdp)

    def test_summarizes_yesterdays_data(self):
        """
        Summarize does a lot, even on the happy path which this is:
            1) It checks to see if there is a starting population
            2) Then it fetches the last population count
            3) Then it fetches the booked and discharged inmates for the next day
               after the last population date from CCJ V1.0 API website
            4) Then it summarizes the changes
            5) Then it writes those summarized changes in the Daily Population

            Scraper is designed to have all of the objects it needs to work with, injected into it,
            this makes testing a lot easier.
        """
        # define all of the return values
        self.dpc.has_no_starting_population.return_value = False
        self.dpc.previous_population.return_value = {'date': self._two_days_ago}
        booked_left_inmates = [randint(0, 77)]
        self.ccj_api.booked_left.return_value = booked_left_inmates
        population_changes = [randint(81, 121)]
        self.sdp.summarize.return_value = population_changes
        self.dpc.writer.return_value = self.csv_writer()

        self.scraper.run()

        # now check that the Scraper performed the operations it needed to
        self.dpc.has_no_starting_population.assert_called_once_with()
        self.dpc.previous_population.assert_called_once_with()
        self.ccj_api.booked_left.assert_called_once_with(self._yesterday)
        self.sdp.summarize.assert_called_once_with(self._yesterday, booked_left_inmates)
        self.dpc.writer.assert_called_once_with()
        self.dpc_writer.store.assert_called_once_with(population_changes)
