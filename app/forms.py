from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FloatField, DateField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired(), Length(max=64)])
    min_price = FloatField('Minimum Price', validators=[DataRequired(), NumberRange(min=0)])
    max_price = FloatField('Maximum Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Service')

class EditServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired(), Length(max=64)])
    min_price = FloatField('Minimum Price', validators=[DataRequired(), NumberRange(min=0)])
    max_price = FloatField('Maximum Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Update Service')

class BookingForm(FlaskForm):
    service = SelectField('Service', coerce=int, validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = StringField('Time', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Book Service')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], coerce=int, validators=[DataRequired()])
    body = TextAreaField('Review', validators=[DataRequired(), Length(max=140)])
    submit = SubmitField('Submit Review')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Search')

class UpdatePlumberStatusForm(FlaskForm):
    status = SelectField('Status', choices=[('available', 'Available'), ('busy', 'Busy'), ('unavailable', 'Unavailable')], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class ManageServiceRequestForm(FlaskForm):
    status = SelectField('Status', choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class UpdateStatusForm(FlaskForm):
    status = StringField('Status', validators=[DataRequired()])
    submit = SubmitField('Update')

class CSVUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Upload')
