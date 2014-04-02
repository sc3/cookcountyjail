from copy import copy
import csv
import os

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from tastypie.exceptions import ApiFieldError, Unauthorized
from tastypie.bundle import Bundle
from tastypie.fields import ToManyField, ToOneField
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.serializers import Serializer
from tastypie.authorization import Authorization

from countyapi.models import CountyInmate, CourtLocation, CourtDate, HousingLocation, HousingHistory, \
    DailyPopulationCounts, DailyBookingsCounts, ChargesHistory
from countyapi.utils import convert_to_int


COUNTY_API_INMATE_RESOURCE = 'countyapi.api.CountyInmateResource'

HOUSING_DATE_DISCOVERED = 'housing_date_discovered'

ABOUT_THIS_DATA = 'about_this_data'

LOCATION_ID = 'location_id'

DATE = 'date'

META = 'meta'

TEXT_CSV = 'text/csv'

DELETE = 'delete'

PUT = 'put'

POST = 'post'

BOOKING_DATE = 'booking_date'

CHARGES_HISTORY = 'charges_history'

HOUSING_HISTORY = 'housing_history'

COURT_DATES = 'court_dates'

GET = 'get'

INMATE_JAIL_ID = 'inmate_jail_id'

HOUSING_LOCATION = 'housing_location'

LOCATION = 'location'

OBJECTS = 'objects'

STD_HTTP_COMMANDS = [GET, POST, PUT, DELETE]

RELATED = 'related'

INMATE = 'inmate'

NEGATIVE_VALUES = {'0', 'false'}

API_PATH_FORMAT = '/api/1.0/%s/'


def use_caching():
    """
    For now this always returns true until we can get better caching mechanism to work
    See earlier version to get original implementation of function
    """
    return True


def cache_ttl():
    default_ttl = 60 * 12  # Time to Live in Cache: 12 minutes
    the_cache_ttl = os.environ.get('CACHE_TTL')
    return convert_to_int(the_cache_ttl, default_ttl) if the_cache_ttl else default_ttl


if use_caching():
    from tastypie.cache import SimpleCache


DISCLAIMER = """
Cook County Jail Inmate data, scraped from
http://www2.cookcountysheriff.org/search2/ nightly.

Learn more about this API at
https://github.com/sc3/cookcountyjail/wiki/API-guide

Learn more about this project at
https://github.com/sc3/cookcountyjail/

The data on jail inmates is not verified. Do not take the data as
definitive, but rather as suggestive. This data can be used to develop
interesting questions, but it cannot be cited as factual.

Developed by the Supreme Chi-Town Coding Crew
(https://github.com/sc3/sc3)
"""

COURT_DATE_URL = API_PATH_FORMAT % 'courtdate'
COURT_LOCATION_URL = API_PATH_FORMAT % 'courtlocation'
COUNTY_INMATE_URL = API_PATH_FORMAT % 'countyinmate'
HOUSING_HISTORY_URL = API_PATH_FORMAT % 'housinghistory'
HISTORY_LOCATION_URL = API_PATH_FORMAT % 'historylocation'
CHARGES_HISTORY_URL = API_PATH_FORMAT % 'chargeshistory'


class JailToOneField(ToOneField):
    def dehydrate(self, bundle, for_list=False):
        foreign_obj = None

        if isinstance(self.attribute, basestring):
            attrs = self.attribute.split('__')
            foreign_obj = bundle.obj

            for attr in attrs:
                previous_obj = foreign_obj
                try:
                    foreign_obj = getattr(foreign_obj, attr, None)
                except ObjectDoesNotExist:
                    foreign_obj = None
        elif callable(self.attribute):
            foreign_obj = self.attribute(bundle)

        if not foreign_obj:
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value."
                                    % (previous_obj, attr))

            return None

        if has_related_request(bundle):
            self.fk_resource = self.get_related_resource(foreign_obj)
            fk_bundle = Bundle(obj=foreign_obj, request=bundle.request)
            return self.dehydrate_related(fk_bundle, self.fk_resource)
        else:
            return super(JailToOneField, self).dehydrate(bundle)


class JailToManyField(ToManyField):
    def dehydrate(self, bundle, for_list=False):
        if not bundle.obj or not bundle.obj.pk:
            if not self.null:
                raise ApiFieldError(
                    "The model '%r' does not have a primary key and can not be used in a ToMany context."
                    % bundle.obj)

            return []

        the_m2ms = None
        previous_obj = bundle.obj
        attr = self.attribute

        if isinstance(self.attribute, basestring):
            attrs = self.attribute.split('__')
            the_m2ms = bundle.obj

            for attr in attrs:
                previous_obj = the_m2ms
                try:
                    the_m2ms = getattr(the_m2ms, attr, None)
                except ObjectDoesNotExist:
                    the_m2ms = None

                if not the_m2ms:
                    break

        elif callable(self.attribute):
            the_m2ms = self.attribute(bundle)

        if not the_m2ms:
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value."
                                    % (previous_obj, attr))

            return []

        self.m2m_resources = []
        m2m_dehydrated = []

        # TODO: Also model-specific and leaky. Relies on there being a
        #       ``Manager`` there.
        if has_related_request(bundle):
            for m2m in the_m2ms.all():
                m2m_resource = self.get_related_resource(m2m)
                m2m_bundle = Bundle(obj=m2m, request=bundle.request)
                self.m2m_resources.append(m2m_resource)
                m2m_dehydrated.append(self.dehydrate_related(m2m_bundle, m2m_resource))


class JailSerializer(Serializer):
    """
    Serialize to json, jsonp, xml, and csv.
    """

    formats = ['json', 'jsonp', 'xml', 'csv']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'csv': TEXT_CSV,
    }

    def to_csv(self, data, options=None):
        """
        Write to a simple CSV format.
        """
        options = options or {}
        data = self.to_simple(data, options)
        response = HttpResponse(mimetype=TEXT_CSV)
        response['Content-Disposition'] = 'attachment; filename="cookcountyjail.csv"'

        writer = csv.writer(response)
        writer.writerow(data[OBJECTS][0].keys())

        for item in data[OBJECTS]:
            writer.writerow(item.values())

        return response


class JailAuthorization(Authorization):

    @staticmethod
    def ip_check(_, bundle):
        if bundle.request.META['REMOTE_ADDR'] in settings.ALLOWED_POST_IPS:
            return True
        raise Unauthorized("You are not allowed to access that resource.")

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        if self.ip_check(object_list, bundle):
            return object_list
        return []

    def create_detail(self, object_list, bundle):
        return self.ip_check(object_list, bundle)

    def update_list(self, object_list, bundle):
        if self.ip_check(object_list, bundle):
            return object_list
        return []

    def update_detail(self, object_list, bundle):
        return self.ip_check(object_list, bundle)

    def delete_list(self, object_list, bundle):
        if self.ip_check(object_list, bundle):
            return object_list
        return []

    def delete_detail(self, object_list, bundle):
        return self.ip_check(object_list, bundle)


class JailResource(ModelResource):
    """
    ModelResource overrides for our project. Add caching and disclaimer.
    """
    def __init__(self, api_name=None):
        """
        Patched init that doesn't use deepcopy,
        see https://github.com/toastdriven/django-tastypie/issues/720
        """
        self.fields = {k: copy(v) for k, v in self.base_fields.iteritems()}

        if api_name:
            self._meta.api_name = api_name

    def alter_detail_data_to_serialize(self, request, data):
        """
        Add message to data.
        """
        data.data[ABOUT_THIS_DATA] = DISCLAIMER
        return data

    def alter_list_data_to_serialize(self, request, data):
        """
        Add message to meta.
        """
        data[META][ABOUT_THIS_DATA] = DISCLAIMER
        return data


class CourtLocationResource(JailResource):
    """
    API endpoint for CourtLocation model, which represents court room.
    """

    class Meta:
        queryset = CourtLocation.objects.all()
        limit = 100
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        serializer = JailSerializer()
        filtering = {
            LOCATION: ALL,
        }

    def dehydrate(self, bundle, for_list=False):
        """
        Show court dates in location lists and detail views.
        """
        if request_path_starts_with(bundle, COURT_LOCATION_URL) and \
                (bundle.request.path != COURT_LOCATION_URL or
                 has_related_request(bundle)):
            dates = bundle.obj.court_dates.all()
            resource = CourtDateResource()
            bundle.data[COURT_DATES] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data[COURT_DATES].append(resource.full_dehydrate(date_bundle, for_list=for_list).data)
        return bundle


class CourtDateResource(JailResource):
    """
    API endpoint for CourtDate model, the unique combination of courtroom,
    inmate, and date used to represent the court history.
    """
    location = JailToOneField(CourtLocationResource, LOCATION, null=True, full=False)
    inmate = JailToOneField(COUNTY_API_INMATE_RESOURCE, INMATE, null=True, full=False)

    class Meta:
        queryset = CourtDate.objects.select_related(LOCATION).select_related(INMATE).all()
        allowed_methods = [GET]
        limit = 100
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        serializer = JailSerializer()
        filtering = {
            DATE: ALL,
            LOCATION: ALL_WITH_RELATIONS,
            INMATE: ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

    def dehydrate(self, bundle, for_list=False):
        """
        Set up bidirectional relationships based on request.
        """

        # Include inmate ID when called from location
        if request_path_starts_with(bundle, COURT_LOCATION_URL):
            bundle.data[INMATE] = bundle.obj.inmate.pk

        # Include location when called from inmate
        if request_path_starts_with(bundle, COUNTY_INMATE_URL):
            location = bundle.obj.location
            resource = CourtLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data[LOCATION] = resource.full_dehydrate(location_bundle, for_list=for_list).data

        # Include primary keys on court dates
        if request_path_starts_with(bundle, COURT_DATE_URL) and not has_related_request(bundle):
            bundle.data[LOCATION_ID] = bundle.obj.location.pk
            bundle.data[LOCATION] = bundle.obj.location.location
            bundle.data[INMATE_JAIL_ID] = bundle.obj.inmate.pk

        # Include full inmate in related query
        if request_path_starts_with(bundle, COURT_DATE_URL) and has_related_request(bundle):
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data[INMATE] = resource.full_dehydrate(inmate_bundle, for_list=for_list).data

            location = bundle.obj.location
            resource = CourtLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data[LOCATION] = resource.full_dehydrate(location_bundle, for_list=for_list).data

        return bundle


class HousingLocationResource(JailResource):
    """
    API endpoint for HousingLocation model, a place or status in the jail.
    """

    class Meta:
        queryset = HousingLocation.objects.all()
        allowed_methods = [GET]
        limit = 100
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        serializer = JailSerializer()
        filtering = {
            HOUSING_LOCATION: ALL,
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
    housing_location = JailToOneField(HousingLocationResource, HOUSING_LOCATION, null=True, full=False)
    inmate = JailToOneField(COUNTY_API_INMATE_RESOURCE, INMATE, null=True, full=False)

    class Meta:
        queryset = HousingHistory.objects.select_related(LOCATION).select_related(INMATE).all()
        allowed_methods = [GET]
        serializer = JailSerializer()
        limit = 100
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        filtering = {
            INMATE: ALL_WITH_RELATIONS,
            HOUSING_DATE_DISCOVERED: ALL,
            HOUSING_LOCATION: ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

    def dehydrate(self, bundle, for_list=False):
        """
        Set up bidirectional relationships based on request.
        """

        # Include inmate ID when called from location
        if request_path_starts_with(bundle, HISTORY_LOCATION_URL):
            bundle.data[INMATE] = bundle.obj.inmate.pk

        # Include location when called from inmate
        if request_path_starts_with(bundle, COUNTY_INMATE_URL):
            location = bundle.obj.housing_location
            resource = HousingLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data[HOUSING_LOCATION] = resource.full_dehydrate(location_bundle, for_list=for_list).data

        # Include primary keys on court dates
        if request_path_starts_with(bundle, HOUSING_HISTORY_URL) and not \
                has_related_request(bundle):
            bundle.data[LOCATION_ID] = bundle.obj.housing_location.pk
            bundle.data[INMATE_JAIL_ID] = bundle.obj.inmate.pk

        # Include full inmate in related query
        if request_path_starts_with(bundle, HOUSING_HISTORY_URL) and \
                has_related_request(bundle):
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data[INMATE] = resource.full_dehydrate(inmate_bundle, for_list=for_list).data

            location = bundle.obj.housing_location
            resource = HousingLocationResource()
            location_bundle = resource.build_bundle(obj=location, request=bundle.request)
            bundle.data[HOUSING_LOCATION] = resource.full_dehydrate(location_bundle, for_list=for_list).data

        return bundle


class ChargesHistoryResource(JailResource):
    """
    API endpoint for ChargesHistory model.
    """
    inmate = JailToOneField(COUNTY_API_INMATE_RESOURCE, INMATE, null=True, full=False)

    class Meta:
        queryset = ChargesHistory.objects.select_related(INMATE).all()
        allowed_methods = [GET]
        serializer = JailSerializer()
        limit = 100
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        filtering = {
            INMATE: ALL_WITH_RELATIONS,
            'charges': ALL,
            'charges_citation': ALL,
            'date_seen': ALL,
            HOUSING_LOCATION: ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

    def dehydrate(self, bundle, for_list=False):
        """
        Set up bidirectional relationships based on request.
        """

        # Include primary keys on court dates
        related_request = has_related_request(bundle)
        if request_path_starts_with(bundle, CHARGES_HISTORY_URL) and not related_request:
            bundle.data[INMATE_JAIL_ID] = bundle.obj.inmate.pk

        # Include full inmate in related query
        if request_path_starts_with(bundle, HOUSING_HISTORY_URL) and related_request:
            inmate = bundle.obj.inmate
            resource = CountyInmateResource()
            inmate_bundle = resource.build_bundle(obj=inmate, request=bundle.request)
            bundle.data[INMATE] = resource.full_dehydrate(inmate_bundle, for_list=for_list).data

        return bundle


class CountyInmateResource(JailResource):
    """
    API endpoint for CountyInmate model, which represents a person in jail.
    """
    court_dates = JailToManyField(CourtDateResource, COURT_DATES)
    housing_history = JailToManyField(HousingHistoryResource, HOUSING_HISTORY)
    charges_history = JailToManyField(ChargesHistoryResource, CHARGES_HISTORY)

    class Meta:
        queryset = CountyInmate.objects.select_related(HOUSING_HISTORY)\
                                       .select_related(CHARGES_HISTORY)\
                                       .select_related(COURT_DATES)\
                                       .all()
        allowed_methods = [GET]
        limit = 100
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        serializer = JailSerializer()
        list_allowed_methods = STD_HTTP_COMMANDS
        detail_allowed_methods = STD_HTTP_COMMANDS
        authorization = JailAuthorization()
        excludes = ['last_seen_date']
        filtering = {
            'jail_id': ALL,
            BOOKING_DATE: ALL,
            'discharge_date_earliest': ALL,
            'gender': ALL,
            'age_at_booking': ALL,
            'bail_amount': ALL,
            HOUSING_LOCATION: ALL,
            'charges_citation': ALL,
            'race': ALL,
            COURT_DATES: ALL_WITH_RELATIONS,
            HOUSING_HISTORY: ALL_WITH_RELATIONS,
            CHARGES_HISTORY: ALL_WITH_RELATIONS,
            'person_id': ALL,
            'in_jail': ALL
        }
        ordering = filtering.keys()

    def dehydrate(self, bundle, for_list=False):
        """
        Show court dates and housing history in inmate lists and detail views.
        """
        if request_path_starts_with(bundle, COUNTY_INMATE_URL) and \
                (bundle.request.path != COUNTY_INMATE_URL or
                 has_related_request(bundle)):
            dates = bundle.obj.court_dates.all()
            resource = CourtDateResource()
            bundle.data[COURT_DATES] = []
            for court_date in dates:
                date_bundle = resource.build_bundle(obj=court_date, request=bundle.request)
                bundle.data[COURT_DATES].append(resource.full_dehydrate(date_bundle, for_list=for_list).data)

            housings = bundle.obj.housing_history.all()
            resource = HousingHistoryResource()
            bundle.data[HOUSING_HISTORY] = []
            for housing in housings:
                date_bundle = resource.build_bundle(obj=housing, request=bundle.request)
                bundle.data[HOUSING_HISTORY].append(resource.full_dehydrate(date_bundle, for_list=for_list).data)

            charges = bundle.obj.charges_history.all()
            resource = ChargesHistoryResource()
            bundle.data[CHARGES_HISTORY] = []
            for charge in charges:
                date_bundle = resource.build_bundle(obj=charge, request=bundle.request)
                bundle.data[CHARGES_HISTORY].append(resource.full_dehydrate(date_bundle, for_list=for_list).data)

        return bundle


class DailyPopulationCountsResource(JailResource):
    """
    API endpoint for DailyPopulationCounts
    """

    class Meta:
        queryset = DailyPopulationCounts.objects.all()
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        serializer = JailSerializer()
        filtering = {
            BOOKING_DATE: ALL
        }
        ordering = filtering.keys()


class DailyBookingsCountsResource(JailResource):
    """
    API endpoint for DailyBookingsCounts
    """

    class Meta:
        queryset = DailyBookingsCounts.objects.all()
        max_limit = 0
        if use_caching():
            cache = SimpleCache(timeout=cache_ttl())
        serializer = JailSerializer()
        filtering = {
            BOOKING_DATE: ALL
        }
        ordering = filtering.keys()


def has_related_request(bundle):
    return bundle.request.REQUEST.get(RELATED) == '1'


def request_path_starts_with(bundle, url):
    return bundle.request.path.startswith(url)
