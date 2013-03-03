import csv
from django.http import HttpResponse
from tastypie.resources import ModelResource, ALL
from tastypie import fields
from countyapi.models import CountyInmate, CourtLocation, CourtDate, HousingLocation, HousingHistory
from django.core.serializers import json
from django.utils import simplejson
from tastypie.serializers import Serializer

class JailSerializer(Serializer):
    json_indent = 2

    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'plist', 'csv']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'csv': 'text/csv',
    }

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)


    def to_csv(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=cookcountyjail.csv'

        writer = csv.writer(response)
        writer.writerow([unicode(key).encode(
                "utf-8", "replace") for key in data['objects'][0].keys()])

        for item in data['objects']:
            writer.writerow([unicode(item[key]).encode(
                "utf-8", "replace") for key in item.keys()])

        return response



class CourtLocationResource(ModelResource):
    class Meta:
        queryset = CourtLocation.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        limit = 2500
        serializer = JailSerializer()

    def dehydrate(self, bundle):
        # Show court dates in location lists and detail views
        if bundle.request.path.startswith('/api/1.0/courtlocation/') and (bundle.request.path != '/api/1.0/courtlocation/' or bundle.request.REQUEST.get('related')):
            dates = bundle.obj.court_dates.all()
            resource = CourtDateResource()
            bundle.data['court_dates'] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data["court_dates"].append(resource.full_dehydrate(date_bundle).data)
        return bundle

class CountyInmateResource(ModelResource):
    class Meta:
        queryset = CountyInmate.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        limit = 100
        serializer = JailSerializer()

        # Exclude non-essential data. Reintroduce to API if needed.
        excludes = ['height', 'weight', 'last_seen_date', 'discharge_date_latest', 'url']

        filtering = {
            'jail_id': ALL,
            'booking_date': ALL,
            'discharge_date_earliest': ALL,
            'gender': ALL,
            'age_at_booking': ALL,
            'bail_amount': ALL,
            'housing_location': ALL,
            'charges': ALL,
            'charges_citation':ALL,
            'race':ALL,
        }

    def dehydrate(self, bundle):
        # Show court dates in inmate lists and detail views
        if bundle.request.path.startswith('/api/1.0/countyinmate/') and (bundle.request.path != '/api/1.0/countyinmate/' or bundle.request.REQUEST.get('related')):
            dates = bundle.obj.court_dates.all()
            resource = CourtDateResource()
            bundle.data['court_dates'] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data["court_dates"].append(resource.full_dehydrate(date_bundle).data)
        return bundle


class CourtDateResource(ModelResource):
    class Meta:
        queryset = CourtDate.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        serializer = JailSerializer()

    def dehydrate(self, bundle):
        # Include inmate ID when called from location
        if bundle.request.path.startswith("/api/1.0/courtlocation/"):
            bundle.data["inmate"] = bundle.obj.inmate.pk

        # Include location when called from inmate
        if bundle.request.path.startswith("/api/1.0/countyinmate/"):
            location = bundle.obj.location
            resource = CourtLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data["location"] = resource.full_dehydrate(location_bundle).data

        # Include primary keys on court dates
        if bundle.request.path.startswith("/api/1.0/courtdate/") and not bundle.request.REQUEST.get('related'):
            bundle.data["location_id"] = bundle.obj.location.pk
            bundle.data["location"] = bundle.obj.location.location
            bundle.data["inmate_jail_id"] = bundle.obj.inmate.pk

        # Include full inmate in related query
        if bundle.request.path.startswith("/api/1.0/courtdate/") and bundle.request.REQUEST.get('related'):
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data["inmate"] = resource.full_dehydrate(inmate_bundle).data
            
            location = bundle.obj.location
            resource = CourtLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data["location"] = resource.full_dehydrate(location_bundle).data

        return bundle

class HousingLocationResource(ModelResource):
    class Meta:
        queryset = HousingLocation.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        serializer = JailSerializer()
        filtering = {
            'housing_location': ALL,
            'division': ALL,
            'sub_division': ALL,
            'sub_division_location': ALL,
            'in_jail': ALL,
            'in_program': ALL
        }
 
class HousingHistoryResource(ModelResource):
    class Meta:
        queryset = HousingHistory.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        serializer = JailSerializer()
        filtering = {
            'inmate': ALL,
            'housing_date': ALL, 
            'housing_location': ALL
        }
