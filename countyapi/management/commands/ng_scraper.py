
from datetime import datetime
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from scraper.scraper import Scraper
from scraper.monitor import Monitor

log = logging.getLogger('main')


class Command(BaseCommand):

    START_DATE = 'start_date'
    VERBOSE_MODE = 'verbose'

    help = "Scrape inmate data from Cook County Sheriff's site."
    option_list = BaseCommand.option_list + (
        make_option('-d', '--day', type='string', action='store', dest=START_DATE, default=None,
                    help='%s %s' % ('Specify day to search for missing inmates, format is YYYY-MM-DD.',
                                    'Not specified then searches all')),
        make_option('--verbose', action="store_true", dest=VERBOSE_MODE, default=False,
                    help='Turn on verbose mode.'),
    )

    def handle(self, *args, **options):
        try:
            monitor = Monitor(log, verbose_debug_mode=options[self.VERBOSE_MODE])
            monitor.debug("%s - Started scraping inmates from Cook County Sheriff's site." % datetime.now())

            scraper = Scraper(monitor)
            if options[self.START_DATE]:
                scraper.check_for_missing_inmates(datetime.strptime(options[self.START_DATE], '%Y-%m-%d').date())
            else:
                scraper.run()

            monitor.debug("%s - Finished scraping inmates from Cook County Sheriff's site." % datetime.now())
        except Exception, e:
            log.exception(e)
