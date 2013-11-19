
from tempfile import mkdtemp
from shutil import rmtree


from ccj.models.daily_population import DailyPopulation
from helpers import inmate_population, count_population, expected_starting_population,\
    convert_hash_values_to_integers, DAY_BEFORE, change_counts, STARTING_DATE, UpdatePopulationCounts,\
    EXCLUDE_SET


class Test_DailyPopulation_Model:

    def setup_method(self, method):
        self._tmp_dir = mkdtemp(dir='/tmp')
        self.dpc = DailyPopulation(self._tmp_dir)

    def _store_starting_population(self):
        inmates = inmate_population()
        population_counts = count_population(inmates, DAY_BEFORE)
        self.dpc.store_starting_population(population_counts)
        return population_counts

    def teardown_method(self, method):
        rmtree(self._tmp_dir)

    def test_no_data_should_return_empty_array(self):
        assert self.dpc.query() == []

    def test_with_no_starting_population(self):
        assert self.dpc.starting_population() == {}

    def test_storing_starting_population(self):
        assert self.dpc.has_no_starting_population()
        population_counts = self._store_starting_population()
        expected = expected_starting_population(population_counts)
        starting_population = self.dpc.starting_population()
        convert_hash_values_to_integers(starting_population, EXCLUDE_SET)
        assert starting_population == expected

    def test_storing_population_change(self):
        starting_population_counts = self._store_starting_population()
        starting_day_inmates = inmate_population()
        population_change_counts = change_counts(starting_day_inmates, STARTING_DATE)
        with self.dpc.writer() as f:
            f.store(population_change_counts)
        populate_change = self.dpc.query()[0]
        convert_hash_values_to_integers(populate_change, EXCLUDE_SET)
        expected = UpdatePopulationCounts(starting_population_counts, population_change_counts).dpc_format()
        assert populate_change == expected
