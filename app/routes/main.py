from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import StudentSignupForm
from app.models import Student, Faculty, LeaveRequest, User
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash
from flask_login import (
    login_required,
    current_user,
    LoginManager,
    login_user,
    logout_user,
)
from datetime import date
from app.models import db
import os


UPLOAD_FOLDER = "static/uploads"  # Adjust this as needed
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"  # or other database URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Optional, bu
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "your-very-secret-key"

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database and tables created.")


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# ------------------ Custom User Loader ------------------
@login_manager.user_loader
def load_user(user_id):
    # First try to load as a student
    user = User.query.get(int(user_id))
    if user:
        return user



@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/about")
def about():
    return render_template("about.html")


### LOGIN SIGNUP ROUTE ....
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usertype = request.form["usertype"]  # 'student' or 'faculty'
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"{usertype.capitalize()} logged in successfully.")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials. Try again.")
    return render_template("registration/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("login"))


# ------------------ Signup Route ------------------
@app.route("/register", methods=["GET", "POST"])
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

        # Create a new User (common base model)

        new_user = User(
            username=data["username"],
            email=data["email"],
            password=hashed_pw,
            name=data["name"],
            dob=datetime.strptime(data['dob'], '%Y-%m-%d').date(),
            mobile=data["mobile"],
            photo=photo_filename,
        )

        # Check if the user is signing up as a student
        if data.get("student") == "yes":  # If student is selected
            new_user.usertype = "student"
            new_student = Student(
                prn=data["prn"],
                branch=data["branch"],
                hostel=data["hostel"],
                user=new_user,  # Associate with the user
            )
            db.session.add(new_student)
        elif data.get("faculty") == "yes":  # If faculty is selected
            new_user.usertype = "faculty"
            new_faculty = Faculty(
                department=data["department"],
                role=data["role"],
                user=new_user,  # Associate with the user
            )
            new_user.usertype = "user"
            db.session.add(new_faculty)
        else:
            db.session.add(new_user)  # Just a regular user (Faculty, Admin, etc.)

        db.session.commit()

        flash("Signup successful! Please log in.")
        return redirect(url_for("login"))  # Redirect to login page

    return render_template("registration/signup.html")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    student = current_user  # Directly use current_user

    if request.method == "POST":
        # Handle profile update
        student.name = request.form["name"]
        student.dob = request.form["dob"]
        student.branch = request.form["branch"]
        student.username = request.form["username"]
        student.email = request.form["email"]
        student.mobile = request.form["mobile"]
        student.hostel = request.form["hostel"]

        if request.form["password"]:  # If password is entered, hash and update it
            student.password = generate_password_hash(
                request.form["password"], method="sha256"
            )

        # Handle profile picture upload
        if "photo" in request.files:
            photo = request.files["photo"]
            if photo.filename != "":
                filename = f"{student.id}_{photo.filename}"
                photo.save(f"./static/uploads/{filename}")
                student.photo = filename

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", student=student)


@app.route("/leave_req", methods=["GET", "POST"])
@login_required
def leave_req():
    if request.method == "POST":
        leave_type = request.form["leave_type"]
        subject = request.form["subject"]
        description = request.form["description"]
        parent_contact = request.form["parent_contact"]

        # Convert string to date objects
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()

        leave = LeaveRequest(
            student_id=current_user.id,
            type=leave_type,
            subject=subject,
            description=description,
            starting_date=start_date,
            ending_date=end_date,
            parents_number=parent_contact,
            approvedby_teacheder="Pending",
            approvedby_hod="Pending",
            approvedby_warden="Pending",
            final_status="Pending",
        )

        db.session.add(leave)
        db.session.commit()
        flash("Leave request submitted successfully!", "success")
        return redirect(url_for("student_dashboard"))

    return render_template("leave_request.html")


@app.route("/dashboard")
# @login_required
def dashboard():
    print(current_user)
    if hasattr(current_user, "usertype") and current_user.usertype == "student":
        return redirect('student_dashboard')
    elif hasattr(current_user, "usertype") and current_user.usertype == "faculty":
        return redirect('faculty_dashboard')
    return "Unknown user type", 400


# Student Dashboard Route
@app.route('/student_dashboard', methods=['GET'])
def student_dashboard():
    # Fetch leave requests for the current student
    leave_requests = LeaveRequest.query.filter_by(student_id=current_user.id).all()

    return render_template('dashboard/student_dashboard.html', leave_requests=leave_requests)


# @app.route('/cancel_leave/<int:leave_id>', methods=['POST'])
# def cancel_leave(leave_id):
#     leave = LeaveRequest.query.get_or_404(leave_id)

#     # You can add current_user checks here if needed:
#     # if leave.student_id != current_user.id:
#     #     flash('You are not authorized to cancel this request.', 'danger')
#     #     return redirect(url_for('dashboard'))

#     if leave.final_status == 'Pending':
#         db.session.delete(leave)
#         db.session.commit()
#         flash('Leave request cancelled successfully.', 'success')
#     else:
#         flash('Only pending leave requests can be cancelled.', 'warning')

#     return redirect(url_for('student_dashboard'))  # Replace with your actual view name

#### FACULTY RELATED CODE ....

if __name__ == "__main__":
    app.run(debug=True)
