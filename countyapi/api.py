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


class CachedModelResource(ModelResource):
    def create_response(self, *args, **kwargs):
        resp = super(CachedModelResource, self).create_response(*args, **kwargs)
        resp['Cache-Control'] = "max-age=3600"
        return resp


class CourtLocationResource(CachedModelResource):
    class Meta:
        queryset = CourtLocation.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        limit = 2500
        serializer = JailSerializer()


class CourtDateResource(CachedModelResource):
    class Meta:
        queryset = CourtDate.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        serializer = JailSerializer()

        filtering = {
            'date': ALL,
            'location': ALL,
            'inmate': ALL,
        }
        ordering = filtering.keys()


class HousingLocationResource(CachedModelResource):
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
        ordering = filtering.keys()
 
class HousingHistoryResource(CachedModelResource):
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
        ordering = filtering.keys()


class CountyInmateResource(CachedModelResource):
    housing_history = fields.ToManyField(HousingHistoryResource, "housing_history", null=True, full=True)
    court_dates = fields.ToManyField(CourtDateResource, "court_dates", null=True, full=True)

    def alter_list_data_to_serialize(self, request, data):
        if request.GET.get('format') == 'csv' or not request.GET.get('related', False):
            for row in data['objects']:
                row.data['housing_history_count'] = len(row.data['housing_history'])
                del row.data['housing_history']
                row.data['court_date_count'] = len(row.data['court_dates'])
                del row.data['court_dates']
        return data

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
        ordering = filtering.keys()
