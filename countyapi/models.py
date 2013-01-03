from django.db import models

class CountyInmate(models.Model):
    jail_id=models.CharField(max_length=15, primary_key=True)
    url=models.CharField(max_length=255)
    race=models.CharField(max_length=4,null=True, blank=True)
    last_seen_date=models.DateTimeField(auto_now=True)
    booking_date=models.DateTimeField(null=True)
    discharge_date_earliest=models.DateTimeField(null=True)
    discharge_date_latest=models.DateTimeField(null=True)
    gender=models.CharField(max_length=1, null=True, blank=True)
    height=models.IntegerField(null=True, blank=True)
    weight=models.IntegerField(null=True, blank=True)
    age_at_booking=models.IntegerField(null=True, blank=True)
    bail_status=models.CharField(max_length=50, null=True)
    bail_amount=models.IntegerField(null=True, blank=True)
    housing_location=models.CharField(null=True,max_length=20)
    charges=models.TextField(null=True)
    charges_citation=models.TextField(null=True)

    def __unicode__(self):
        return self.jail_id
    
    class Meta:
        ordering = ['-jail_id']


class CourtDate(models.Model):
    inmate=models.ForeignKey('CountyInmate', related_name="court_dates")
    location=models.ForeignKey('CourtLocation', related_name="court_dates")
    date=models.DateField()

    class Meta:
        ordering = ['date']


class CourtLocation(models.Model):
    location=models.TextField()


class InmateRecordCount(models.Model):
    """ This is a silly example. @TODO Create real summaries. """
    date = models.DateTimeField(auto_now_add=True)
    record_count = models.IntegerField()
