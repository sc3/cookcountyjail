import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate
from optparse import make_option
import datetime
from utils import calculate_age
from utils import create_update_inmate

log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=" #YYYY-MMDDNNN

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
        records = 0
        seen = []
        today = datetime.date.today()
            
        if not options.get('booking_date') or len(options.get('booking_date')) != 8:
            log.debug("Booking date is required in format: YYYYMMDD.")
            return
        
        dates = date_dict(options.get('booking_date'))
        log.debug("Searching for inmates booked from %d-%d-%d to today" % (dates['year'],dates['month'],dates['day']))
        booking_date = datetime.date((dates['year']),dates['month'],dates['day'])
        
        if booking_date >= today: 
        	log.debug("Booking date must be before today")
        	return 
        	
        one_day = datetime.timedelta(1)
        while(booking_date < today):
            for booked in range(1000):
                booked = add_char(booked,3)
                url = "%s%s-%s%s%s" % (BASE_URL, booking_date.year, add_char(booking_date.month), add_char(booking_date.day), booked)
                new_id = create_update_inmate(url)
                if new_id != None:
                	seen.append(new_id)
                            
            booking_date = booking_date + one_day
        records = len(seen)
        log.debug("Imported %s inmate records" % records)


