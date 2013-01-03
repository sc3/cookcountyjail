import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate
from optparse import make_option
import datetime
from utils import calculate_age

log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=" #YYYY-MMDDNNN

def create_inmate(url):
    seen = [] # List to store jail ids
    rows_processed = 0 # Rows processed counter
    
    
    # Get and parse inmate page
    inmate_result = requests.get(url)
    
    if inmate_result.status_code != requests.codes.ok:
        log.debug("Error getting %s, status code: %s" % (url, inmate_result.status_code))
        return seen, rows_processed

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
    bday_parts = columns[2].text_content().strip().split('/')
    bday = datetime.datetime(int(bday_parts[2]), int(bday_parts[0]), int(bday_parts[1]))
    inmate.age_at_booking = calculate_age(bday)
    
    # Split booked date into parts and reconstitute as string
    booked_parts = columns[7].text_content().strip().split('/')
    inmate.booking_date = "%s-%s-%s" % (booked_parts[2], booked_parts[0], booked_parts[1])
    
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
    rows_processed += 1
    if jail_id not in seen:
        seen.append(jail_id)


    return seen, rows_processed

def date_dict(booking_date_option):
    date = booking_date_option
    dates_dictionary = {'year': int(date[0:4]), 'month' : int(date[4:6]), 'day' : int(date[6:]) }
    return dates_dictionary

def add_char(short_string, length = 2,char = '0'):
    short_string = str(short_string)
    while(len(short_string) != length):
        short_string = char + short_string
    return short_string

class Command(BaseCommand):
    help = "Scrape inmates from the given booking day until today."
    option_list= BaseCommand.option_list + (
        make_option('-b', '--booking_date', type='string', action='store', dest='booking_date', default=None,
            help='Scrapes inmates with a booking date grater than the given argument. Date is in format of YYYYMMDD'),
    )
    
    def handle(self, *args, **options):
        # Global counters
        records = []
        rows_processed = 0
        today = datetime.date.today()
        
    
        if not options.get('booking_date') or len(options.get('booking_date')) != 8:
            log.debug("Booking date is required in format: YYYYMMDD.")
            return
        
        dates = date_dict(options.get('booking_date'))
        log.debug("Searching for inmates booked from %d-%d-%d to today" % (dates['year'],dates['month'],dates['day']))
        
        booking_date = datetime.date((dates['year']),dates['month'],dates['day'])
        print type(booking_date)
        
        while(booking_date < today):
            for booked in range(1000):
                booked = add_char(booked,3)
                url = "%s%s-%s%s%s" % (BASE_URL, booking_date.year, add_char(booking_date.month), add_char(booking_date.day), booked)
                #Request code over here
                new_records, new_rows_processed = create_inmate(url)
                records += new_records
                rows_processed += new_rows_processed
                create_inmate(url)
            
            
            try:
                dates['day'] = dates['day'] + 1
                booking_date = datetime.date((dates['year']),dates['month'],dates['day'])
            except ValueError:
                try:
                    dates['month'] = dates['month'] + 1
                    dates['day'] =  1
                    booking_date = datetime.date((dates['year']),dates['month'],dates['day'])
                except ValueError:
                    try:
                        dates['year'] = dates['year'] + 1
                        dates['month'] = 1
                        dates['day'] =  1
                        booking_date = datetime.date((dates['year']),dates['month'],dates['day'])
                    except ValueError:
                        log.debug ("Unknown Eror.")

            log.debug("Imported %s inmate records (%s rows processed)" % (len(records), rows_processed))


