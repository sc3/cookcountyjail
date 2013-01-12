import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate, CourtDate, CourtLocation
from optparse import make_option
from datetime import datetime
from countyapi.management.commands.utils import process_urls

log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2"

class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    option_list= BaseCommand.option_list + (
        make_option('-l', '--limit', type='int', action='store', dest='limit', default=False,
            help='Limit number of results.'),
        make_option('-s', '--search', type='string', action='store', dest='search', default=None,
            help='Specify last name search term to use instead of looping from A-Z (e.g. "B", "Johnson").'),
        make_option('-d', '--discharge', action='store_true', dest='discharge', default=False,
            help='Calculate discharge date.'),
    )

    def handle(self, *args, **options):
        log.debug("Scraping inmates from Cook County Sheriff's site.")

        self.options = options

        # Global counters
        records = 0
        seen = []

        # Set search to option or string.uppercase (all uppercase letters)
        if options['search']:
            search_list = [options['search']]
        else:
            search_list = string.uppercase

        # Search
        for search in search_list:
            log.debug("Search: '%s'" % search)

            # Simulates a search on the website
            url = "%s/%s" % (BASE_URL, 'locatesearchresults.asp')
            results = requests.post(url, data={'LastName': search, 'FirstName': '', 'Submit': 'Begin Search'})

            # Create pquery object
            document = pq(results.content)

            # Get links from last column of each row
            inmate_urls = document('#mainContent table tr td:last-child a')
            
            # Uniquify urls, reduce the number of queries by about 40%
            seen_urls = set([])
            filtered_urls = []
            for url in inmate_urls :
                if url.attrib['href'] not in seen_urls :
                    filtered_urls.append(url)
                    seen_urls.add(url.attrib['href'])
                    

            # Process URLs
            new_seen = (process_urls(BASE_URL,filtered_urls,records,options['limit']))
            seen += new_seen 
            records = len(seen)
            
            # Break if limit reached
            if options['limit'] and records >= options['limit']:
                break
        
        # Calculate discharge date range
        if options['discharge']:
            log.debug("--discharge (-d) flag used. Calculating discharge dates.")
            discharged = self.calculate_discharge_date(seen)
            log.debug("%s inmates discharged." % len(discharged))
        
        log.debug("Imported %s inmate records)" % (records))
       
    def calculate_discharge_date(self, seen):
        """
        Given a list of jail ids, find inmates with no discharge date that
        aren't in the list. Inmate who haven't been discharged 
        """
        now = datetime.now()
        not_present_or_discharged = CountyInmate.objects.filter(discharge_date_earliest__exact=None).exclude(jail_id__in=seen)
        for inmate in not_present_or_discharged:
            inmate.discharge_date_earliest = inmate.last_seen_date
            inmate.discharge_date_latest = now
            log.debug("Discharged %s - Earliest: %s earliest, Latest: %s" % (inmate.jail_id, inmate.last_seen_date, now))
            inmate.save()
        return not_present_or_discharged


