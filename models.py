"""SQLAlchemy models for Bathroom Buddy"""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class Restroom(db.Model):
    """Restrooms in the system"""

    __tablename__ = 'restrooms'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.Text,
        nullable=False,
    )

    street = db.Column(
        db.Text,
        nullable=False,
    )

    city = db.Column(
        db.Text,
        nullable=False,
    )

    state = db.Column(
        db.Text,
        nullable=False,
    )

    country = db.Column(
        db.Text,
        nullable=False,
    )

    accessible = db.Column(
        db.Boolean,
        nullable=True,
    )

    latitude = db.Column(
        db.Float,
        nullable=False,
    )

    longitude = db.Column(
        db.Float,
        nullable=False,
    )

    upvote = db.Column(
        db.Integer,
        nullable=True,
    )

    downvote = db.Column(
        db.Integer,
        nullable=True,
    )

    user = db.relationship('User')


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.Text,
        nullable=False,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    favorties = db.relationship(
        'Restroom',
        secondary="favorites"
    )


    def __repr__(self):
        return f"<User #{self.id}: {self.name}, {self.email}>"
    
    @classmethod
    def signup(cls, name, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            name=name,
            email=email,
            password=hashed_pwd
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, email, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(email=email).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Favorite(db.Model):
    """Mapping user favorites to bathrooms."""

    __tablename__ = 'favorites' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    restroom_id = db.Column(
        db.Integer,
        db.ForeignKey('restrooms.id', ondelete='cascade')
    )

def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
