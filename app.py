"""app for Bathroom Buddy"""
import os
import GoogleMapsAPIKey

from flask import Flask, request, render_template, jsonify, session, flash, redirect, g, abort, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from forms import UserAddForm, LoginForm, UserEditForm
from GoogleSearch import GoogleSearchClass
from models import db, connect_db, Restroom, User, Favorite, Blacklist

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
db.create_all()

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
def homepage():
    """Show homepage:

    - anon users: no favorites
    - logged in: favorites already saved
    """

    if g.user:

        restroom = (Restroom
                    .query
                    .filter(Restroom.user_id))
                    

        fav_restroom_ids = [fav.place_id for fav in g.user.favorites]

        return render_template('homepage.html', restroom=restroom, favorites=fav_restroom_ids)

    else:
        return render_template('home_general.html')

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
            return render_template('login.html', form=form, user=user)

        do_login(user)

        return redirect("/")

    else:
        return render_template('signup.html', form=form)

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

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

        flash("You've been logged out", 'success')

        return redirect ('/')


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


#############################################
########  SEARCH FEATURES ################
#############################################

@app.route('/search')
def searchbox():
    """Search area for restroom"""

    search = request.args.get('q')

    client = GoogleSearchClass(api_key = API_KEY, address_or_postal_code=search)
    search_result=client.search()
    filtered_list = client.filter_results()
    detailed_list = client.detail()
    filtered=list(filtered_list)
    
    if search_result['status'] == "INVALID_REQUEST":
        raise ValueError('invalid zip code or address')
        
    for restroom in filtered[0]:
        name = restroom['name']
        latitude = restroom['geometry']['location']['lat']
        longitude = restroom['geometry']['location']['lng']
        address = restroom['vicinity']
        place_id = restroom['place_id'] 
        user_id = g.user.id

        restroom_query = Restroom.query.filter_by(place_id=place_id)
        blacklist_query = Blacklist.query.filter_by(restroom_id=place_id)

        if restroom_query.count() > 0 or blacklist_query.count() > 0:
           pass
        else:
            restroom = Restroom(name=name,
                            latitude=latitude,
                            longitude=longitude,
                            address=address,
                            place_id=place_id,
                            user_id = user_id
                          )
            db.session.add(restroom)
            db.session.commit()
        
        
    return render_template('restrooms.html', detailed_list=detailed_list, filtered=filtered[0], restroom=restroom)

#####################################################
##########  FAVORITING RESTROOMS #############
########################################################
@app.route('/users/<int:user_id>/favorites')
def show_favorites(user_id):
    """Show list of favorites by user"""


    user = User.query.get_or_404(user_id)

    return render_template('favorites.html', user=user, favorites=user.favorites)



@app.route('/restrooms/<restroom_place_id>')
def restroom(restroom_place_id):
    """Show restroom detail """

    restroom = Restroom.query.get_or_404(restroom_place_id)
  
    return render_template('restroom_detail.html', restroom=restroom)


@app.route('/restrooms/<restroom_place_id>/favorite', methods=['POST'])
def add_favorite(restroom_place_id):
    """Toggle a favorite restroom for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    favorite_restroom = Restroom.query.get_or_404(restroom_place_id)

    user_favorites = g.user.favorites

    if favorite_restroom in user_favorites:
        g.user.favorites = [favorite for favorite in user_favorites if favorite != favorite_restroom]
    else:
        g.user.favorites.append(favorite_restroom)

    db.session.commit()

    return redirect(request.referrer)

##############################################
########### BlackList Locations ##############
#############################################


@app.route('/restrooms/<restroom_place_id>/blacklist', methods=['GET'])
def blacklist_restroom(restroom_place_id):
    """Add restroom to blacklist"""

    if not g.user:
        flash("Access unauthorized")
        return redirect("/")

    blacklist_restroom = Restroom.query.get_or_404(restroom_place_id)

    restroom = Blacklist(
            name = blacklist_restroom.name,
            restroom_id = blacklist_restroom.place_id
    )

    db.session.add(restroom)
    db.session.commit()


    return render_template('delete.html', blacklist_restroom=blacklist_restroom)

@app.route('/restrooms/<restroom_place_id>/delete', methods=['POST'])
def delete_restroom(restroom_place_id):
    """Delete location from restroom table"""


    restroom = Restroom.query.get_or_404(restroom_place_id)
    db.session.delete(restroom)
    db.session.commit()
    flash('location deleted')

    return redirect('/')




#################################################
    ######### Error Handling #################
#################################################

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('error_page.html'), 404

#  @app.errorhandler(Exception)
#  def handle_exception(e):
#     """handle all exceptions"""
#      if isinstance(e, HTTPException):
#          print(e)
#          return e
    
#     return render_template("error_page.html", e=e), 500

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req









