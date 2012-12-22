from tastypie.resources import ModelResource
from countyapi.models import CountyInmate


class CountyInmateResource(ModelResource):
    class Meta:
        queryset = CountyInmate.objects.all()
        allowed_methods = ['get']