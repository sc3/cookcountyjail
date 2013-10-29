#
# Model for sumarized Daily Population Changes
#

from flask.json import dumps
from os.path import isfile
from os import environ
import csv


class DailyPopulationChanges:

    def __init__(self):
        self._path = app.config['DPC_PATH']
        self._column_names = ['date', 'booked_male_as']
        self.initialize_file()


    def _format_stored(self, entry):
        """ Takes a flat dict, and turns it into a nested dict
            of the form expected by the API, for example: 

        {
            'date': '2013-10-18',
            'booked_male_as': '5'
        } 

        BECOMES

        {
            'Date': '2013-10-18',
            'Booked': {
                'Male': {'As': '5'}
            }
        }                                                """

        mydict = {}
        for k, v in entry.iteritems():
            levels = k.split('_')
            if len(levels) == 1:
                mydict[k.title()] = v
            else:
                temp = mydict
                for i, l in enumerate(levels):
                    l = l.title()
                    if i == len(levels)-1:
                        temp[l] = v
                    else:
                        temp[l] = {}
                    temp = temp[l] 
        return mydict


    def _format_expected(self, entry):
        """ Inverse of '_format_stored' method, mostly useful for testing.
            Takes a nested dict of the form expected by the API and turns
            it into a flat dict. For example:

        {
            'Date': '2013-10-18',
            'Booked': {
                'Male': {'As': '5'}
            }
        }

        BECOMES

        {
            'date': '2013-10-18',
            'booked_male_as': '5'
        }                                                """

        # ugly, non-DRY code
        mydict = {}
        temp = entry
        name = ''
        depth = 0
        while isinstance(temp, dict):
            depth += 1
            for k, v in temp.iteritems():
                temp = v
                if depth <= 1:
                    name = k.lower()
                else:
                    name += k.lower()
                if not isinstance(temp, dict):
                    mydict[name] = temp
                else:
                    name += '_'
        return mydict


    def initialize_file(self):
        """ Make sure the file exists. If it doesn't, first create it,
            then initialize it with our fieldnames in CSV format. """
        # make sure the file exists
        if not isfile(self._path):
            # If not, create a file and 
            # put an empty list inside it
            self.clear()


    def clear(self):
        """ Write just our fieldnames in CSV format to the file we're 
            wrapping, creating the file if it doesn't already exist. """
        # lock here
        try:
            with open(self._path, 'w') as f:
                w = csv.writer(f)
                w.writerow(self._column_names)
        except IOError:
            raise Exception("There's something wrong with the path " 
                "configured for our file's creation on your system, "
                "at '{0}'.".format(self._path))


    def store(self, entry):
        """ Append an entry to our file. Expects a dict object.

            If a non-dict-like object is stored using this method, 
            we won't know until we hit the formatting methods, 
            while querying it, which is confusing. """
        assert isinstance(entry, dict)
        # lock here
        with open(self._path, 'a') as f:
            w = csv.writer(f)
            w.writerow(entry.values())


    def query(self):
        """ Return the data stored in our file as 
            Python objects. """
        #lock here
        with open(self._path) as f:
            r = csv.DictReader(f)
            return [self._format_stored(row) for row in r]


    def to_json(self):
        """ Return the data stored in our file as JSON. """
        return dumps(self.query())



##########
#
# modules which this module's dependents are also dependent on
#
###############


from ccj.app import app