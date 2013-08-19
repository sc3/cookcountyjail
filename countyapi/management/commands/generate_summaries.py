from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate, DailyPopulationCounts, DailyBookingsCounts
from django.db.models import Max, Min, Q
from copy import copy

GENDER_LOOKUP = {
    'M': 'male',
    'F': 'female',
}

MIN_DATE = datetime(2013, 1, 1)

class Command(BaseCommand):

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def handle(self, *args, **options):
        DailyPopulationCounts.objects.all().delete()
        DailyBookingsCounts.objects.all().delete()

        template = {
            'total': 0,
            'female_as': 0,
            'female_b': 0,
            'female_bk': 0,
            'female_in': 0,
            'female_lb': 0,
            'female_lw': 0,
            'female_lt': 0,
            'female_w': 0,
            'female_wh': 0,
            'male_as': 0,
            'male_b': 0,
            'male_bk': 0,
            'male_in': 0,
            'male_lb': 0,
            'male_lw': 0,
            'male_lt': 0,
            'male_w': 0,
            'male_wh': 0,
        }

        booking_template = {
            'total': 0,
            'female_as': 0,
            'female_b': 0,
            'female_bk': 0,
            'female_in': 0,
            'female_lb': 0,
            'female_lw': 0,
            'female_lt': 0,
            'female_w': 0,
            'female_wh': 0,
            'female_minors': 0,
            'male_as': 0,
            'male_b': 0,
            'male_bk': 0,
            'male_in': 0,
            'male_lb': 0,
            'male_lw': 0,
            'male_lt': 0,
            'male_w': 0,
            'male_wh': 0,
            'male_minors': 0,
        }

        counts = {}
        booking_counts = {}

        min_date = MIN_DATE
        max_date = CountyInmate.objects.all().aggregate(
            Max('booking_date'))['booking_date__max'] + timedelta(days=1)

        for day in self.daterange(min_date, max_date):
            print("Processing %s-%s-%s" % (day.year, day.month, day.day))
            inmates = CountyInmate.objects.filter(booking_date__lte=day)\
                .filter(Q(discharge_date_earliest__gt=day) | Q(discharge_date_earliest__isnull=True))
                
            inmates_booked = CountyInmate.objects.filter(booking_date=day)
            
            daily_pop_row = self.count_dictionary(inmates, template)
            booking_row = self.count_dictionary(inmates_booked, booking_template, track_minors=True)
            
            counts[day.strftime('%Y-%m-%d')] = daily_pop_row
            booking_counts[day.strftime('%Y-%m-%d')] = booking_row

        self.save_count(counts, DailyPopulationCounts)
        self.save_count(booking_counts, DailyBookingsCounts)

    def count_dictionary(self, inmates, counts_template, track_minors=False):
        row = copy(counts_template)
        for inmate in inmates:
            gender = GENDER_LOOKUP[inmate.gender]
            
            key = "%s_%s" % (gender, inmate.race.lower())
            self.up_count(row, key)
            self.up_count(row, 'total')
            
            if track_minors:
                age = inmate.age_at_booking
                inmate_is_minor = True if age < 18 else False
                
                if inmate_is_minor:
                    minor_key = "%s_%s" % (gender, 'minors')
                    self.up_count(row, minor_key)
        return row
    
    def up_count(self, dict_obj, key, value=1):
        try:
            dict_obj[key] += value
        except KeyError:
            pass
    
    def save_count(self, counts_dict, model):
        for date, count in counts_dict.items():
            daily_count = model(booking_date=date, **count)
            daily_count.save()
