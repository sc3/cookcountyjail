# Run your virtualenv's version of gunicorn, with 4 workers, 
# on port 8000 of your localhost, using a Python WSGI callable 
# located underneath ccj in app.py, and called app
gunicorn -w 4 -b 127.0.0.1:8000 ccj.app:app 


