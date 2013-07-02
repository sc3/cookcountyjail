from parallelizer import Parallelizer
from utils import create_update_inmate
from countyapi.models import CountyInmate
from datatime import datetime
import logging


#
# WARNING! This has not been tested, it requires the Postgres Eventlet driver
#          is used in Django
#          I do not know how to do that so require assistance from others to
#          do this and when that is done then this can be tested
#          Norbert Winklareth - 2013/06/26
#

#
# This provides an alternative algorithm to audit the Cook County Inmates
# It uses parallel processing via eventlet
#
# Algorithm:
#    First pass synchronizes known inmates against records in the
#    Cook County Jail system

#    Seecond pass looks for missing inmate records from January 1st, 2013
#    and record any found
#
# The key to making this work is to use the function create_update_inmate
# from utils.py. This function does all of the work of either creating a new
# record if the inmate is not known or updating it if it is.
#

log = logging.getLogger('main')


class AuditCookCountyInmateRecords:
    """
    Audits the existing records, synchroizing them against Cook County
    Sherrif's Jail website and looks for missing inmates as well.
    """

    __one_day_delta = datetime.timedelta(1)
    __processed_inmates = None
    __parallelizer = None

    __COOK_COUNTY_INMATE_DETAILS_URL = \
        'http://www2.cookcountysheriff.org/search2/details.asp?jailnumber='

    def __initi__(self, number_of_workers=50):
        self.__parallelizer = Parallelizer(self.__check_inmate_record,
                                           number_of_workers)

    def audit(self):
        """
        Performs the audit
        """
        self.__processed_inmates = set([])
        self.__pass_one()
        self.__pass_two()

    def __booking_dates(self, start_date, end_date):
        """
        generates the set of booking days from the start date upto and
        including the end date
        """
        while start_date <= end_date:
            yield start_date
            start_date += self.__one_day_delta

    def __check_inmate_record(self, args):
        """
        checks for inmate record, using create_update_inmate
            arg[0] is the inmate booking id to process
            arg[1] is optional, if exists add inmate id if it was processed
        """
        r_val = create_update_inmate(self.__COOK_COUNTY_INMATE_DETAILS_URL +
                                     args[0])
        if len(args) > 1 and r_val is not None:
            args[1].add(r_val)

    def __missing_jail_ids(self, day, known_inmates, wanted_range=350):
        """
        generates set of inmate ids that have not been examined for a
        specified day
        """
        prefix = day.strftime("%Y-%m%d")  # prefix example: 2013-0101
        for booking_number in range(wanted_range):
            jail_id = prefix + "%03d" % booking_number
            if jail_id not in self.__processed_inmates:
                yield jail_id

    def __pass_one(self):
        """
        Syncronized records for inmates stored in our system
        """
        log.debug("%s - starting Pass One: inmate record syncronization" %
                  datetime.today())
        for known_inmate in CountyInmate.objects.all():
            self.__processed_inmates.add(known_inmate.jail_id)
            self.__parallelizer.do_task([known_inmate.jail_id])
        self.__parallelizer.wait_until_tasks_done()
        log.debug("%s - finished Pass One, processed %s inmate records" %
                  (str(datetime.today()), str(len(self.__processed_inmates))))

    def __pass_two(self):
        """
        Looks for uncaptured inmates
        """
        log.debug("%s - starting Pass Two: find missing inmates" %
                  datetime.today())
        start_date = datetime(2013, 1, 1)  # hard coded date we began scraping
        end_date = datetime.today() - self.__one_day_delta  # no audit today
        found_inmates = set([])
        inmates_searched_for = 0
        for day in self.__booking_dates(start_date, end_date):
            for inmate_to_check_for in self.__missing_jail_ids(day):
                inmates_searched_for += 1
                self.__parallelizer.do_task([inmate_to_check_for,
                                             found_inmates])
        self.__parallelizer.wait_until_tasks_done()
        log.debug("%s - finished Pass two, %s, looked at is %d" %
                  (str(datetime.today()),
                   "found %d missing inmates" % len(found_inmates),
                   inmates_searched_for))
