from random import randint
from ccj.models.daily_population_changes \
    import DailyPopulationChanges as DPC
from helper import flatten_dpc_dict, safe_remove_file


class Test_DailyPopulationChanges_Model:

    def setup_method(self, method):
        self._tmp_file = '/tmp/t_dpc.tmp'
        safe_remove_file(self._tmp_file)
        self.dpc = DPC(self._tmp_file)

    def teardown_method(self, method):
        safe_remove_file(self._tmp_file)

    def test_no_data_should_return_empty_array(self):
        assert self.dpc.query() == []

    def test_one_data_should_return_array_with_data(self):
        expected = [{
            'Date': '2013-10-18',
            'Males': {
                'Booked': {'AS': str(randint(0, 101))}
            }
        }]
        data = flatten_dpc_dict(expected[0])
        self.dpc.store(data)
        assert self.dpc.query() == expected

    def test_multiple_data_should_return_array_with_data(self):
        expected = [
            {
                'Date': '2013-10-18',
                'Males': {
                    'Booked': {'AS': str(randint(0, 101))}
                }
            },
            {
                'Date': '2013-10-19',
                'Males': {
                    'Booked': {'AS': str(randint(0, 101))}
                }
            },
            {
                'Date': '2013-10-20',
                'Males': {
                    'Booked': {'AS': str(randint(0, 101))}
                }
            }
        ]
        for entry in expected:
            e = flatten_dpc_dict(entry)
            self.dpc.store(e)
        assert self.dpc.query() == expected
