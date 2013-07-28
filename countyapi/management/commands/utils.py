from datetime import datetime, date
import logging
import requests
from time import sleep
from random import random

############################################################################################################
#
# TODO:
#    1) Should log performance stats on fetch page
#
############################################################################################################


STD_INITIAL_SLEEP_PERIOD = 0.1
STD_NUMBER_ATTEMPTS = 3
STD_SLEEP_PERIODS = [1.61, 7, 13, 23, 41]

log = logging.getLogger('main')


def convert_to_date(date_to_convert):
    """
    Converts strings of the format YYYY-MM-DD to date object
    """
    today = date.today()
    date_elements = date_to_convert.split('-')
    if len(date_elements) != 3:
        return today
    return date(convert_to_int(date_elements[0], today.year),
                convert_to_int(date_elements[1], today.month),
                convert_to_int(date_elements[2], today.day))


def convert_to_int(possible_number, use_if_not_int):
    """
    Save conversion of string to int with ability to specify default if string is not a number
    """
    try:
        result = int(possible_number)
    except ValueError:
        result = use_if_not_int
    return result


def get_next_sleep_period(current_sleep_period, attempt):
    """
    get_next_sleep_period - implements a cascading fall off sleep period with
    a bit of randomness control the periods by setting the values in the
    array, STD_SLEEP_PERIODS
    """
    index = attempt - 1
    if index >= len(STD_SLEEP_PERIODS):
        index = -1
    return current_sleep_period * random() + STD_SLEEP_PERIODS[index]


def http_get(url, number_attempts=STD_NUMBER_ATTEMPTS,
             initial_sleep_period=STD_INITIAL_SLEEP_PERIOD,
             quiet=False):
    attempt = 1
    sleep_period = initial_sleep_period
    loud = not quiet
    while attempt <= number_attempts:
        sleep(sleep_period)
        try:
            if loud:
                log.debug("%s - Retreiving inmate %s record" % (str(datetime.now()), url))
            results = requests.get(url)
        except requests.exceptions.RequestException:
            results = None
        if results is not None and results.status_code == requests.codes.ok:
            return results
        status_code = "Exception thrown" if results is None else results.status_code
        if loud:
            log.debug("Error getting %s, status code: %s, Attempt #: %s" %
                      (url, status_code, attempt))
        sleep_period = get_next_sleep_period(sleep_period, attempt)
        attempt += 1
    return None


def http_post(url, post_values, number_attempts=STD_NUMBER_ATTEMPTS,
              initial_sleep_period=STD_INITIAL_SLEEP_PERIOD):
    attempt = 1
    sleep_period = initial_sleep_period
    while attempt <= number_attempts:
        sleep(sleep_period)
        try:
            results = requests.post(url, data=post_values)
            if results.status_code == requests.codes.ok:
                return results
        except requests.exceptions.RequestException:
            pass
        sleep_period = get_next_sleep_period(sleep_period, attempt)
        attempt += 1
    return None


def join_with_space_and_convert_spaces(segments, replace_with='-'):
    """
    Helper function joins array pieces together and then replaces any spaces
    with specified value.
    """
    return " ".join(segments).replace(" ", replace_with)


def just_empty_lines(lines):
    for line in lines:
        if len(line) > 0:
            return False
    return True


def strip_line(line):
    return line.strip()


def strip_the_lines(lines):
    return map(strip_line, lines)
