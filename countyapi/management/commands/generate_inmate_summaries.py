import logging
from django.core.management.base import BaseCommand
from countyapi.models import CountyInmate, InmateRecordCount

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Generate inmate summaries."
    def handle(self, *args, **kwargs):
        log.debug('Summarizing inmate records')
        record = InmateRecordCount(record_count=CountyInmate.objects.count())
        record.save()
