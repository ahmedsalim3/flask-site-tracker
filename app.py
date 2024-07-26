from flask import Flask, render_template, request, redirect, url_for, current_app
from flask_login import LoginManager, UserMixin, logout_user, login_required, login_user
import sqlite3
import secrets
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, ValidationError, EqualTo, URL
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from flask_login import current_user
import bcrypt
from flask import flash

app = Flask(__name__)
secret_key = secrets.token_hex()
app.secret_key = secret_key
login_manager = LoginManager()
login_manager.init_app(app)
app.app_context().push()

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

class Website:
    def __init__(self, id, user_id, name, url):
        self.id = id
        self.user_id = user_id
        self.url = url
        self.name = name

def get_user_by_id(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = {}'.format(int(user_id)))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    else:
        return None
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        conn = sqlite3.connect('database.db')
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
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM websites WHERE user_id = :user_id AND url = :url',
                  {'user_id': current_user.id, 'url': url.data})
        website_data = c.fetchone()
        conn.close()
        if website_data:
            raise ValidationError('This website URL is already added.')

# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # TODO 1: Implement the user registration.
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute(
            'INSERT INTO users (username, password) VALUES (:username, :password)',
            {'username': username, 'password': hashed_password}
        )
        conn.commit()
        conn.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # TODO 2: Implement the user login.
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            'SELECT * FROM users WHERE username = :username', {'username': username}
        )
        user_data = c.fetchone()
        conn.close()

        if user_data is None or not User(user_data[0], user_data[1], user_data[2]).check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        login_user(User(user_data[0], user_data[1], user_data[2]),
                   remember=form.remember_me.data)
        return redirect(url_for('dashboard'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # TODO 3: Implement the function for adding websites to user profiles.
    form = WebsiteForm()
    if form.validate_on_submit():
        name = form.name.data
        url = form.url.data
        user_id = current_user.id

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO websites (user_id, name, url) VALUES (:user_id, :name, :url)',
            {'user_id': user_id, 'name': name, 'url': url}
        )
        conn.commit()
        conn.close()

        flash('Website added successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM websites WHERE user_id = :user_id', {'user_id': current_user.id}
    )
    websites = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', form=form, websites=websites)

@app.route('/dashboard/<int:website_id>/delete', methods=['POST'])
@login_required
def delete(website_id):
    # TODO 4: Implement the function for deleting websites from user profiles.
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM websites WHERE id = :id AND user_id = :user_id',
        {'id': website_id, 'user_id': current_user.id}
    )
    conn.commit()
    conn.close()

    flash('Website deleted successfully!', 'success')

    return redirect(url_for("dashboard"))

def create_tables():
    # Creates new tables in the database.db database if they do not already exist.
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    with current_app.open_resource("schema.sql") as f:
        c.executescript(f.read().decode("utf8"))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
