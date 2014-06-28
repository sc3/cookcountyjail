"""

models.py

Database models

See:
https://docs.google.com/drawings/d/1WAXGB1l5QcX_2XV5_VjvVNNxOO9UvGIh5jXgakNnICo/

"""

from ccj.app import db

"""
Base Models

"""

class Person(db.Model):
    """
    A person model used to identify people who
    are in the jail and stores general
    information.

    We don't track first or last names.

    """
    id = db.Column(db.Integer, primary_key=True)

    # a hash to uniquely identify the person
    # if he or she came back to the jail
    hash = db.Column(db.Unicode(64), unique=True, nullable=False)

    # gender can only be M(male) or F(female)
    gender = db.Column(db.Enum("M", "F", name="pgender"))

    # race would be harder to parse with an
    # enum so we are sticking to good old
    # strings
    race = db.Column(db.Unicode(4), nullable=False)

    # the date this person was added to the
    # database
    date_created = db.Column(db.Date, nullable=False)

class ChargeDescription(db.Model):
    """
    Every inmate gets a charge when they are
    booked. Often this changes overtime for
    some reason.

    """

    id = db.Column(db.Integer, primary_key=True)

    # the charge will have a description
    description = db.Column(db.Unicode, nullable=False, unique=True)

    date_created = db.Column(db.Date, nullable=False)

class Statute(db.Model):
    """
    A statute.

    """

    id = db.Column(db.Integer, primary_key=True)

    citation = db.Column(db.Unicode, nullable=False, unique=True)

    date_created = db.Column(db.Date, nullable=False)

class Housing(db.Model):
    """
    This model represents a place where
    an inmate is housed during his stay
    at the jail.

    """
    id = db.Column(db.Integer, primary_key=True)

    # the entire housing location without
    # any alterations
    location = db.Column(db.Unicode, nullable=False)

    # the inmates are housed in different
    # divisions
    division = db.Column(db.Unicode)

    # a way to specify where in a division the
    # inmate is located
    sub_division = db.Column(db.Unicode)

    # and an even further specific location
    # in the division
    sub_division_location = db.Column(db.Unicode)

    date_created = db.Column(db.Date, nullable=False)

    # some location represent inmates who
    # aren't really housed in the jail
    # for example when being under Day Release
    in_jail = db.Column(db.Boolean)

    # some inmates are in special programs
    # that can be deducted based on their
    # housing location
    in_program = db.Column(db.Unicode)

class CourtBuilding(db.Model):
    """
    A court building where an inmate goes to trial.

    """

    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.Unicode, nullable=False)

    name = db.Column(db.Unicode)

    branch = db.Column(db.Unicode)

    address = db.Column(db.Unicode)

    city = db.Column(db.Unicode)

    state = db.Column(db.Unicode)

    zip = db.Column(db.Unicode)

    date_created = db.Column(db.Date, nullable=False)

class CourtRoom(db.Model):
    """
    The court room in a court building
    where an inmate is trialed.

    """
    id = db.Column(db.Integer, primary_key=True)

    # the court room's number
    number = db.Column(db.Integer, nullable=False)

    court_building_id = db.Column(db.Integer, db.ForeignKey('court_building.id'),
                                  nullable=False)

    court_building = db.relationship('CourtBuilding',
        backref=db.backref('court_rooms', lazy='dynamic'))


    date_created = db.Column(db.Date, nullable=False)

"""
Temporal Models

"""

class ChargeHistory(db.Model):
    """
    During a stay, some people's charges
    change. With this model we would be able to
    see a stay's charges.

    """

    id = db.Column(db.Integer, primary_key=True)

    # a charge history will have a stay related
    # to it
    stay_id = db.Column(db.ForeignKey('stay.id'), nullable=False)
    stay = db.relationship('Stay',
        backref=db.backref('charges', lazy='dynamic'))

    # and a statute
    statute_id = db.Column(db.ForeignKey('statute.id'), nullable=False)
    statute = db.relationship('Statute',
        backref=db.backref('charges', lazy='dynamic'))

    # with a description
    charge_description_id = db.Column(db.ForeignKey('charge_description.id'),
                                      nullable=False)
    charge_description = db.relationship('ChargeDescription',
        backref=db.backref('charges', lazy='dynamic'))

    date_created = db.Column(db.Date, nullable=False)

class HousingHistory(db.Model):
    """
    During a stay, a person can be moved through
    out the jail. This model lets us see how
    people are moved from housing location to
    housing location.

    """

    id = db.Column(db.Integer, primary_key=True)

    # the refrence to the stay in which
    # a person is being housed
    stay_id = db.Column(db.ForeignKey('stay.id'), nullable=False)
    stay = db.relationship('Stay',
        backref=db.backref('housings', lazy='dynamic'))

    # the housing location
    housing_id = db.Column(db.ForeignKey('housing.id'), nullable=False)
    housing = db.relationship('Housing',
        backref=db.backref('housings', lazy='dynamic'))

    date_created = db.Column(db.Date, nullable=False)

class CourtHistory(db.Model):
    """
    During a stay a person has to go to court.
    Often more than once or twice.

    """
    id = db.Column(db.Integer, primary_key=True)

    court_date = db.Column(db.Date, nullable=False)

    # the reference to the stay in which
    # a person is being housed
    stay_id = db.Column(db.ForeignKey('stay.id'), nullable=False)
    stay = db.relationship('Stay',
        backref=db.backref('court_dates', lazy='dynamic'))

    court_room_id = db.Column(db.ForeignKey('court_room.id'), nullable=False)
    court_room = db.relationship('CourtRoom',
        backref=db.backref('court_dates', lazy='dynamic'))

    date_created = db.Column(db.Date, nullable=False)

class Stay(db.Model):
    """
    A person stays in the Cook County Jail and leaves.
    This model represents one of those stays. They
    might come back or not. If the hash is the same
    we will see people who come back and have multiple
    stays.

    """
    id = db.Column(db.Integer, primary_key=True)

    # the id assigned by the jail to the inmate
    jail_id_num = db.Column(db.Unicode(15), unique=True, nullable=False)

    # the reported date in which the inmate was booked
    booking_date = db.Column(db.Date, nullable=False)

    # the status can be set or not
    bail_status = db.Column(db.Enum('Bond in Process', 'No Bond', 'Set', name='bail_states'),
                            nullable=False)

    # how much is needed to bail this inmate
    bail_amount = db.Column(db.Integer, nullable=False)

    # how old was the inmate when he was
    # booked
    age_at_booking = db.Column(db.Integer, nullable=False)

    # we also see their weights and heights
    weight = db.Column(db.Integer, nullable=False)

    height = db.Column(db.Integer, nullable=False)

    # the date when the inmate isn't reported
    # as still being in the system
    discharge_date = db.Column(db.Date)

    # a reference to the person who
    # is 'staying' in the jail
    person_id = db.Column(db.ForeignKey('person.id'), nullable=False)

    person = db.relationship('Person',
        backref=db.backref('stays', lazy='dynamic'))

    date_created = db.Column(db.Date, nullable=False)

