from flask import Flask, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__, static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)
db = SQLAlchemy(app)

import os


@app.route('/version')
def version_info():
    """
    Temporary api return.
    """
    return jsonify(Version="2.0",
                   Build=777,
                   Deployed='2013-10-15')


@app.route('/os_env_info')
def env_info():
    """
    Displays information about the current OS environment.
    Used for development purposes, to be deleted when this is no longer a dev branch.
    """
    return jsonify(cwd=os.getcwd()
                   )
