from mock import Mock, call
from datetime import datetime
from countyapi.utils import strip_the_lines
from countyapi.management.scraper.court_date_info import CourtDateInfo

class TestCourtDateInfo:

    """ 
        Tests CourtDateInfo class. 

        ::_parse_court_location

        - whether incorrect # of lines or other unknown format
            result in returning the raw court location string, 
            plus an empty dict. 
        - whether the raw court location string which gets
            returned no matter what is normalized
        - whether branch name, room number, and address parts 
            get parsed correctly with a valid court string.

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

    def test_single_line_court_location_results_in_no_parse(self):

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

        parse_result = \
                court_date_info_under_test._parse_court_location()

        assert parse_result[0] == raw_court_house_location
        assert parse_result[1] == {}


    def test_multiple_line_court_location_string_gets_normalized(self):

        raw_court_house_location = (u'Branch 62\r\n          '
                u'Branch 62, Room:402\r\n       \t  '
                u'555 West Harrison Room: 402\r\n       \t \t'
                u'Chicago, IL\xa060607')

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

        result_string = \
                court_date_info_under_test._parse_court_location()[0]

        normalized_location_string = \
                (u'Branch 62\n'
                 u'Branch 62, Room:402\n'
                 u'555 West Harrison Room: 402'
                 u'\nChicago, IL 60607')

        assert result_string == normalized_location_string


    def test_valid_court_location_results_in_all_fields_parsed_correctly(self):

        raw_court_house_location = (u'Branch 62\r\n          '
                u'Branch 62, Room:402\r\n       \t  '
                u'555 West Harrison Room: 402\r\n       \t \t'
                u'Chicago, IL\xa060607')

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

        parsed_fields = \
                court_date_info_under_test._parse_court_location()[1]

        parsed_fields = {
            'location_name': u'Branch 62',
            'branch_name': u'Branch 62',
            'room_number': 402,
            'address': u'555 West Harrison',
            'city': u'Chicago',
            'state': u'IL',
            'zip_code': 60607,
        }

        
