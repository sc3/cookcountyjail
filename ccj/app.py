#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, jsonify, request, Response
from flask.json import dumps
from flask.ext.sqlalchemy import SQLAlchemy
from os import getcwd
from datetime import datetime

from ccj.models.daily_population import DailyPopulation as DPC
from ccj.models.version_info import VersionInfo
from ccj import config


STARTUP_TIME = datetime.now()


app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

if app.config['IN_TESTING']:
    app.debug = True


@app.route('/daily_population', methods=['GET'])
def daily_population():
    """
    returns the set of summarized daily population changes.
    """
    return Response(DPC(app.config['DPC_DIR_PATH']).to_json(),  mimetype='application/json')


@app.route('/os_env_info')
def env_info():
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this is no longer a dev branch.
    """
    r_val = jsonify(
        cwd=getcwd(),
        remote_addr=request.environ.get('REMOTE_ADDR', 'not set'),
        headers=str(request.headers),
        environ=str(request.environ)
        )
    return r_val


@app.route('/starting_population', methods=['GET'])
def starting_population():
    """
    returns the set of starting daily population values used to calculate daily changes.
    """
    return Response(dumps(DPC(app.config['DPC_DIR_PATH']).starting_population()), headers={'Access-Control-Allow-Origin': '*'}, mimetype='application/json')


@app.route('/version')
def version_info():
    """
    returns the version info
    """
    args = request.args
    v_i = VersionInfo(STARTUP_TIME).fetch(all_version_info=('all' in args and args['all'] == '1'))
    return Response(dumps(v_i), mimetype='application/json')
