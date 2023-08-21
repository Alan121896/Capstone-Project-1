from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()
from flask_login import UserMixin

class Cocktail(db.Model):
    __tablename__ = 'cocktail'  
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    instructions = db.Column(db.Text)


def get_cocktail_by_id(drink_id):
    """Fetch details of a specific cocktail by its ID."""
    url = f"https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i={drink_id}"
    response = requests.get(url)
    data = response.json()
    return data['drinks'][0] if data['drinks'] else None

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('cocktail_id', db.Integer, db.ForeignKey('cocktails.id'))
)

class User( UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    favorite_cocktails = db.relationship('Cocktail', secondary=favorites, backref=db.backref('favorited_by', lazy='dynamic'))

    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


