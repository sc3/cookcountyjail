from .app import app, db
from .models import *
from . import config

app.config.from_object(config)
