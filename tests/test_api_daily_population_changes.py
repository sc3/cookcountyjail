#
# Tests the web API wiring to class that provides dail popultaion changes
# functionality.
#

from ccj import app
from flask.json import dumps

class Test_API_DailyPopulationChanges:

    def test_fetch_with_nothing_stored_returns_empty_array(self):
        d_c_p = app.test_client().get('/daily_population_changes')
        assert d_c_p.data == '[]'

    def test_post_with_nothing_sent_returns_empty_array(self):

        # catch errors here if they occur
        app.config['TESTING'] = True

        # fake data
        expected = {}

        with app.test_client() as c:

            # make a POST request with data
            response = c.post('/daily_population_changes', 
                            data=dumps(expected), 
                            content_type='application/json')

            # make sure data was received
            assert response.status_code == 201

            d_c_p = app.test_client().get('/daily_population_changes')
            assert d_c_p.data == '[]'


