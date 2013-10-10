from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__, static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)
db = SQLAlchemy(app)


@app.route('/version')
def temp_api():
    """
    Temporary api return.
    """
    return 'Version 2.0, Build 123'
