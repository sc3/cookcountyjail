

class DailyPopulationCount:
    def to_json(self):
        return '[]'


class TestDailyPopulationCount:

    def test_no_data_to_json_should_return_empty_array(self):
        assert DailyPopulationCount().to_json() == '[]'
