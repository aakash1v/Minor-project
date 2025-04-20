from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from forms import StudentSignupForm
from models import Student, Faculty, Admin, Warden, Hostel
from datetime import datetime
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'  # Adjust this as needed
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # or other database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional, bu
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "your-very-secret-key"

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database and tables created.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/leave_req')
def leave_req():
    return render_template('leave_request.html')

### LOGIN SIGNUP ROUTE ....
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        student = Student.query.filter_by(email=email).first()

        if student and check_password_hash(student.password, password):  # Check hashed password
            session['student_id'] = student.id
            flash('Login successful!', 'success')
            return redirect(url_for('leave_req'))  
        else:
            flash('Invalid email or password', 'danger')

    return render_template('registration/login.html')

@app.route('/logout')
def logout():
    session.pop('student_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def signup():
    form = StudentSignupForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_student = Student.query.filter(
            (Student.prn == form.prn.data) |
            (Student.username == form.username.data) |
            (Student.email == form.email.data)
        ).first()

        if existing_student:
            flash("PRN, Username, or Email already exists.", "danger")
            return render_template("signup.html", form=form)

        # Handle file upload (if any)
        photo_filename = None
        if form.photo.data:
            photo_file = form.photo.data
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join('static/uploads', photo_filename)
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
            photo=f'uploads/{photo_filename}',  # Store photo filename
        )

        # Add to session and commit to database
        try:
            db.session.add(student)
            db.session.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()  # Rollback on error
            flash(f"An error occurred: {e}", "danger")

    return render_template('registration/register.html', form=form)


### PROFILE PAGE ...
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    # Get the logged-in student
    student = Student.query.get(session['student_id'])

    if request.method == 'POST':
        # Handle profile update
        student.name = request.form['name']
        student.dob = request.form['dob']
        student.branch = request.form['branch']
        student.username = request.form['username']
        student.email = request.form['email']
        student.mobile = request.form['mobile']
        student.hostel = request.form['hostel']

        if request.form['password']:  # If password is entered, hash and update it
            student.password = generate_password_hash(request.form['password'], method='sha256')

        # Handle profile picture upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '':
                photo.save(f'./static/profile_pics/{student.id}_{photo.filename}')
                student.photo = f'{student.id}_{photo.filename}'

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))  # Redirect back to profile after update

    return render_template('profile.html', student=student)


if __name__ == "__main__":
    app.run(debug=True)