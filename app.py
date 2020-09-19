"""app for Bathroom Buddy"""
import os
import GoogleMapsAPIKey

from flask import Flask, request, render_template, jsonify, session, flash, redirect, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, Restroom, User, Favorite
from forms import UserAddForm, LoginForm, UserEditForm
from GoogleSearch import GoogleSearchClass

API_KEY = GoogleMapsAPIKey.api_key

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///bathroom_buddy_db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
# db.create_all()

debug = DebugToolbarExtension(app)



@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/')
def home():
    """Show home page"""

    return render_template('home.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                name=form.name.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Email already exists", 'danger')
            return render_template('users/login.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.email.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.name}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

        flash("You've been logged out", 'success')

        return redirect ('/login')

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

##########################################

@app.route('/users/<int:user_id>/favorites')
def users_show(user_id):
    """Show user profile with favorites listed"""

    user = User.query.get_or_404(user_id)

    # listing users favorite restrooms 
    favorites = (Favorite
                .query
                .filter(Favorite.user_id == user_id)
                .limit(100)
                .all())
    return render_template('users/favorites.html', user=user, favorites=favorites)

# ############################################

@app.route('/search')
def searchbox():
    """Search area for restroom"""

    search = request.args.get('q')

    client = GoogleSearchClass(api_key = API_KEY, address_or_postal_code=search)
    client.search()
    # search_result2 = dict(search_result)
    
    client.filter_results()
    detailed_list = client.detail()

    # if search_result['status'] != "OK":
    #     flash("Not a valid address or zip code", "danger")
    #     return ('/')

    return render_template('restrooms.html', detailed_list=detailed_list)

#####################################################

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req









