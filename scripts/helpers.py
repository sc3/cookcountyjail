#
# contains a set of helper functions
#

import os

GENDERS = ['F', 'M']

RACE_COUNTS = {'AS': 0, 'BK': 0, 'IN': 0, 'LT': 0, 'UN': 0, 'WH': 0}

RACE_MAP = {'A': 'AS', 'AS': 'AS', 'B': 'BK', 'BK': 'BK', 'IN': 'IN', 'LB': 'LT', 'LT': 'LT', 'LW': 'LT', 'W': 'WH',
            'WH': 'WH'}


def in_production():
    """
    returns true if environment variable CCJ_PRODUCTION is set to 1
    """
    ccj_production = 'CCJ_PRODUCTION'
    return ccj_production in os.environ and os.environ[ccj_production] == '1'
