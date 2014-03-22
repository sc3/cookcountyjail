
from django.db.utils import DatabaseError

from countyapi.utils import convert_to_int, strip_the_lines

from countyapi.models import CourtLocation


class CourtDateInfo:

    def __init__(self, inmate, inmate_details, monitor):
        self._inmate = inmate
        self._inmate_details = inmate_details
        self._monitor = monitor

    def _debug(self, msg):
        self._monitor.debug('CourtDateInfo: %s' % msg)

    def _parse_court_location(self):
        """
        Takes a location string of the form:

        "Criminal C\nCriminal Courts Building, Room:506\n2650 South California Avenue Room: 506\nChicago, IL 60608"

        The lines can contain spurious white-space at the beginning and end of the lines, these are stripped

         and returns two values, cleaned up version the input string and a dict of the form:
        {
            'location_name': 'Criminal C',
            'branch_name': 'Criminal Courts Building',
            'room_number': 506,
            'address': '2650 South California Avenue',
            'city': 'Chicago',
            'state': 'IL',
            'zip_code': 60608,
        }

        If location is malformed, then original location string is returned with an empty dict
        """

        location_string = self._inmate_details.court_house_location()
        lines = strip_the_lines(location_string.splitlines())
        if len(lines) == 4:
            try:
                # The first line is the location_name
                location_name = lines[0]

                # Second line must be split into room number and branch name
                branch_line = lines[1].split(', Room:')
                branch_name = branch_line[0].strip()
                room_number = convert_to_int(branch_line[1], 0)

                # Third line has address - remove room number and store
                address = lines[2].split('Room:')[0].strip()

                # Fourth line has city, state and zip separated by spaces,
                # or a weird unicode space character
                city_state_zip = lines[3].replace(u'\xa0', u' ').split(' ')

                city = " ".join(city_state_zip[0:-2]).replace(',', '').strip()
                state = city_state_zip[-2].strip()
                zip_code = convert_to_int(city_state_zip[-1], 60639)

                d = {
                    'location_name': location_name,
                    'branch_name': branch_name,
                    'room_number': room_number,
                    'address': address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                }
                return "\n".join(lines), d

            except IndexError:
                self._debug("Following Court location has unknown format: %s" % location_string)
                return "\n".join(lines), {}

        else:
            self._debug("Following Court location doesn't have right number of lines: %s" % location_string)
            return location_string, {}

    def save(self):
        # Court date parsing
        try:
            next_court_date = self._inmate_details.next_court_date()
            if next_court_date is not None:
                # Get location record by parsing next Court location string
                next_court_location, parsed_location = self._parse_court_location()
                try:
                    location, _ = CourtLocation.objects.get_or_create(location=next_court_location, **parsed_location)
                except DatabaseError as e:
                    self._debug("For inmate %s, could not save Court Location '%s'.\nException is %s" %
                                (self._inmate.jail_id, next_court_location, str(e)))

                try:
                    # Get or create a court date for this inmate
                    court_date, _ = self._inmate.court_dates.get_or_create(date=next_court_date.strftime('%Y-%m-%d'),
                                                                           location=location)
                except DatabaseError as e:
                    self._debug("For inmate %s, could not save next Court Date history '%s'.\nException is %s" %
                                (self._inmate.jail_id, court_date, str(e)))
        except Exception, e:
            self._debug("Unknown exception for inmate '%s'\nException is %s" % (self._inmate.jail_id, str(e)))
