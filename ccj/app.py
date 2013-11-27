#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, jsonify, request, Response
from flask.json import dumps
from flask.ext.sqlalchemy import SQLAlchemy
from os import getcwd, path
from os.path import isfile, join
from datetime import datetime

from ccj.models.daily_population import DailyPopulation as DPC
from ccj import config

STARTUP_TIME = datetime.now()

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

if app.config['IN_TESTING']:
    app.debug = True

BUILD_INFO_PATH = 'build_info'
CURRENT_FILE_PATH = join(BUILD_INFO_PATH,'current')
PREVIOUS_FILE_PATH = join(BUILD_INFO_PATH,'previous')
VERSION_NUMBER = "2.0-dev"


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
    return Response(dumps(DPC(app.config['DPC_DIR_PATH']).starting_population()),  mimetype='application/json')


@app.route('/version')
def version_info():
    """
    returns the version info
    """
    args = request.args
    if 'all' in args and args['all'] == '1':
        r_val = []
        previous_build_info('.', r_val)
    else:
        r_val = build_info('.')
    return Response(dumps(r_val),  mimetype='application/json')


def build_info(dir_name):
    file_name = join(dir_name, CURRENT_FILE_PATH)
    return {'Version': VERSION_NUMBER, 'Build': current_build_info(file_name), 'Deployed': deployed_at(file_name),
            'Person': person_id(dir_name)}


def current_build_info(file_name):
    return file_contents(file_name, 'running-on-dev-box')


def deployed_at(file_name):
    if isfile(file_name):
        mtime = path.getmtime(file_name)
        r_val = datetime.fromtimestamp(mtime)
    else:
        r_val = STARTUP_TIME
    return str(r_val)


def file_contents(file_name, default_rvalue):
    if isfile(file_name):
        with open(file_name, 'r') as f:
            return f.read().strip()
    return default_rvalue


def person_id(dir_name):
    return file_contents(join(dir_name, 'email'), 'Brian or Norbert')


def previous_build_info(dir_path, r_val):
    r_val.append(build_info(join(dir_path, BUILD_INFO_PATH)))
    previous_file_name = join(dir_path, PREVIOUS_FILE_PATH)
    if isfile(previous_file_name):
        previous_build_info(join('..', file_contents(previous_file_name, '')), r_val)
