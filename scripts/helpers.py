#
# contains a set of helper functions
#

import os


GENDER = 'gender'
GENDERS = ['F', 'M']
IN_JAIL = 'in_jail'
JAIL_ID = 'jail_id'

RACE = 'race'

RACE_ASIAN = 'AS'
RACE_ASIAN_ABBR = 'A'
RACE_BLACK = 'BK'
RACE_BLACK_ABBR = 'B'
RACE_INDIAN = 'IN'
RACE_LATINO = 'LT'
RACE_LATINO_BLACK = 'LB'
RACE_LATINO_WHITE = 'LW'
RACE_UNKNOWN = 'UN'
RACE_WHITE = 'WH'
RACE_WHITE_ABBR = 'W'

RACE_COUNTS = {RACE_ASIAN: 0, RACE_BLACK: 0, RACE_INDIAN: 0, RACE_LATINO: 0, RACE_UNKNOWN: 0, RACE_WHITE: 0}

RACE_MAP = {
    RACE_ASIAN_ABBR: RACE_ASIAN,
    RACE_ASIAN: RACE_ASIAN,
    RACE_BLACK_ABBR: RACE_BLACK,
    RACE_BLACK: RACE_BLACK,
    RACE_INDIAN: RACE_INDIAN,
    RACE_LATINO_BLACK: RACE_LATINO,
    RACE_LATINO: RACE_LATINO,
    RACE_LATINO_WHITE: RACE_LATINO,
    RACE_WHITE_ABBR: RACE_WHITE,
    RACE_WHITE: RACE_WHITE
}


def in_production():
    """
    returns true if environment variable CCJ_PRODUCTION is set to 1
    """
    ccj_production = 'CCJ_PRODUCTION'
    return ccj_production in os.environ and os.environ[ccj_production] == '1'


def map_race_id(race_id):
    if race_id in RACE_MAP:
        return RACE_MAP[race_id]
    return RACE_UNKNOWN
