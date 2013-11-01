#
# Tests the web API wiring to class that provides daily population changes
# functionality.
#

from json import loads
from random import randint
import os

from ccj.models.daily_population_changes \
    import DailyPopulationChanges as DPC
from ccj.app import app
from helper import flatten_dpc_dict


class Test_DailyPopulationChanges_API:

    def setup_method(self, method):
        self.dpc = DPC()
        app.testing = True
        self.client = app.test_client()

    def teardown_method(self, method):
        self.dpc.clear()
        os.remove(self.dpc._path)

    def test_fetch_with_nothing_stored_returns_empty_array(self):
        expected = '[]'
        result = self.client.get('/daily_population_changes')
        assert result.status_code == 200
        assert result.data == expected

    def test_post_with_one_entry_should_store_result(self):
        expected = [
            {
                'Date': '2013-10-30',
                'Males': {
                    'Booked': {'AS': str(randint(0, 101))}
                }
            }
        ]
        result = self.client.post('/daily_population_changes',
                                  data=flatten_dpc_dict(expected[0]))
        assert result.status_code == 201

        result = self.client.get('/daily_population_changes')
        assert loads(result.data, encoding='ASCII') == expected

    def test_external_post_fails(self):

        data = {
            'Date': '2013-10-30',
            'Males': {
                'Booked': {'As': str(randint(0, 101))}
            }
        }

        result = self.client.post('/daily_population_changes',
                                  data=flatten_dpc_dict(data),
                                  environ_overrides={'REMOTE_ADDR': '127.0.0.2'})
        assert result.status_code == 401
