from ccj import db

class Person(db.Model):
    id = db.Column(db.String(15), primary_key=True) # extra 3 characthers just in case?
    gender = db.Column(db.String(1), nullable=True)
    race = db.Column(db.String(2), nullable=True)
    hash = db.Column(db.String(64), nullable=True)
    date_created = db.Column(db.DateTime, nullable=True)

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return '<Person %r>' % self.id
