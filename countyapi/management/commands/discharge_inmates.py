from datetime import datetime
import logging

from django.core.management.base import BaseCommand

from countyapi.management.commands.utils import http_get
from countyapi.models import CountyInmate


log = logging.getLogger('main')


class Command(BaseCommand):
    """
    This scans over the database of inmates and dtermines which of them of been discharged.
    It does this by finding all of the inmates whose last_seen_date is prior to today and
    who have not been discharged and checks if they stil have a details page. If they do
    then their last_seen_date is updated to today. If they do not have a details page then
    they are marked as discharged.
    """
    help = "Scan known inmates and discharge any not found on Cook County Sheriff's website."
    option_list = BaseCommand.option_list + ()

    __COOK_COUNTY_INMATE_DETAILS_URL = \
        'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='
    __NUMBER_OF_ATTEMPTS = 5

    # does not take use the args and options parameters
    def handle(self, *args, **options):
        log.debug("%s - Scaning for inmates to discharge." % str(datetime.now()))

        discharged = 0
        today = self.beginning_of_today()
        inmates = CountyInmate.objects.filter(discharge_date_earliest__exact=None, last_seen_date__lt=today)
        log.debug("Number inmates to check is %d." % len(inmates))
        now = datetime.now()
        for inmate in inmates:
            inmate_page = http_get(self.__COOK_COUNTY_INMATE_DETAILS_URL + inmate.jail_id, self.__NUMBER_OF_ATTEMPTS)
            if inmate_page is None:
                inmate.discharge_date_earliest = inmate.last_seen_date
                inmate.discharge_date_latest = now
                discharged += 1
                log.debug("Discharged %s - Earliest: %s, Latest: %s" % (inmate.jail_id,
                                                                        inmate.discharge_date_earliest,
                                                                        now))
                inmate.save()
        log.debug("%s - Discharged %d." % (str(datetime.now()), discharged))

    def beginning_of_today(self):
        date_format = '%Y-%m-%d'
        return datetime.strptime(datetime.today().strftime(date_format), date_format)
