
from helpers import GENDER, IN_JAIL, JAIL_ID, map_race_id, RACE_COUNTS, RACE
from copy import copy

FEMALES_IN_JAIL = 'females_in_jail'
MALES_IN_JAIL = 'males_in_jail'


def _add_gender_race_counts(r_val, gender_in_jail, gender_population_total, race_counts):
    r_val[gender_in_jail] = gender_population_total
    for race, counts in race_counts.iteritems():
        r_val['%s_%s' % (gender_in_jail, race.lower())] = counts


def calculate_in_jail_population(inmates, housing_history, housing_locations):
    population_count = 0
    females = 0
    males = 0
    female_counts = copy(RACE_COUNTS)
    male_counts = copy(RACE_COUNTS)
    for inmate in inmates:
        housing_location_id = housing_history.inmates_latest(inmate[JAIL_ID])
        if housing_locations.is_in_jail(housing_location_id):
            population_count += 1
            if inmate[GENDER] == 'F':
                females += 1
                female_counts[map_race_id(inmate[RACE])] += 1
            else:
                males += 1
                male_counts[map_race_id(inmate[RACE])] += 1
    r_val = {IN_JAIL: population_count}
    _add_gender_race_counts(r_val, FEMALES_IN_JAIL, females, female_counts)
    _add_gender_race_counts(r_val, MALES_IN_JAIL, males, male_counts)
    return r_val
