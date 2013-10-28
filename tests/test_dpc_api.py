#
# Tests the web API wiring to class that provides daily population changes
# functionality.
#

from flask.json import dumps
from random import randint
from ccj.models.daily_population_changes \
        import DailyPopulationChanges as DPC
import os


class Test_DailyPopulationChanges_API:

    def setup_method(self, method):
        self.dpc = DPC()
        self.client = app.test_client()

    def teardown_method(self, method):
        self.dpc.clear()
        os.remove(self.dpc._path)

    def test_fetch_with_nothing_stored_returns_empty_array(self):

        expected = []
        result = self.client.get('/daily_population_changes')
        assert result.status_code == 200
        assert result.data == dumps(expected)

    def test_post_with_one_entry_should_store_result(self):

        expected = [
        {
            'Date': '2013-10-30',
            'Booked': {
                'Male': {'AS': str(randint(0, 101))}
            }
        }]

        result = self.client.post('/daily_population_changes', 
                                    data=self.dpc._expected_to_storage(expected[0]))
        assert result.status_code == 201

        result = self.client.get('/daily_population_changes')
        assert result.data == dumps(expected)


##########
#
# modules which this module's dependents are also dependent on
#
###############


from ccj.app import app
