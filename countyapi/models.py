from django.db import models

class CountyInmate(models.Model):
    jail_id=models.CharField(max_length=16, primary_key=True)
    last_name=models.CharField(max_length=255)
    first_name=models.CharField(max_length=255)
    # @TODO Add other fields
    # See e.g. http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=2012-0813098 

    def __unicode__(self):
        return "%s, %s (%s)" % (self.last_name, self.first_name, self.jail_id)
