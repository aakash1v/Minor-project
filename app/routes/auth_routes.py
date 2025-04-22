# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user
from app.models import User
from app.forms import StudentSignupForm
from app.models import db, User, Student, Faculty
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from app.mail_utils import send_contact_email
from sqlalchemy.exc import IntegrityError


auth_bp = Blueprint("auth", __name__)



UPLOAD_FOLDER = "static/uploads"  # Adjust this as needed
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route("/")
def home():
    return render_template("index.html")


@auth_bp.route("/contact" , methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if name and email and message:
            try:
                send_contact_email(name, email, message)
                flash('Your message has been sent successfully!', 'success')
                return redirect(url_for('auth.contact'))
            except Exception as e:
                print(f"Error sending contact email: {e}")
                flash('An error occurred while sending your message. Please try again later.', 'danger')
        else:
            flash('Please fill out all fields.', 'warning')

    return render_template('contact.html')


@auth_bp.route("/about")
def about():
    return render_template("about.html")



#### LOGIN AND SIGNUP ROUTES..


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usertype = request.form["usertype"]  # student/faculty

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"{usertype.capitalize()} logged in successfully.", "success")
            if user.usertype == "student":
                return redirect(url_for("stud.student_dashboard"))  #
            elif user.usertype == "faculty":
                return redirect(url_for('faculty.faculty_dashboard'))
            else:
                return redirect(url_for('auth.home'))


        flash("Invalid credentials. Try again.", "danger")
    return render_template("registration/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# ------------------ Signup Route ------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        password = data['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256') 

        # Process file upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join("static/profile", photo_filename))

        new_user = User(
            username=data["username"],
            email=data["email"],
            password=hashed_pw,
            name=data["name"],
            dob=datetime.strptime(data['dob'], '%Y-%m-%d').date(),
            mobile=data["mobile"],
            photo=photo_filename,
        )

        try:
            if data.get("student") == "yes":
                new_user.usertype = "student"
                new_student = Student(
                    prn=data["prn"],
                    branch=data["branch"],
                    hostel=data["hostel"],
                    user=new_user,
                )
                db.session.add(new_student)

            elif data.get("faculty") == "yes":
                new_user.usertype = "faculty"
                new_faculty = Faculty(
                    department=data["department"],
                    role=data["role"],
                    user=new_user,
                )
                db.session.add(new_faculty)

            else:
                new_user.usertype = "user"
                db.session.add(new_user)

            db.session.commit()
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except IntegrityError as e:
            db.session.rollback()
            # Handle duplicate email or username nicely
            if "UNIQUE constraint failed: user.email" in str(e):
                flash("This email is already registered. Please use another email.", "danger")
            elif "UNIQUE constraint failed: user.username" in str(e):
                flash("This username is already taken. Please choose a different one.", "danger")
            else:
                flash("An error occurred during signup. Please try again.", "danger")

    return render_template("registration/signup.html")


