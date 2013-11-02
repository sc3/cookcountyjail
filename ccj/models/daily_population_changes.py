#
# Model for sumarized Daily Population Changes
#

from json import dumps
from os.path import isfile
import csv


class DailyPopulationChanges:

    def __init__(self, path, logger=None):
        self._path = path
        self._column_names = ['date', 'booked_males_as']
        self._logger = logger
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

    def _format_stored(self, entry):
        """
        Takes a flat dict, and turns it into a nested dict
        of the form expected by the API, for example:

        {
            'date': '2013-10-18',
            'booked_males_as': '5'
        }

        BECOMES

        {
            'Date': '2013-10-18',
            'Males': {
                'Booked': {'AS': '5'}
            }
        }
        """

        mydict = {'Males': {'Booked': {'AS': None}}}
        for k, v in entry.iteritems():
            levels = k.split('_')
            if len(levels) == 1:
                mydict[k.title()] = v
            else:
                change = levels[0].capitalize()
                gender = levels[1].capitalize()
                race = levels[2].upper()
                mydict[gender][change][race] = v
        return mydict

    def _initialize_file(self):
        """ Make sure the file exists. If it doesn't, first create it,
            then initialize it with our fieldnames in CSV format. """
        # make sure the file exists
        if not isfile(self._path):
            # If not, create a file and
            # put an empty list inside it
            self.clear()

    def _debug_log(self, message):
        if self._logger:
            self._logger.debug(message)

    def store(self, entry):
        """
        Append an entry to our file. Expects a dict object.

        If a non-dict-like object is stored using this method,
        we won't know until we hit the formatting methods,
        while querying it, which is confusing.
        """
        assert isinstance(entry, dict)
        # lock here
        with open(self._path, 'a') as f:
            w = csv.writer(f)
            w.writerow(entry.values())

    def query(self):
        """
        Return the data stored in our file as Python objects.
        """
        #lock here
        self._debug_log('Entered query')
        with open(self._path) as f:
            r = csv.DictReader(f)
            query_results = [self._format_stored(row) for row in r]
            self._debug_log('Exiting query')
            return query_results

    def to_json(self):
        """
        Return the data stored in our file as JSON.
        """
        self._debug_log('Entered to_json')
        query_results = self.query()
        self._debug_log('In to_json - converting query results to json')
        json_value = dumps(query_results)
        self._debug_log('Exiting to_json')
        return json_value
