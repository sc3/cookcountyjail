from datetime import datetime
from random import randint
from flask.json import dumps
from ccj.models.daily_population_changes \
    import DailyPopulationChanges as DPC
import os

class Test_DailyPopulationChanges_Model:

    def setup_method(self, method):
        self.dpc = DPC()

    def teardown_method(self, method):
        self.dpc.clear()
        os.remove(self.dpc._path)

    def test_no_data_should_return_empty_array(self):
        assert self.dpc.query() == []

    def test_one_data_should_return_array_with_data(self):
        expected = [{
            'Date': '2013-10-18',
            'Booked': {
                'Male': {'As': str(randint(0, 101))}
            }
        }]
        data = self.dpc._format_expected(expected[0])
        self.dpc.store(data)
        assert self.dpc.query() == expected

    def test_multiple_data_should_return_array_with_data(self):
        expected = [
        {
            'Date': '2013-10-18',
            'Booked': {
                'Male': {'As': str(randint(0, 101))}
            }
        },
        {
            'Date': '2013-10-19',
            'Booked': {
                'Male': {'As': str(randint(0, 101))}
            }
        },
        {
            'Date': '2013-10-20',
            'Booked': {
                'Male': {'As': str(randint(0, 101))}
            }
        }
        ]
        for entry in expected:
            e = self.dpc._format_expected(entry)
            self.dpc.store(e)
        assert self.dpc.query() == expected




##########
#
# modules which this module's dependents are also dependent on
#
###############


from ccj.app import app

