from datetime import datetime, date
import logging
from pyquery import PyQuery as pq
import requests
from time import sleep
from random import random
import re

from django.db.utils import DatabaseError

from countyapi.models import CountyInmate, CourtLocation, HousingLocation


NUMBER_OF_ATTEMPTS = 5
STD_INITIAL_SLEEP_PERIOD = 0.25
STD_NUMBER_ATTEMPTS = 3
STD_SLEEP_PERIODS = [1.61, 7, 13, 23, 41]

log = logging.getLogger('main')


def convert_to_int(possible_number, use_if_not_int):
    """
    Save conversion of string to int with ability to specify default if string is not a number
    """
    try:
        result = int(possible_number)
    except ValueError:
        result = use_if_not_int
    return result


def create_update_inmate(url):
    """
    Fetches inmates detail page and creates or updates inmates record based on it,
    otherwise returns as inmate's details were not found
    """
    inmate_details = InmateDetails(url)
    if not inmate_details.found():
        return None

    inmate, created = inmate_record_get_or_create(inmate_details)
    store_booking_date(inmate, inmate_details)
    store_physical_characteristics(inmate, inmate_details)
    store_housing_location(inmate, inmate_details)
    store_bail_info(inmate, inmate_details)
    store_charges(inmate, inmate_details)
    store_next_court_info(inmate, inmate_details)
    inmate.save()
    log.debug("%s - %s inmate %s" % (str(datetime.now()), "Created" if created else "Updated", inmate))
    return inmate.jail_id


def fetch_page(url, number_attempts=STD_NUMBER_ATTEMPTS, initial_sleep_period=STD_INITIAL_SLEEP_PERIOD):
    attempt = 1
    sleep_period = initial_sleep_period
    while attempt <= number_attempts:
        sleep(sleep_period)
        try:
            log.debug("%s - Retreiving inmate %s record" % (str(datetime.now()), url))
            results = requests.get(url)
        except requests.exceptions.RequestException:
            results = None
        if results is not None and results.status_code == requests.codes.ok:
            return results
        status_code = "Exception thrown" if results is None else results.status_code
        log.debug("Error getting %s, status code: %s, Attempt #: %s" % (url, status_code, attempt))
        sleep_period = get_next_sleep_period(sleep_period, attempt)
        attempt += 1
    return None


def get_next_sleep_period(current_sleep_period, attempt):
    """
    get_next_sleep_period - implements a cascading fall off sleep period with a bit of randomness
    control the periods by setting the values in the array, STD_SLEEP_PERIODS
    """
    index = attempt - 1
    if index >= len(STD_SLEEP_PERIODS):
        index = -1
    return current_sleep_period * random() + STD_SLEEP_PERIODS[index]


def inmate_record_get_or_create(inmate_details):
    """
    Gets or creates inmate record based on jail_id and stores the url used to fetch the inmate info
    """
    inmate, created = CountyInmate.objects.get_or_create(jail_id=inmate_details.jail_id())
    inmate.url = inmate_details.url
    return inmate, created


def join_with_space_and_convert_spaces(segments, replace_with='-'):
    """
    Helper function joins array pieces together and then replaces any spaces with specified value
    """
    return " ".join(segments).replace(" ", replace_with)


def parse_court_location(location_string):
    """
    Takes a location string of the form:

    "Criminal C\nCriminal Courts Building, Room:506\n2650 South California Avenue Room: 506\nChicago, IL 60608"

    The lines can contain spurious white-space at the beginning and end of the lines, these are stripped

     and returns two values, cleaned up version the input string and a dict of the form:
    {
        'location_name': 'Criminal C',
        'branch_name': 'Criminal Courts Building',
        'room_number': 506,
        'address': '2650 South California Avenue',
        'city': 'Chicago',
        'state': 'IL',
        'zip_code': 60608,
    }

    If location is malformed, then original location string is returned with an empty dict
    """

    lines = strip_the_lines(location_string.splitlines())
    if len(lines) == 4:
        try:
            # The first line is the location_name
            location_name = lines[0]

            # Second line must be split into room number and branch name
            branch_line = lines[1].split(', Room:')
            branch_name = branch_line[0].strip()
            room_number = convert_to_int(branch_line[1], 0)

            # Third line has address - remove room number and store
            address = lines[2].split('Room:')[0].strip()

            # Fourth line has city, state and zip separated by spaces,
            # or a weird unicode space character
            city_state_zip = lines[3].replace(u'\xa0', u' ').split(' ')

            city = " ".join(city_state_zip[0:-2]).replace(',', '').strip()
            state = city_state_zip[-2].strip()
            zip_code = convert_to_int(city_state_zip[-1], 60639)

            d = {
                'location_name': location_name,
                'branch_name': branch_name,
                'room_number': room_number,
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
            }
            return "\n".join(lines), d

        except IndexError:
            log.debug("Following Court location has unknown format: %s" % location_string)
            return location_string, {}

    else:
        log.debug("Following Court location doesn't have right number of lines: %s" % location_string)
        return location_string, {}


def process_housing_location(location_object):
    """
    Receives a housing location from the HousingLocation table and parses it editing the different fields
    """
    location_segments = location_object.housing_location.replace("-", " ").split()  # Creates a list with the housing location information

    if location_segments == [] or convert_to_int(location_segments[0], None) is None:
        # Location did not start with a number so no further parsing
        if location_object.housing_location == "":
            location_object.housing_location = "UNKNOWN"
        return

    location_object.division = location_segments[0]
    if len(location_segments) == 1:  # Executed only if the housing information is a single division number ex: '01-'
        return

    set_day_release(location_object, location_segments)

    location_start = convert_to_int(location_segments[0], -1)

    if location_start in [2, 8, 9, 11, 14] or (location_start == 1 and "ABO" in location_object.housing_location):
        set_sub_division(location_object, location_segments[1], location_segments[2:])
        return
    elif location_start == 3:
        if "AX" in location_object.housing_location:
            set_sub_division(location_object, location_segments[2], location_segments[3:])
            return
    elif location_start in [5, 6, 10]:
        set_sub_division(location_object, location_segments[2] + location_segments[1], location_segments[3:])
        return
    elif location_start == 15:
        set_location_15_values(location_object, location_segments)
        return
    elif location_start == 16:
        return
    elif location_start == 17:
        set_location_17_values(location_object, location_segments)
        return
    elif location_start == 4:
        set_location_04_values(location_object, location_segments)

    set_sub_division(location_object, join_with_space_and_convert_spaces(location_segments[1:3], ""), location_segments[3:])
    return


def process_urls(base_url, inmate_urls, records, limit=None):
    """
    Initiates processing of based in inmate_urls
    """
    processed_jail_ids = []  # List to record processed jail ids in

    for url in inmate_urls:
        url = "%s/%s" % (base_url, url.attrib['href'])
        new_id = create_update_inmate(url)
        if new_id is not None and new_id not in processed_jail_ids:
            processed_jail_ids.append(new_id)
        if limit and (records + len(processed_jail_ids)) >= limit:
            break

    return processed_jail_ids


def set_day_release(location_object, location_segments):
    for element in location_segments:
        if element == "DR":
            location_object.in_program = "Day Release"
            location_object.in_jail = False
        elif element == "DRAW":
            location_object.in_program == "Day Release, AWOL"
            location_object.in_jail = False


def set_location_04_values(location_object, location_segments):
    if "M1" in location_object.housing_location:
        location_object.in_program = "Protective Custody"
    elif "N1" in location_object.housing_location:
        location_object.in_program = "Segregation"


def set_location_15_values(location_object, location_segments):
    if location_segments[1] == "EM":
        location_object.in_program = "Electronic Monitoring"
        location_object.in_jail = False
    elif location_segments[1] == "EMAW":
        location_object.in_program = "Electronic Monitoring, AWOL"
        location_object.in_jail = False
    elif location_segments[1] in ["KK", "LV", "US"]:
        location_object.in_program = "Other County"
        location_object.in_jail = False
    else:
        location_object.sub_division = location_segments[1]


def set_location_17_values(location_object, location_segments):
    if location_segments[1] == "MOMS":
        location_object.in_program = "MOMS Program"
    elif location_segments[1] == "SFFP":
        location_object.in_program = "Sherrif Female Furlough Program"
        location_object.in_jail = False
    elif location_segments[1] == "SFFPAW":
        location_object.in_program = "Sherrif Female Furlough Program, AWOL"
        location_object.in_jail = False


def set_sub_division(location_object, sub_division, sub_division_location):
    location_object.sub_division = sub_division
    location_object.sub_division_location = join_with_space_and_convert_spaces(sub_division_location)


def store_bail_info(inmate, inmate_details):
    # Bond: If the value is an integer, it's a dollar
    # amount. Otherwise, it's a status, e.g. "* NO BOND *".
    inmate.bail_amount = convert_to_int(inmate_details.bail_amount().replace(',', ''), None)
    if inmate.bail_amount is None:
        inmate.bail_status = inmate_details.bail_amount().replace('*', '').strip()
    else:
        inmate.bail_status = None


def store_booking_date(inmate, inmate_details):
    inmate.booking_date = inmate_details.booking_date().strftime('%Y-%m-%d')


def store_charges(inmate, inmate_details):
    """
    Stores the inmates charges if they are new or if they have been changes
    Charges: charges come on two lines. The first line is a citation and the
    # second is an optional description of the charges.
    """
    charges = strip_the_lines(inmate_details.charges().splitlines())
    if charges == []:
        return

    # Capture Charges and Citations if specified
    parsed_charges = charges[0]
    parsed_charges_citation = charges[1] if len(charges) > 1 else ''

    if len(inmate.charges_history.all()) != 0:
        inmate_latest_charge = inmate.charges_history.latest('date_seen')  # last known charge
        # if the last known charge is different than the current info then create a new charge
        if inmate_latest_charge.charges != parsed_charges or inmate_latest_charge.charges_citation != parsed_charges_citation:
            new_charge = inmate.charges_history.create(charges=parsed_charges, charges_citation=parsed_charges_citation)
            new_charge.date_seen = datetime.now().date()
            new_charge.save()
    else:
        # if the inmate has no charges then create a new one with the parsed info
        new_charge = inmate.charges_history.create(charges=parsed_charges, charges_citation=parsed_charges_citation)
        new_charge.date_seen = datetime.now().date()
        new_charge.save()


def store_housing_location(inmate, inmate_details):
    inmate.housing_location = inmate_details.housing_location()
    inmate_housing_location, created_location = HousingLocation.objects.get_or_create(housing_location=inmate.housing_location)
    process_housing_location(inmate_housing_location)
    try:
        housing_history, new_history = inmate.housing_history.get_or_create(housing_location=inmate_housing_location)
        if new_history:
            housing_history.housing_date = date.today()
        housing_history.save()
        inmate_housing_location.save()
    except DatabaseError:
        log.debug("Could not save housing location '%s'" % inmate.housing_location)


def store_next_court_info(inmate, inmate_details):
    # Court date parsing
    next_court_date = inmate_details.next_court_date()
    if next_court_date is not None:
        # Get location record by parsing next Court location string
        next_court_location, parsed_location = parse_court_location(inmate_details.court_house_location())
        location, new_location = CourtLocation.objects.get_or_create(location=next_court_location, **parsed_location)

        # Get or create a court date for this inmate
        court_date, new_court_date = inmate.court_dates.get_or_create(date=next_court_date.strftime('%Y-%m-%d'), location=location)


def store_physical_characteristics(inmate, inmate_details):
    inmate.gender = inmate_details.gender()
    inmate.race = inmate_details.race()
    inmate.height = inmate_details.height()
    inmate.weight = inmate_details.weight()
    inmate.age_at_booking = inmate_details.age_at_booking()


def strip_line(line):
    return line.strip()

def strip_the_lines(lines):
    return map(strip_line, lines)


class InmateDetails:
    """
    Handles the processing of the Inmate Detail information page on the Cook County Jail website.
    Presents a consistent named interface to the information

    Strips spurious whitspace from text content before returning them

    Dates are returned as datetime objects
    """
    def __init__(self, url):
        self.url = url
        inmate_result = fetch_page(url, NUMBER_OF_ATTEMPTS)
        self.__inmate_found = inmate_result is not None
        if not self.__inmate_found:
            return

        inmate_doc = pq(inmate_result.content)
        self.__columns = inmate_doc('table tr:nth-child(2n) td')

    def age_at_booking(self):
        """From http://stackoverflow.com/questions/2217488/age-from-birthdate-in-python"""
        birth_date, booking_date = self.birth_date(), self.booking_date()
        if birth_date.month <= booking_date.month and birth_date.day <= booking_date.day:
            return (booking_date.year - birth_date.year)
        return booking_date.year - birth_date.year - 1

    def bail_amount(self):
        return self.column_content(10)

    def birth_date(self):
        return self.convert_date(2)

    def booking_date(self):
        return self.convert_date(7)

    def charges(self):
        return self.column_content(11)

    def column_content(self, columns_index):
        return self.__columns[columns_index].text_content().strip()

    def convert_date(self, column_index):
        try:
            result = datetime.strptime(self.column_content(column_index), '%m/%d/%Y')
        except ValueError:
            result = None
        return result

    def court_house_location(self):
        return self.column_content(13)

    def found(self):
        return self.__inmate_found

    def gender(self):
        return self.column_content(4)

    def height(self):
        return self.column_content(5)

    def housing_location(self):
        return self.column_content(8)

    def jail_id(self):
        return self.column_content(0)

    def next_court_date(self):
        return self.convert_date(12)

    def race(self):
        return self.column_content(3)

    def weight(self):
        return self.column_content(6)
