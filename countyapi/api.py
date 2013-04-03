import csv
from django.http import HttpResponse
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.serializers import Serializer
from tastypie.cache import SimpleCache
from countyapi.models import CountyInmate, CourtLocation, CourtDate, HousingLocation, HousingHistory
from copy import copy

DISCLAIMER = """Cook County Jail Inmate data, scraped from
http://www2.cookcountysheriff.org/search2/ nightly.

Learn more about this API at
https://github.com/sc3/cookcountyjail/wiki/API-guide

Learn more about this project at
https://github.com/sc3/cookcountyjail/

The data on jail inmates is not verified. Do not take the data as
definitive, but rather as suggestive. This data can be used to develop
interesting questions, but it cannot be cited as factual.

Developed by the Supreme Chi-Town Coding Crew
(https://github.com/sc3/sc3)"""


class JailSerializer(Serializer):
    """Serialize to json, jsonp, xml, and csv."""

    formats = ['json', 'jsonp', 'xml', 'csv']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'csv': 'text/csv',
    }

    def to_csv(self, data, options=None):
        """Write to a simple CSV format."""
        options = options or {}
        data = self.to_simple(data, options)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cookcountyjail.csv"'

        writer = csv.writer(response)
        writer.writerow(data['objects'][0].keys())

        for item in data['objects']:
            writer.writerow(item.values())

        return response


class JailResource(ModelResource):
    """ModelResource overrides for our project. Add caching and disclaimer."""
    def __init__(self, api_name=None):
        """Patched init that doesn't use deepcopy, see https://github.com/toastdriven/django-tastypie/issues/720"""
        self.fields = {k: copy(v) for k, v in self.base_fields.iteritems()}

        if not api_name is None:
            self._meta.api_name = api_name

    def alter_detail_data_to_serialize(self, request, data):
        """Add message to data."""
        data.data['about_this_data'] = DISCLAIMER
        return data

    def alter_list_data_to_serialize(self, request, data):
        """Add message to meta."""
        data['meta']['about_this_data'] = DISCLAIMER
        return data


class CourtLocationResource(JailResource):
    """
    API endpoint for CourtLocation model, which represents court room.
    """

    class Meta:
        queryset = CourtLocation.objects.all()
        limit = 100
        max_limit = 0
        cache = SimpleCache(timeout=720)
        serializer = JailSerializer()
        filtering = {
            'location': ALL,
        }

    def dehydrate(self, bundle):
        """Show court dates in location lists and detail views."""
        if bundle.request.path.startswith('/api/1.0/courtlocation/') and (bundle.request.path != '/api/1.0/courtlocation/' or bundle.request.REQUEST.get('related') == '1'):
            dates = bundle.obj.court_dates.all()
            resource = CourtDateResource()
            bundle.data['court_dates'] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data["court_dates"].append(resource.full_dehydrate(date_bundle).data)
        return bundle


class CourtDateResource(JailResource):
    """
    API endpoint for CourtDate model, the unique combination of courtroom,
    inmate, and date used to represent the court history.
    """
    location = fields.ToOneField(CourtLocationResource, "location", null=True, full=False)
    inmate = fields.ToOneField('countyapi.api.CountyInmateResource', "inmate", null=True, full=False)

    class Meta:
        queryset = CourtDate.objects.all()
        allowed_methods = ['get']
        limit = 100
        max_limit = 0
        cache = SimpleCache(timeout=720)
        serializer = JailSerializer()
        filtering = {
            'date': ALL,
            'location': ALL_WITH_RELATIONS,
            'inmate': ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()


    def dehydrate(self, bundle):
        """Set up bidirectional relationships based on request."""

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
        if bundle.request.path.startswith("/api/1.0/courtdate/") and not bundle.request.REQUEST.get('related') == '1':
            bundle.data["location_id"] = bundle.obj.location.pk
            bundle.data["location"] = bundle.obj.location.location
            bundle.data["inmate_jail_id"] = bundle.obj.inmate.pk

        # Include full inmate in related query
        if bundle.request.path.startswith("/api/1.0/courtdate/") and bundle.request.REQUEST.get('related') == '1':
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data["inmate"] = resource.full_dehydrate(inmate_bundle).data

            location = bundle.obj.location
            resource = CourtLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data["location"] = resource.full_dehydrate(location_bundle).data

        return bundle

class HousingLocationResource(JailResource):
    """
    API endpoint for HousingLocation model, a place or status in the jail.
    """

    class Meta:
        queryset = HousingLocation.objects.all()
        allowed_methods = ['get']
        limit = 100
        max_limit = 0
        cache = SimpleCache(timeout=720)
        serializer = JailSerializer()
        filtering = {
            'housing_location': ALL,
            'division': ALL,
            'sub_division': ALL,
            'sub_division_location': ALL,
            'in_jail': ALL,
            'in_program': ALL
        }
        ordering = filtering.keys()
 
class HousingHistoryResource(JailResource):
    """
    API endpoint for HousingHistory model, the unique combination of housing
    location, inmate, and date used to represent the housing history.
    """
    housing_location = fields.ToOneField(HousingLocationResource, "housing_location", null=True, full=False)
    inmate = fields.ToOneField('countyapi.api.CountyInmateResource', "inmate", null=True, full=False)
    class Meta:
        queryset = HousingHistory.objects.all()
        allowed_methods = ['get']
        serializer = JailSerializer()
        limit = 100
        max_limit = 0
        cache = SimpleCache(timeout=720)
        filtering = {
            'inmate': ALL_WITH_RELATIONS,
            'housing_date': ALL, 
            'housing_location': ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

    def dehydrate(self, bundle):
        """Set up bidirectional relationships based on request."""
        #import ipdb; ipdb.set_trace();

        # Include inmate ID when called from location
        if bundle.request.path.startswith("/api/1.0/historylocation/"):
            bundle.data["inmate"] = bundle.obj.inmate.pk

        # Include location when called from inmate
        if bundle.request.path.startswith("/api/1.0/countyinmate/"):
            location = bundle.obj.housing_location
            resource = HousingLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data["housing_location"] = resource.full_dehydrate(location_bundle).data

        # Include primary keys on court dates
        if bundle.request.path.startswith("/api/1.0/housinghistory/") and not bundle.request.REQUEST.get('related') == '1':
            bundle.data["location_id"] = bundle.obj.housing_location.pk
            bundle.data["inmate_jail_id"] = bundle.obj.inmate.pk

        # Include full inmate in related query
        if bundle.request.path.startswith("/api/1.0/housinghistory/") and bundle.request.REQUEST.get('related') == '1':
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data["inmate"] = resource.full_dehydrate(inmate_bundle).data

            location = bundle.obj.housing_location
            resource = HousingLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data["housing_location"] = resource.full_dehydrate(location_bundle).data

        return bundle

class CountyInmateResource(JailResource):
    """
    API endpoint for CountyInmate model, which represents a person in jail.
    """
    court_dates = fields.ToManyField(CourtDateResource, "court_dates")
    housing_history = fields.ToManyField(HousingHistoryResource, "housing_history")

    class Meta:
        queryset = CountyInmate.objects.prefetch_related('housing_history').prefetch_related('court_dates').all()
        allowed_methods = ['get']
        limit = 100
        max_limit = 0
        cache = SimpleCache(timeout=720)
        serializer = JailSerializer()
        excludes = ['last_seen_date',]
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
            'court_dates': ALL_WITH_RELATIONS,
            'housing_history': ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

    def dehydrate(self, bundle):
        """Show court dates and housing history in inmate lists and detail views."""
        if bundle.request.path.startswith('/api/1.0/countyinmate/') and (bundle.request.path != '/api/1.0/countyinmate/' or bundle.request.REQUEST.get('related') == '1'):
            dates = bundle.obj.court_dates.all()
            resource = CourtDateResource()
            bundle.data['court_dates'] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data["court_dates"].append(resource.full_dehydrate(date_bundle).data)

            dates = bundle.obj.housing_history.all()
            resource = HousingHistoryResource()
            bundle.data['housing_history'] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data["housing_history"].append(resource.full_dehydrate(date_bundle).data)
        return bundle

