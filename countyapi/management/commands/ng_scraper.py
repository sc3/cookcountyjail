
from datetime import datetime
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from countyapi.management.scraper.scraper import Scraper

START_DATE = 'start_date'

log = logging.getLogger('main')


class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    option_list = BaseCommand.option_list + (
        make_option('-d', '--day', type='string', action='store', dest=START_DATE, default=None,
                    help='%s %s' % ('Specify day to search for missing inmates, format is YYYY-MM-DD.',
                                    'Not specified then searches all')),
    )

    def handle(self, *args, **options):
        log.debug("%s - Started scraping inmates from Cook County Sheriff's site." % datetime.now())

        scraper = Scraper(log)
        if options[START_DATE]:
            scraper.check_for_missing_inmates(datetime.strptime(options[START_DATE], '%Y-%m-%d').date())
        else:
            scraper.run()

        log.debug("%s - Finished scraping inmates from Cook County Sheriff's site." % datetime.now())
