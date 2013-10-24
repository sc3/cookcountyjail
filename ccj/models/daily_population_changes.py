#
# Model for sumarized Daily Population Changes
#

from datetime import datetime
from json import dumps


class DailyPopulationChanges:

    def __init__(self):
        self.__population_counts = []

    def __expand_entry(self, entry):
        return {
            'Date': datetime.strftime(entry[0], '%Y-%m-%d'),
            'Booked': {
                'Males': {'AS': entry[1]}
            }
        }

    def query(self):
        return dumps(map(self.__expand_entry, self.__population_counts))

    def store(self, date, booked_male_as=0):
        self.__population_counts.append([date, booked_male_as])
