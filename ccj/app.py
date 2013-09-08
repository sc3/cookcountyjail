from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__, static_url_path='')
db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/')
def temp():
    return "Unavailable during the shift to version 2.0 of the API."

@app.route('/api/2.0/version')
def temp_api():
    """
    Temporary api return.
    """
    return version_and_build()

def version_and_build():
    app_version_and_build = 'Version 2.0, Build 123'
    print(app_version_and_build)
    return (app_version_and_build)

if __name__ == '__main__':
    version_and_build()
