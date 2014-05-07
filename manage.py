#!/usr/bin/env python
import argparse
import sys

from ccj import app, db
from scripts import setup_db

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

manager = Manager(app)
migrate = Migrate(app, db, directory='./ccj/models/migrations')

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()

