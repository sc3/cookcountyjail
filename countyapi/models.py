from django.db import models

class CountyInmate(models.Model):
    jail_id=models.CharField(max_length=64, primary_key=True)
    url=models.CharField(max_length=255)
    race=models.CharField(max_length=4)
    last_seen_date=models.DateTimeField(auto_now=True)
    booked_date=models.DateField()
    booked_datetime=models.DateTimeField(null=True)
    discharge_date=models.DateTimeField(null=True)

    
    # @TODO Add other fields
    # See e.g. http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=2012-0813098 

    def __unicode__(self):
        return self.jail_id

class InmateRecordCount(models.Model):
    """ This is a silly example. @TODO Create real summaries. """
    date = models.DateTimeField(auto_now_add=True)
    record_count = models.IntegerField()
