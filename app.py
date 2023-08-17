from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, Cocktail, connect_db, get_cocktail_by_id
import requests 


app = Flask(__name__)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone_1'
app.config['SECRET_KEY'] = '1'


connect_db(app)

db.create_all()


def get_random_cocktails(number=6):
    """Fetch a specified number of random cocktails."""
    cocktails = []
    for _ in range(number):
        url = "https://www.thecocktaildb.com/api/json/v1/1/random.php"
        response = requests.get(url)
        data = response.json()
        cocktails.extend(data['drinks'])

        # Ensure that the new cocktails are not the same as the previously stored ones
    previous_cocktails = session.get('previous_cocktails', [])
    while set(cocktail['idDrink'] for cocktail in cocktails) & set(previous_cocktails):
        cocktails = get_random_cocktails(number)
    return cocktails
    

def search_cocktail(name):
    url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={name}"
    response = requests.get(url)
    data = response.json()
    return data['drinks']

def save_to_db(cocktails):
    for cocktail in cocktails:
        name = cocktail['strDrink']
        image_url = cocktail['strDrinkThumb']
        instructions = cocktail['strInstructions']
        new_cocktail = Cocktail(name, image_url, instructions)
        db.session.add(new_cocktail)
    db.session.commit()


@app.route('/')
def index():
    if 'previous_cocktails' not in session or request.args.get('rerandomize'):
        cocktails = get_random_cocktails()
        # Store the current cocktails' IDs in the session for later checks
        session['previous_cocktails'] = [cocktail['idDrink'] for cocktail in cocktails]
    else:
        cocktails = get_random_cocktails()

    return render_template('index.html', cocktails=cocktails)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        cocktail_name = request.form['cocktail_name']
        session['last_search'] = cocktail_name
    else:  # If it's a GET request
        cocktail_name = session.get('last_search', None)
        if not cocktail_name:
            return redirect(url_for('index'))  # If there's no stored search query, go to the main page

    cocktails = search_cocktail(cocktail_name)
    return render_template('index.html', cocktails=cocktails)



@app.route('/cocktail/<int:drink_id>')
def cocktail_detail(drink_id):
    # Store the referer URL in session
    session['last_visited'] = request.headers.get("Referer", url_for('index'))  # default to index if no referer

    cocktail = get_cocktail_by_id(drink_id)
    if not cocktail:
        return "Cocktail not found", 404

    return render_template('cocktail_detail.html', cocktail=cocktail)
    

@app.route('/filter', methods=['GET'])
def filter_page():

    alcohols = ['Vodka', 'Gin', 'Rum', 'Tequila', 'Whiskey', 'Bourbon','Brandy', 'Mezcal', 'Absinthe', 'Beer', ]
    return render_template('filter.html', alcohols=alcohols)


def filter_by_alcohol(alcohol_type):
    url = f"https://www.thecocktaildb.com/api/json/v1/1/filter.php?i={alcohol_type}"
    response = requests.get(url)
    data = response.json()
    return data['drinks']

@app.route('/filter_results/<alcohol_type>')
def filter_results(alcohol_type):
    cocktails = filter_by_alcohol(alcohol_type)
    return render_template('index.html', cocktails=cocktails)