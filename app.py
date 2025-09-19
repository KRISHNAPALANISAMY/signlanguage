# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route("/")
# def home():
#     return render_template("index.html")

# @app.route("/about")
# def about():
#     return render_template("about.html")

# @app.route("/contact")
# def contact():
#     return render_template("contact.html")

# @app.route("/signup")
# def signup():
#     return render_template("signup.html")

# if __name__ == "__main__":
#     app.run(debug=True)

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import os
import pandas as pd
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

def backup_users():
    from app import User  # make sure your User model is imported

    users = User.query.all()
    data = [{
        "ID": u.id,
        "Email": u.email,
        "PasswordHash": u.password
    } for u in users]

    df = pd.DataFrame(data)

    # Ensure backups folder exists
    backup_dir = os.path.join(os.path.dirname(__file__), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Create filename with timestamp
    filename = os.path.join(
        backup_dir,
        f"users_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    # Save to Excel
    df.to_excel(filename, index=False)
    print(f"[BACKUP] Saved {filename}")

# Schedule the backup job when Flask starts
scheduler = BackgroundScheduler()
scheduler.add_job(func=backup_users, trigger="interval", hours=24)  # every 24 hours
scheduler.start()

# Load env vars
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "dev-secret"

# DATABASE_URL should be like: mysql+pymysql://user:pass@host/dbname
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------
# Models
# ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str):
        # use werkzeug to generate a salted hash (PBKDF2 by default)
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

# ---------------------
# Routes
# ---------------------
@app.route("/")
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return f"Hello {user.email} — <a href='{url_for('logout')}'>Logout</a>"
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password required", "warning")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('register'))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Save user id in session (simple approach)
            session['user_id'] = user.id
            flash("Login successful", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("Logged out", "info")
    return redirect(url_for('login'))


if __name__ == "__main__":
    # Create tables if they don't exist (for development). In production use migrations.
    with app.app_context():
        db.create_all()
    app.run(debug=True)
