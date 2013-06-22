import datetime
import logging
import requests
from utils import fetch_page
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate


log = logging.getLogger('main')


class Command(BaseCommand):
    def handle(self, *args, **options):
        log.debug("Starting database audit")
        start_date = {'year': 2013, 'month': 1, 'day': 1}  # hard coded date we began scraping
        today = datetime.datetime.today()  # todays date
        end_date = {'year': today.year, 'month': today.month, 'day': today.day}
        database_audit(start_date, end_date)
        log.debug("Ended database audit")


def booking_dates(start_date, end_date):
    s_date = datetime.datetime(start_date['year'], start_date['month'], start_date['day'])
    e_date = datetime.datetime(end_date['year'], end_date['month'], end_date['day'])
    one_day = datetime.timedelta(1)
    while s_date <= e_date:
        yield s_date
        s_date += one_day


def inmates_for_date(date):
    """
    Returns all inmates for a given date.
    """
    return CountyInmate.objects.filter(booking_date=date)


def jail_ids(booking_date, wanted_range=500):
    """
    Returns an object that generates jail ids from the given booking date eg: 2013-0101000, 2013-0101001.
    """
    prefix = booking_date.strftime("%Y-%m%d")  # prefix example: 2013-0101
    for booking_number in range(wanted_range):
        yield prefix + "%03d" % booking_number  # add to the prefix the current booking number


def urls(booking_date, url="http://www2.cookcountysheriff.org/search2/details.asp?jailnumber="):
    """
    Generator object that well generates urls in the format url + jail_id
    """
    jail_id_generator = jail_ids(booking_date)
    for jail_id in jail_id_generator:
        yield url + jail_id


def database_audit(start_date, end_date):
    """
    Iterates from the start date and end date, it generates booking_dates. For every date it queries the inmates
    in the database that were booked that day. Iterates through the inmates, checks that every inmate that is discharged,
    isn't in the sherrif's inmate locator. And calls single_inmate_discharge_date_audit on them
    """
    booking_dates_generator = booking_dates(start_date, end_date)
    for day in booking_dates_generator:
        inmates = inmates_for_date(day)
        for inmate in inmates:
            if inmate.discharge_date_earliest:
                single_inmate_discharge_date_audit(inmate)
                results = fetch_page(inmate.url)
                if results.status_code == requests.codes.ok:
                    log.debug("Inmate with %s status code found and had %s discharge date" % (inmate.status_code, inmate.discharge_date_earliest))
                    inmate.discharge_date_earliests = None
                    inmate.discharge_date_latets = None
                inmate.save()


def single_inmate_discharge_date_audit(inmate):
    """
    If an inmate's discharge date earliests is less than the last time he/she was seen, set the discharges DATES to the
    last time he/she was seen. Warning does not check if the inmate is in the Sherrif's inmate locator.
    """
    if inmate.discharge_date_earliest < inmate.last_seen_date:
        log.debug("Inmate: %s has discharge date earliests: %s, last date seen: %s" % (inmate.jail_id, inmate.discharge_date_earliests, inmate.last_seen_date))
        inmate.discharge_date_earliest = inmate.last_seen_date
        inmate.discharge_date_latests = inmate.last_seen_date
