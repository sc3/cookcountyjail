import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate
from optparse import make_option

log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2"

class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    option_list= BaseCommand.option_list + (
        make_option('-l', '--limit', type='int', action='store', dest='limit', default=None,
            help='Limit number of results.'),
        make_option('-s', '--search', type='string', action='store', dest='search', default=None,
            help='Specify last name search term to use instead of looping from A-Z (e.g. "B", "Johnson").'),
    )

    def handle(self, *args, **options):
        log.debug("Scraping inmates from Cook County Sheriff's site.")

        self.options = options

        # Global counters
        records = []
        rows_processed = 0

        if options['search']:
            search_list = [options['search']]
        else:
            search_list = string.uppercase

        # Search
        for search in search_list:
            log.debug("Search: '%s'" % search)
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
            if len(records) >= options['limit']:
                break

        log.debug("Imported %s inmate records (%s rows processed)" % (len(records), rows_processed))
            # @TODO Keep track of jail IDs, query for records with jail
            # ids not in current set that also don't have discharge dates.
            # If record "fell out", assign discharge date to today.

    def process_urls(self, inmate_urls):
        seen = [] # List to store jail ids
        rows_processed = 0 # Rows processed counter
        for url in inmate_urls:
            url = "%s/%s" % (BASE_URL, url.attrib['href'])

            # Get and parse inmate page
            inmate_result = requests.get(url)
            inmate_doc = pq(inmate_result.content)
            inmate_columns = inmate_doc('table tr:last-child td')

            # Jail ID is first td
            jail_id = inmate_columns[0].text_content().strip()

            # Last name is in second td, before comma
            #last_name = 

            # First name and initials are in second td, after comma
            #first_name = 

            # Get or create inmate based on jail_id
            inmate, created = CountyInmate.objects.get_or_create(jail_id=jail_id)

            # Set inmate fields
            inmate.url = url
            inmate.last_name = inmate_columns[1].text_content().split(',')[0]
            inmate.first_name = inmate_columns[1].text_content().split(',')[1].strip()
            # @TODO Handle all fields

            inmate.save()

            if jail_id not in seen:
                seen.append(jail_id)

            log.debug("%s inmate %s" % ("Created" if created else "Updated" , inmate))

            rows_processed += 1

            # Break on limit
            if len(seen) >= self.options['limit']:
                done = True
                break

        return seen, rows_processed
