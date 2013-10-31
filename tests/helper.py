#
# Contains helper functions for testing
#


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
