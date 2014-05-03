from django.conf.urls import patterns, include, url
from tastypie.api import Api
from countyapi.api import CountyInmateResource, CourtLocationResource, \
    CourtDateResource, HousingLocationResource, HousingHistoryResource, \
    DailyPopulationCountsResource, DailyBookingsCountsResource, ChargesHistoryResource

v1_api = Api(api_name='1.0')
v1_api.register(CountyInmateResource())
v1_api.register(CourtLocationResource())
v1_api.register(CourtDateResource())
v1_api.register(HousingLocationResource())
v1_api.register(HousingHistoryResource())
v1_api.register(DailyPopulationCountsResource())
v1_api.register(DailyBookingsCountsResource())
v1_api.register(ChargesHistoryResource())

urlpatterns = patterns('', url(r'^api/', include(v1_api.urls)))
