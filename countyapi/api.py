from tastypie.resources import ModelResource, ALL
from tastypie import fields
from countyapi.models import CountyInmate, CourtLocation, CourtDate
from django.core.serializers import json
from django.utils import simplejson
from tastypie.serializers import Serializer

class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)


class CourtLocationResource(ModelResource):
    class Meta:
        queryset = CourtLocation.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        serializer = PrettyJSONSerializer()

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
        serializer = PrettyJSONSerializer()

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

    def dehydrate(self, bundle):
        # Include inmate when called from location
        if bundle.request.path.startswith("/api/1.0/courtlocation/"):
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data["inmate"] = resource.full_dehydrate(inmate_bundle).data

        # Include location when called from inmate
        if bundle.request.path.startswith("/api/1.0/countyinmate/"):
            location = bundle.obj.location
            resource = CourtLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data["location"] = resource.full_dehydrate(location_bundle).data

        return bundle


