"""
A person database model.
See:

https://docs.google.com/drawings/d/1WAXGB1l5QcX_2XV5_VjvVNNxOO9UvGIh5jXgakNnICo/

"""

from ccj.app import db

class Person(db.Model):
    """
    A person model used to identify people who
    come back to the jail and stores general
    information about that person.

    We don't track first or last names.

    """
    # a hash to uniquely identify the person
    # if he or she came back to the jail
    hash = db.Column(db.Unicode, primary_key=True)

    # gender can only be M(male) or F(female)
    gender = db.Column(db.Enum("M", "F"))

    # race would be harder to parse with an
    # enum so we are sticking to good old
    # strings
    race = db.Column(db.Unicode)

    # the date this person was added to the
    # database
    date_created = db.Column(db.Date)



