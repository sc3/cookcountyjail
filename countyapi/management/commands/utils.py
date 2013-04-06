import logging
import requests
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate, CourtDate, CourtLocation, HousingHistory, HousingLocation
from datetime import datetime
from datetime import date

log = logging.getLogger('main')

def create_update_inmate(url):
    # Get and parse inmate page
    inmate_result = requests.get(url)
    
    if inmate_result.status_code != requests.codes.ok:
        log.debug("Error getting %s, status code: %s" % (url, inmate_result.status_code))
        return
    
    inmate_doc = pq(inmate_result.content)
    columns = inmate_doc('table tr:nth-child(2n) td')
    
    # Jail ID is needed to get_or_create object. Everything else must
    # be set after inmate object is created or retrieved.
    jail_id = columns[0].text_content().strip()
    
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

    # Housing location parsing
    inmate_housing_location, created_location = HousingLocation.objects.get_or_create(housing_location = columns[8].text_content().strip())
    process_housing_location(inmate_housing_location)
    housing_history, new_history = inmate.housing_history.get_or_create(housing_location=inmate_housing_location)
    if new_history:
        housing_history.housing_date = date.today()
    housing_history.save()
    inmate_housing_location.save()
     
    # Calculate age
    #if (inmate.age_at_booking = None):
    bday_parts = columns[2].text_content().strip().split('/')
    bday = datetime(int(bday_parts[2]), int(bday_parts[0]), int(bday_parts[1]))
    # Split booked date into parts and reconstitute as string
    booked_parts = columns[7].text_content().strip().split('/')
    inmate.booking_date = "%s-%s-%s" % (booked_parts[2], booked_parts[0], booked_parts[1])
    booking_datetime = datetime(int(booked_parts[2]), int(booked_parts[0]), int(booked_parts[1]))
    inmate.age_at_booking = calculate_age(bday,booking_datetime)

    # If the value can be converted to an integer, it's a dollar
    # amount. Otherwise, it's a status, e.g. "* NO BOND *".
    try:
        bail_amount = columns[10].text_content().strip().replace(',','')
        inmate.bail_amount = int(bail_amount)
    except ValueError:
        inmate.bail_status = columns[10].text_content().replace('*','').strip()

    # Charges come on two lines. The first line is a citation and the
    # second is an optional description of the charges.
    charges = columns[11].text_content().splitlines()
    for n,line in enumerate(charges):
        charges[n] = line.strip()
    inmate.charges_citation = charges[0]
    try:
        inmate.charges = charges[1]
    except IndexError: pass

    court_date_parts = columns[12].text_content().strip().split('/')
    if len(court_date_parts) == 3:
        # Get location by splitting lines, stripping, and re-joining
        next_court_location = columns[13].text_content().splitlines()
        for n,line in enumerate(next_court_location):
            next_court_location[n] = line.strip()
        next_court_location = "\n".join(next_court_location)
        
        # Get or create the location
        parsed_location = parse_location(next_court_location)
        if parsed_location is None:
            parsed_location = {}
        location, new_location = CourtLocation.objects.get_or_create(location=next_court_location, **parsed_location)
 
        # Parse next court date
        next_court_date = "%s-%s-%s" % (court_date_parts[2], court_date_parts[0], court_date_parts[1])
        
        # Get or create a court date for this inmate
        court_date, new_court_date = inmate.court_dates.get_or_create(date=next_court_date, location=location)
    # Save it!
    inmate.save()
    log.debug("%s inmate %s" % ("Created" if created else "Updated" , inmate))

    # Update global counters
   
    return jail_id

def parse_location(location_string):
    """
    Takes a location string of the form:

    "Criminal C\nCriminal Courts Building, Room:506\n2650 South California Avenue Room: 506\nChicago, IL 60608\n"

     and returns a dict of the form:
    {
        'location_name': 'Criminal C',
        'branch_name': 'Criminal Courts Building',
        'room_number': 506,
        'address': '2650 South California Avenue',
        'city': 'Chicago',
        'state':'IL',
        'zip_code': 60608,
    }
    """
    lines = location_string.split('\n')

    if len(lines) == 5:
        try:
            # The first line is the locaiton_name
            location_name = lines[0]

            # Second line must be split into room number and branch name
            branch_line = lines[1].split(', Room:')
            branch_name = branch_line[0]
            room_number = int(branch_line[1])

            # Third line has address - remove room number and store
            address = lines[2].split('Room:')[0]

            city_state_zip = lines[3].split(' ')
            city = city_state_zip[0].replace(',', '')
            state = city_state_zip[1]
            zip_code = int(city_state_zip[2])

            d = {
                'location_name': location_name,
                'branch_name': branch_name,
                'room_number': room_number,
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
            }
            return d
        except Exception:
            log.debug("Unknown format found in location: %s" % location_string)
            return None
    else:
        log.debug("Unknown format found in location: %s" % location_string)
        return None


def process_urls(base_url,inmate_urls,records,limit=None):
    seen = [] # List to store jail ids
   
    for url in inmate_urls:	
        url = "%s/%s" % (base_url, url.attrib['href'])
        new_id = create_update_inmate(url)
        if new_id not in seen and new_id != None:
        	seen.append(new_id)
        if (limit and (records + len(seen)) >= limit):
    		break    
    
    return seen

def calculate_age(born,booking_date):
    """From http://stackoverflow.com/questions/2217488/age-from-birthdate-in-python"""
    if born.month <= booking_date.month and born.day <= booking_date.day:
        return (booking_date.year - born.year) 
    else:
        return booking_date.year - born.year -1

def process_housing_location(location_object):
    """Receives a housing location from the HousingLocation table and parses it editing the different fields"""
    location_segments = location_object.housing_location.replace("-"," ").split() # Creates a list with the housing location information 
    try:
        # If successful then the location starts with a integer, implies inmate is in a division
        int(location_segments[0])
    except (ValueError, IndexError):
        # Location starts with a letter stuff here there for not in a division and no further parsing
        if location_object.housing_location == "":
            location_object.housing_location = "UNKNOWN"
        return

    location_start = location_segments[0]
    location_segments_len = len(location_segments)
    housing_location = location_object.housing_location
    location_object.division = location_start

    if location_segments_len == 1: # Executed only if the housing information is a single division number ex: '01-' 
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
        location_object.sub_division_location = " ".join(location_segments[2:]).replace(" ","-")
        return
    if location_start == "03" and "AX" in housing_location:
        location_object.sub_division = location_segments[2]
        location_object.sub_division_location = " ".join(location_segments[3:]).replace(" ","-")
        return
    if location_start == "5" or location_start == "6" or location_start == "10":
        location_object.sub_division = location_segments[2] + location_segments[1]
        location_object.sub_division_location = " ".join(location_segments[3:]).replace(" ","-")
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
    
    location_object.sub_division = " ".join(location_segments[1:3]).replace(" ","")
    location_object.sub_division_location = " ".join(location_segments[3:]).replace(" ","-")
    return

