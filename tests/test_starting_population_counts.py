#
# Tests the program that generates the Starting Population Counts
#

import httpretty
from datetime import datetime, timedelta
from json import dumps
from random import randint
from scripts.summarize_daily_population \
    import SummarizeDailyPopulation

# select count(*) from countyapi_countyinmate
#   where booking_date < '2013-07-22' and
#   (discharge_date_earliest is null or
#    discharge_date_earliest >= '2013-07-21');

STARTING_DATE = '2013-07-22'

DAY_BEFORE = str(datetime.strptime(STARTING_DATE, '%Y-%m-%d').date() - timedelta(1))

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


class TestStartingPopulationCounts:

    @staticmethod
    def _pick_race(gender):
        distribution = FEMALE_DISTRIBUTION if gender == 'F' else MALE_DISTRIBUTION
        point = randint(1, 1000)
        for race_info in distribution:
            if race_info[0] <= point <= race_info[1]:
                return race_info[2]

    @staticmethod
    def _count_gender_race(gender, race, inmates):
        count = 0
        for inmate in inmates:
            if inmate['gender'] == gender and inmate['race'] == race:
                count +=1
        return count

    def _count_population(self, inmates):
        counts = {
            'F': {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0},
            'M': {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0},
        }
        for gender in GENDERS:
            counts[gender]['AS'] = self._count_gender_race(gender, 'A', inmates) +\
                                   self._count_gender_race(gender, 'AS', inmates)
            counts[gender]['BK'] = self._count_gender_race(gender, 'B', inmates) +\
                                   self._count_gender_race(gender, 'BK', inmates)
            counts[gender]['IN'] = self._count_gender_race(gender, 'IN', inmates)
            counts[gender]['LT'] = self._count_gender_race(gender, 'LB', inmates) +\
                                   self._count_gender_race(gender, 'LT', inmates) +\
                                   self._count_gender_race(gender, 'LW', inmates)
            counts[gender]['UN'] = self._count_gender_race(gender, 'UN', inmates)
            counts[gender]['WH'] = self._count_gender_race(gender, 'W', inmates) +\
                                   self._count_gender_race(gender, 'WH', inmates)
        for gender in GENDERS:
            total = 0
            for count in counts[gender].itervalues():
                total += count
            field_name = self._population_field_name(gender)
            counts[field_name] = total
        counts['population'] = counts['population_females'] + counts['population_males']
        return counts

    def _discharged_null_inmate_records(self, booked_before_date, number_to_make):
        how_many_to_make = {'F': number_to_make / 2, 'M': number_to_make}
        return [{'gender': gender, 'race': self._pick_race(gender)}
                for gender, count in how_many_to_make.iteritems() for i in range(0, count)]

    def _discharged_on_or_after_start_date_records(self, booked_start_date, number_to_make):
        how_many_to_make = {'F': number_to_make / 2, 'M': number_to_make}
        return [{'gender': gender, 'race': self._pick_race(gender)}
                for gender, count in how_many_to_make.iteritems() for i in range(0, count)]

    def _expected_population_values(self, population_counts):
        expected = {
            'date': DAY_BEFORE,
            'population': population_counts['population']
        }
        for gender in GENDERS:
            population_field_name = self._population_field_name(gender)
            expected[population_field_name] = population_counts[population_field_name]
            for race, count in population_counts[gender].iteritems():
                field_name = '%s_%s' % ( population_field_name, race.lower())
                expected[field_name] = count
        return [expected]

    def _population_field_name(self, gender):
        return 'population_females' if gender == 'F' else 'population_males'

    @httpretty.activate
    def test_build_starting_population_count(self):
        cook_county_url = 'http://cookcountyjail.recoveredfactory.net'
        county_inmate_api = '%s/api/1.0/countyinmate' % cook_county_url
        not_discharged_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__isnull=True' % \
            (county_inmate_api, STARTING_DATE)
        discharged_after_start_date_command = \
            '%s?format=json&limit=0&booking_date__lt=%s&discharge_date_earliest__gte=%s' % \
            (county_inmate_api, STARTING_DATE, STARTING_DATE)
        book_not_null_inmate_records = self._discharged_null_inmate_records(STARTING_DATE, randint(15, 31))
        discharged_on_or_after_start_date_records = \
            self._discharged_on_or_after_start_date_records(STARTING_DATE, randint(21, 37))
        inmates = book_not_null_inmate_records + discharged_on_or_after_start_date_records
        population_counts = self._count_population(inmates)
        expected = self._expected_population_values(population_counts)

        cook_county_get_count = {}

        def fulfill_countyapi_request(method, uri, headers):
            assert uri == not_discharged_command or uri == discharged_after_start_date_command
            if uri == not_discharged_command:
                cook_county_get_count['not_discharged_cmd'] = True
                response = {
                    'meta': {'total_count': len(book_not_null_inmate_records)},
                    'objects': book_not_null_inmate_records
                }
            else:
                cook_county_get_count['discharged_after_start_date_command'] = True
                response = {
                    'meta': {'total_count': len(discharged_on_or_after_start_date_records)},
                    'objects': discharged_on_or_after_start_date_records
                }

            return 200, headers, dumps(response)

        httpretty.register_uri(httpretty.GET, county_inmate_api,
                               body=fulfill_countyapi_request)

        starting_population = SummarizeDailyPopulation().build_starting_population()

        last_request = httpretty.last_request()
        assert last_request.method == "GET"
        assert len(cook_county_get_count) == 2
        assert starting_population == expected
