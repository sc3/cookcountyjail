#
# Tests the web API wiring to class that provides daily popultaion changes
# functionality.
#

from ccj import app
from flask.json import dumps
from ccj.models.daily_population_changes import DailyPopulationChanges as DPC
import pytest

class Test_DailyPopulationChanges_API:

    def tear_down(self):
        # remove the last thing we added
        dpc = DPC('/tmp/dpc.json')
        dpc.pop()

    def test_fetch_with_nothing_stored_returns_empty_array(self):
        c = app.test_client()
        result = c.get('/daily_population_changes')
        assert result.status_code == 200

    def test_post_data_should_succeed(self):

        # key-value pairs with fake data
        data = dict(
            date='2222-02-22',
            booked_male_as='22',
        )

        # simulate a client for our application
        c = app.test_client()
        # make a POST request with data
        result = c.post('/daily_population_changes', data=data)
        # make sure data was received
        assert result.status_code == 201

        # undo what we just did 
        self.tear_down()