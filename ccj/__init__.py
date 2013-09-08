from app import app, db
from models import *
import config

app.config.from_object(config)
