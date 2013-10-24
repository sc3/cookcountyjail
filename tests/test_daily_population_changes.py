from datetime import datetime
from random import randint
from json import dumps
from ccj.models.daily_population_changes import DailyPopulationChanges


class TestDailyPopulationChanges:

    def test_no_data_to_json_should_return_empty_array(self):
        assert DailyPopulationChanges().query() == '[]'

    def test_one_data_to_json_should_return_array_with_data(self):
        d_p_c = DailyPopulationChanges()
        expected = {
            'Date': '2013-10-18',
            'Booked': {
                'Males': {'AS': randint(0, 101)}
            }
        }
        self.__store_population_count(d_p_c, expected)
        assert d_p_c.query() == dumps([expected])

    def test_multiple_data_to_json_should_return_array_with_data(self):
        d_p_c = DailyPopulationChanges()
        expected = [
            {
                'Date': '2013-10-15',
                'Booked': {
                    'Males': {'AS': randint(0, 101)}
                }
            },
            {
                'Date': '2013-10-16',
                'Booked': {
                    'Males': {'AS': randint(0, 101)}
                }
            },
            {
                'Date': '2013-10-17',
                'Booked': {
                    'Males': {'AS': randint(0, 101)}
                }
            }
        ]
        for entry in expected:
            self.__store_population_count(d_p_c, entry)
        assert d_p_c.query() == dumps(expected)

    def __store_population_count(self, d_p_c, entry):
        d_p_c.store(datetime.strptime(entry['Date'], '%Y-%m-%d'),
                    booked_male_as=entry['Booked']['Males']['AS']
                    )
