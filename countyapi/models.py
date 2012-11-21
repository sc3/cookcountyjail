from django.db import models

class CountyInmate(models.Model):
    jail_id=models.CharField(max_length=12, primary_key=True)
    last_name=models.CharField(max_length=100)
    first_name=models.CharField(max_length=100)
    # @TODO Add other fields
    # See e.g. http://www2.cookcountysheriff.org/search2/details.asp?jailnumber=2012-0813098 
