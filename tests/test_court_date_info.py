from mock import Mock, call
from datetime import datetime
from countyapi.management.scraper.court_date_info import CourtDateInfo

class TestCourtDateInfo:

    """ 
        Tests CourtDateInfo class. 

        ::_parse_court_location

        - whether number of lines other than 4 is not parsed
        - whether unknown formats get handled in expected way; esp. at
            various splits
        - whether branch name gets represented correctly
        - whether room number gets represented correctly
        - whether address parts get represented correctly

        ::save

        - whether there being no court date gets handled in expected way
        - whether format of next_court_date is correct
        - whether DB exceptions get handled correctly
        - whether unknown exceptions get handled correctly

        Resources to fake:

        - inmate_details
            - inmate_details.court_house_location()
            - inmate_details.next_court_date()
        - django_inmate
            - inmate.court_dates.get_or_create(bar, baz)
        - django_courtlocation
            - ...
        - django_courtdate 
            - ...
        - monitor
            - monitor.debug()

    """

    def test_single_line_court_location_is_not_parsed(self):

        inmate_id_used = '2014-0326058'

        raw_court_house_location = 'yadayada yada'

        raw_next_court_date = datetime(2014, 4, 9, 0, 0)

        inmate_details = Mock()
        inmate_details.court_house_location.return_value = \
                raw_court_house_location
        inmate_details.next_court_date = \
                raw_next_court_date

        django_court_date = Mock()

        django_inmate = Mock()
        django_inmate.court_dates.get_or_create.return_value = \
                django_court_date

        monitor = Mock()

        court_date_info_under_test = CourtDateInfo(django_inmate, 
                inmate_details, monitor)

        result_court_location = \
                court_date_info_under_test._parse_court_location()

        assert result_court_location == ('yadayada yada', {})


