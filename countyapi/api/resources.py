from tastypie.resources import ModelResource
from tastypie import fields
from countyapi.models import CountyInmate, CourtLocation, CourtDate

class CourtLocationResource(ModelResource):
    court_dates = fields.ToManyField('countyapi.api.resources.CourtDateResource', 'court_dates', full=True)
    class Meta:
        queryset = CourtLocation.objects.all()
        allowed_methods = ['get']

class CourtLocationDateResource(ModelResource):
    class Meta:
        queryset = CourtLocation.objects.all()

class CourtDateResource(ModelResource):
    location = fields.ForeignKey('countyapi.api.resources.CourtLocationDateResource', 'location', full=True)
    class Meta:
        queryset = CourtDate.objects.all()
        allowed_methods = ['get']
    
class CountyInmateResource(ModelResource):
    court_dates = fields.ToManyField('countyapi.api.resources.CourtDateResource', 'court_dates', full=True)
    class Meta:
        queryset = CountyInmate.objects.all()
        allowed_methods = ['get']
        limit = 100
        filtering = {
            'jail_id': ['exact'],
            'race': ['exact'],
            'last_seen_date': ['exact', 'lte', 'lt', 'gte', 'gt'],
            'booking_date': ['exact', 'lte', 'lt',  'gte', 'gt'],
            'discharge_date_earliest': ['exact', 'lte', 'lt', 'gte', 'gt'],
            'discharge_date_latest': ['exact', 'lte', 'lt', 'gte', 'gt'],
            'gender': ['exact'],
            'height': ['lte', 'lt', 'gte', 'gt'],
            'weight': ['lte', 'lt', 'gte', 'gt'],
            'age_at_booking': ['exact', 'lte', 'lt', 'gte', 'gt'],
            'bail_amount': ['lte', 'lt', 'gte', 'gt'],
            'housing_location': ['exact'],
            'charges': ['exact'],
            'charges_citation': ['exact'],
        }
