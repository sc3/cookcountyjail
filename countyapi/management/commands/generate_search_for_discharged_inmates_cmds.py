from datetime import date
import logging

from django.core.management.base import BaseCommand

from countyapi.models import CountyInmate


log = logging.getLogger('main')


class Command(BaseCommand):
    """
    Generates a list of commands to check inmates found from scaning over the database of
    inmates and find all of the ones that have not been seen today and have not been
    discharged.
    """
    help = \
        'Generate list of commands of inmates to check to see have been discharge from the Cook County Sheriff\'s Jail.'
    option_list = BaseCommand.option_list + ()

    __COOK_COUNTY_INMATE_DETAILS_URL = \
        'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='
    __NUMBER_OF_ATTEMPTS = 5

    # does not take use the args and options parameters
    def handle(self, *args, **options):
        inmates = CountyInmate.objects.filter(discharge_date_earliest__exact=None, last_seen_date__lt=date.today())
        for inmate in inmates:
            print('python /home/ubuntu/apps/cookcountyjail/manage.py check_inmate -j %s' % inmate.jail_id)
