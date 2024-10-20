from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, logout_user, login_required, login_user, current_user
import sqlite3
import bcrypt
from configs import Config
from forms import RegisterForm, LoginForm, WebsiteForm

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

def get_user_by_id(user_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (int(user_id),))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()

        if user_data is None or not User(user_data[0], user_data[1], user_data[2]).check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        login_user(User(user_data[0], user_data[1], user_data[2]), remember=form.remember_me.data)
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
    form = WebsiteForm()
    if form.validate_on_submit():
        name = form.name.data
        url = form.url.data
        user_id = current_user.id
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('INSERT INTO websites (user_id, name, url) VALUES (?, ?, ?)', (user_id, name, url))
        conn.commit()
        conn.close()
        flash('Website added successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM websites WHERE user_id = ?', (current_user.id,))
    websites = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', form=form, websites=websites)

@app.route('/dashboard/<int:website_id>/delete', methods=['POST'])
@login_required
def delete(website_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('DELETE FROM websites WHERE id = ? AND user_id = ?', (website_id, current_user.id))
    conn.commit()
    conn.close()
    flash('Website deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

def create_tables():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    with open(app.config['SCHEMA'], 'r') as f:
        c.executescript(f.read())
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
