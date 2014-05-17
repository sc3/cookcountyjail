#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext import restful as rest

from json import loads
from os import getcwd
from datetime import datetime, date

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
    """
    The Proccess route handles all database input.
    Scraper instances make POST requests to to this
    route and it takes care of saving the data.

    In the near future scrapers might be whitelisted.

    The process route expects all data to be in a 'data'
    key in the request's body. The data must be valid JSON.

    Example data:

    {

    }

    """
    def post(self):

        data = None

        today = date.today()

        try:
            data = loads(request.form['data'])

        except ValueError:
            return {"message": "Error parsing json data", "status": 500}, 500

        # the Person's attributes
        phash = data.get("hash")
        gender = data.get("gender")
        race = data.get("race")

        if phash:
            new_person, person = get_or_create(db.session, Person, hash=phash)
            person.gender = gender
            person.race = race

            if new_person:
                person.date_created = today

            db.session.add(person)

        charge_d = data.get('charge_description')

        if charge_d:
            new_charge_description, charge_description = get_or_create(db.session,
                                                                    ChargeDescription,
                                                                    description=charge_d)

            if new_charge_description:
                charge_description.date_created = today

            db.session.add(charge_description)

        citation = data.get('citation')

        if citation:
            new_statue, statute = get_or_create(db.session, Statute, citation=citation)

            if new_statue:
                statute.date_created = today

            db.session.add(statute)

        db.session.commit()
        return {"message": "saved", "status": 200}


api.full_resource(env_info, "/os_env_info")
api.full_resource(daily_population, "/daily_population")
api.full_resource(starting_population, "/starting_population")
api.full_resource(version, "/version")
api.full_class_resource(Process, "/process")

api.less_resource(Person)
api.less_resource(ChargeDescription)
api.less_resource(Statute)
api.less_resource(Housing)
api.less_resource(CourtBuilding)
api.less_resource(CourtRoom)

