from django.core.management.base import BaseCommand
from django.core.exceptions import MultipleObjectsReturned
from countyapi.models import CourtDate, CourtLocation, CountyInmate, HousingHistory, HousingLocation
from utils import http_get
from inmate_utils import parse_court_location
from optparse import make_option

import json
import collections

class Command(BaseCommand):

    help = "Copies all data from the CookCountyJail database."
    option_list = BaseCommand.option_list + (
        make_option('-a', '--api', type='string', action='store', dest='api', default=False,
                    help='APIs to clone by name, separated by comma'), 
        make_option('-l', '--limit', type='string', action='store', dest='limit', default=False,
                    help='Clone only the first n records')
        )

    def handle(self, *args, **options):

        """
             Copies all data from each API endpoint of the server's CookCountyJail
             database onto the caller's local machine. 

             NOTE: For the time being, cloning the whole database is impossible;
             the 'courtdate' and 'housinghistory' API endpoints aren't functional 
             as it stands: each will stall for about 4 minutes before giving up with 
             a 504 error if you try to query them with 'limit=0', which is the default.
            Thus it's recommended to either supply an '--api' flag excluding those two 
            APIs (e.g. 'countyinmate, courtlocation, housinglocation'), or to supply a 
             '--limit' flag with some large number (e.g. '2000'). 

             For best results, you might want to do both, in two separate runs:
             "./manage.py clone_db -a 'countyinmate, courtlocation, housinglocation' "
             And then:
             "./manage.py clone_db -a 'courtdate, housinghistory' -l 2000 "
             You could just see how high you can increase that limit before it fails.
        """

        base_url = "http://cookcountyjail.recoveredfactory.net/api/1.0/"
        suffix = "?format=json&limit=0"
        exclude = []  
        
        # ordereddict mapping APIs with:
        # --> a Django model that can be used to create an object; and,
        # --> a set of identifying filters needed to initialize that object
        api_map = collections.OrderedDict([
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
        foreign_map = {
            'inmate' : ('inmate_jail_id', 'countyinmate'),
            'location' : ('location', 'courtlocation'),
            'housing_location' : ('location_id', 'housinglocation')
        }

         # set a limit if necessary
        if options['limit']:
            suffix = '?format=json&limit=%s' % options['limit']

        # build a list of excluded APIs if necessary
        if options['api']:
            for k in api_map.keys():
                if k not in options['api'].split(', '):
                    exclude.append(k)      

        # iterate over our APIs
        for api in api_map.keys():

            # if '--api' flag was given, but this API wasn't included, ignore it.
            if api in exclude:
                continue

            # for each API, get the model we'll use to re-create all of its data            
            model = api_map[api][0]

            # for each API, get the identifying filters we'll need to initialize each object of this type
            identifiers = api_map[api][1]

            # query our server to get all the data of a particular API
            result = http_get("%s%s%s" % (base_url, api, suffix), number_attempts=1, quiet=False)
            if result:

                # parse the json we get back into a dictionary of keys and values
                json_results = json.loads(result.text)

                # all our data is stored inside the 'objects' attribute
                for json_obj in json_results['objects']:

                    # this a dict of filters we'll use to initialize our object, when we create it.
                    # if we have foreign keys to deal with, we'll have to first get_or_create
                    # an object based on those foreign keys.
                    filters = {}

                    # but if there's only one filter, the model doesn't have any foreign keys,
                    # so it's a simpler case.
                    if len(identifiers) == 1:

                        # here, we basically just mindlessly copy the value from the json object
                        # into our dict of filters
                        filters = {identifiers[0]: json_obj[identifiers[0]]}
                    else:

                        # otherwise, iterate through the filters
                        for i in identifiers:

                            # if we have defined an attribute as requiring foreignkey
                            # lookup, we get to work. 
                            if i in foreign_map.keys():
                                json_key = foreign_map[i][0]
                                foreign_api = foreign_map[i][1]
                                foreign_model = api_map[foreign_api][0]
                                foreign_key = api_map[foreign_api][1][0]

                                # do a foreign key lookup; this means doing get_or_create to instantiate
                                # the object before including it as an attribute of our object;
                                # note that we take the first match if there are multiple
                                try:
                                    foreigner, created = foreign_model.objects.get_or_create(
                                            **{foreign_key: json_obj[json_key]})
                                except MultipleObjectsReturned:
                                    foreigner = foreign_model.objects.filter(
                                            **{foreign_key: json_obj[json_key]})[0]

                                # include the result with our list of filters
                                filters[i] = foreigner

                            else:

                                # if an attribute isn't defined in our map above as a foreign key, 
                                # it would get pulled from the json object like normal. 
                                filters[i] = json_obj[i]

                    # here, we actually create our object, again taking the first
                    # available, if there are multiple
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
                       if k not in filters.keys() and v is not None and \
                                k in [a for a in obj.__dict__ if not a.startswith('_')]:
                            setattr(obj, k, v)

                    # finally, we're done.
                    obj.save()
            
        