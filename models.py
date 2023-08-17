from flask_sqlalchemy import SQLAlchemy
import requests
db = SQLAlchemy()

class Cocktail(db.Model):
    __tablename__ = 'cocktail'  
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    instructions = db.Column(db.Text)

    # def __init__(self, name, image_url, instructions):
    #     self.name = name
    #     self.image_url = image_url
    #     self.instructions = instructions

def get_cocktail_by_id(drink_id):
    """Fetch details of a specific cocktail by its ID."""
    url = f"https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i={drink_id}"
    response = requests.get(url)
    data = response.json()
    return data['drinks'][0] if data['drinks'] else None





def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


