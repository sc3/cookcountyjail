#
# Tests the web API wiring to class that provides dail popultaion changes
# functionality.
#

from ccj import app


class Test_API_DailPopulationChanges:

    def test_fetch_with_nothing_stored_returns_empty_array(self):
        d_c_p = app.test_client().get('/daily_population_changes')
        assert d_c_p.data == '[]'
