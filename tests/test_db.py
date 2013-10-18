#!/usr/bin/env python

from ccj.app import app
from ccj.app import db
from fabric.api import local
import sys

# make sure PostgreSQL DB is being used
db_string = app.config['SQLALCHEMY_DATABASE_URI']
if db_string.find('postgresql') == -1:
    sys.exit("pgsql not being used; make sure CCJ_PRODUCTION is set")

# Declare a model
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_string = db.Column(db.String)
    def __init__(self, test):
        self.test_string = test
    def __repr__(self):
        return '<Test %r>' % self.test_string


# Add some new data to the DB
db.create_all()
one = Test('first')
two = Test('second')
db.session.add(one)
db.session.add(two)
db.session.commit()

################
#
# IF BOTH THE FOLLOWING QUERY STATEMENT AND THE LATER `DROP` 
# STATEMENT ARE IN THE SCRIPT, SUBPROCESS (and thus Fabric) HANGS.
# See PEP 3145 or http://bugs.python.org/issue13817 for possible 
# explanations.
#
#####################

#tests = Test.query.all()
#if not (tests and tests[0].test_string == 'first' and tests[1].test_string == 'second'):
#    sys.exit("pgsql not working: data not persisting")


# Check if 'test' table is in DB
result = local('psql cookcountyjail_v2_0_dev -c "\dt"', capture=True)
if result.find('test') == -1:
    sys.exit("pgsql not working: table not actually in DB")

 
# Drop 'test' table from DB
local('psql cookcountyjail_v2_0_dev -c "DROP TABLE test;"', capture=True)


# Everything worked.
sys.exit("pgsql working")
