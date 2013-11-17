from random import randint
from ccj.models.daily_population import DailyPopulation as DPC
from tempfile import mkdtemp
from shutil import rmtree


class Test_DailyPopulationChanges_Model:

    def setup_method(self, method):
        self._tmp_dir = mkdtemp(dir='/tmp')
        self.dpc = DPC(self._tmp_dir)

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
