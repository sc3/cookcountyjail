#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext import restful as rest

from os import getcwd
from datetime import datetime

from ccj.models.daily_population import DailyPopulation as DPC
from ccj.models.version_info import VersionInfo
from ccj import config

STARTUP_TIME = datetime.now()

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

from ccj.models.models import Person, Charge, Housing, CourtBuilding, CourtRoom
from rest_api import CcjApi

api = CcjApi(app, db)

if app.config['IN_TESTING']:
    app.debug = True

def env_info():
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this
    is no longer a dev branch.

    """
    return {"cwd": getcwd(),
            "remote_addr": request.environ.get('REMOTE_ADDR', 'not set'),
            "headers": str(request.headers),
            "environ": str(request.environ)}

def daily_population():
    """
    returns the set of summarized daily population changes.

    """
    return DPC(app.config['DPC_DIR_PATH']).query()

def starting_population():
    """
    returns the set of starting daily population values used
    to calculate daily changes.

    """
    return DPC(app.config['DPC_DIR_PATH']).starting_population()

def version():
    """
    returns the version info

    """
    args = request.args
    return VersionInfo(STARTUP_TIME).fetch(all_version_info=('all' in args and args['all'] == '1'))

class Process(rest.Resource):
    def post(self):
        return {"status": "saved"}

api.full_resource(env_info, "/os_env_info")
api.full_resource(daily_population, "/daily_population")
api.full_resource(starting_population, "/starting_population")
api.full_resource(version, "/version")
api.full_class_resource(Process, "/process")

api.less_resource(Person)
api.less_resource(Charge)
api.less_resource(Housing)
api.less_resource(CourtBuilding)
api.less_resource(CourtRoom)


