from datetime import datetime, date
import logging
from pyquery import PyQuery as pq
import string

from django.core.management.base import BaseCommand

from countyapi.management.commands.inmate_utils import store_inmates_details
from countyapi.management.commands.utils import http_post, convert_to_int
from countyapi.models import CountyInmate
from optparse import make_option


log = logging.getLogger('main')

BASE_URL = "http://www2.cookcountysheriff.org/search2"
SEARCH_URL = "%s/%s" % (BASE_URL, 'locatesearchresults.asp')
NUMBER_OF_ATTEMPTS = 5


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
        log.debug("%s - Scraping inmates from Cook County Sheriff's site." % str(datetime.now()))

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
        start_date = date.today()
        for search_term in search_list:
            log.debug("Search: '%s'" % search_term)

            # Simulates a search on the website
            post_values = {'LastName': search_term, 'FirstName': '', 'Submit': 'Begin Search'}
            results = http_post(SEARCH_URL, post_values, NUMBER_OF_ATTEMPTS)
            if results is None:
                log.debug("Search failed: '%s'." % search_term)
                continue

            inmate_urls = self.extract_inmate_urls(results.content)

            # Uniquify urls, reduce the number of queries by about 40%
            seen_urls = set([])
            filtered_urls = []
            for url in inmate_urls:
                if self.okay_to_fetch_url(url, seen_urls, start_date):
                    filtered_urls.append(url)
                    seen_urls.add(url.attrib['href'])

            # Process URLs
            new_seen = store_inmates_details(BASE_URL, filtered_urls, options['limit'], records)
            seen += new_seen
            records = len(seen)

            # Break if limit reached
            if options['limit'] and records >= options['limit']:
                break

        # Calculate discharge date range
        if options['discharge']:
            if options['limit'] or options['search']:
                log.debug("Discharge date option is incompatible with limit and search options")
                raise BaseException("Discharge date option is incompatible with limit and search options")
            log.debug("--discharge (-d) flag used. Calculating discharge dates.")
            discharged = self.calculate_discharge_date(seen)
            log.debug("%s inmates discharged." % len(discharged))

        log.debug("%s - Imported %s inmate records)" % (str(datetime.now()), records))

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
            log.debug("Discharged %s - Earliest: %s, Latest: %s" % (inmate.jail_id, inmate.discharge_date_earliest, now))
            inmate.save()
        return not_present_or_discharged

    def okay_to_fetch_url(self, url, seen_urls, start_date):
        href = url.attrib['href']
        if href not in seen_urls:
            # booking date must be yesterday or less
            # Also prior to 2010 the format of a jail id is not in the format YYYY-MMDDNNN it was YYYY-NNNNNNN
            # so have to parse for year first and is before this one
            booking_date = href.split('=')[1]
            booking_year = datetime.strptime(booking_date[0:4], '%Y').year
            if booking_year < start_date.year:
                return True
            the_month = booking_date[5:7]
            the_day = booking_date[7:9]
            inmates_booking_date = date(booking_year, convert_to_int(the_month, 1),
                                        convert_to_int(the_day, 1))
            return inmates_booking_date < start_date
        return False