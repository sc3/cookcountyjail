
import time
beginning = time.clock()

import logging
from collections import namedtuple

from django.core.management.base import BaseCommand
from django.db.utils import DatabaseError

import ijson

from countyapi.models import ChargesHistory, CountyInmate, CourtDate, \
    CourtLocation, HousingHistory, HousingLocation

log = logging.getLogger('main')

DbEntry = namedtuple('DbEntry', 'pk model fields')

FIELDS_PREFIX_LENGTH = len('item.fields.')

VALUE_EVENTS = set(['boolean', 'null', 'number', 'string'])

CHARGES_HISTORY_MNAME = 'countyapi.chargeshistory'
COUNTY_INMATE_MNAME = 'countyapi.countyinmate'
COURT_DATE_MNAME = 'countyapi.courtdate'
COURT_LOCATION_MNAME = 'countyapi.courtlocation'
HOUSING_HISTORY_MNAME = 'countyapi.housinghistory'
HOUSING_LOCATION_MNAME = 'countyapi.housinglocation'

FIRST_PASS_MODELS = set([COUNTY_INMATE_MNAME, COURT_LOCATION_MNAME, HOUSING_LOCATION_MNAME])
SECOND_PASS_MODELS = set([CHARGES_HISTORY_MNAME, COURT_DATE_MNAME, HOUSING_HISTORY_MNAME])


class Command(BaseCommand):

    help = "Incrementally load a datadump"

    def handle(self, *args, **options):
        """
        Audits the Cook County Jail Database reports on what it finds, primarily looking for
        incorrect records and it also reports on general stats.

        Initially ony looking at inmate records.
        @param args:
        @param options:
        @return: None
        """

        if len(args) != 1:
            log.error('Must specify a datadump file to load.')
            exit(1)

        self.__jsonFileName = args[0]
        self.__setup_model_mapping()
        self.__initialize()

        self.__populate_database(FIRST_PASS_MODELS)
        self.__populate_database(SECOND_PASS_MODELS)
        print 'Incremental loading took %f seconds.' % (time.clock() - beginning)

    def __activate_json_parser(self):
        self.__jsonParser = ijson.parse(open(self.__jsonFileName, 'r'))
        self.__jsonParser.next() # skip over the start of the list

    def __fetch_db_entry(self, models_to_populate):
        db_entry = None
        while db_entry is None:
            prefix, event, _ = self.__jsonParser.next()
            if prefix != 'item' or event != 'start_map':
                return None
            self.__jsonParser.next()
            pk = self.__jsonParser.next()[2]

            # skip to model type
            self.__jsonParser.next()
            model = self.__jsonParser.next()[2]
            store_model = model in models_to_populate

            # fetch fields and their values
            fields = self.__fetch_fields(store_model)
            if store_model:
                db_entry = DbEntry(pk, model, fields)
        return db_entry

    def __fetch_fields(self, store_model):
        fields = {}
        run = True
        while run:
            prefix, event, value = self.__jsonParser.next()
            if prefix == 'item' and event == 'end_map':
                run = False
            elif not store_model:
                continue
            elif event in VALUE_EVENTS:
                fields[prefix[FIELDS_PREFIX_LENGTH:]] = value
        return fields

    def __initialize(self):
        self.__num_charges_history = 0
        self.__next_charges_history_id = 1
        self.__num_county_inmates = 0
        self.__num_court_dates = 0
        self.__next_court_date_id = 1
        self.__num_court_location = 0
        self.__next_court_location_id = 1
        self.__num_housing_location = 0
        self.__num_housing_history = 0
        self.__next_housing_history_id = 1

    def __populate_database(self, models_to_populate):
        self.__activate_json_parser()
        try:
            while True:
                db_entry = self.__fetch_db_entry(models_to_populate)
                if db_entry:
                    self.__modelMapping[db_entry.model](db_entry)
        except StopIteration:
            pass

    def __setup_model_mapping(self):
        self.__modelMapping = {
            CHARGES_HISTORY_MNAME: self.__store_charges_history,
            COUNTY_INMATE_MNAME: self.__store_county_inmate,
            COURT_DATE_MNAME: self.__store_court_date,
            COURT_LOCATION_MNAME: self.__store_court_location,
            HOUSING_HISTORY_MNAME: self.__store_housing_history,
            HOUSING_LOCATION_MNAME: self.__store_housing_location,
        }

    def __store_charges_history(self, db_entry):
        self.__num_charges_history += 1
        self.__next_charges_history_id = self.__validate_expected_id('Charges History', db_entry,
                                                                     self.__next_charges_history_id)
        self.__next_charges_history_id += 1

    def __store_county_inmate(self, db_entry):
        self.__num_county_inmates += 1

    def __store_court_date(self, db_entry):
        self.__num_court_dates += 1
        self.__next_court_date_id = self.__validate_expected_id('Court Date', db_entry,
                                                                self.__next_court_date_id)
        self.__next_court_date_id += 1

    def __store_court_location(self, db_entry):
        self.__num_court_location += 1
        self.__next_court_location_id = self.__validate_expected_id('Court Location', db_entry,
                                                                    self.__next_court_location_id)
        self.__next_court_location_id += 1

    def __store_housing_history(self, db_entry):
        self.__num_housing_history += 1
        self.__next_housing_history_id = self.__validate_expected_id('Housing History', db_entry,
                                                                     self.__next_housing_history_id)
        self.__next_housing_history_id += 1

    def __store_housing_location(self, db_entry):
        self.__num_housing_location += 1

    @staticmethod
    def __validate_expected_id(id_name, db_entry, expected_value):
        if db_entry.pk != expected_value:
            print 'Expected %s id of %d, received %d' % (id_name, db_entry.pk, expected_value)
            return db_entry.pk
        return expected_value


#
# Information on how DB Model Data is stored
#

# item start_map None
# item map_key pk
# item.pk string 1993-9303175
# item map_key model
# item.model string countyapi.countyinmate
# item map_key fields
# item.fields start_map None
# item.fields map_key booking_date
# item.fields.booking_date string 1993-01-17
# item.fields map_key weight
# item.fields.weight number 150
# item.fields map_key bail_amount
# item.fields.bail_amount number 100000
# item.fields map_key gender
# item.fields.gender string M
# item.fields map_key discharge_date_latest
# item.fields.discharge_date_latest null None
# item.fields map_key height
# item.fields.height number 507
# item.fields map_key race
# item.fields.race string LW
# item.fields map_key age_at_booking
# item.fields.age_at_booking number 27
# item.fields map_key discharge_date_earliest
# item.fields.discharge_date_earliest null None
# item.fields map_key in_jail
# item.fields.in_jail boolean True
# item.fields map_key person_id
# item.fields.person_id string 3681c63d85a13c859fed8464f36cb59b547d315a11cc1517e68063805b1838c7
# item.fields map_key bail_status
# item.fields.bail_status null None
# item.fields map_key last_seen_date
# item.fields.last_seen_date string 2014-11-08T12:40:32.666
# item.fields end_map None
# item end_map None
#
#
# item start_map None
# item map_key pk
# item.pk number 1
# item map_key model
# item.model string countyapi.courtdate
# item map_key fields
# item.fields start_map None
# item.fields map_key inmate
# item.fields.inmate string 2012-0808003
# item.fields map_key date
# item.fields.date string 2012-12-14
# item.fields map_key location
# item.fields.location number 1
# item.fields end_map None
# item end_map None
#
#
# item start_map None
# item map_key pk
# item.pk number 1
# item map_key model
# item.model string countyapi.courtlocation
# item map_key fields
# item.fields start_map None
# item.fields map_key city
# item.fields.city null None
# item.fields map_key location_name
# item.fields.location_name null None
# item.fields map_key room_number
# item.fields.room_number null None
# item.fields map_key branch_name
# item.fields.branch_name null None
# item.fields map_key state
# item.fields.state null None
# item.fields map_key location
# item.fields.location string Criminal C
# Criminal Courts Building, Room:506
# 2650 South California Avenue Room: 506
# Chicago, IL 60608
#
# item.fields map_key address
# item.fields.address null None
# item.fields map_key zip_code
# item.fields.zip_code null None
# item.fields end_map None
# item end_map None
#
#
# item start_map None
# item map_key pk
# item.pk number 1
# item map_key model
# item.model string countyapi.housinghistory
# item map_key fields
# item.fields start_map None
# item.fields map_key inmate
# item.fields.inmate string 2012-0808003
# item.fields map_key housing_location
# item.fields.housing_location string 11-DA-1-109
# item.fields map_key housing_date_discovered
# item.fields.housing_date_discovered string 2013-03-29
# item.fields end_map None
# item end_map None
#
#
# item start_map None
# item map_key pk
# item.pk string
# item map_key model
# item.model string countyapi.housinglocation
# item map_key fields
# item.fields start_map None
# item.fields map_key division
# item.fields.division string
# item.fields map_key in_jail
# item.fields.in_jail boolean True
# item.fields map_key sub_division
# item.fields.sub_division string
# item.fields map_key in_program
# item.fields.in_program string
# item.fields map_key sub_division_location
# item.fields.sub_division_location string
# item.fields end_map None
# item end_map None
#
#
# item start_map None
# item map_key pk
# item.pk number 1
# item map_key model
# item.model string countyapi.chargeshistory
# item map_key fields
# item.fields start_map None
# item.fields map_key inmate
# item.fields.inmate string 2013-0629140
# item.fields map_key charges
# item.fields.charges string POSS AMT CON SUB EXCEPT(A)/(D)
# item.fields map_key date_seen
# item.fields.date_seen string 2013-07-02
# item.fields map_key charges_citation
# item.fields.charges_citation string 720 ILCS 570 402(c) [5101110]
# item.fields end_map None
# item end_map None
