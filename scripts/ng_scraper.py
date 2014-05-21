#!/usr/bin/env python

from datetime import datetime
import logging, argparse

from scraper.scraper import Scraper
from scraper.monitor import Monitor

log = logging.getLogger('main')


def ng_scraper():

    parser = argparse.ArgumentParser(description="Scrape inmate data from Cook County Sheriff's site.")
    parser.add_argument('-d', '--day', action='store', dest='start_date', default=None,
                        help=('Specify day to search for missing inmates, format is YYYY-MM-DD. '
                                'If not specified, searches all days.'))
    parser.add_argument('--verbose', action="store_true", dest='verbose', default=False,
                        help='Turn on verbose mode.')

    args = parser.parse_args()

    try:
        monitor = Monitor(log, verbose_debug_mode=args.verbose)
        monitor.debug("%s - Started scraping inmates from Cook County Sheriff's site." % datetime.now())

        scraper = Scraper(monitor)
        if args.start_date:
            scraper.check_for_missing_inmates(datetime.strptime(args.start_date, '%Y-%m-%d').date())
        else:
            scraper.run()

        monitor.debug("%s - Finished scraping inmates from Cook County Sheriff's site." % datetime.now())
    except Exception, e:
        log.exception(e)

if __name__ == '__main__':
    ng_scraper()