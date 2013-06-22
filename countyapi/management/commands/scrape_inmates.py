from datetime import datetime
import logging
from pyquery import PyQuery as pq
import requests
import string
from random import random
from time import sleep

from django.core.management.base import BaseCommand

from countyapi.management.commands.utils import process_urls
from countyapi.models import CountyInmate
from optparse import make_option


log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2"
SEARCH_URL = "%s/%s" % (BASE_URL, 'locatesearchresults.asp')


class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    option_list = BaseCommand.option_list + (
        make_option('-l', '--limit', type='int', action='store', dest='limit', default=False,
                    help='Limit number of results.'),
        make_option('-s', '--search', type='string', action='store', dest='search', default=None,
                    help='Specify last name search term to use instead of looping from A-Z (e.g. "B", "Johnson").'),
        make_option('-d', '--discharge', action='store_true', dest='discharge', default=False,
                    help='Calculate discharge date.'),
    )

    def extract_inmate_urls(self, inmate_search_page):
        # Create pquery object
        document = pq(inmate_search_page)

        # Get links from last column of each row
        return document('#mainContent table tr td:last-child a')

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
        for search_term in search_list:
            log.debug("Search: '%s'" % search_term)

            # Simulates a search on the website
            results = self.search_website(search_term)
            if results is None:
                continue

            inmate_urls = self.extract_inmate_urls(results.content)

            # Uniquify urls, reduce the number of queries by about 40%
            seen_urls = set([])
            filtered_urls = []
            for url in inmate_urls:
                if url.attrib['href'] not in seen_urls:
                    filtered_urls.append(url)
                    seen_urls.add(url.attrib['href'])

            # Process URLs
            new_seen = (process_urls(BASE_URL, filtered_urls, records, options['limit']))
            seen += new_seen
            records = len(seen)

            # Break if limit reached
            if options['limit'] and records >= options['limit']:
                break

        # Calculate discharge date range

        if options['discharge']:
            if options['limit'] or options['search']:
                log.debug("Discharge date option is incompatible with limit and search options")
                return
            log.debug("--discharge (-d) flag used. Calculating discharge dates.")
            discharged = self.calculate_discharge_date(seen)
            log.debug("%s inmates discharged." % len(discharged))

        log.debug("Imported %s inmate records)" % (records))

    def calculate_discharge_date(self, seen):
        """
        Given a list of jail ids, find inmates with no discharge date that
        aren't in the list. Inmate who haven't been discharged
        """
        now = datetime.datetime.now()
        not_present_or_discharged = CountyInmate.objects.filter(discharge_date_earliest__exact=None).exclude(jail_id__in=seen)
        for inmate in not_present_or_discharged:
            inmate.discharge_date_earliest = inmate.last_seen_date
            inmate.discharge_date_latest = now
            log.debug("Discharged %s - Earliest: %s earliest, Latest: %s" % (inmate.jail_id, inmate.last_seen_date, now))
            inmate.save()
        return not_present_or_discharged

    def search_website(self, search_term):
        attempt = 1
        max_attempts = 5
        delay = 0.25
        while attempt <= max_attempts:
            delay += attempt * random()
            sleep(delay)
            try:
                results = requests.post(SEARCH_URL, data={'LastName': search_term, 'FirstName': '', 'Submit': 'Begin Search'})
                if results.status_code == requests.codes.ok:
                    return results
            except requests.exceptions.RequestException:
                pass
            attempt += 1
        log.debug("Search for '%s' failed" % search_term)
        return None
