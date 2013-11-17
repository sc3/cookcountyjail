#
# Contains helper functions for testing
#

from os import remove
from os.path import exists
from random import randint


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


GENDERS = ['F', 'M']
DAY_BEFORE = '2013-07-21'
STARTING_DATE = '2013-07-22'


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


def count_population(inmates):
    counts = {
        'F': {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0},
        'M': {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0},
    }
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
    for gender in GENDERS:
        total = 0
        for count in counts[gender].itervalues():
            total += count
        field_name = population_field_name(gender)
        counts[field_name] = total
    counts['population'] = counts['population_females'] + counts['population_males']
    return counts


def discharged_null_inmate_records(booked_before_date, number_to_make):
    how_many_to_make = {'F': number_to_make / 2, 'M': number_to_make}
    return [{'gender': gender, 'race': pick_race(gender)}
            for gender, count in how_many_to_make.iteritems() for i in range(0, count)]


def discharged_on_or_after_start_date_inmate_records(booked_start_date, number_to_make):
    how_many_to_make = {'F': number_to_make / 2, 'M': number_to_make}
    return [{'gender': gender, 'race': pick_race(gender)}
            for gender, count in how_many_to_make.iteritems() for i in range(0, count)]


def expected_starting_population(population_counts):
    expected = {
        'date': DAY_BEFORE,
        'population': population_counts['population']
    }
    for gender in GENDERS:
        base_field_name = population_field_name(gender)
        expected[base_field_name] = population_counts[base_field_name]
        for race, count in population_counts[gender].iteritems():
            field_name = '%s_%s' % (base_field_name, race.lower())
            expected[field_name] = count
    return [expected]


def flatten_dpc_dict(entry):
    """
    Takes a Daily Population Changes returned dict and turns
    it into a flat dict. For example:

    {
        'Date': '2013-10-18',
        'Males': {
            'Booked': {'AS': '5'}
        }
    }

    BECOMES

    {
        'date': '2013-10-18',
        'booked_male_as': '5'
    }
    """

    # ugly, non-DRY code
    mydict = {}
    name = ''
    for k, v in entry.iteritems():
        name = k.lower()
        if name == 'date':
            mydict['date'] = v
        else:
            for change, population in v.iteritems():
                for race, number in population.iteritems():
                    mydict['%s_%s_%s' % (change.lower(), name, race.lower())] = number
    return mydict


def pick_race(gender):
    distribution = FEMALE_DISTRIBUTION if gender == 'F' else MALE_DISTRIBUTION
    point = randint(1, 1000)
    for race_info in distribution:
        if race_info[0] <= point <= race_info[1]:
            return race_info[2]


def population_field_name(gender):
    return 'population_females' if gender == 'F' else 'population_males'


def starting_inmate_population():
    return discharged_null_inmate_records('', randint(27, 39)) +\
        discharged_on_or_after_start_date_inmate_records('', randint(34, 51))
