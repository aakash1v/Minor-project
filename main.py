from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import StudentSignupForm
from models import Student, Faculty, Admin, Warden, Hostel, LeaveRequest
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from datetime import date
from models import db
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
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect to this view if not logged in


@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))


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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        student = Student.query.filter_by(email=email).first()

        if student and check_password_hash(student.password, password):
            login_user(student)
            flash('Login successful!', 'success')
            return redirect(url_for('leave_req'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('registration/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def signup():
    form = StudentSignupForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_student = Student.query.filter(
            (Student.prn == form.prn.data)
            | (Student.username == form.username.data)
            | (Student.email == form.email.data)
        ).first()

        if existing_student:
            flash("PRN, Username, or Email already exists.", "danger")
            return render_template("signup.html", form=form)

        # Handle file upload (if any)
        photo_filename = None
        if form.photo.data:
            photo_file = form.photo.data
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join("static/uploads", photo_filename)
            photo_file.save(photo_path)

        # Create new student
        student = Student(
            prn=form.prn.data,
            name=form.name.data,
            dob=form.dob.data,
            branch=form.branch.data,
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            mobile=form.mobile.data,
            hostel=form.hostel.data,
            photo=f"uploads/{photo_filename}",  # Store photo filename
        )

        # Add to session and commit to database
        try:
            db.session.add(student)
            db.session.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()  # Rollback on error
            flash(f"An error occurred: {e}", "danger")

    return render_template("registration/register.html", form=form)


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
            issue_date=date.today(),
            approvedby_teacheder="Pending",
            approvedby_hod="Pending",
            approvedby_warden="Pending",
            final_status="Pending",
        )

        db.session.add(leave)
        db.session.commit()
        flash("Leave request submitted successfully!", "success")
        return redirect(url_for("home"))

    return render_template("leave_request.html")



# Student Dashboard Route
@app.route('/dashboard', methods=['GET'])
@login_required
def student_dashboard():
    # Fetch leave requests for the current student
    leave_requests = LeaveRequest.query.filter_by(student_id=current_user.id).all()
    
    return render_template('dashboard/student_dashboard.html', leave_requests=leave_requests)


@app.route('/cancel_leave/<int:leave_id>', methods=['POST'])
def cancel_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)

    # You can add current_user checks here if needed:
    # if leave.student_id != current_user.id:
    #     flash('You are not authorized to cancel this request.', 'danger')
    #     return redirect(url_for('dashboard'))

    if leave.final_status == 'Pending':
        db.session.delete(leave)
        db.session.commit()
        flash('Leave request cancelled successfully.', 'success')
    else:
        flash('Only pending leave requests can be cancelled.', 'warning')

    return redirect(url_for('student_dashboard'))  # Replace with your actual view name



if __name__ == "__main__":
    app.run(debug=True)
