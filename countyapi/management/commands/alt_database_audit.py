from parallelizer import parallelizer
from eventlet.green import urllib2
from eventlet.green import socket
import utils
from countyapi.models import CountyInmate
from datatime import datetime


#
# WARNING! This has not been tested, it requires the Postgres Eventlet driver is used in Django
#          I do not know how to do that so reuire assistance from others
#          Norbert Winklareth - 2013/06/26
#

#
# This provides an alternative algorithm to audit the Cook County Inmates
# It uses parallel processing via eventlet
#
# Algorithm:
#    Create worker pool()
#    for x in existing inmate records:
#       add x.jail_id to seen
#       queue x.jail_id
#    wait for processing to be finished
#
#    for day in start_date to end_date:
#       for x in possible jail_ids_for_current_day
#          if x not in seen:
#             queue jail_id
#    wait for processing to be finished
#
#  That is the entire algorithm. The first pass synchronizes known inmates against
#  Jail system. The second pass looks for missing inmate records.
#
#  The key to making this work is to use the function create_update_inmate from utils.py.
#  This does all of the work of either creating a new record if the inmate is not known
#  or updating it if it is.
#
#  The use of worker pool parellelizes the execution so it does not take forever.
#


log = logging.getLogger('main')

class AuditCookCountyInmateRecords:
    """
    Audits the existing records, synchroizing them against Cook County Sherrif's Jail website
    and looks for missing inmates as well.
    """

    __one_day_delta = datetime.timedelta(1)

    def __initi__(self, number_of_workers=50):
        self.__parallelizer = Parallelizer(self.__check_inmate_record, number_of_workers)

    def __booking_dates(start_date, end_date):
        while start_date <= end_date:
            yield start_date
            start_date += self.__one_day_delta

    def __check_inmate_record(self, args):
        create_update_inmate('http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=' + args[0])

    def __missing_jail_ids(day, known_inmates, wanted_range=350):
        prefix = day.strftime("%Y-%m%d")  # prefix example: 2013-0101
        for booking_number in range(wanted_range):
            jail_id = prefix + "%03d" % booking_number
            if jail_id not in known_inmate:
                yield jail_id

    def run(self):
        log.debug("%s - starting record syncronization, pass one" % datetime.today())
        processed_inmates = set([])

        # Pass one: syncronized known inmates
        # By the way fetching reccords should cause I/O Eventlet switching to occur
        for known_inmate in CountyInmate.objects.all():
            processed_inmates.add(known_inmate.jail_id)
            self.__parallelizer.do_task([known_inmate.jail_id])
        self.__parallelizer.wait_until_tasks_done()
        log.debug("%s - finished Pass One, starting Pass two, processed %s inmate records" % (str(datetime.today()), str(len(processed_inmates))))

        # Pass two: look for missed inmates
        start_date = datetime(2013, 1, 1}  # hard coded date we began scraping
        end_date = datetime.today() - __one_day_delta  # yesterday, nothing to audit for today
        for day in self.__booking_dates(start_date, end_date):
            for inmate_to_check_for in self.__missing_jail_ids(day, known_inmates):
                processed_inmates.add(inmate_to_check_for)
                self.__parallelizer.do_task([inmate_to_check_for])
        self.__parallelizer.wait_until_tasks_done()
        log.debug("%s - finished Pass two, total number of inmates looked at is %s" % (str(datetime.today()), str(len(processed_inmates))))
