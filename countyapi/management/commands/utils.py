from datetime import datetime, date
import logging
import requests
from time import sleep
from random import random
from countyapi.models import CountyInmate
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


def discharge_inmates(last_date_scraped):
    """
    Discharges all the inmates who weren't seen last in the 'last date scraped'.

    Warning:
        CountyInmate.last_seen_date is a datetime field and so is the last_date_scraped param. 
        Imagine an inmate is found on datetime.datetime(2013, 8, 18, 17, 40, 18, 131163)
        And this function is ran after the scrape at datetime.datetime(2013, 8, 18, 17, 41, 13, 759409)
        Let scraped_inmate_time = datetime.datetime(2013, 8, 18, 17, 40, 18, 131163)
        Let last_date_scraped = datetime.datetime(2013, 8, 18, 17, 41, 13, 759409)
        Then the database filter last_seen_date__lt=last_date_scraped would not filter anyone. Even though both the inmates and the scrape where in the same day.
        Everyone would be discharged! This is one of the problems.
        Another would be if the scraper is ran before midnight and the discharge is done after midnight.
    """

    last_date_scraped = obj_to_datetime(last_date_scraped)
    inmates_to_discharge = CountyInmate.objects.filter(discharge_date_earliest__exact=None, last_seen_date__lt=last_date_scraped)

    for inmate in inmates_to_discharge:
        inmate.discharge_date_earliest = inmate.last_seen_date
        inmate.discharge_date_latest = last_date_scraped
        inmate.save()
    return inmates_to_discharge

def obj_to_datetime(obj_to_parse):
    """
    Converts a dictionary, string, date or datetime into a datetime.

    If obj_to_parse is a dictionary it returns a datetime object from the dictionary's 'month', 'day' and 'year' values.
    If obj_to_parse is a string it needs to be in a format of YYYY-MM-DD, it delegates the parsing to 'convert_to_datetime'.
    If obj_to_parse is a date then it uses the date's year, month and day attributes.
    If obj_to_parse is a datetime then it returns the object itself.
    Else returns None.

    """
    if isinstance(obj_to_parse, str):
        # If the object is a string use the conver_to_datetime function
        obj_to_parse = convert_to_datetime(obj_to_parse) 
        
        if obj_to_parse is None:
            # convert_to_datetime returns None if the string doen't have three '-' in the string, 
            # or if any of the splitted elements isn't convertable to an int object
            raise TypeError('obj_to_parse string could not be parsed. Does it follow the YYYY-MM-DD format?')
        else:
            return obj_to_parse

    elif isinstance(obj_to_parse, dict):
        try:
            return datetime(year=convert_to_int(obj_to_parse['year'], None), 
                                         month=convert_to_int(obj_to_parse['month'], None),
                                         day=convert_to_int(obj_to_parse['day'], None))
        except KeyError:
            raise KeyError('If obj_to_parse is a dictionary object it must have a year, month and day keys.')

    elif isinstance(obj_to_parse, date):
        return datetime(year = obj_to_parse.year, month=obj_to_parse.month, day=obj_to_parse.day)

    elif isinstance(obj_to_parse, datetime):
        return obj_to_parse

    else:
        raise TypeError("Unable to parse obj_to_parse type's")


def convert_to_date(date_to_convert):
    """
    Parses a string into datetime object. If string isn't in the right format, returns date.today().
    date_to_convert = A string object in the format of YYYY-MM-DD
    """
    today = date.today()
    date_elements = parse_str_to_date(date_to_convert)
    if date_elements:
        return date(convert_to_int(date_elements[0], today.year),
                    convert_to_int(date_elements[1], today.month),
                    convert_to_int(date_elements[2], today.day))
    return today


def convert_to_datetime(date_to_convert):
    """
    Parses a string into datetime object. If string isn't in the right format, unlike convert_to_date, returns None.
    date_to_convert = A string object in the format of YYYY-MM-DD
    """
    date_elements = parse_str_to_date(date_to_convert)
    if date_elements:
        try:
            return datetime(convert_to_int(date_elements[0], None),
                convert_to_int(date_elements[1], None),
                convert_to_int(date_elements[2], None))
        except TypeError:
            return None
    else:
        return None


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
             quiet=False, retrieval_msg="Retrieving inmate record at"):
    attempt = 1
    sleep_period = initial_sleep_period
    loud = not quiet
    while attempt <= number_attempts:
        sleep(sleep_period)
        try:
            if loud:
                log.debug("%s - %s %s " % (str(datetime.now()), retrieval_msg, url))
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


def parse_str_to_date(date_to_parse):
    """
    Converts strings of the format YYYY-MM-DD to list object splitted at '-'
    """
    date_elements = date_to_parse.split('-')
    if len(date_elements) == 3:
        return date_elements
    return None


def strip_line(line):
    return line.strip()


def strip_the_lines(lines):
    return map(strip_line, lines)
