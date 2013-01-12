import logging
import requests
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate, CourtDate, CourtLocation
from datetime import datetime

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

    # @TODO This try block is a little too liberal.
    court_date_parts = columns[12].text_content().strip().split('/')
    try:
        inmate.next_court_date = "%s-%s-%s" % (court_date_parts[2], court_date_parts[0], court_date_parts[1])
        # Get location by splitting lines, stripping, and re-joining
        next_court_location = columns[13].text_content().splitlines()
        for n,line in enumerate(next_court_location):
            next_court_location[n] = line.strip()
        inmate.next_court_location = "\n".join(next_court_location)
    except: pass

    # Save it!
    inmate.save()
    log.debug("%s inmate %s" % ("Created" if created else "Updated" , inmate))

    # Update global counters
   
    return jail_id

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







