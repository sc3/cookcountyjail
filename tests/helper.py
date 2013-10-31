#
# Contains helper functions for testing
#


def flatten_dpc_dict(entry):
    """
    Takes a Daily Population Changes returned dict and turns
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
    }
    """

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
