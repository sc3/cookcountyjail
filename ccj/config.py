import os
_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % os.path.join(_basedir, 'ccjdb.db')
