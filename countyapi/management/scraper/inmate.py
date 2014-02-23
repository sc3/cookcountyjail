
from datetime import datetime, date
from django.db.utils import DatabaseError

from countyapi.management.commands.utils import convert_to_int

from countyapi.models import CountyInmate

from charges import Charges
from court_date_info import CourtDateInfo
from housing_location_info import HousingLocationInfo


class Inmate:
    """
    Inmate handling code lifted whole sale from inmate_utils file in countypai/management/commands
    """

    def __init__(self, inmate_details, monitor):
        self._inmate_details = inmate_details
        self._monitor = monitor
        self._inmate = None
        self._jail_id = inmate_details.jail_id()

    @staticmethod
    def active_inmates():
        return CountyInmate.objects.filter(discharge_date_earliest__exact=None, last_seen_date__lt=date.today())

    def _clear_discharged(self):
        """
        Because the Cook County Jail website has issues, we can have misclassified inmates as discharged. This
        function clears the discharge fields, so the inmate is no longer classified as being discharged.
        """
        self._inmate.discharge_date_earliest = None
        self._inmate.discharge_date_latest = None

    def _debug(self, msg):
        self._monitor.debug('Inmate: %s' % msg)

    def discharge(self, inmate_id, monitor):
        try:
            inmate = CountyInmate.objects.get(jail_id=inmate_id)
            if inmate:
                now = datetime.now()
                inmate.discharge_date_earliest = inmate.last_seen_date
                inmate.discharge_date_latest = now
                inmate.save()
        except DatabaseError as e:
            monitor.debug("Could not save inmate '%s'\nException is %s" % (inmate.jail_id, str(e)))

    def _inmate_record_get_or_create(self):
        """
        Gets or creates inmate record based on jail_id and stores the url used to fetch the inmate info
        """
        inmate, created = CountyInmate.objects.get_or_create(jail_id=self._jail_id)
        return inmate, created

    def save(self):
        """
        Fetches inmates detail page and creates or updates inmates record based on it,
        otherwise returns as inmate's details were not found
        """
        msg_template = '%%s save inmate: %s' % self._jail_id
        self._debug(msg_template % 'started')
        try:
            self._inmate, created = self._inmate_record_get_or_create()
            self._clear_discharged()
            self._store_person_id()
            self._store_booking_date()
            self._store_physical_characteristics()
            self._store_housing_location()
            self._store_bail_info()
            self._store_charges()
            self._store_next_court_info()
            try:
                self._inmate.save()
                self._debug("%s - %s inmate %s" % (str(datetime.now()), "Created" if created else "Updated",
                                                   self._inmate))
            except DatabaseError as e:
                self._debug("Could not save inmate '%s'\nException is %s" % (self._jail_id, str(e)))
        except DatabaseError as e:
            self._debug("Fetch failed for inmate '%s'\nException is %s" % (self._jail_id, str(e)))
        finally:
            self._debug(msg_template % 'finished')

    def _store_bail_info(self):
        # Bond: If the value is an integer, it's a dollar
        # amount. Otherwise, it's a status, e.g. "* NO BOND *".
        self._inmate.bail_amount = convert_to_int(self._inmate_details.bail_amount().replace(',', ''), None)
        if self._inmate.bail_amount is None:
            self._inmate.bail_status = self._inmate_details.bail_amount().replace('*', '').strip()
        else:
            self._inmate.bail_status = None

    def _store_booking_date(self):
        self._inmate.booking_date = self._inmate_details.booking_date()

    def _store_charges(self):
        charges_info = Charges(self._inmate, self._inmate_details, self._monitor)
        charges_info.save()

    def _store_housing_location(self):
        housing_location_info = HousingLocationInfo(self._inmate, self._inmate_details, self._monitor)
        housing_location_info.save()

    def _store_next_court_info(self):
        next_court_date_info = CourtDateInfo(self._inmate, self._inmate_details, self._monitor)
        next_court_date_info.save()

    def _store_person_id(self):
        self._inmate.person_id = self._inmate_details.hash_id()

    def _store_physical_characteristics(self):
        self._inmate.gender = self._inmate_details.gender()
        self._inmate.race = self._inmate_details.race()
        self._inmate.height = self._inmate_details.height()
        self._inmate.weight = self._inmate_details.weight()
        self._inmate.age_at_booking = self._inmate_details.age_at_booking()
