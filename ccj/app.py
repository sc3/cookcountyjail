#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, request, render_template, current_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext import restful as rest

from json import loads, dumps
from os import getcwd
from datetime import datetime, date
from functools import wraps

from ccj.models.daily_population import DailyPopulation as DPC
from ccj.models.version_info import VersionInfo
from ccj import config

from rest_api import CcjApi, get_or_create

STARTUP_TIME = datetime.now()

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

from ccj.models.models import Person, ChargeDescription, Statute, Housing, CourtBuilding, CourtRoom

api = CcjApi(app, db)

if app.config['IN_TESTING']:
    app.debug = True


def jsonp(func):
    """
    Wraps JSONified output for JSONP requests.
    
    From http://flask.pocoo.org/snippets/79/
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = dumps(func(*args, **kwargs))
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about-api')
def about_api():
    return render_template('api.html')

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

@jsonp
def daily_population():
    """
    returns the set of summarized daily population changes.

    """
    return DPC(app.config['DPC_DIR_PATH']).query()

@jsonp
def starting_population():
    """
    returns the set of starting daily population values used
    to calculate daily changes.

    """
    return DPC(app.config['DPC_DIR_PATH']).starting_population()

@jsonp
def version():
    """
    returns the version info

    """
    args = request.args
    return VersionInfo(STARTUP_TIME).fetch(all_version_info=('all' in args and args['all'] == '1'))


api.full_resource(env_info, "/os_env_info")
api.full_resource(daily_population, "/daily_population")
api.full_resource(starting_population, "/starting_population")
api.full_resource(version, "/version")

api.less_resource(Person)
api.less_resource(ChargeDescription)
api.less_resource(Statute)
api.less_resource(Housing)
api.less_resource(CourtBuilding)
api.less_resource(CourtRoom)

