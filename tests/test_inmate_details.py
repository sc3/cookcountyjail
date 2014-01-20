# coding=utf-8
from datetime import datetime
from pyquery import PyQuery as pq
import hashlib


class InmateDetails:
    """
    Handles the processing of the Inmate Detail information page on the
    Cook County Jail website.
    Presents a consistent named interface to the information

    Strips spurious whitespace from text content before returning them

    Dates are returned as datetime objects
    """

    def __init__(self, html):
        inmate_doc = pq(html)
        self.__columns = inmate_doc('table tr:nth-child(2n) td')

    def age_at_booking(self):
        """
        Calculates the inmates age at the time of booking,
        code taken from http://is.gd/ep7Thb
        """
        birth_date, booking_date = self._birth_date(), self.booking_date()
        if (birth_date.month <= booking_date.month and
                birth_date.day <= booking_date.day):
            return booking_date.year - birth_date.year
        return booking_date.year - birth_date.year - 1

    def bail_amount(self):
        return self._column_content(10)

    def _birth_date(self):
        return self._convert_date(2)

    def booking_date(self):
        return self._convert_date(7)

    def charges(self):
        return self._column_content(11)

    def _column_content(self, columns_index):
        return self.__columns[columns_index].text_content().strip()

    def _convert_date(self, column_index):
        try:
            result = datetime.strptime(self._column_content(column_index),
                                       '%m/%d/%Y')
        except ValueError:
            result = None
        return result

    def court_house_location(self):
        return self._column_content(13)

    def gender(self):
        return self._column_content(4)

    def hash_id(self):
        id_string = "%s%s%s%s" % (
            self._name().replace(" ", ""),
            self._birth_date().strftime('%m%d%Y'),
            self.race()[0],
            self.gender(),
        )
        byte_string = id_string.encode('utf-8')
        return hashlib.sha256(byte_string).hexdigest()

    def height(self):
        return self._column_content(5)

    def housing_location(self):
        return self._column_content(8)

    def jail_id(self):
        return self._column_content(0)

    def _name(self):
        return self._column_content(1)

    def next_court_date(self):
        return self._convert_date(12)

    def race(self):
        return self._column_content(3)

    def weight(self):
        return self._column_content(6)


from datetime import datetime
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
