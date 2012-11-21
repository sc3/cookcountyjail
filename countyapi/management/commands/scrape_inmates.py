import logging
import requests
from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
import string
from countyapi.models import CountyInmate

BASE_URL = "http://www2.cookcountysheriff.org/search2/"

class Command(BaseCommand):
    help = "Scrape inmate data from Cook County Sheriff's site."
    def handle(self, *args, **kwargs):
        # Search, A-Z
        for search in string.uppercase[:26]:
            results = requests.post( "%s/%s" % (BASE_URL, 'locatesearchresults.asp'),
                    data={'LastName': search, 'FirstName': '', 'Submit': 'Begin Search'})
            
            # Create pquery object
            document = pq(results.content)

            # Get links from last column of each row
            inmate_urls = document('#mainContent table tr td:last-child a')

            # Get each link
            for url in inmate_urls:
                inmate_result = requests.get("%s/%s" % (BASE_URL, url.attrib['href']))
                inmate_doc = pq(inmate_result.content)
                inmate_columns = inmate_doc('table tr:last-child td')

                # Jail ID is first td
                jail_id = inmate_columns[0].text_content().strip()

                # Last name is in second td, before comma
                last_name = inmate_columns[1].text_content().strip().split(',')[0]

                # First name and initials are in second td, after comma
                first_name = inmate_columns[1].text_content().strip().split(',')[1]

                # Get or create inmate based on jail_id
                inmate, created = CountyInmate.objects.get_or_create(jail_id=jail_id)

                # Set processed inmate fields
                inmate.last_name = last_name
                inmate.first_name = first_name
                # @TODO Generalize to handle all fields

                inmate.save()
            # @TODO Keep track of jail IDs, query for records with jail
            # ids not in current set that also don't have discharge dates.
            # If record "fell out", assign discharge date to today.
