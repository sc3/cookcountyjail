from datetime import datetime
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate, DailyPopulationCounts
from copy import copy

GENDER_LOOKUP = {
    'M': 'male',
    'F': 'female',
}

class Command(BaseCommand):

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
        for inmate in CountyInmate.objects.all().iterator():
            day = inmate.booking_date.strftime('%Y-%m-%d')
            if not counts.get(day):
                counts[day] = copy(template)
            key = "%s_%s" % (GENDER_LOOKUP[inmate.gender], inmate.race.lower())
            counts[day][key] += 1
            counts[day]['total'] += 1
        for date, count in counts.items():
            # New count
            daily_count = DailyPopulationCounts.objects.create(**count)
            daily_count.date = date
            daily_count.save()


