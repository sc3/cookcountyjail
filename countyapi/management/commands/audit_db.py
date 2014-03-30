
from datetime import datetime
import logging

from django.core.management.base import BaseCommand
from django.db.utils import DatabaseError

from countyapi.models import CountyInmate


IN_JAIL_INCORRECT = 'in_jail_incorrect'
NO_HOUSING_LOC = 'no_housing_location'
NUMBER = 'number'

log = logging.getLogger('main')


class Command(BaseCommand):

    help = "Audit the Cook County Jail Database looking for records in invalid states."

    inmate_stats = {
        NUMBER: 0,
        NO_HOUSING_LOC: 0,
        IN_JAIL_INCORRECT: 0,
    }

    # Django uses lazy evaluation when dealing with the database so for instance the test
    #        inmate.housing_history.all() == []
    # will fail as the left hand side of the comparison is returning an object that is not
    # a list, it may evaluate to an empty list. This means that you have force the lazy
    # evaluation to occur so you get the right testing to occur

    def handle(self, *args, **options):
        """
        Audits the Cook County Jail Database reports on what it finds, primarily looking for
        incorrect records and it also reports on general stats.

        Initially ony looking at inmate records.
        @param args:
        @param options:
        @return: None
        """
        start_time = datetime.now()
        inmate_id = 'Uninitialized'
        print("Starting database audit: %s" % str(start_time))
        try:
            for inmate in CountyInmate.objects.all():
                self.increment_stat(NUMBER)
                inmate_id = inmate.jail_id
                self.check_in_jail(inmate)
        except DatabaseError as e:
            log.error("Inmate is '%s'\nException is %s" % (inmate_id, str(e)))
        except Exception, e:
            log.exception(e)

        self.display_audit_results()

        print("Audit took %s." % str(datetime.now() - start_time))

    def check_in_jail(self, inmate):
        if inmate.discharge_date_earliest is None:
            housing_history = inmate.housing_history.all()
            housing_history_length = len(housing_history)
            if housing_history_length == 0:
                self.increment_stat(NO_HOUSING_LOC)
                if not inmate.in_jail:
                    self.increment_stat(IN_JAIL_INCORRECT)
            else:
                if inmate.in_jail != housing_history[housing_history_length - 1].housing_location.in_jail:
                    self.increment_stat(IN_JAIL_INCORRECT)
        elif inmate.in_jail:
            self.increment_stat(IN_JAIL_INCORRECT)

    def display_audit_results(self):
        print("Number inmates checked: %d" % self.inmate_stats[NUMBER])
        if self.inmate_stats[IN_JAIL_INCORRECT] != 0:
            print("Number inmates with incorrect 'in_jail' values: %d" % self.inmate_stats[IN_JAIL_INCORRECT])
        if self.inmate_stats[NO_HOUSING_LOC] != 0:
            print("Number inmates with no housing location: %d" % self.inmate_stats[NO_HOUSING_LOC])

    def increment_stat(self, fault_name):
        self.inmate_stats[fault_name] += 1
