#
# Model for sumarized Daily Population Changes
#

from json import dumps
from os.path import isfile
import csv
from contextlib import contextmanager
import os.path

GENDERS = ['F', 'M']


class DailyPopulation:

    def __init__(self, dir_path):
        self._dir_path = dir_path
        self._path = os.path.join(dir_path, 'dpc.csv')
        self._column_names = ['date', 'males_booked_as']
        self._initialize_file()

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
                w.writerow(self._column_names)
        except IOError:
            raise Exception("There's something wrong with the path "
                            "configured for our file's creation on your system, "
                            "at '{0}'.".format(self._path))

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
        row = {'date': day_before_starting_date}
        self._add_population_counts(row, population_counts)
        try:
            with open(self.starting_population_path(), 'w') as f:
                w = csv.writer(f)
                w.writerow([column_name for column_name in row.iterkeys()])
                w.writerow([column_value for column_value in row.itervalues()])
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
            writer.store(dp_values_for_yesterday)
        """
        class CSV_Storer:
            def __init__(self, csv_writer):
                self._csv_writer = csv_writer

            def store(self, entry):
                """
                Append an entry to our file. Expects a dict object.
                """
                assert isinstance(entry, dict)
                self._csv_writer.writerow(entry.values())

        with open(self._path, 'a') as f:
            csv_writer = CSV_Storer(csv.writer(f))
            try:
                yield csv_writer
            finally:
                pass
