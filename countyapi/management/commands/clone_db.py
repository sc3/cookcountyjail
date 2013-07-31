from django.core.management.base import BaseCommand
from countyapi.models import CourtDate, CourtLocation, CountyInmate, HousingHistory, HousingLocation
from utils import http_get
from inmate_utils import parse_court_location
from django.core.exceptions import MultipleObjectsReturned
from optparse import make_option

import json
import collections

class Command(BaseCommand):

    def handle(self, *args, **options):

        """
             Copies all data from each API endpoint of the server's CookCountyJail
             database onto the caller's local machine. 
        """

        base_url = "http://cookcountyjail.recoveredfactory.net/api/1.0/"
        suffix = "?format=json&limit=0"

        # ordereddict mapping APIs with:
        # --> a Django model that can be used to create an object; and,
        # --> a set of identifying filters needed to initialize that object
        api_to_model_and_id = collections.OrderedDict([
            ('countyinmate', (CountyInmate, ['jail_id'])),
            ('courtlocation', (CourtLocation, ['location'])),
            ('housinglocation', (HousingLocation, ['housing_location'])),
            ('courtdate', (CourtDate, ['date', 'inmate', 'location'])),
            ('housinghistory', (HousingHistory, ['inmate', 'housing_location']))
        ])
        
        # dict mapping an identifying filter with:
        # --> a key to index into our json object with, whose
        #     value is the value that will be used to initialize 
        #     the object we'll create with our foreign model
        # --> an API to use to get a model and initializing filters;
        #     these will be used to create the foreign object 
        id_to_jsonkey_and_api = {
            'inmate' : ('inmate_jail_id', 'countyinmate'),
            'location' : ('location', 'courtlocation'),
            'housing_location' : ('location_id', 'housinglocation')
        }

        # iterate over our APIs
        for api in api_to_model_and_id.keys():

            # for each API, get the model we'll use to re-create all of its data            
            model = api_to_model_and_id[api][0]

            # for each API, get the identifying filters we'll need to initialize each object of this type
            identifiers = api_to_model_and_id[api][1]

            # query our server to get all the data of a particular API
            result = http_get("%s%s%s" % (base_url, api, suffix), number_attempts=1, quiet=False)
            if result:

                # parse the json we get back into a dictionary of keys and values
                json_results = json.loads(result.text)

                # all our data is stored inside the 'objects' attribute
                for json_obj in json_results['objects']:

                    # this a dict of filters we'll use to initialize our object, when we create it.
                    # if we have foreign keys to deal with, getting the value for each filter
                    # is a bit more complex.
                    filters = {}

                    # but if there's only one filter, the model doesn't have any foreign keys,
                    # so it's a simpler case.
                    if len(identifiers) == 1:

                        # here, we basically just mindlessly copy the value from the json object
                        # into our dict of filters
                        filters = {identifiers[0]: json_obj[identifiers[0]]}
                    else:

                        # iterate through the filters
                        for i in identifiers:

                            # if we have defined an attribute as requiring foreignkey
                            # lookup, we get to work. Continuing from the example above,
                            # this IS the case for the 'inmate' and 'location' identifiers
                            if i in id_to_jsonkey_and_api.keys():
                                json_key = id_to_jsonkey_and_api[i][0]
                                foreign_api = id_to_jsonkey_and_api[i][1]
                                foreign_model = api_to_model_and_id[foreign_api][0]
                                foreign_key = api_to_model_and_id[foreign_api][1][0]
                                try:
                                    foreigner, created = foreign_model.objects.get_or_create(**{foreign_key: json_obj[json_key]})
                                except MultipleObjectsReturned:
                                    foreigner = foreign_model.objects.filter(**{foreign_key: json_obj[json_key]})[0]
                                filters[i] = foreigner
                            else:

                                # but the 'date' attribute isn't defined in our map, 
                                # so it would get pulled from the json object like normal.
                                filters[i] = json_obj[i]

                    # here, we actually create our object.
                    try:
                        obj, created = model.objects.get_or_create(**filters)
                    except MultipleObjectsReturned: 
                        obj = model.objects.filter(**filters)[0]

                    # now that we've created our object, we take all the 
                    # remaining attributes from our json object, and
                    # reassign them to our new django object.
                    for k, v in json_obj.iteritems():

                        # if the value is None, it stays None; 
                        # if we already assigned the key in filters, don't reassign; 
                        # if key is not part of our model, don't bother assigning it (e.g. 'resource_uri', '_state')
                       if k not in filters.keys() and v is not None and k in [a for a in obj.__dict__ if not a.startswith('_')]:
                            setattr(obj, k, v)

                    # finally, we're done.
                    obj.save()
            
        