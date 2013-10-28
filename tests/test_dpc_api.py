#
# Tests the web API wiring to class that provides daily population changes
# functionality.
#

from ccj import app
from flask.json import dumps
from random import randint
from ccj.models.daily_population_changes import DailyPopulationChanges as DPC
import pytest

class Test_DailyPopulationChanges_API:

    def setup_method(self, method):
        # make sure file for API backend exists
        self.dpc = DPC('/tmp/dpc.json')
        # create a client
        self.client = app.test_client()

    def teardown_method(self, method):
        # remove the last thing we added, to keep the DB clean
        self.dpc.pop()

    def test_get_with_nothing_stored_returns_empty_array(self):

        expected = []

        # make the GET call
        result = self.client.get('/daily_population_changes')

        # make sure it returned successfully
        assert result.status_code == 200

        # expect to get nothing back
        assert result.data == dumps(expected)

    def test_post_with_one_entry_should_store_result(self):

        expected = [
        {
            'Date': '2013-10-30',
            'Booked': {
                'Male': {'AS': str(randint(0, 101))}
            }
        }]

        # make a POST request with data
        result = self.client.post('/daily_population_changes', 
                                    data=self._format(expected[0]))

        # make sure data was received
        assert result.status_code == 201
        
        # make sure the data is now sent out by the API
        # (This will fail if there's already data stored before this test is run...)
        # (Have to fix this by making this test run the API with a different backing it.)
        result = self.client.get('/daily_population_changes')
        assert result.data == dumps(expected)

    def _format(self, d):
        return {'date': d['Date'], 'booked_male_as': d['Booked']['Male']['AS']}