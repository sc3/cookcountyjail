from datetime import datetime
from pyquery import PyQuery as pq
from utils import http_get

NUMBER_OF_ATTEMPTS = 5


class InmateDetails:
    """
    Handles the processing of the Inmate Detail information page on the
    Cook County Jail website.
    Presents a consistent named interface to the information

    Strips spurious whitspace from text content before returning them

    Dates are returned as datetime objects
    """

    def __init__(self, url, attempts=NUMBER_OF_ATTEMPTS, quiet=False):
        self.url = url
        inmate_result = http_get(url, number_attempts=attempts, quiet=quiet)
        self.__inmate_found = inmate_result is not None
        if self.__inmate_found:
            inmate_doc = pq(inmate_result.content)
            self.__columns = inmate_doc('table tr:nth-child(2n) td')

    def age_at_booking(self):
        """
        Calculates the inmates age at the time of booking,
        code taken from http://is.gd/ep7Thb
        """
        birth_date, booking_date = self.birth_date(), self.booking_date()
        if (birth_date.month <= booking_date.month and
                birth_date.day <= booking_date.day):
            return (booking_date.year - birth_date.year)
        return booking_date.year - birth_date.year - 1

    def bail_amount(self):
        return self.column_content(10)

    def birth_date(self):
        return self.convert_date(2)

    def booking_date(self):
        return self.convert_date(7)

    def charges(self):
        return self.column_content(11)

    def column_content(self, columns_index):
        return self.__columns[columns_index].text_content().strip()

    def convert_date(self, column_index):
        try:
            result = datetime.strptime(self.column_content(column_index),
                                       '%m/%d/%Y')
        except ValueError:
            result = None
        return result

    def court_house_location(self):
        return self.column_content(13)

    def found(self):
        return self.__inmate_found

    def gender(self):
        return self.column_content(4)

    def height(self):
        return self.column_content(5)

    def housing_location(self):
        return self.column_content(8)

    def jail_id(self):
        return self.column_content(0)

    def next_court_date(self):
        return self.convert_date(12)

    def race(self):
        return self.column_content(3)

    def weight(self):
        return self.column_content(6)
