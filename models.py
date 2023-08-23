from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class Cocktail(db.Model):
    __tablename__ = 'cocktails'  
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    instructions = db.Column(db.Text)
    

    def toggle_favorite(self, user):
        if self in user.favorite_cocktails:
            user.favorite_cocktails.remove(self)
        else:
            user.favorite_cocktails.append(self)

    
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


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    favorite_cocktails = db.relationship('Cocktail', secondary=favorites, backref=db.backref('favorited_by', lazy='dynamic'))

    def set_password(self, password):
        """Set hashed password for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hashed one."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    def get_id(self):
        return str(self.id)
    

def connect_db(app):
    """Connect to database."""
    db.app = app
    db.init_app(app)


