#
# Fetches the Daily Population values for a date
# and summarizes population changes for it.
#

from copy import copy
from datetime import datetime
from helpers import GENDERS, RACE_COUNTS, RACE_MAP


class SummarizeDailyPopulation:

    def __init__(self):
        self._change_counts = None

    @staticmethod
    def calculate_starting_population(inmates, population_date):
        counts = {'date': population_date}
        for gender in GENDERS:
            counts[gender] = copy(RACE_COUNTS)
        for inmate in inmates:
            race = SummarizeDailyPopulation._map_race_id(inmate)
            counts[inmate['gender']][race] += 1
        return counts

    def _count_changes(self, inmates):
        for inmate in inmates:
            #action = 'left' if inmate['discharge_date_earliest'] else 'booked'
            if inmate['discharge_date_earliest']:
                action = 'left'
            else:
                action = 'booked'
            race = self._map_race_id(inmate)
            self._change_counts[inmate['gender']][action][race] += 1

    def _initialize_change_counts(self, change_date):
        self._change_counts = {'date': change_date}
        for gender in GENDERS:
            self._change_counts[gender] = {
                'booked': copy(RACE_COUNTS),
                'left': copy(RACE_COUNTS)
            }

    @staticmethod
    def _map_race_id(inmate):
        race = inmate['race']
        return RACE_MAP[race] if race in RACE_MAP else 'UN'

    def summarize(self, change_date, inmates):
        """
        Summarizes population change by counting how many inmates where booked and how many where discharged
        Assumes that the parameter inmates contains only the set of inmates booked and the set of inmates
        discharged for the date specified in parameter change_date
        """
        self._initialize_change_counts(change_date)
        booking_date_and_time = datetime.strftime(change_date,'%Y-%m-%dT%H:%M:%S')
        self._count_changes(inmates)
        return self._change_counts
