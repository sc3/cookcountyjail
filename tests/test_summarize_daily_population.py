
from scripts.summarize_daily_population import SummarizeDailyPopulation
from helpers import change_counts, count_population, inmate_population, STARTING_DATE


class Test_SummarizeDailyPopulation:

    def setup_method(self, method):
        self.sdp = SummarizeDailyPopulation()

    def test_calculate_starting_population(self):
        inmates = inmate_population()
        expected = count_population(inmates, STARTING_DATE, calculate_totals=False)
        starting_population = self.sdp.calculate_starting_population(inmates, STARTING_DATE)
        assert starting_population == expected

    def test_summarize_population_changes(self):
        inmates = inmate_population()
        expected = change_counts(inmates)
        assert self.sdp.summarize(STARTING_DATE, inmates) == expected

