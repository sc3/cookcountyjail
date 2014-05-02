#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, jsonify, request, Response
from flask.json import dumps
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext import restful as rest
from os import getcwd
from datetime import datetime

from ccj.models.daily_population import DailyPopulation as DPC
from ccj.models.version_info import VersionInfo
from ccj import config

STARTUP_TIME = datetime.now()

class CcjApi(rest.Api):
    """
    An Api subclass of flask-restful's Api, because
    we will do a lot of custom stuff.
    """
    def create_resource(self, get_fun, route):
        """
        This magical method accepts a function and
        a route. After using this method, the
        app's given route will respond with the
        function. Only use this for routes that only
        respond to GET requests.

        Returns the flask.ext.restful.Resource object.

        """
        resource = simple_resource(get_fun.func_name, get_fun)
        self.add_resource(resource, route)
        return resource

def simple_resource(class_name, get_fun):
    """
    Returns a Resource subclass(to be added to the API),
    which responds to just Get requests with get_fun.

    """
    return type(class_name, (rest.Resource,), {'get': get_fun})

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)
api = CcjApi(app)

if app.config['IN_TESTING']:
    app.debug = True

def env_info(self):
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this
    is no longer a dev branch.

    """

    return jsonify(cwd=getcwd(),
                    remote_addr=request.environ.get('REMOTE_ADDR', 'not set'),
                    headers=str(request.headers),
                    environ=str(request.environ))

def daily_population(self):
    """
    returns the set of summarized daily population changes.

    """
    return DPC(app.config['DPC_DIR_PATH']).to_json()

def starting_population(self):
    """
    returns the set of starting daily population values used
    to calculate daily changes.

    """
    return DPC(app.config['DPC_DIR_PATH']).starting_population()

def version(self):
    """
    returns the version info

    """
    args = request.args
    return VersionInfo(STARTUP_TIME).fetch(all_version_info=('all' in args and args['all'] == '1'))

EnvInfo = api.create_resource(env_info, "/os_env_info")
DailyPopulation = api.create_resource(daily_population, "/daily_population")
StartingPopulation = api.create_resource(starting_population, "/starting_population")
Version = api.create_resource(version, "version")


