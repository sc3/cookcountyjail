from django.core import serializers
from django.http import HttpResponse

from models import CountyInmate

def data_json(request):
    objects = CountyInmate.objects.all()
    return HttpResponse(serializers.serialize('json', objects[:5000]), 
    	content_type="application/json")
