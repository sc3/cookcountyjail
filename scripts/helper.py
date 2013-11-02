#
# contains a set of helper functions
#

import os


def daily_population_changes_url():
    if in_production():
        port_number, api_path = '', 'api/2.0/'
    else:
        port_number, api_path = ':5000', ''
    return 'http://127.0.0.1%s/%sdaily_population_changes' % (port_number, api_path)


def in_production():
    """
    returns true if environment variable CCJ_PRODUCTION is set to 1
    """
    ccj_production = 'CCJ_PRODUCTION'
    return ccj_production in os.environ and os.environ[ccj_production] == '1'
