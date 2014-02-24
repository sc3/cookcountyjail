from datetime import datetime, date, timedelta
import logging
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate
from countyapi.management.commands.utils import convert_to_date
from optparse import make_option

log = logging.getLogger('main')

# Needs to be outside of the class
MAX_INMATE_NUMBER = 350  # 350


class Command(BaseCommand):
    """
    This was originally part of the datebase_audit code written by Wliberto.
    That code was split into two commands:
        * validate_inmate_records which checks if existing
          inmate database records to see if they are correct
        * look_for_missing_inmates which is this one and it checks to see if
          there are any missing inmate records and adds them to the database
    While these commands can be called on their own they are meant to be used
    in script and a command, generate_database_audit_script, has been added
    for that purpose.

    Note that this operation can take a very long time which is why the
    generate script was written, as it parallelizes the execution to reduce
    the running time of the script.
    """

    help = "Audits the collected inmates and scans Cook Count Sheriff's website looking for unknown inmates."
    option_list = BaseCommand.option_list + (
        make_option('-d', '--day', type='string', action='store', dest='day', default=None,
                    help='%s %s' % ('Specify day to search for missing inmates, format is YYYY-MM-DD.',
                                    'Not specified then searches all')),
        make_option('-y', '--yesterday', action='store_true', dest='yesterday',
                    help='Specify day to search for missing inmates is yesterday.'),
    )

    COOK_COUNTY_JAIL_INMATE_DETAILS_URL = "http://www2.cookcountysheriff.org/search2/details.asp?jailnumber="
    ONE_DAY = timedelta(1)
    START_DATE = '2013-01-01'

    def handle(self, *args, **options):
        if options['yesterday']:
            self.check_yesterday_for_missing_inmates()
        else:
            self.check_for_missed_inmates(self.start_date(options['day']), self.end_date(options['day']))

    def booking_dates(self, start_date, end_date):
        while start_date <= end_date:
            yield start_date
            start_date += self.ONE_DAY

    def check_for_missed_inmates(self, start_date, end_date):
        """
        Iterates over the set of possible inmates for the specified day. If the inmate has already been seen then don't
        check for them.  If an inmate is found then an entry is created for them.
        """
        log.debug("%s - Starting search for missing inmates, starting on %s" %
                  (str(datetime.now()), start_date.strftime('%Y-%m-%d')))
        found_inmates = 0
        for day in self.booking_dates(start_date, end_date):
            seen_inmates = set([inmate.jail_id for inmate in inmates_for_date(day)])
            for inmate_jail_id in self.jail_ids(day):
                if inmate_jail_id not in seen_inmates:
                    print('python /home/ubuntu/apps/cookcountyjail/manage.py check_inmate -j %s' % inmate_jail_id)
        log.debug("%s - Ended search for missing inmates on %s, found %d." %
                  (str(datetime.now()), end_date.strftime('%Y-%m-%d'), found_inmates))

    def check_yesterday_for_missing_inmates(self):
        yesterday = date.today() - self.ONE_DAY
        self.check_for_missed_inmates(yesterday, yesterday)

    def end_date(self, day):
        today = date.today()
        if day:
            e_date = convert_to_date(day)
            if e_date < today:
                return e_date
        return today - self.ONE_DAY

    def jail_ids(self, booking_date, wanted_range=MAX_INMATE_NUMBER):
        """
        Returns an object that generates jail ids from the given booking date eg: 2013-0101000, 2013-0101001.
        """
        prefix = booking_date.strftime("%Y-%m%d")  # prefix example: 2013-0101
        for booking_number in range(1, wanted_range + 1):
            yield prefix + "%03d" % booking_number  # add to the prefix the current booking number

    def start_date(self, day):
        if day is None:
            day = self.START_DATE
        return convert_to_date(day)


def inmates_for_date(booking_date):
    """
    Returns all inmates for a given date.
    @param booking_date: booking date to search for
    @rtype : list of inmates booked on specified day
    """
    return CountyInmate.objects.filter(booking_date=booking_date)
