
from datetime import datetime
import logging

from django.core.management.base import BaseCommand

from countyapi.management.scraper.scraper import Scraper


log = logging.getLogger('main')


class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    option_list = BaseCommand.option_list + (
    )

    def handle(self, *args, **options):
        log.debug("%s - Started scraping inmates from Cook County Sheriff's site." % datetime.now())

        scraper = Scraper(log)
        scraper.run()

        log.debug("%s - Finished scraping inmates from Cook County Sheriff's site." % datetime.now())
