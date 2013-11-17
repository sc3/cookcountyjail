from random import randint
from ccj.models.daily_population import DailyPopulation as DPC
from tempfile import mkdtemp
from shutil import rmtree
import csv


class Test_DailyPopulation_Model:
    def setup_method(self, method):
        self._tmp_dir = mkdtemp(dir='/tmp')
        self.dpc = DPC(self._tmp_dir)

    def stub_starting_population_file(self):
        #row = {'a': randint(0, 1001)}
        row = {'a': '2'}
        file_name = self.dpc.starting_population_path()
        with open(file_name, 'w') as f:
            w = csv.writer(f)
            w.writerow([column_name for column_name in row.iterkeys()])
            w.writerow([value for value in row.itervalues()])
        return row

    def teardown_method(self, method):
        rmtree(self._tmp_dir)

    def test_no_data_should_return_empty_array(self):
        assert self.dpc.query() == []

    def test_multiple_data_should_return_array_with_data(self):
        expected = [
            {
                'date': '2013-10-18',
                'males_booked_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-19',
                'males_booked_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-20',
                'males_booked_as': str(randint(0, 101))
            }
        ]
        with self.dpc.writer() as f:
            for entry in expected:
                f.store(entry)
        assert self.dpc.query() == expected

    def test_successive_stores_should_be_return_array_with_data(self):
        expected1 = [
            {
                'date': '2013-10-18',
                'males_booked_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-19',
                'males_booked_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-20',
                'males_booked_as': str(randint(0, 101))
            }
        ]
        expected2 = [
            {
                'date': '2013-10-21',
                'males_booked_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-22',
                'males_booked_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-23',
                'males_booked_as': str(randint(0, 101))
            }
        ]
        with self.dpc.writer() as f:
            for entry in expected1:
                f.store(entry)
        with self.dpc.writer() as f:
            for entry in expected2:
                f.store(entry)
        assert self.dpc.query() == (expected1 + expected2)

    def test_has_starting_population(self):
        assert not self.dpc.has_starting_population()
        self.stub_starting_population_file()
        assert self.dpc.has_starting_population()

    def test_with_no_starting_population(self):
        assert self.dpc.starting_population() == []

    def test_starting_population(self):
        expected = self.stub_starting_population_file()
        assert self.dpc.starting_population() == [expected]
