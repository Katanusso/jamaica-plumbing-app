# models.py

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reviews = db.relationship('Review', backref='author', lazy='dynamic')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    plumber_profile = db.relationship('Plumber', uselist=False, backref='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Plumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    services = db.relationship('Service', backref='plumber', lazy='dynamic')
    reviews = db.relationship('Review', backref='plumber', lazy='dynamic')
    status = db.Column(db.String(64), default='available')
    bookings = db.relationship('Booking', backref='plumber', lazy='dynamic')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def average_rating(self):
        total_reviews = self.reviews.count()
        if total_reviews == 0:
            return 0
        total_rating = sum([review.rating for review in self.reviews])
        return total_rating / total_reviews

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    min_price = db.Column(db.Float, nullable=False)
    max_price = db.Column(db.Float, nullable=False)
    plumber_id = db.Column(db.Integer, db.ForeignKey('plumber.id'), nullable=False)
    bookings = db.relationship('Booking', backref='service', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plumber_id = db.Column(db.Integer, db.ForeignKey('plumber.id'))
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(64), default='pending')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    rating = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plumber_id = db.Column(db.Integer, db.ForeignKey('plumber.id'))
