from datetime import datetime, timedelta
import logging
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate
from countyapi.management.commands.inmate_details import InmateDetails
from countyapi.management.commands.inmate_utils import create_update_inmate
from countyapi.management.commands.utils import convert_to_date
from optparse import make_option

log = logging.getLogger('main')


class Command(BaseCommand):
    """
    This was originally part of the datebase_audit code written by Wliberto.
    That code was split into two commands:
        * validate_inmate_records which is this one which checks if existing
          inmate database records to see if they are correct
        * look_for_missing_inmates which checks to see if there are any
          missing inmate records
    While these commands can be called on their own they are meant to be used
    in script and a command, generate_datebase_audit_script, has been added
    for that purpose.
    """

    help = "Validates existing inmate records against Cook Count Sherif's website."

    option_list = BaseCommand.option_list + (
        make_option('-s', '--start_day', type='string', action='store', dest='start_date', default=None,
                    help="%s %s" % ('Specify booking day to start validating inmates, format is YYYY-MM-DD.',
                                    'If specified by itself all days after till yesterday are also searched.')),
        make_option('-e', '--end_day', type='string', action='store', dest='end_date', default=None,
                    help="%s %s" % ('Specify booking day to end validating inmates, format is YYYY-MM-DD.',
                                    'If specfied by itself then all booking days before are also searched.')),
    )

    COOK_COUNTY_JAIL_INMATE_DETAILS_URL = "http://www2.cookcountysheriff.org/search2/details.asp?jailnumber="
    ONE_DAY = timedelta(1)

    def handle(self, *args, **options):
        self.validate_known_inmates(options['start_date'], options['end_date'])

    def fetch_inmates(self, start_date, end_date):
        if start_date is None and end_date is None:
            return CountyInmate.objects.filter()
        s_date = convert_to_date(start_date) if start_date is not None else None
        e_date = convert_to_date(end_date) if end_date is not None else None
        if s_date is None:
            return CountyInmate.objects.filter(booking_date__lte=e_date)
        elif e_date is None:
            return CountyInmate.objects.filter(booking_date__gte=s_date)
        return CountyInmate.objects.filter(booking_date__gte=s_date, booking_date__lte=e_date)

    def header_format_start_end_dates(self, start_date, end_date):
        if start_date is None and end_date is None:
            return ''
        if start_date is None:
            return " from beginning to %s" % end_date
        elif end_date is None:
            return " from %s to today" % start_date
        return " from %s to %s" % (start_date, end_date)

    def validate_known_inmates(self, start_date, end_date):
        updated = 0
        discharged = 0
        log.debug("%s - Starting validation of existing inmate records%s" %
                  (str(datetime.now()), self.header_format_start_end_dates(start_date, end_date)))
        for inmate in self.fetch_inmates(start_date, end_date):
            log.debug("Checking inmate %s." % inmate.jail_id)
            inmate_details = InmateDetails(self.COOK_COUNTY_JAIL_INMATE_DETAILS_URL + inmate.jail_id,
                                           quiet=True, attempts=3)
            if inmate_details.found():
                updated += 1
                create_update_inmate(inmate_details, inmate)
            elif inmate.discharge_date_earliest is None:
                discharged += 1
                inmate.discharge_date_earliest = inmate.last_seen_date
                inmate.discharge_date_latest = datetime.now()
                inmate.save()
        log.debug("%s - Ended validation, updated %d and discharged %d inmate records." %
                  (str(datetime.now()), updated, discharged))
