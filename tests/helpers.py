#
# Contains helper functions for testing
#

from random import randint
from datetime import datetime, date, timedelta
from copy import copy
from scripts.helpers import RACE_MAP


#
# The following distribution are based on analysis of inmates collected from
# Cook County Jail from January 1st, 013 to November 1st, 2013
#
# The distribution was scaled to 1000, a slight skew was introduced to handle
# A and U race inmates by scaling them up to 1.
#
FEMALE_DISTRIBUTION = [
    [1, 1, 'A'],
    [2, 6, 'AS'],
    [7, 8, 'B'],
    [9, 708, 'BK'],
    [709, 710, 'IN'],
    [711, 715, 'LB'],
    [716, 745, 'LT'],
    [746, 806, 'LW'],
    [807, 807, 'U'],
    [808, 809, 'W'],
    [810, 1000, 'WH']
]

MALE_DISTRIBUTION = [
    [1, 1, 'A'],
    [2, 7, 'AS'],
    [8, 8, 'B'],
    [9, 714, 'BK'],
    [715, 715, 'IN'],
    [716, 718, 'LB'],
    [719, 819, 'LT'],
    [820, 885, 'LW'],
    [886, 886, 'U'],
    [887, 888, 'W'],
    [889, 1000, 'WH']
]

ACTIONS = ['booked', 'left']

EXCLUDE_SET = {'date'}

GENDER_NAME_MAP = {'F': 'females', 'M': 'males'}
GENDERS = ['F', 'M']
DAY_BEFORE = '2013-07-21'
STARTING_DATE = '2013-07-22'
NEXT_DAY = '2013-07-23'
NAME_FORMATTER = '%s_%s'

RACE_COUNTS = {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0}


def change_counts(inmates):
    starting_datetime = STARTING_DATE + 'T00:00:00'
    counts = initialize_change_counts()
    for inmate in inmates:
        if inmate['booking_date'] == starting_datetime:
            action = 'booked'
        else:
            action = 'left'
        race = inmate['race']
        race = RACE_MAP[race] if race in RACE_MAP else 'UN'
        counts[inmate['gender']][action][race] += 1
    return counts


def convert_hash_values_to_integers(hash_to_convert, excluding):
    for key, value in hash_to_convert.iteritems():
        if key not in excluding:
            hash_to_convert[key] = int(value)


def count_gender_race(gender, race, inmates):
    count = 0
    for inmate in inmates:
        if inmate['gender'] == gender and inmate['race'] == race:
            count +=1
    return count


def count_population(inmates, population_date=None, calculate_totals=True):
    counts = {}
    if population_date:
        counts['date'] = population_date
    for gender in GENDERS:
        counts[gender] = copy(RACE_COUNTS)
    for gender in GENDERS:
        counts[gender]['AS'] = count_gender_race(gender, 'A', inmates) +\
                               count_gender_race(gender, 'AS', inmates)
        counts[gender]['BK'] = count_gender_race(gender, 'B', inmates) +\
                               count_gender_race(gender, 'BK', inmates)
        counts[gender]['IN'] = count_gender_race(gender, 'IN', inmates)
        counts[gender]['LT'] = count_gender_race(gender, 'LB', inmates) +\
                               count_gender_race(gender, 'LT', inmates) +\
                               count_gender_race(gender, 'LW', inmates)
        counts[gender]['UN'] = count_gender_race(gender, 'UN', inmates)
        counts[gender]['WH'] = count_gender_race(gender, 'W', inmates) +\
                               count_gender_race(gender, 'WH', inmates)
    if calculate_totals:
        for gender in GENDERS:
            total = 0
            for count in counts[gender].itervalues():
                total += count
            field_name = population_field_name(gender)
            counts[field_name] = total
        counts['population'] = counts['population_females'] + counts['population_males']
    return counts


def discharged_null_inmate_records(number_to_make):
    starting_datetime = STARTING_DATE + 'T00:00:00'
    how_many_to_make = {'F': number_to_make / 2, 'M': number_to_make}
    return [{'gender': gender, 'race': pick_race(gender), 'booking_date': starting_datetime,
             'discharge_date_earliest': None}
            for gender, count in how_many_to_make.iteritems() for i in range(0, count)]


def discharged_on_or_after_start_date_inmate_records(number_to_make, discharged_date='Random'):
    how_many_to_make = {'F': number_to_make / 2, 'M': number_to_make}
    discharge_date = RandomDates(discharged_date)
    return [{'gender': gender, 'race': pick_race(gender), 'booking_date': DAY_BEFORE,
             'discharge_date_earliest': discharge_date.next()}
            for gender, count in how_many_to_make.iteritems() for i in range(0, count)]


def expected_starting_population(population_counts):
    expected = {
        'date': DAY_BEFORE,
        'population': population_counts['population']
    }
    for gender in GENDERS:
        for action in ACTIONS:
            base_field_name = NAME_FORMATTER % (GENDER_NAME_MAP[gender], action)
            for race in RACE_COUNTS.iterkeys():
                expected[NAME_FORMATTER % (base_field_name, race.lower())] = 0
    for gender in GENDERS:
        base_field_name = population_field_name(gender)
        expected[base_field_name] = population_counts[base_field_name]
        action_base_field_name = NAME_FORMATTER % (GENDER_NAME_MAP[gender], 'booked')
        for race, count in population_counts[gender].iteritems():
            field_name = NAME_FORMATTER % (base_field_name, race.lower())
            expected[field_name] = count
            expected[NAME_FORMATTER % (action_base_field_name, race.lower())] = count
    return expected


def initialize_change_counts(cur_date=STARTING_DATE):
    counts = {'date': cur_date}
    for gender in GENDERS:
        counts[gender] = {
            'booked': copy(RACE_COUNTS),
            'left': copy(RACE_COUNTS)
        }
    return counts


def inmate_population():
    low, high = 34, 51
    return discharged_null_inmate_records(randint(low, high)) +\
        discharged_on_or_after_start_date_inmate_records(randint(low, high))


def pick_race(gender):
    distribution = FEMALE_DISTRIBUTION if gender == 'F' else MALE_DISTRIBUTION
    point = randint(1, 1000)
    for race_info in distribution:
        if race_info[0] <= point <= race_info[1]:
            return race_info[2]


def population_field_name(gender):
    return 'population_females' if gender == 'F' else 'population_males'


class RandomDates:

    def __init__(self, starting_date):
        if starting_date.lower() == 'random':
            self._starting_date = datetime.strptime(NEXT_DAY, '%Y-%m-%d').date()
            self._number_days = (date.today() - self._starting_date).days - 1
            self._one_day = timedelta(1)
            self._next = self._random_next
        else:
            self._starting_date = starting_date
            self._next = self._static_next

    def next(self):
        return self._next()

    def _random_next(self):
        return str(self._starting_date + (self._one_day * randint(0, self._number_days))) + 'T01:01:01'

    def _static_next(self):
        return self._starting_date


class UpdatePopulationCounts:

    def __init__(self, starting_population_counts, population_change_counts):
        self._population_change_counts = population_change_counts
        self._new_population_counts = copy(starting_population_counts)
        self._new_population_counts['date'] = population_change_counts['date']

    def dpc_format(self):
        self._update_counts()
        return self._dpc_format()

    def _dpc_format(self):
        dpc_formatted = {'date': self._new_population_counts['date']}
        dpc_formatted['population'] = self._new_population_counts['population']
        for gender in GENDERS:
            base_field_name = population_field_name(gender)
            dpc_formatted[base_field_name] = self._new_population_counts[base_field_name]
            for race, counts in self._new_population_counts[gender].iteritems():
                dpc_formatted[NAME_FORMATTER % (base_field_name, race.lower())] = counts
        for gender in GENDERS:
            for action, race_counts in self._population_change_counts[gender].iteritems():
                base_field_name = NAME_FORMATTER % (GENDER_NAME_MAP[gender], action)
                for race, counts in race_counts.iteritems():
                    dpc_formatted[NAME_FORMATTER % (base_field_name, race.lower())] = counts
        return dpc_formatted

    def _update_counts(self):
        self._new_population_counts['population'] = 0
        for gender in GENDERS:
            self._update_booked(gender)
            self._update_left(gender)
            self._new_population_counts['population'] += self._new_population_counts[population_field_name(gender)]

    def _update_booked(self, gender):
        field_name = population_field_name(gender)
        for race, counts in self._population_change_counts[gender]['booked'].iteritems():
            self._new_population_counts[field_name] += counts
            self._new_population_counts[gender][race] += counts

    def _update_left(self, gender):
        field_name = population_field_name(gender)
        for race, counts in self._population_change_counts[gender]['left'].iteritems():
            self._new_population_counts[field_name] -= counts
            self._new_population_counts[gender][race] -= counts
