from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from models import db, Cocktail, User, connect_db, get_cocktail_by_id
from forms import RegistrationForm, LoginForm
import requests 
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone_1'
app.config['SECRET_KEY'] = '1'


login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


connect_db(app)
# db.drop_all()
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


@app.route('/index/<letter>', methods=['GET'])
def index_by_letter(letter):
    cocktails = get_cocktails_by_letter(letter)
    return render_template('index.html', cocktails=cocktails)

def get_cocktails_by_letter(letter):
    """Fetch list of cocktails that start with the given letter."""
    url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?f={letter}"
    response = requests.get(url)
    data = response.json()
    return data['drinks']


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
    app.logger.debug(f"Fetched cocktail for ID {drink_id}: {cocktail}")
    if not cocktail:
        return "Cocktail not found", 404

    return render_template('cocktail_detail.html', cocktail=cocktail)
    

@app.route('/filter', methods=['GET'])
def filter_page():

    alcohols = ['Vodka', 'Gin', 'Rum', 'Tequila', 'Whiskey', 'Bourbon','Brandy', 'Mezcal', 'Champagne']
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# @app.route('/favorite/<int:drink_id>', methods=['POST'])
# @login_required
# def favorite_cocktail(drink_id):
#     app.logger.debug(f"Inside favorite_cocktail for drink ID: {drink_id}")
#     cocktail = Cocktail.query.get_or_404(drink_id)
#     cocktail.toggle_favorite(current_user)
#     db.session.commit()
#     return redirect(url_for('cocktail_detail', drink_id=drink_id))  

@app.route('/favorite/<int:drink_id>', methods=['POST'])
@login_required
def favorite_cocktail(drink_id):
    app.logger.debug(f"Attempting to toggle favorite for drink ID: {drink_id}")

    cocktail = Cocktail.query.get(drink_id)

    if not cocktail:
        app.logger.warning(f"Cocktail with ID {drink_id} not found in the database. Fetching from API...")
        
        # Fetch cocktail details from the API
        cocktail_data = get_cocktail_by_id(drink_id)
        if not cocktail_data:
            app.logger.error(f"Failed to fetch cocktail with ID {drink_id} from the API.")
            return "Failed to fetch cocktail from API", 404
        
        # Create a new cocktail instance and add to database
        cocktail = Cocktail(id=cocktail_data['idDrink'], name=cocktail_data['strDrink'], image_url=cocktail_data['strDrinkThumb'], instructions=cocktail_data['strInstructions'])
        db.session.add(cocktail)
        db.session.commit()
        app.logger.info(f"Cocktail with ID {drink_id} added to the database.")

    cocktail.toggle_favorite(current_user)
    db.session.commit()
    
    app.logger.debug(f"Successfully toggled favorite for drink ID: {drink_id}")

    return redirect(url_for('cocktail_detail', drink_id=drink_id))


@app.route('/favorites')
@login_required
def favorites():

    for cocktail in current_user.favorite_cocktails:
        print(cocktail.image_url)

    return render_template('favorites.html', cocktails=current_user.favorite_cocktails)


