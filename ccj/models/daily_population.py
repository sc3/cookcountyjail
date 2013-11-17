#
# Model for sumarized Daily Population Changes
#

from json import dumps
from os.path import isfile
import csv
from contextlib import contextmanager
import os.path


class DailyPopulation:

    def __init__(self, dir_path):
        self._dir_path = dir_path
        self._path = os.path.join(dir_path, 'dpc.csv')
        self._column_names = ['date', 'males_booked_as']
        self._initialize_file()

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
