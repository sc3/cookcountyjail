from random import randint
from tempfile import mkdtemp
from shutil import rmtree
import csv

from ccj.models.daily_population import DailyPopulation
from helpers import inmate_population, count_population, expected_starting_population,\
    convert_hash_values_to_integers, DAY_BEFORE, change_counts, STARTING_DATE, UpdatePopulationCounts

EXCLUDE_SET = set(['date'])


class Test_DailyPopulation_Model:

    def setup_method(self, method):
        self._tmp_dir = mkdtemp(dir='/tmp')
        self.dpc = DailyPopulation(self._tmp_dir)

    def _store_starting_population(self):
        inmates = inmate_population()
        population_counts = count_population(inmates)
        self.dpc.store_starting_population(DAY_BEFORE, population_counts)
        return population_counts

    def teardown_method(self, method):
        rmtree(self._tmp_dir)

    def test_no_data_should_return_empty_array(self):
        assert self.dpc.query() == []
    #
    #def test_multiple_data_should_return_array_with_data(self):
    #    expected = [
    #        {
    #            'date': '2013-10-18',
    #            'males_booked_as': str(randint(0, 101))
    #        },
    #        {
    #            'date': '2013-10-19',
    #            'males_booked_as': str(randint(0, 101))
    #        },
    #        {
    #            'date': '2013-10-20',
    #            'males_booked_as': str(randint(0, 101))
    #        }
    #    ]
    #    with self.dpc.writer() as f:
    #        for entry in expected:
    #            f.store(entry)
    #    assert self.dpc.query() == expected
    #
    #def test_successive_stores_should_be_return_array_with_data(self):
    #    expected1 = [
    #        {
    #            'date': '2013-10-18',
    #            'males_booked_as': str(randint(0, 101))
    #        },
    #        {
    #            'date': '2013-10-19',
    #            'males_booked_as': str(randint(0, 101))
    #        },
    #        {
    #            'date': '2013-10-20',
    #            'males_booked_as': str(randint(0, 101))
    #        }
    #    ]
    #    expected2 = [
    #        {
    #            'date': '2013-10-21',
    #            'males_booked_as': str(randint(0, 101))
    #        },
    #        {
    #            'date': '2013-10-22',
    #            'males_booked_as': str(randint(0, 101))
    #        },
    #        {
    #            'date': '2013-10-23',
    #            'males_booked_as': str(randint(0, 101))
    #        }
    #    ]
    #    with self.dpc.writer() as f:
    #        for entry in expected1:
    #            f.store(entry)
    #    with self.dpc.writer() as f:
    #        for entry in expected2:
    #            f.store(entry)
    #    assert self.dpc.query() == (expected1 + expected2)

    def test_with_no_starting_population(self):
        assert self.dpc.starting_population() == []

    def test_storing_starting_population(self):
        assert not self.dpc.has_starting_population()
        population_counts = self._store_starting_population()
        expected = expected_starting_population(population_counts)
        starting_population = self.dpc.starting_population()
        convert_hash_values_to_integers(starting_population[0], EXCLUDE_SET)
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
        #assert populate_change == [expected]
        for key, value in populate_change.iteritems():
            expected_value = expected[key]
            assert value == expected_value
