from datetime import datetime, date, timedelta
import logging
from inmate_details import InmateDetails
from utils import convert_to_int, join_with_space_and_convert_spaces, just_empty_lines, strip_the_lines

from django.db.utils import DatabaseError

from countyapi.models import CountyInmate, CourtLocation, HousingLocation

############################################################################################################
#
# TODO:
#    1) this should be turned into a class
#    2) Should also collect or log performance stats, how many inmate records fetched, how many failed,
#       how long it took, etc.
#
############################################################################################################


log = logging.getLogger('main')

ONE_DAY = timedelta(1)


def clear_discharged(inmate):
    """
    Because the Cook County Jail website has issues, we can misclassify inmates as discharged. This
    function clears the discharge fields, so the inmate is no longer classified as missing.
    """
    inmate.discharge_date_earliest = None
    inmate.discharge_date_latest = None


def create_update_inmate(inmate_details, inmate=None):
    """
    Fetches inmates detail page and creates or updates inmates record based on it,
    otherwise returns as inmate's details were not found
    """
    if inmate is None:
        inmate, created = inmate_record_get_or_create(inmate_details)
    else:
        created = False
    clear_discharged(inmate)
    store_person_id(inmate, inmate_details)
    store_booking_date(inmate, inmate_details)
    store_physical_characteristics(inmate, inmate_details)
    store_housing_location(inmate, inmate_details)
    store_bail_info(inmate, inmate_details)
    store_charges(inmate, inmate_details)
    store_next_court_info(inmate, inmate_details)
    try:
        inmate.save()
        log.debug("%s - %s inmate %s" % (str(datetime.now()), "Created" if created else "Updated", inmate))
    except DatabaseError as e:
        log.debug("Could not save inmate '%s'\nException is %s" % (inmate.jail_id, str(e)))
    return inmate


def inmate_record_get_or_create(inmate_details):
    """
    Gets or creates inmate record based on jail_id and stores the url used to fetch the inmate info
    """
    inmate, created = CountyInmate.objects.get_or_create(jail_id=inmate_details.jail_id())
    return inmate, created


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
    location_segments = location_object.housing_location.replace("-", " ").split()
    if location_segments == [] or convert_to_int(location_segments[0], None) is None:
        # Location did not start with a number so no further parsing
        if location_object.housing_location == "":
            location_object.housing_location = "UNKNOWN"
        return

    location_object.division = location_segments[0]
    if len(location_segments) == 1:  # Execute only if the housing information is a single division number ex: '01-'
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
        set_location_05_06_10_values(location_object, location_segments)
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

    set_sub_division(location_object, join_with_space_and_convert_spaces(location_segments[1:3], ""),
                     location_segments[3:])
    return


def set_day_release(location_object, location_segments):
    for element in location_segments:
        if element == "DR":
            location_object.in_program = "Day Release"
            location_object.in_jail = False
        elif element == "DRAW":
            location_object.in_program = "Day Release, AWOL"
            location_object.in_jail = False


def set_location_04_values(location_object, _):
    if "M1" in location_object.housing_location:
        location_object.in_program = "Protective Custody"
    elif "N1" in location_object.housing_location:
        location_object.in_program = "Segregation"


def set_location_05_06_10_values(location_object, location_segments):
    if len(location_segments) == 2:
        set_sub_division(location_object, location_segments[1], [])
    else:
        set_sub_division(location_object, location_segments[2] + location_segments[1], location_segments[3:])


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


def store_person_id(inmate, inmate_details):
    inmate.person_id = inmate_details.hash_id()


def store_bail_info(inmate, inmate_details):
    # Bond: If the value is an integer, it's a dollar
    # amount. Otherwise, it's a status, e.g. "* NO BOND *".
    inmate.bail_amount = convert_to_int(inmate_details.bail_amount().replace(',', ''), None)
    if inmate.bail_amount is None:
        inmate.bail_status = inmate_details.bail_amount().replace('*', '').strip()
    else:
        inmate.bail_status = None


def store_booking_date(inmate, inmate_details):
    inmate.booking_date = inmate_details.booking_date()


def store_charges(inmate, inmate_details):
    """
    Stores the inmates charges if they are new or if they have been changes
    Charges: charges come on two lines. The first line is a citation and the
    # second is an optional description of the charges.
    """
    charges = strip_the_lines(inmate_details.charges().splitlines())
    if just_empty_lines(charges):
        return

    # Capture Charges and Citations if specified
    parsed_charges_citation = charges[0]
    parsed_charges = charges[1] if len(charges) > 1 else ''
    create_new_charge = True
    if len(inmate.charges_history.all()) != 0:
        inmate_latest_charge = inmate.charges_history.latest('date_seen')  # last known charge
        # if the last known charge is different than the current info then create a new charge
        if inmate_latest_charge.charges == parsed_charges and \
           inmate_latest_charge.charges_citation == parsed_charges_citation:
            create_new_charge = False
    if create_new_charge:
        try:
            new_charge = inmate.charges_history.create(charges=parsed_charges, charges_citation=parsed_charges_citation)
            new_charge.date_seen = datetime.now().date()
            new_charge.save()
        except DatabaseError as e:
            log.debug("Could not save charges '%s' and citation '%s'\nException is %s" % (parsed_charges,
                                                                                          parsed_charges_citation,
                                                                                          str(e)))


def store_housing_location(inmate, inmate_details):
    housing_location = inmate_details.housing_location()
    if housing_location != '':
        try:
            inmate_housing_location, created_location = \
                HousingLocation.objects.get_or_create(housing_location=housing_location)
            if created_location:
                process_housing_location(inmate_housing_location)
                inmate_housing_location.save()
        except DatabaseError as e:
            log.debug("Could not save housing location '%s'\nException is %s" % (inmate.housing_location, str(e)))
        try:
            housing_history, new_history = \
                inmate.housing_history.get_or_create(housing_location=inmate_housing_location)
            if new_history:
                housing_history.housing_date_discovered = yesterday()
                housing_history.save()
        except DatabaseError as e:
            log.debug("Could not save housing history '%s'\nException is %s" % (housing_history.housing_location_id,
                                                                                str(e)))


def store_inmates_details(base_url, inmate_urls, limit=None, records=0):
    """
    Initiates processing of inmate_urls
    """
    processed_jail_ids = []  # List to record processed jail ids in

    for url in inmate_urls:
        url = "%s/%s" % (base_url, url.attrib['href'])
        inmate_details = InmateDetails(url)
        if inmate_details.found():
            inmate = create_update_inmate(inmate_details)
            if inmate.jail_id not in processed_jail_ids:
                processed_jail_ids.append(inmate.jail_id)
        if limit and (records + len(processed_jail_ids)) >= limit:
            break

    return processed_jail_ids


def store_next_court_info(inmate, inmate_details):
    # Court date parsing
    next_court_date = inmate_details.next_court_date()
    if next_court_date is not None:
        # Get location record by parsing next Court location string
        next_court_location, parsed_location = parse_court_location(inmate_details.court_house_location())
        location, _ = CourtLocation.objects.get_or_create(location=next_court_location, **parsed_location)

        # Get or create a court date for this inmate
        inmate.court_dates.get_or_create(date=next_court_date.strftime('%Y-%m-%d'), location=location)


def store_physical_characteristics(inmate, inmate_details):
    inmate.gender = inmate_details.gender()
    inmate.race = inmate_details.race()
    inmate.height = inmate_details.height()
    inmate.weight = inmate_details.weight()
    inmate.age_at_booking = inmate_details.age_at_booking()


def yesterday():
    return date.today() - ONE_DAY
