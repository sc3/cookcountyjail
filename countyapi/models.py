from django.db import models

class CountyInmate(models.Model):
    jail_id=models.CharField(max_length=64, primary_key=True)
    url=models.CharField(max_length=255)
    last_name=models.CharField(max_length=255)
    first_name=models.CharField(max_length=255)
    # @TODO Add other fields
    # See e.g. http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=2012-0813098 

    def __unicode__(self):
        if self.last_name and self.first_name:
            return "%s - %s, %s" % (self.jail_id, self.last_name, self.first_name)
        return self.jail_id

class InmateRecordCount(models.Model):
    """ This is a silly example. @TODO Create real summaries. """
    date = models.DateTimeField(auto_now_add=True)
    record_count = models.IntegerField()
