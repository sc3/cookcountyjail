from django.db.utils import DatabaseError

from countyapi.utils import convert_to_int, join_with_space_and_convert_spaces, yesterday
from countyapi.models import HousingLocation


class HousingLocationInfo:

    def __init__(self, inmate, inmate_details, monitor):
        self._inmate = inmate
        self._inmate_details = inmate_details
        self._monitor = monitor
        self._housing_location = None
        self._location_segments = None

    def _debug(self, msg):
        self._monitor.debug('HousingLocationInfo: %s' % msg)

    def _process_housing_location(self):
        """
        Receives a housing location from the HousingLocation table and parses it editing the different fields
        """
        self._location_segments = self._housing_location.housing_location.replace("-", " ").split()
        if self._location_segments == [] or convert_to_int(self._location_segments[0], None) is None:
            # Location did not start with a number so no further parsing
            if self._housing_location.housing_location == "":
                self._housing_location.housing_location = "UNKNOWN"
            return

        self._housing_location.division = self._location_segments[0]
        if len(self._location_segments) == 1:  # Execute only if the housing information is a single division number
            return                             # ex: '01-'

        self._set_day_release()

        location_start = convert_to_int(self._location_segments[0], -1)

        if location_start in [2, 8, 9, 11, 14] or (location_start == 1 and
                                                   "ABO" in self._housing_location.housing_location):
            self._set_sub_division(self._location_segments[1], self._location_segments[2:])
            return
        elif location_start == 3:
            if "AX" in self._housing_location.housing_location:
                self._set_sub_division(self._location_segments[2], self._location_segments[3:])
                return
        elif location_start in [5, 6, 10]:
            self._set_location_05_06_10_values()
            return
        elif location_start == 15:
            self._set_location_15_values()
            return
        elif location_start == 16:
            return
        elif location_start == 17:
            self._set_location_17_values()
            return
        elif location_start == 4:
            self._set_location_04_values()

        self._set_sub_division(join_with_space_and_convert_spaces(self._location_segments[1:3], ""),
                               self._location_segments[3:])

    def save(self):
        try:
            inmate_housing_location = self._inmate_details.housing_location()
            if inmate_housing_location != '':
                try:
                    self._housing_location, created_location = \
                        HousingLocation.objects.get_or_create(housing_location=inmate_housing_location)
                    if created_location:
                        self._process_housing_location()
                        self._housing_location.save()
                        self._debug('New housing location encountered: %s' % self._housing_location.housing_location)
                except DatabaseError as e:
                    self._debug("Could not save housing location '%s'\nException is %s" % (inmate_housing_location,
                                                                                           str(e)))
                try:
                    housing_history, new_history = \
                        self._inmate.housing_history.get_or_create(housing_location=self._housing_location)
                    if new_history:
                        housing_history.housing_date_discovered = yesterday()
                        housing_history.save()
                        self._inmate.in_jail = self._housing_location.in_jail
                except DatabaseError as e:
                    self._debug("For inmate %s, could not save housing history '%s'.\nException is %s" %
                                (self._inmate.jail_id, inmate_housing_location, str(e)))
        except Exception, e:
            self._debug("Unknown exception for inmate '%s'\nException is %s" % (self._inmate.jail_id, str(e)))

    def _set_day_release(self):
        for element in self._location_segments:
            if element == "DR":
                self._housing_location.in_program = "Day Release"
                self._housing_location.in_jail = False
            elif element == "DRAW":
                self._housing_location.in_program = "Day Release, AWOL"
                self._housing_location.in_jail = False

    def _set_location_04_values(self):
        if "M1" in self._housing_location.housing_location:
            self._housing_location.in_program = "Protective Custody"
        elif "N1" in self._housing_location.housing_location:
            self._housing_location.in_program = "Segregation"

    def _set_location_05_06_10_values(self):
        if len(self._location_segments) == 2:
            self._set_sub_division(self._location_segments[1], [])
        else:
            self._set_sub_division(self._location_segments[2] + self._location_segments[1], self._location_segments[3:])

    def _set_location_15_values(self):
        if self._location_segments[1] == "EM":
            self._housing_location.in_program = "Electronic Monitoring"
            self._housing_location.in_jail = False
        elif self._location_segments[1] == "EMAW":
            self._housing_location.in_program = "Electronic Monitoring, AWOL"
            self._housing_location.in_jail = False
        elif self._location_segments[1] in ["KK", "LV", "US"]:
            self._housing_location.in_program = "Other County"
            self._housing_location.in_jail = False
        else:
            self._housing_location.sub_division = self._location_segments[1]

    def _set_location_17_values(self):
        if self._location_segments[1] == "MOMS":
            self._housing_location.in_program = "MOMS Program"
        elif self._location_segments[1] == "SFFP":
            self._housing_location.in_program = "Sherrif Female Furlough Program"
            self._housing_location.in_jail = False
        elif self._location_segments[1] == "SFFPAW":
            self._housing_location.in_program = "Sherrif Female Furlough Program, AWOL"
            self._housing_location.in_jail = False

    def _set_sub_division(self, sub_division, sub_division_location):
        self._housing_location.sub_division = sub_division
        self._housing_location.sub_division_location = join_with_space_and_convert_spaces(sub_division_location)
