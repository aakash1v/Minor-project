# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user
from app.models import User
from app.forms import StudentSignupForm
from app.models import db, User, Student, Faculty
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from app.mail_utils import send_contact_email, send_otp
from sqlalchemy.exc import IntegrityError
import random

def otp_generator():
    return random.randint(100000, 999999)


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
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"{user.name.capitalize()} logged in successfully.", "success")
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
        password = data['password'].strip()
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256') 

        # Process file upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join("static/profile", photo_filename))

        new_user = User(
            username=data["username"].strip(),
            email=data["email"].strip(),
            password=hashed_pw,
            name=data["name"].strip().capitalize(),
            dob=datetime.strptime(data['dob'], '%Y-%m-%d').date(),
            mobile=data["mobile"],
            photo=photo_filename,
        )

        try:
            if data.get("student") == "yes":
                new_user.usertype = "student"
                new_student = Student(
                    prn=data["prn"].strip(),
                    branch=data["branch"].strip().lower(),
                    hostel=data["hostel"].strip().lower(),
                    user=new_user,
                )
                db.session.add(new_student)

            elif data.get("faculty") == "yes":
                new_user.usertype = "faculty"
                new_faculty = Faculty(
                    department=data["department"].strip().lower(),
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


@auth_bp.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == "POST":
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            otp = otp_generator()
            session['reset_email'] = user.email
            session['reset_otp'] = otp
            send_otp(user.name, user.email, otp)
            flash("OTP sent successfully!", "success")
            return redirect(url_for('auth.otp_verify'))
        else:
            flash("Email doesn't exist. Please enter the correct email.", "danger")

    return render_template('registration/forget_password.html')


@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def otp_verify():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        actual_otp = session.get('reset_otp')

        if int(entered_otp) == int(actual_otp):
            session['otp_verified'] = True
            print(session['otp_verified'])
            flash("OTP verified. You can now set a new password.", "success")
            return redirect(url_for('auth.set_new_password'))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template('registration/otp_verification.html')


@auth_bp.route('/new_password', methods=['GET', 'POST'])
def set_new_password():
    if session['otp_verified'] != True:
        flash("Don't be smart 😃 😃please verify ur otp first \nthen only u can update password of ur account!!", "danger")
        return redirect(url_for('auth.forget_password'))
    print(session['otp_verified'])
    
    if request.method == 'POST':
        password = request.form.get('password1')
        confirm_password = request.form.get('password2')

        if password != confirm_password:
            flash("Passwords do not match. Try again.", "danger")
            return render_template('registration/new_password.html')

        email = session.get('reset_email')
        user = User.query.filter_by(email=email).first()

        if user:
            user.password = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.commit() 
            flash("Password updated successfully!", "success")
            return redirect(url_for('auth.login'))  # or your login route
        else:
            flash("User session expired. Try again.", "danger")
            return redirect(url_for('auth.forget_password'))

    return render_template('registration/new_password.html')
