from datetime import datetime, date
import logging
from pyquery import PyQuery as pq
import requests
from time import sleep
from random import random
import re
from sys import exit

from django.db.utils import DatabaseError

from countyapi.models import CountyInmate, CourtLocation, HousingLocation


NUMBER_OF_ATTEMPTS = 5
STD_INITIAL_SLEEP_PERIOD = 0.25
STD_NUMBER_ATTEMPTS = 3
STD_SLEEP_PERIODS = [1, 3, 5, 8, 13]

IS_INTEGER = re.compile('\d+$')

log = logging.getLogger('main')


def calculate_age(born, booking_date):
    """From http://stackoverflow.com/questions/2217488/age-from-birthdate-in-python"""
    if born.month <= booking_date.month and born.day <= booking_date.day:
        return (booking_date.year - born.year)
    else:
        return booking_date.year - born.year - 1


def convert_to_int(possible_number, use_if_not_int):
    try:
        result = int(possible_number)
    except ValueError:
        result = use_if_not_int
    return result


def create_update_inmate(url):
    # Get and parse inmate page

    inmate_details = InmateDetails(url)
    inmate_result = fetch_page(url, NUMBER_OF_ATTEMPTS)

    if not inmate_details.found() or inmate_result is None:
        if inmate_details.found() or inmate_result is not None:
            log.debug("Error fetch mismatch for %s" % url)
        return

    inmate_doc = pq(inmate_result.content)
    columns = inmate_doc('table tr:nth-child(2n) td')

    # Jail ID is needed to get_or_create object. Everything else must
    # be set after inmate object is created or retrieved.
    jail_id = columns[0].text_content().strip()
    assert_same(jail_id, inmate_details.jail_id(), url, 'jail_id')

    # Get or create inmate based on jail_id
    inmate, created = CountyInmate.objects.get_or_create(jail_id=jail_id)

    # Record url
    inmate.url = url

    # Record columns with simple values
    inmate.race = columns[3].text_content().strip()
    inmate.gender = columns[4].text_content().strip()
    inmate.height = columns[5].text_content().strip()
    inmate.weight = columns[6].text_content().strip()
    inmate.housing_location = columns[8].text_content().strip()

    assert_same(inmate.race, inmate_details.race(), url, 'race')
    assert_same(inmate.gender, inmate_details.gender(), url, 'gender')
    assert_same(inmate.height, inmate_details.height(), url, 'height')
    assert_same(inmate.weight, inmate_details.weight(), url, 'weight')
    assert_same(inmate.housing_location, inmate_details.housing_location(), url, 'housing_location')

    store_housing_location(inmate)

    # Age parsing
    bday_parts = columns[2].text_content().strip().split('/')
    bday = datetime(int(bday_parts[2]), int(bday_parts[0]), int(bday_parts[1]))
    assert_same(bday, inmate_details.birth_date(), url, 'birth_date')

    # Split booked date into parts and reconstitute as string
    booked_parts = columns[7].text_content().strip().split('/')
    inmate.booking_date = "%s-%s-%s" % (booked_parts[2], booked_parts[0], booked_parts[1])
    assert_same(inmate.booking_date, inmate_details.booking_date().strftime('%Y-%m-%d'), url, 'booking_date')

    booking_datetime = datetime(int(booked_parts[2]), int(booked_parts[0]), int(booked_parts[1]))
    inmate.age_at_booking = calculate_age(bday, booking_datetime)
    assert_same(inmate.age_at_booking, inmate_details.age_at_booking(), url, 'age_at_booking)')

    # Bond: If the value can be converted to an integer, it's a dollar
    # amount. Otherwise, it's a status, e.g. "* NO BOND *".
    try:
        bail_amount = columns[10].text_content().strip().replace(',', '')
        inmate.bail_amount = int(bail_amount)
        inmate.bail_status = None
    except ValueError:
        inmate.bail_status = columns[10].text_content().replace('*', '').strip()
        inmate.bail_amount = None
    new_bail_amount, new_bail_status = store_bail_info(inmate, inmate_details)
    assert_same(inmate.bail_amount, new_bail_amount, url, 'bail_amount')
    assert_same(inmate.bail_status, new_bail_status, url, 'bail_status')

    store_charges(inmate, inmate_details, columns, url)

    store_next_court_info(inmate, inmate_details, columns, url)

    inmate.save()
    log.debug("%s inmate %s" % ("Created" if created else "Updated", inmate))

    return jail_id


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
    if (attempt - 1) < len(STD_SLEEP_PERIODS):
        index = attempt - 1
    else:
        index = -1
    return current_sleep_period * random() + STD_SLEEP_PERIODS[index]


def process_urls(base_url, inmate_urls, records, limit=None):
    seen = []  # List to store jail ids

    for url in inmate_urls:
        url = "%s/%s" % (base_url, url.attrib['href'])
        new_id = create_update_inmate(url)
        if new_id is not None and new_id not in seen:
            seen.append(new_id)
        if (limit and (records + len(seen)) >= limit):
            break

    return seen


def process_housing_location(location_object):
    """Receives a housing location from the HousingLocation table and parses it editing the different fields"""
    location_segments = location_object.housing_location.replace("-", " ").split()  # Creates a list with the housing location information

    if location_segments == [] or IS_INTEGER.match(location_segments[0]) is None:
        # Location did not start with a number so no further parsing
        if location_object.housing_location == "":
            location_object.housing_location = "UNKNOWN"
        return

    location_start = location_segments[0]
    location_segments_len = len(location_segments)
    housing_location = location_object.housing_location
    location_object.division = location_start

    if location_segments_len == 1:  # Executed only if the housing information is a single division number ex: '01-'
        return

    for element in location_segments:
        if element == "DR":
            location_object.in_program = "Day Release"
            location_object.in_jail = False
        if element == "DRAW":
            location_object.in_program == "Day Release, AWOL"
            location_object.in_jail = False

    if ((location_start == "02" or location_start == "08" or location_start == "09" or location_start == "11" or location_start == "14") or (location_start == "01" and "ABO" in housing_location)):
        location_object.sub_division = location_segments[1]
        location_object.sub_division_location = " ".join(location_segments[2:]).replace(" ", "-")
        return
    if location_start == "03" and "AX" in housing_location:
        location_object.sub_division = location_segments[2]
        location_object.sub_division_location = " ".join(location_segments[3:]).replace(" ", "-")
        return
    if location_start == "5" or location_start == "6" or location_start == "10":
        location_object.sub_division = location_segments[2] + location_segments[1]
        location_object.sub_division_location = " ".join(location_segments[3:]).replace(" ", "-")
        return
    if location_start == "15":
        if location_segments[1] == "EM":
            location_object.in_program = "Electronic Monitoring"
            location_object.in_jail = False
        elif location_segments[1] == "EMAW":
            location_object.in_program = "Electronic Monitoring, AWOL"
            location_object.in_jail = False
        elif location_segments[1] == "KK" or location_segments[1] == "LV" or location_segments[1] == "US":
            location_object.in_program = "Other Countie"
            location_object.in_jail = False
        else:
            location_object.sub_division = location_segments[1]
        return
    if location_start == "16":
        location_object.division = location_start
        return
    if location_start == "17":
        if location_segments[1] == "MOMS":
            location_object.in_program = "MOMS Program"
        elif location_segments[1] == "SFFP":
            location_object.in_program = "Sherrif Female Furlough Program"
            location_object.in_jail = False
        elif location_segments[1] == "SFFPAW":
            location_object.in_program = "Sherrif Female Furlough Program, AWOL"
            location_object.in_jail = False
        return
    if location_start == "04":
        if "M1" in housing_location:
            location_object.in_program = "Protective Custody"
        elif "N1" in housing_location:
            location_object.in_program = "Segregation"

    location_object.sub_division = " ".join(location_segments[1:3]).replace(" ", "")
    location_object.sub_division_location = " ".join(location_segments[3:]).replace(" ", "-")
    return


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

    lines = location_string.splitlines()

    if len(lines) == 4:
        try:
            strip_the_lines(lines)
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


def store_bail_info(inmate, inmate_details):
    # Bond: If the value is an integer, it's a dollar
    # amount. Otherwise, it's a status, e.g. "* NO BOND *".
    bail_amount = inmate_details.bail_amount().replace(',', '')
    bail_status = None
    if IS_INTEGER.match(bail_amount):
        bail_amount = int(bail_amount)
        # inmate.bail_amount = int(bail_amount)
    else:
        # inmate.bail_status = inmate_details.bail_amount().replace('*', '').strip()
        bail_status = inmate_details.bail_amount().replace('*', '').strip()
        bail_amount = None
    return bail_amount, bail_status


def store_charges(inmate, inmate_details, columns, url):
    """
    Stores the inmates charges if they are new or if they have been changes
    Charges: charges come on two lines. The first line is a citation and the
    # second is an optional description of the charges.
    """
    charges = columns[11].text_content().strip().splitlines()
    assert_same(charges, inmate_details.charges().splitlines(), url, 'charges')

    # terminate early if they have no charges
    if charges == []:
        return

    # Variables to keep our parsed strings
    parsed_charges = ""
    parsed_charges_citation = ""
    for n, line in enumerate(charges):
        charges[n] = line.strip()
    parsed_charges = charges[0]
    try:
        parsed_charges_citation = charges[1]
    except IndexError:
        pass

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


def store_housing_location(inmate):
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


def store_next_court_info(inmate, inmate_details, columns, url):
    # Court date parsing
    court_date_parts = columns[12].text_content().strip()
    next_court_date = inmate_details.next_court_date()
    if next_court_date is None:
        next_court_date = ''
    else:
        next_court_date = next_court_date.strftime('%m/%d/%Y')
    assert_same(court_date_parts, next_court_date, url, 'court_date')
    court_date_parts = court_date_parts.split('/')
    if len(court_date_parts) == 3:
        # Get location by splitting lines, stripping, and re-joining
        next_court_location = columns[13].text_content().strip()
        new_next_court_location = inmate_details.court_house_location()
        assert_same(next_court_location, new_next_court_location, url, 'court house location')
        next_court_location = next_court_location.splitlines()
        for n, line in enumerate(next_court_location):
            next_court_location[n] = line.strip()
        next_court_location = "\n".join(next_court_location)

        # Get or create the location object
        new_next_court_location, parsed_location = parse_court_location(new_next_court_location)
        assert_same(next_court_location, new_next_court_location, url, 'parsed court house location')
        location, new_location = CourtLocation.objects.get_or_create(location=next_court_location, **parsed_location)

        # Parse next court date
        next_court_date = "%s-%s-%s" % (court_date_parts[2], court_date_parts[0], court_date_parts[1])
        assert_same(next_court_date, inmate_details.next_court_date().strftime('%Y-%m-%d'), url, 'next court appearance formatted')

        # Get or create a court date for this inmate
        court_date, new_court_date = inmate.court_dates.get_or_create(date=next_court_date, location=location)


def strip_the_lines(lines):
    for n, line in enumerate(lines):
        lines[n] = line.strip()


def assert_same(orig_value, new_value, url, field_name):
    if orig_value != new_value:
        log.debug("Error, mismatch %s values: %s != %s for %s" % (field_name, str(orig_value), str(new_value), url))
        exit(1)


class InmateDetails:
    """
    Handles the processing of the Inmate Detail information page on the Cook County Jail website.
    Presents a consistent named interface to the information
    """
    def __init__(self, url):
        self.__url = url
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
