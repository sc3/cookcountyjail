"""
rest_api.py

Contains all the source code used to create
the actual API.

See CcjApi, simple_resource and ReadResource.

"""

from flask.ext import restful as full
from flask.ext import restless as less

class CcjApi():
    """
    An Api wrapper around flask-restless and flask-restful,
    because we are very lazy.

    restful will handle the very custom api routes like os env info,
    while restless will handle exposing the database models through a
    read only interface with sorting, filtering ect ect.

    Add resources with full_resource and less_resource.

    What's the difference?
    Full resources are function or class based routes that handle your
    custom logic.

    Less rources just need a database model and flask will provide all
    the logic for sorting, filtering ect ect.

    """
    @staticmethod
    def simple_resource(class_name, get_fun):
        """
        Returns a Resource subclass(to be added to the API),
        which responds to just Get requests with get_fun.

        """

        def _method(self):
            # this will be the new class' method
            # that is called on Get requests
            # a wrapper aroud the get function
            return get_fun()

        return type(class_name, (full.Resource,), {'get': _method})

    def __init__(self, app, db):
        self.app = app
        self.db = db
        self._full = full.Api(app)
        self._less = less.APIManager(app, flask_sqlalchemy_db=db)

    def full_resource(self, get_fun, route):
        """
        This magical method accepts a function and
        a route. After using this method, the
        app's given route will respond with the
        function. Only use this for routes that only
        respond to GET requests.

        Returns the flask.ext.restful.Resource object.

        """
        resource = CcjApi.simple_resource(get_fun.func_name, get_fun)

        self.full_class_resource(resource, route)

        return resource

    def full_class_resource(self, resource, route):
        """
        Adds a resource at the given route. Resource should
        be a class subclassing restful.Resource.

        """
        self._full.add_resource(resource, route)
        return self

    def less_resource(self, db_model):
        """
        Adds a read only route with all the
        data from the db_model.

        """
        self._less.create_api(db_model, url_prefix='', methods=['GET'])
        return self


