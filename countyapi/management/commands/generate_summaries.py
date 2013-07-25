from datetime import datetime
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate, InmateSummaries


class Command(BaseCommand):

    def handle(self, *args, **options):
        inmates = CountyInmate.objects.filter(discharge_date_earliest=None, discharge_date_latest=None).count()
        InmateSummaries.objects.create(current_inmate_count=inmates, date=datetime.today())
