
import os.path
import csv
from collections import OrderedDict
import shutil


class RawInmateData:

    HEADER_METHOD_NAMES = OrderedDict([
        ('Booking_Id', 'jail_id'),
        ('Booking_Date', 'booking_date'),
        ('Inmate_Hash', 'hash_id'),
        ('Gender', 'gender'),
        ('Race', 'race'),
        ('Height', 'height'),
        ('Weight', 'weight'),
        ('Age_At_Booking', 'age_at_booking'),
        ('Housing_Location', 'housing_location'),
        ('Charges', 'charges'),
        ('Bail_Amount', 'bail_amount'),
        ('Court_Date', 'next_court_date'),
        ('Court_Location', 'court_house_location')
    ])

    def __init__(self, today, raw_inmate_dir, build_dir):
        self.__today = today
        self.__raw_inmate_dir = raw_inmate_dir
        self.__build_dir = build_dir
        self.__build_file_writer = None
        self.__build_file = None
        self.__build_file_name = None

    def add(self, inmate_details):
        if self.__build_file_writer is None:
            self.__open_build_file()
        inmate_info = [
            getattr(inmate_details, method_name)() for method_name in RawInmateData.HEADER_METHOD_NAMES.itervalues()
        ]
        self.__build_file_writer.writerow(inmate_info)

    def __ensure_year_dir(self):
        year_dir = os.path.join(self.__raw_inmate_dir, self.__today.strftime('%Y'))
        try:
            os.makedirs(year_dir)
        except OSError:
            if not os.path.isdir(year_dir):
                raise
        return year_dir

    def __file_name(self):
        return self.__today.strftime('%Y-%m-%d.csv')

    def finish(self):
        self.__build_file.close()
        year_dir = self.__ensure_year_dir()
        shutil.move(self.__build_file_name, year_dir)

    def __open_build_file(self):
        self.__build_file_name = os.path.join(self.__build_dir, self.__file_name())
        self.__build_file = open(self.__build_file_name, "w")
        self.__build_file_writer = csv.writer(self.__build_file)
        header_names = [header_name for header_name in RawInmateData.HEADER_METHOD_NAMES.iterkeys()]
        self.__build_file_writer.writerow(header_names)
