from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from os import getcwd, path
from os.path import isfile, join
from datetime import datetime
import json


app = Flask(__name__)
db = SQLAlchemy(app)


CURRENT_FILE_PATH = 'build_info/current'
PREVIOUS_FILE_PATH = 'build_info/previous'
VERSION_NUMBER = "2.0-dev"


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
    return json.dumps(r_val)


@app.route('/os_env_info')
def env_info():
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this is no longer a dev branch.
    """
    return jsonify(cwd=getcwd()
                   )


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
