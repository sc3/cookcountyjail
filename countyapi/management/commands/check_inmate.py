from datetime import datetime
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from countyapi.models import CountyInmate

from countyapi.management.commands.inmate_utils import create_update_inmate
from countyapi.management.commands.inmate_details import InmateDetails


log = logging.getLogger('main')


class Command(BaseCommand):
    """
    Checks to see if inmate specifed by a jail_id exists in the Cook County Jail System.
    If they do then if they are not in the datebase an entry is created for them, if
    they are in the dtaabase then the entry is updated. If the inmate is not in CCJ System
    then if they have an entry in the database and the entry is not marked as discharged
    then the inmate is marked as discharged in the databaae.
    """
    help = "Checks if inmate is listed on Cook County Sheriff's website and updates database accordingly."
    option_list = BaseCommand.option_list + (
        make_option('-j', '--jail_id', type='string', action='store', dest='jail_id', default=None,
                    help='Specify inmate, with a jail_id to check on.'),
    )

    __COOK_COUNTY_INMATE_DETAILS_URL = \
        'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='
    __NUMBER_OF_ATTEMPTS = 5

    # does not take use the args and options parameters
    def handle(self, *args, **options):
        if options['jail_id']:
            inmate_details = InmateDetails(self.__COOK_COUNTY_INMATE_DETAILS_URL + options['jail_id'],
                                           attempts=self.__NUMBER_OF_ATTEMPTS, quiet=True)
            if inmate_details.found():
                create_update_inmate(inmate_details)
            else:
                inmate = CountyInmate.objects.get(jail_id=options['jail_id'])
                if inmate:
                    now = datetime.now()
                    inmate.discharge_date_earliest = inmate.last_seen_date
                    inmate.discharge_date_latest = now
                    inmate.save()
                    log.debug("%s - Discharged inmate %s." % (str(now), options['jail_id']))
