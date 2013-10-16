from flask import Flask, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix
from os.path import isfile
from datetime.datetime import now


app = Flask(__name__, static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)
db = SQLAlchemy(app)

import os


@app.route('/version')
def version_info():
    """
    returns the version info
    """
    return jsonify(Version="2.0",
                   Build=current_build_info(),
                   Deployed=deployed_at())


@app.route('/os_env_info')
def env_info():
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this is no longer a dev branch.
    """
    return jsonify(cwd=os.getcwd()
                   )


def current_build_info():
    return file_contents('build_info/current', 'running-on-dev-box')


def deployed_at():
    return file_contents('build_info/deployed_at', str(now()))


def file_contents(fname, default_rvalue):
    if isfile(fname):
        with open(fname, 'r') as f:
            return f.read().strip()
    return default_rvalue
