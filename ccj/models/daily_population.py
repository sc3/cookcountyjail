#
# Model for sumarized Daily Population Changes
#

from json import dumps
from os.path import isfile
import csv
from contextlib import contextmanager
import os.path
from copy import copy


ACTIONS = ['booked', 'left']
GENDER_NAME_MAP = {'F': 'females', 'M': 'males'}
GENDERS = ['F', 'M']
RACES = ['AS', 'BK', 'IN', 'LT', 'UN', 'WH']


class DailyPopulation:

    def __init__(self, dir_path):
        self._dir_path = dir_path
        self._path = os.path.join(dir_path, 'dpc.csv')
        self._initialize_file()

    def _add_booked(self, new_population, gender, population_changes):
        population_base_field_name = self._population_field_name(gender)
        booked_base_field_name = '%s_%s' % (GENDER_NAME_MAP[gender], 'booked')
        for race, counts in population_changes[gender]['booked'].iteritems():
            race_lower_case = race.lower()
            new_population['population'] += counts
            new_population[population_base_field_name] += counts
            new_population['%s_%s' % (population_base_field_name, race_lower_case)] += counts
            new_population['%s_%s' % (booked_base_field_name, race_lower_case)] = counts

    def _add_left(self, new_population, gender, population_changes):
        population_base_field_name = self._population_field_name(gender)
        booked_base_field_name = '%s_%s' % (GENDER_NAME_MAP[gender], 'left')
        for race, counts in population_changes[gender]['left'].iteritems():
            race_lower_case = race.lower()
            new_population['population'] -= counts
            new_population[population_base_field_name] -= counts
            new_population['%s_%s' % (population_base_field_name, race_lower_case)] -= counts
            new_population['%s_%s' % (booked_base_field_name, race_lower_case)] = counts

    @staticmethod
    def _add_population_counts(row, population_counts):
        row['population'] = population_counts['population']
        for gender in GENDERS:
            base_field_name = DailyPopulation._population_field_name(gender)
            row[base_field_name] = population_counts[base_field_name]
            for race, count in population_counts[gender].iteritems():
                field_name = '%s_%s' % (base_field_name, race.lower())
                row[field_name] = count

    def clear(self):
        """ Write our fieldnames in CSV format to the file we're wrapping,
            creating the file if it doesn't already exist. """
        # lock here
        try:
            with open(self._path, 'w') as f:
                w = csv.writer(f)
                w.writerow(self.column_names())
        except IOError:
            raise Exception("There's something wrong with the path "
                            "configured for our file's creation on your system, "
                            "at '{0}'.".format(self._path))

    def column_names(self):
        column_names = ['date', 'population']
        for gender in GENDERS:
            base_field_name = self._population_field_name(gender)
            column_names.append(base_field_name)
            for race in RACES:
                column_names.append('%s_%s' % (base_field_name, race.lower()))
        for gender in GENDERS:
            gender_long_name = GENDER_NAME_MAP[gender]
            for action in ACTIONS:
                for race in RACES:
                    column_names.append('%s_%s_%s' % (gender_long_name, action, race.lower()))
        return column_names

    def _dict_from_column_names(self):
        result = {}
        for column_name in self.column_names():
            result[column_name] = 0
        return result

    def has_starting_population(self):
        starting_population = self.starting_population()
        return len(starting_population) == 1

    def _initialize_file(self):
        """ Make sure the file exists. If it doesn't, first create it,
            then initialize it with our fieldnames in CSV format. """
        # make sure the file exists
        if not isfile(self._path):
            # If not, create a file and
            # put an empty list inside it
            self.clear()

    def _last_row(self):
        row = None
        with open(self._path) as f:
            rows = csv.DictReader(f)
            for cur_row in rows:
                row = cur_row
        return row

    def next_entry(self, previous_population, population_changes):
        new_population = copy(previous_population)
        new_population['date'] = population_changes['date']
        for gender in GENDERS:
            self._add_booked(new_population, gender, population_changes)
            self._add_left(new_population, gender, population_changes)
        return new_population

    @staticmethod
    def _population_field_name(gender):
        return 'population_females' if gender == 'F' else 'population_males'

    def query(self):
        """
        Return the data stored in our file as Python objects.
        """
        #lock here
        with open(self._path) as f:
            rows = csv.DictReader(f)
            query_results = [row for row in rows]
            return query_results

    def _previous_population(self):
        previous_population = self._last_row()
        if not previous_population:
            previous_population = self.starting_population()[0]
        for key, value in previous_population.iteritems():
            if key != 'date':
                previous_population[key] = int(value)
        return previous_population

    def starting_population(self):
        file_name = self.starting_population_path()
        if os.path.isfile(file_name):
            with open(file_name) as f:
                rows = csv.DictReader(f)
                starting_population = [row for row in rows]
                return starting_population
        return []

    def starting_population_path(self):
        return os.path.join(self._dir_path, 'dpc_starting_population.csv')

    def store_starting_population(self, day_before_starting_date, population_counts):
        """
        Stores the population counts in starting_population file
        Format for population counts is:
        {
            'population': 0,
            'population_females': 0,
            'population_males': 0,
            'F': {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0},
            'M': {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0},
        }
        """
        row = self._dict_from_column_names()
        row['date'] = day_before_starting_date
        self._add_population_counts(row, population_counts)
        try:
            with open(self.starting_population_path(), 'w') as f:
                w = csv.writer(f)
                w.writerow(self.column_names())
                w.writerow([row[column_name] for column_name in self.column_names()])
        except IOError:
            raise Exception("Error: writing to file %s, " % self.starting_population_path())

    def to_json(self):
        """
        Return the data stored in our file as JSON.
        """
        query_results = self.query()
        json_value = dumps(query_results)
        return json_value

    @contextmanager
    def writer(self):
        """
        Yields a writer object, so Daily Population Dict values can be stored.
        Intended to be used in a "with" statement like this:

        with dp.writer() as writer:
            writer.store(population_changes)
        """
        class CsvPopulationStore:

            def __init__(self, dpc, writer, previous_entry):
                self._dpc = dpc
                self._writer = writer
                self._previous_entry = previous_entry

            def store(self, population_changes):
                """
                Append an entry to our file. Expects a dict object.
                """
                assert isinstance(population_changes, dict)
                entry = self._dpc.next_entry(self._previous_entry, population_changes)
                self._writer.writerow([entry[column_name] for column_name in self._dpc.column_names()])
                self._previous_entry = entry

        with open(self._path, 'a') as f:
            csv_writer = CsvPopulationStore(self, csv.writer(f), self._previous_population())
            try:
                yield csv_writer
            finally:
                pass
