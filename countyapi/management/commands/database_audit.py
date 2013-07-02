import datetime
import logging
import requests
from utils import fetch_page
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate
from countyapi.management.commands.utils import create_update_inmate

log = logging.getLogger('main')


class Command(BaseCommand):

    COOK_COUNTY_JAIL_INMATE_DETAILS_URL = "http://www2.cookcountysheriff.org/search2/details.asp?jailnumber="

    def handle(self, *args, **options):
        log.debug("Starting database audit")
        start_date = {'year': 2013, 'month': 1, 'day': 1}  # hard coded date we began scraping
        today = datetime.datetime.today()  # todays date
        end_date = {'year': today.year, 'month': today.month, 'day': today.day - 1}  # yesterday, nothing to audit for today
        self.database_audit(start_date, end_date)
        log.debug("Ended database audit")

    def audit_known_inmates_for_day(self, day):
        """
        Iterates through the set of known inmates for specified day, adds them to the seen_imate list and then checks that
        if the inmate is marked discharged, it checks to see if that is true on the Sherrif's website. If the inmate still
        exists then it updates the inmates entry to indicate this.
        """
        seen_inmates = set([])
        for inmate in self.inmates_for_date(day):
            seen_inmates.add(inmate.jail_id)
            if inmate.discharge_date_earliest:
                self.check_if_inmate_has_really_been_discharged(inmate)
            else:
                self.check_that_inmate_still_in_system(inmate)
        return seen_inmates

    def booking_dates(self, start_date, end_date):
        s_date = datetime.datetime(start_date['year'], start_date['month'], start_date['day'])
        e_date = datetime.datetime(end_date['year'], end_date['month'], end_date['day'])
        one_day = datetime.timedelta(1)
        while s_date <= e_date:
            yield s_date
            s_date += one_day

    def check_for_missed_inmates(self, day, seen_inmates):
        """
        Iterates over the set of possible inmates for the specified day. If the inmate has already been seen then don't
        check for them.  If an inmate is found then an entry is created for them.
        """
        possible_inmates = self.jail_ids(day)
        for inmate_jail_id in possible_inmates:
            if inmate_jail_id not in seen_inmates:
                create_update_inmate(self.COOK_COUNTY_JAIL_INMATE_DETAILS_URL + inmate_jail_id)

    def check_if_inmate_has_really_been_discharged(self, inmate):
        results = fetch_page(inmate.url)
        if results is not None and results.status_code == requests.codes.ok:
            log.debug("Inmate with %s status code found and had %s discharge date" % (inmate.status_code, inmate.discharge_date_earliest))
            self.clear_inmate_discharge_info(inmate)
        else:
            self.single_inmate_discharge_date_audit(inmate)

    def check_that_inmate_still_in_system(self, inmate):
        results = fetch_page(inmate.url)
        if results is None or results.status_code != requests.codes.ok:
            log.debug("Inmate %s no longer in Jail system" % (inmate.jail_id))
            self.set_inmate_discharge_dates_to_last_seen(inmate)

    def clear_inmate_discharge_info(self, inmate):
        inmate.discharge_date_earliests = None
        inmate.discharge_date_latets = None
        inmate.save()

    def database_audit(self, start_date, end_date):
        """
        Iterates from the start date and end date, processing known inmates and then checking to see if there are unknown
        inmates for the current day.
        """
        booking_dates_generator = self.booking_dates(start_date, end_date)
        for day in booking_dates_generator:
            seen_inmates = self.audit_known_inmates_for_day(day)
            self.check_for_missed_inmates(day, seen_inmates)

    def inmates_for_date(self, date):
        """
        Returns all inmates for a given date.
        """
        return CountyInmate.objects.filter(booking_date=date)

    def jail_ids(self, booking_date, wanted_range=500):
        """
        Returns an object that generates jail ids from the given booking date eg: 2013-0101000, 2013-0101001.
        """
        prefix = self.booking_date.strftime("%Y-%m%d")  # prefix example: 2013-0101
        for booking_number in range(wanted_range):
            yield prefix + "%03d" % booking_number  # add to the prefix the current booking number

    def set_inmate_discharge_dates_to_last_seen(self, inmate):
        inmate.discharge_date_earliest = inmate.last_seen_date
        inmate.discharge_date_latests = inmate.last_seen_date
        inmate.save()

    def single_inmate_discharge_date_audit(self, inmate):
        """
        If an inmate's discharge date earliests is less than the last time he/she was seen, set the discharges DATES to the
        last time he/she was seen. Warning does not check if the inmate is in the Sherrif's inmate locator.
        """
        if inmate.discharge_date_earliest < inmate.last_seen_date:
            log.debug("Inmate: %s has discharge date earliests: %s, last date seen: %s" % (inmate.jail_id, inmate.discharge_date_earliests, inmate.last_seen_date))
            self.set_inmate_discharge_dates_to_last_seen(inmate)
