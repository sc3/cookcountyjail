#
# app.py is a Controller file and should do very little,
#        processing should be pushed down into model files.
#

from flask import Flask, jsonify, request, abort
from flask.json import dumps
from flask.ext.sqlalchemy import SQLAlchemy
from os import getcwd, path
from os.path import isfile, join
from datetime import datetime

from ccj.models.daily_population_changes \
    import DailyPopulationChanges as DPC
from ccj import config


app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

if app.config['IN_TESTING']:
    app.debug = True

CURRENT_FILE_PATH = 'build_info/current'
PREVIOUS_FILE_PATH = 'build_info/previous'
VERSION_NUMBER = "2.0-dev"


@app.route('/daily_population_changes', methods=['GET'])
def read_daily_population_changes():
    """
    returns the set of sumarized daily population changes.
    """
    return DPC(app.config['DPC_PATH']).to_json()


@app.route('/daily_population_changes', methods=['POST'])
def create_daily_population_change():
    if request.environ.get('REMOTE_ADDR', '127.0.0.1') != '127.0.0.1':
        abort(401)
    post_data = request.form
    DPC(app.config['DPC_PATH']).store(post_data)
    return jsonify(post_data), 201


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
        r_val = build_info(CURRENT_FILE_PATH)
    return dumps(r_val)


@app.route('/os_env_info')
def env_info():
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this is no longer a dev branch.
    """
    return jsonify(cwd=getcwd())


def build_info(fname):
    return {'Version': VERSION_NUMBER, 'Build': current_build_info(fname), 'Deployed': deployed_at(fname)}


def current_build_info(fname):
    return file_contents(fname, 'running-on-dev-box')


def deployed_at(fname):
    if isfile(fname):
        mtime = path.getmtime(fname)
        r_val = datetime.fromtimestamp(mtime)
    else:
        r_val = datetime.now()
    return str(r_val)


def file_contents(fname, default_rvalue):
    if isfile(fname):
        with open(fname, 'r') as f:
            return f.read().strip()
    return default_rvalue


def previous_build_info(dir_path, r_val):
    r_val.append(build_info(join(dir_path, CURRENT_FILE_PATH)))
    previous_fname = join(dir_path, PREVIOUS_FILE_PATH)
    if isfile(previous_fname):
        previous_build_info(join('..', file_contents(previous_fname, '')), r_val)
