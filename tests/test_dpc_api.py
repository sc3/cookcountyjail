#
# Tests the web API wiring to class that provides daily population changes
# functionality.
#

from json import loads

from ccj.app import app
from ccj.models.daily_population import DailyPopulation as DPC
from tempfile import mkdtemp
from shutil import rmtree
from helpers import inmate_population, count_population, DAY_BEFORE, change_counts, \
    UpdatePopulationCounts, EXCLUDE_SET, convert_hash_values_to_integers, expected_starting_population

DAILY_POPULATION_API_PATH = '/daily_population'
STARTING_POPULATION_API_PATH = '/starting_population'


class Test_DailyPopulationChanges_API:

    def _parseJSON(self, obj):
        if isinstance(obj, dict):
            newobj = {}
            for key, value in obj.iteritems():
                key = str(key)
                newobj[key] = self._parseJSON(value)
        elif isinstance(obj, list):
            newobj = []
            for value in obj:
                newobj.append(self._parseJSON(value))
        elif isinstance(obj, unicode):
            newobj = str(obj)
        else:
            newobj = obj
        return newobj

    def setup_method(self, method):
        app.testing = True
        self._tmp_dir = mkdtemp(dir='/tmp')
        app.config['DPC_DIR_PATH'] = self._tmp_dir
        self.dpc = DPC(self._tmp_dir)
        self.client = app.test_client()

    def _store_starting_population(self):
        inmates = inmate_population()
        population_counts = count_population(inmates, DAY_BEFORE)
        self.dpc.store_starting_population(population_counts)
        return population_counts

    def teardown_method(self, method):
        rmtree(self._tmp_dir)

    def test_fetch_with_nothing_stored_returns_empty_array(self):
        expected = '[]'
        result = self.client.get(DAILY_POPULATION_API_PATH)
        assert result.status_code == 200
        assert result.data == expected

    def test_fetch_when_has_population(self):
        starting_population_counts = self._store_starting_population()
        starting_day_inmates = inmate_population()
        population_change_counts = change_counts(starting_day_inmates)
        with self.dpc.writer() as f:
            f.store(population_change_counts)
        expected = UpdatePopulationCounts(starting_population_counts, population_change_counts).dpc_format()
        result = self.client.get(DAILY_POPULATION_API_PATH)
        assert result.status_code == 200
        fetched_data = self._parseJSON(loads(result.data)[0])
        convert_hash_values_to_integers(fetched_data, EXCLUDE_SET)
        assert fetched_data == expected

    def test_external_post_fails(self):

        data = {}
        result = self.client.post('/daily_population', 
                        data=data, 
                        environ_overrides={'REMOTE_ADDR': '8.8.8.8'})
        assert result.status_code == 401

    def test_starting_population_api(self):
        starting_population_counts = self._store_starting_population()
        expected = expected_starting_population(starting_population_counts)
        result = self.client.get(STARTING_POPULATION_API_PATH)
        assert result.status_code == 200
        fetched_data = self._parseJSON(loads(result.data))
        convert_hash_values_to_integers(fetched_data, EXCLUDE_SET)
        assert fetched_data == expected
