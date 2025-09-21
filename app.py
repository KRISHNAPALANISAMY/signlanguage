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
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# ---------------------
# Load environment variables
# ---------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")

# MySQL configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------
# Model
# ---------------------
class User(db.Model):
    __tablename__ = "student"  # explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

# ---------------------
# Excel Sync
# ---------------------
def save_to_excel():
    users = User.query.all()
    data = [{"ID": u.id, "Name": u.name, "Email": u.email} for u in users]
    df = pd.DataFrame(data)
    df.to_excel("students.xlsx", index=False)
    print("[SYNC] Excel updated: students.xlsx")

# ---------------------
# Routes
# ---------------------
@app.route("/")
def index():
    users = User.query.all()
    return render_template("index.html", users=users)

from sqlalchemy.exc import IntegrityError  # Make sure this import is at the top

@app.route("/add", methods=["POST"])
def add_user():
    name = request.form.get("name")
    email = request.form.get("email")

    if not name or not email:
        flash("Name and Email required", "warning")
        return redirect(url_for("index"))

    user = User(name=name, email=email)
    db.session.add(user)

    try:
        db.session.commit()
        save_to_excel()
        flash("Student added successfully", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Email already exists!", "danger")  # Alert for duplicate email

    return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    save_to_excel()
    flash("Student deleted", "info")
    return redirect(url_for("index"))

@app.route("/update/<int:id>", methods=["POST"])
def update_user(id):
    user = User.query.get_or_404(id)
    user.name = request.form.get("name")
    user.email = request.form.get("email")
    db.session.commit()
    save_to_excel()
    flash("Student updated", "success")
    return redirect(url_for("index"))

# ---------------------
# Main
# ---------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # creates the 'student' table if not exists
        save_to_excel()  # create initial Excel file
    app.run(debug=True)
