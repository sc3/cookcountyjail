from random import randint
from ccj.models.daily_population import DailyPopulation as DPC
from helper import safe_remove_file


class Test_DailyPopulationChanges_Model:

    def setup_method(self, method):
        self._tmp_file = '/tmp/t_dpc.tmp'
        safe_remove_file(self._tmp_file)
        self.dpc = DPC(self._tmp_file)

    def teardown_method(self, method):
        safe_remove_file(self._tmp_file)

    def test_no_data_should_return_empty_array(self):
        assert self.dpc.query() == []

    def test_multiple_data_should_return_array_with_data(self):
        expected = [
            {
                'date': '2013-10-18',
                'booked_males_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-19',
                'booked_males_as': str(randint(0, 101))
            },
            {
                'date': '2013-10-20',
                'booked_males_as': str(randint(0, 101))
            }
        ]
        with self.dpc.writer() as f:
            for entry in expected:
                f.store(entry)
        assert self.dpc.query() == expected
