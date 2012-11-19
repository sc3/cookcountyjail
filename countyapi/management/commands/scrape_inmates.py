import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq

log = logging.getLogger('countyapi.management.commands.scrape_inmates')

class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    def handle(self, *args, **kwargs):
        # @TODO scrape and load
        # Search, A-Z
        results = requests.post('http://www2.cookcountysheriff.org/search2/locatesearchresults.asp',
                data={'LastName': 'A', 'FirstName': '', 'Submit': 'Begin Search'})
        document = pq(results.content)
        rows = document('#mainContent table tr')
        # Loop over rows to extract URL for record
        # Follow link
        # get_or_create new inmate record
