from django.conf.urls import patterns, include, url
from tastypie.api import Api
from countyapi.api import CountyInmateResource, CourtLocationResource, CourtDateResource

v1_api = Api(api_name='1.0')
v1_api.register(CountyInmateResource())
v1_api.register(CourtLocationResource())
v1_api.register(CourtDateResource())

urlpatterns = patterns('',
    url(r'', include(v1_api.urls)),
)
