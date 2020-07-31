from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    crsid = db.Column(db.String(7), db.CheckConstraint('crsid = lower(crsid)'))
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    society_id = db.Column(db.Integer, db.ForeignKey('societies.id'), nullable=False)

    # will it work if I use the backref here?
    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"


class Society(db.Model):
    __tablename__ = "societies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    admins = db.relationship('User', backref="society", lazy=True)
    description = db.Column(db.String, unique=False, nullable=True)

    website = db.Column(db.String, unique=False, nullable=True, default='https://www.srcf.net')
    welcome_text = db.Column(db.String, unique=False, nullable=True, default='Your welcome text here!')
    logo = db.Column(db.String, unique=False, nullable=True, default='default.png')
    banner_text = db.Column(db.String, unique=False, nullable=True)
    banner_color = db.Column(db.String, unique=False, nullable=True)
    mute_on_start = db.Column(db.Boolean, nullable=False, default=False)
    disable_private_chat = db.Column(db.Boolean, nullable=False, default=False)

    
    def __repr__(self):
        return f"Society('{self.name}', '{self.admins}')"

