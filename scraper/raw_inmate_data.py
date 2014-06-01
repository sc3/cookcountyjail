
import os.path
import csv
from collections import OrderedDict
import shutil

RAW_INMATE_DATA_BUILD_DIR = 'CCJ_RAW_INMATE_DATA_BUILD_DIR'
RAW_INMATE_DATA_RELEASE_DIR = 'CCJ_RAW_INMATE_DATA_RELEASE_DIR'
STORE_RAW_INMATE_DATA = 'CCJ_STORE_RAW_INMATE_DATA'

FEATURE_CONTROL_IDS = [RAW_INMATE_DATA_BUILD_DIR, RAW_INMATE_DATA_RELEASE_DIR]
FEATURE_SWITCH_IDS = [STORE_RAW_INMATE_DATA]


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

    def __init__(self, snap_shot_date, feature_controls, monitor):
        if feature_controls is None:
            feature_controls = {}
        self.__klass = type(self)
        self.__klass_name = self.__klass.__name__
        self.__monitor = monitor
        self.__snap_shot_date = snap_shot_date
        self.__raw_inmate_dir = None
        self.__build_dir = None
        self.__build_file_writer = None
        self.__build_file = None
        self.__build_file_name = None
        self.__feature_activated = False
        self.__configure_feature(feature_controls)

    def add(self, inmate_details):
        if not self.__feature_activated:
            return
        if self.__build_file_writer is None:
            self.__open_build_file()
        inmate_info = [
            getattr(inmate_details, method_name)() for method_name in RawInmateData.HEADER_METHOD_NAMES.itervalues()
        ]
        self.__build_file_writer.writerow(inmate_info)

    def __configure_feature(self, feature_controls):
        if not (STORE_RAW_INMATE_DATA in feature_controls and feature_controls[STORE_RAW_INMATE_DATA]):
            return
        okay, self.__build_dir = self.__feature_control(feature_controls, RAW_INMATE_DATA_BUILD_DIR)
        if not okay:
            return
        okay, self.__raw_inmate_dir = self.__feature_control(feature_controls, RAW_INMATE_DATA_RELEASE_DIR)
        if not okay:
            return
        self.__feature_activated = True

    def __debug(self, msg, debug_level=None):
        self.__monitor.debug('{0}: {1}'.format(self.__klass_name, msg), debug_level)

    def __ensure_year_dir(self):
        year_dir = os.path.join(self.__raw_inmate_dir, self.__snap_shot_date.strftime('%Y'))
        try:
            os.makedirs(year_dir)
        except OSError:
            if not os.path.isdir(year_dir):
                raise
        return year_dir

    def __feature_control(self, feature_controls, feature_control):
        okay, dir_name = False, None
        if feature_control in feature_controls:
            dir_name = feature_controls[feature_control]
            okay = os.path.isdir(dir_name)
            if not okay:
                self.__debug("'%s' does not exist or is not a directory" % dir_name)
        return okay, dir_name

    def __file_name(self):
        return self.__snap_shot_date.strftime('%Y-%m-%d.csv')

    def finish(self):
        if not self.__feature_activated:
            return
        self.__build_file.close()
        year_dir = self.__ensure_year_dir()
        shutil.move(self.__build_file_name, year_dir)

    def __open_build_file(self):
        self.__build_file_name = os.path.join(self.__build_dir, self.__file_name())
        self.__build_file = open(self.__build_file_name, "w")
        self.__build_file_writer = csv.writer(self.__build_file)
        header_names = [header_name for header_name in RawInmateData.HEADER_METHOD_NAMES.iterkeys()]
        self.__build_file_writer.writerow(header_names)
