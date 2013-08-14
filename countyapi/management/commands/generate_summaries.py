from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate, DailyPopulationCounts
from django.db.models import Max, Min, Q
from copy import copy

GENDER_LOOKUP = {
    'M': 'male',
    'F': 'female',
}

MIN_DATE = datetime(2013, 1, 1)

class Command(BaseCommand):

    def daterange(self, start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def handle(self, *args, **options):
        DailyPopulationCounts.objects.all().delete()
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
        counts = {}

        min_date = MIN_DATE
        max_date = CountyInmate.objects.all().aggregate(
                Max('booking_date'))['booking_date__max'] + timedelta(days=1)

        for day in self.daterange(min_date, max_date):
            print "Processing %s-%s-%s" % (day.month, day.day, day.year)
            inmates = CountyInmate.objects.filter(booking_date__lte=day)\
                    .filter(Q(discharge_date_earliest__gt=day) | Q(discharge_date_earliest__isnull=True))
            row = copy(template)
            for inmate in inmates:
                key = "%s_%s" % (GENDER_LOOKUP[inmate.gender], inmate.race.lower())
                try:
                    row[key] += 1
                    row['total'] += 1
                except KeyError: pass
            counts[day.strftime('%Y-%m-%d')] = row
        for date, count in counts.items():
            daily_count = DailyPopulationCounts(date=date, **count)
            daily_count.save()

        # This counts daily admissions, not total population
        #for inmate in CountyInmate.objects.all().iterator():
            #try:
                #day = inmate.booking_date.strftime('%Y-%m-%d')
                #if not counts.get(day):
                    #counts[day] = copy(template)
                #key = "%s_%s" % (GENDER_LOOKUP[inmate.gender], inmate.race.lower())
                #counts[day][key] += 1
                #counts[day]['total'] += 1
            #except AttributeError:
                #pass
        #for date, count in counts.items():
            ## New count
            #daily_count = DailyPopulationCounts.objects.create(**count)
            #daily_count.date = date
            #daily_count.save()

