import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate
from optparse import make_option
from datetime import datetime

log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2"

def calculate_age(born):
    """From http://stackoverflow.com/questions/2217488/age-from-birthdate-in-python"""
    today = date.today()
    try: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year)
    except ValueError:
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year

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
        records = []
        rows_processed = 0

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

            # Process URLs
            new_records, new_rows_processed = self.process_urls(inmate_urls)
            records += new_records
            rows_processed += new_rows_processed

            # Break if limit reached
            if options['limit'] and len(records) >= options['limit']:
                break

        # Calculate discharge date range
        if options['discharge']:
            log.debug("--discharge (-d) flag used. Calculating discharge dates.")
            discharged = self.calculate_discharge_date(records)
            log.debug("%s inmates discharged." % len(discharged))

        log.debug("Imported %s inmate records (%s rows processed)" % (len(records), rows_processed))

    def process_urls(self, inmate_urls):
        seen = [] # List to store jail ids
        rows_processed = 0 # Rows processed counter
        for url in inmate_urls:
            url = "%s/%s" % (BASE_URL, url.attrib['href'])

            # Get and parse inmate page
            inmate_result = requests.get(url)

            if inmate_result.status_code != requests.codes.ok:
                log.debug("Error getting %s, status code: %s" % (url, inmate_result.status_code))
                continue

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

            # Split booked date into parts and reconstitute as string
            booked_parts = columns[7].text_content().strip().split('/')
            inmate.booked_date = "%s-%s-%s" % (booked_parts[2], booked_parts[0], booked_parts[1])

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

            # Break on limit
            if self.options['limit'] and len(seen) >= self.options['limit']:
                done = True
                break

        return seen, rows_processed

    def calculate_discharge_date(self, records):
        """
        Given a list of jail ids, find inmates with no discharge date that
        aren't in the list. Inmate who haven't been discharged 
        """
        now = datetime.now()
        not_present_or_discharged = CountyInmate.objects.filter(discharge_date_earliest__exact=None).exclude(jail_id__in=records)
        for inmate in not_present_or_discharged:
            inmate.discharge_date_earliest = inmate.last_seen_date
            inmate.discharge_date_latest = now
            log.debug("Discharged %s - Earliest: %s earliest, Latest: %s" % (inmate.jail_id, inmate.last_seen_date, now))
            inmate.save()
        return not_present_or_discharged


