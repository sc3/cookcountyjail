
#from mock import Mock
from helpers import inmate_population, random_string, JAIL_ID, GENDER, RACE, RACE_COUNTS, map_race_id
from random import randint, choice

from scripts.in_jail_calculator import calculate_in_jail_population


FEMALES_IN_JAIL = 'females_in_jail'
HOUSING_LOC = 'housing_loc'
IN_JAIL = 'in_jail'
JOIN_FIELD_PARTS = '%s_%s'
INMATE = 'inmate'
MALES_IN_JAIL = 'males_in_jail'


def random_in_jail():
    return choice([True, False, True, True, True, True, True, True, False, True])


class HousingHistory:
    def __init__(self, inmates, housing_locations):
        self._housing_locations = housing_locations
        self._history = {}
        for inmate in inmates:
            self._history[inmate[JAIL_ID]] = {INMATE: inmate, HOUSING_LOC: housing_locations.next_loc_id()}

    def expected_values(self):
        expected = {
            IN_JAIL: 0,
            FEMALES_IN_JAIL: 0,
            MALES_IN_JAIL: 0
        }
        for race in RACE_COUNTS.iterkeys():
            expected[JOIN_FIELD_PARTS % (FEMALES_IN_JAIL, race.lower())] = 0
            expected[JOIN_FIELD_PARTS % (MALES_IN_JAIL, race.lower())] = 0
        for h_info in self._history.itervalues():
            if self._housing_locations.is_in_jail(h_info[HOUSING_LOC]):
                expected[IN_JAIL] += 1
                gender = 'females' if h_info[INMATE][GENDER] == 'F' else 'males'
                gender_in_jail = JOIN_FIELD_PARTS % (gender, IN_JAIL)
                expected[gender_in_jail] += 1
                expected[JOIN_FIELD_PARTS % (gender_in_jail, map_race_id(h_info[INMATE][RACE]).lower())] += 1
        return expected

    def inmates_latest(self, jail_id):
        return self._history[jail_id][HOUSING_LOC]


class HousingLocations:

    def __init__(self):
        self._locations = {'C SHIPMENT': {IN_JAIL: False}}
        pass

    def is_in_jail(self, loc_id):
        return self._locations[loc_id][IN_JAIL]

    def next_loc_id(self):
        index = randint(0, int(len(self._locations) * 1.2))
        if index < len(self._locations):
            for loc_id in self._locations.iterkeys():
                if index == 0:
                    return loc_id
                index -= 1
        loc_id = random_string()
        self._locations[loc_id] = {IN_JAIL: random_in_jail()}
        return loc_id


class TestStartingPopulationInJail:

    def test_starting_population_in_jail(self):
        inmates = inmate_population()
        housing_locations = HousingLocations()
        housing_history = HousingHistory(inmates, housing_locations)
        expected = housing_history.expected_values()
        stats = calculate_in_jail_population(inmates, housing_history, housing_locations)
        fields = [IN_JAIL, FEMALES_IN_JAIL, MALES_IN_JAIL]
        for race in RACE_COUNTS.iterkeys():
            fields.append(JOIN_FIELD_PARTS % (FEMALES_IN_JAIL, race.lower()))
            fields.append(JOIN_FIELD_PARTS % (MALES_IN_JAIL, race.lower()))
        for field in fields:
            # assert stats[field] == expected[field]
            if stats[field] != expected[field]:
                assert stats[field] == expected[field]


