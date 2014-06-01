#!/usr/bin/env python

from datetime import datetime, date, timedelta
import logging, argparse
import os

from scraper.scraper import Scraper
from scraper.monitor import Monitor

log = logging.getLogger('main')

#TODO: these feature controls should be move to the class that needs them, however users should be able to find them
#
# The values in these next two constants configure features, which are loaded in from environment variables
#
# The CONTROL IDS contain parametrization values for features
#
# The SWITCH IDS are used to turn on and off features
#
FEATURE_CONTROL_IDS = ['CCJ_RAW_INMATE_DATA_RELEASE_DIR', 'CCJ_RAW_INMATE_DATA_BUILD_DIR']
FEATURE_SWITCH_IDS = ['CCJ_STORE_RAW_INMATE_DATA']

NEGATIVE_VALUES = {'0', 'false'}


def env_var_active(env_var):
    """
    Calculates if an environment variable is set.
    """
    env_var_value = os.environ.get(env_var)
    return env_var_value and env_var_value.lower() not in NEGATIVE_VALUES


def feature_controls():

    def set_feature_info(cur_features_info, feature_control):
        cur_features_info[feature_control] = os.environ.get(feature_control)
        return cur_features_info

    def set_feature_switch(cur_feature_switches, feature):
        cur_feature_switches[feature] = env_var_active(feature)
        return cur_feature_switches

    return reduce(set_feature_switch,
                  FEATURE_SWITCH_IDS,
                  reduce(set_feature_info, FEATURE_CONTROL_IDS, {}))


def ng_scraper():

    parser = argparse.ArgumentParser(description="Scrape inmate data from Cook County Sheriff's site.")
    parser.add_argument('-d', '--day', action='store', dest='start_date', default=None,
                        help=('Specify day to search for missing inmates, format is YYYY-MM-DD. '
                              'If not specified, searches all days.'))
    parser.add_argument('--verbose', action="store_true", dest='verbose', default=False,
                        help='Turn on verbose mode.')

    args = parser.parse_args()

    try:
        monitor = Monitor(log, verbose_debug_mode=args.verbose)
        monitor.debug("%s - Started scraping inmates from Cook County Sheriff's site." % datetime.now())

        scraper = Scraper(monitor)
        if args.start_date:
            scraper.check_for_missing_inmates(datetime.strptime(args.start_date, '%Y-%m-%d').date())
        else:
            scraper.run(date.today() - timedelta(1), feature_controls())

        monitor.debug("%s - Finished scraping inmates from Cook County Sheriff's site." % datetime.now())
    except Exception, e:
        log.exception(e)

if __name__ == '__main__':
    ng_scraper()