from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError, EqualTo, URL
import sqlite3
from flask_login import current_user
from configs import Config

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        conn = sqlite3.connect(Config.DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = :username', {'username': username.data})
        user = c.fetchone()
        conn.close()
        if user:
            raise ValidationError('Username already exists.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class WebsiteForm(FlaskForm):
    name = StringField('Website Name', validators=[DataRequired()])
    url = StringField('Website URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Add Website')

    def validate_url(self, url):
        if not url.data.startswith(('http://', 'https://')):
            url.data = 'http://' + url.data
        conn = sqlite3.connect(Config.DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM websites WHERE user_id = :user_id AND url = :url',
                  {'user_id': current_user.id, 'url': url.data})
        website_data = c.fetchone()
        conn.close()
        if website_data:
            raise ValidationError('This website URL is already added.')