
from datetime import date, datetime, timedelta
from mock import Mock
from random import randint

from scripts.scraper import Scraper


ONE_DAY = timedelta(1)


class Test_Scraper:

    def _date_before_today(self, number_of_missing_days):
        return str(self._today - ONE_DAY * number_of_missing_days)

    def setup_method(self, method):
        # initialize date values
        self._today = date.today()

        # now setup needed mock objects that are injected into Scraper object
        self.ccj_api = Mock()
        self.dpc = Mock()
        self.sdp = Mock()

        # Create scraper object with mocked objects
        self.scraper = Scraper(self.ccj_api, self.dpc, self.sdp)

    def test_summarizes_does_run_if_summary_already_exists(self):
        """
        If yesterday is already summarized then SummarizeDailyPopulation does nothing
        """
        # define all of the return values
        self.dpc.has_no_starting_population.return_value = False
        self.dpc.previous_population.return_value = {'date': self._date_before_today(1)}

        self.scraper.run()

        # now check that the Scraper performed the operations it needed to
        self.dpc.has_no_starting_population.assert_called_once_with()
        self.dpc.previous_population.assert_called_once_with()
        assert self.ccj_api.call_args_list == []
        assert self.sdp.call_args_list == []
        assert not self.dpc.writer.called

    def test_summarizes_catching_up(self):
        """
        If Scraper finds that the date of last population summarized is earlier
        than the day before yesterday, it must fetch and summarize all of the
        missing days and then do yesterday's.
        """
        self.dpc.has_no_starting_population.return_value = False
        sdpsc = SummarizeDailyPopulationStateChecker(self._today, randint(0, 5))
        self.dpc.previous_population = Mock(side_effect=sdpsc.dpc_previous_population)
        self.ccj_api.booked_left = Mock(side_effect=sdpsc.ccj_api_booked_left)
        self.sdp.summarize = Mock(side_effect=sdpsc.sdp_summarize)
        self.dpc.writer = Mock(side_effect=sdpsc.dpc_writer)

        self.scraper.run()

        # now check that the Scraper performed the operations it needed to
        self.dpc.has_no_starting_population.assert_called_once_with()
        assert sdpsc.finished()


class State(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

STATES = State(['starting', 'dpc_previous_population', 'ccj_api_booked_left', 'sdp_summarize', 'dpc_writer',
                'dpc_writer_store'])


class SummarizeDailyPopulationStateChecker(object):
    """
    Uses the generator object model pattern to provide a set of test values and check
    that the order of operations is correct

    The summarization that the Scraper does is a lot, even on the happy path only get yesterday:
        1) It checks to see if there is a starting population
        2) Then it fetches the last population count
        3) Then it fetches the booked and discharged inmates for the next day
           after the last population date from CCJ V1.0 API website
        4) Then it summarizes the changes
        5) Then it writes those summarized changes in the Daily Population

    When the dates to be filled in then it essentially repeats steps 2 through 5
    """
    def __init__(self, today, number_days_to_check):
        self._state = STATES.starting
        assert number_days_to_check >= 0
        number_days_to_check += 2 # adjust so we start with day before yesterday
        self._yesterday = today - ONE_DAY
        self._starting_date = today - ONE_DAY * number_days_to_check
        assert self._starting_date < self._yesterday
        self._current_date = self._starting_date
        self._return_values = {}

        # setup to handle DailyPopulation.writer mechanism
        dpc_writer_store = self

        class CsvWriterStub:
            """
            This class is needed to handle the with semantics of the object
            the DailyPopulation.writer method returns.
            This implementation returns a mock version of that object so that
            the values it receives can be validated
            """
            def __enter__(self):
                return dpc_writer_store
            def __exit__(self, type, value, traceback):
                pass

        self._csv_writer = CsvWriterStub

    def ccj_api_booked_left(self, date_to_fetch):
        """
        This the starting point function for the summarize cycle - fetch population changes for a specified day
        """
        assert self._state == STATES.dpc_previous_population or self._state == STATES.dpc_writer_store
        self._state = STATES.ccj_api_booked_left
        assert self._current_date < self._yesterday
        self._current_date += ONE_DAY
        assert date_to_fetch == str(self._current_date)
        r_val = [randint(0, 77)]
        self._return_values[self._state] = r_val
        return r_val

    def dpc_previous_population(self):
        assert self._state == STATES.starting
        self._state = STATES.dpc_previous_population
        return {'date': str(self._starting_date)}

    def dpc_writer(self):
        assert self._state == STATES.sdp_summarize
        self._state = STATES.dpc_writer
        return self._csv_writer()

    def finished(self):
        return self._state == STATES.dpc_writer_store and self._current_date == self._yesterday

    def sdp_summarize(self, current_date, booked_left_inmates):
        assert self._state == STATES.ccj_api_booked_left
        self._state = STATES.sdp_summarize
        assert current_date == str(self._current_date)
        assert booked_left_inmates == self._return_values[STATES.ccj_api_booked_left]
        r_val = {'date': current_date, 'val': randint(44, 79)}
        self._return_values[self._state] = r_val
        return r_val

    def store(self, population_changes):
        assert self._state == STATES.dpc_writer
        self._state = STATES.dpc_writer_store
        assert population_changes == self._return_values[STATES.sdp_summarize]
