# coding=utf-8

from datetime import datetime

from countyapi.management.scraper.inmate_details import InmateDetails

INMATE_1 = '2014-0117015'
inmates_html = {}
MARKHAM_COURT_HOUSE_LOCATION = \
    "Markham\n          Markham, Room:101\n       	  16501 South Kedzie Parkway Room: 101\n       	 	Markham, IL 60426"


class Test_InmateDetails:

    def setup_method(self, method):
        for jail_id in [INMATE_1]:
            if jail_id not in inmates_html:
                with open("tests/data/%s.html" % jail_id, "r") as inmates_file:
                    inmates_html[jail_id] = inmates_file.read()

    def test_inmate_details(self):
        inmate_details = InmateDetails(inmates_html[INMATE_1])
        assert inmate_details.age_at_booking() == 52
        assert inmate_details.bail_amount() == '20,000'
        assert inmate_details.charges() == "625 ILCS 5 6-303(d) [5883000]\n\t  DRIVING REVOKED/SUSPENDED 2ND+"
        #TODO: figure out how to deal with the spurious 0xa0 character in this value
        # assert inmate_details.court_house_location() == MARKHAM_COURT_HOUSE_LOCATION
        assert inmate_details.gender() == 'M'
        assert inmate_details.hash_id() == '10e8e7c4a10c26216c8567b66156937240875bd945702d0f003c97fce773f29b'
        assert inmate_details.height() == '509'
        assert inmate_details.housing_location() == '02-D2-T-3-T'
        assert inmate_details.jail_id() == INMATE_1
        assert inmate_details.next_court_date() == datetime(2014, 2, 7)
        assert inmate_details.race() == 'BK'
        assert inmate_details.weight() == '195'
