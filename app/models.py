from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ------------------ User (Common Base for Student and Faculty) ------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date)
    mobile = db.Column(db.String(15))
    usertype = db.Column(db.String(255))
    photo = db.Column(db.String(255))

    # Relationship to Student and Faculty
    student_profile = db.relationship('Student', backref='user', uselist=False)
    faculty_profile = db.relationship('Faculty', backref='user', uselist=False)

# ------------------ Student ------------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prn = db.Column(db.String(20), unique=True, nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    hostel = db.Column(db.String(100), nullable=False)

    # ForeignKey to link Student with User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship to LeaveRequest
    leave_requests = db.relationship('LeaveRequest', backref='student', lazy=True)

# ------------------ Faculty ------------------
class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g. 'teacher', 'hod', etc.
    admin_approved = db.Column(db.Boolean, default=False)

    # ForeignKey to link Faculty with User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ------------------ Leave Request ------------------
class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    type = db.Column(db.String(50))  # e.g. Medical, Personal, etc.
    subject = db.Column(db.String(100))
    description = db.Column(db.Text)
    starting_date = db.Column(db.Date)
    ending_date = db.Column(db.Date)
    issue_date = db.Column(db.DateTime)  
    parents_number = db.Column(db.String(15))
    parents_name = db.Column(db.String(100))

    approvedby_teacher = db.Column(db.String(100))
    approvedby_hod = db.Column(db.String(100))
    approvedby_warden = db.Column(db.String(100))
    final_status = db.Column(db.String(50))  # e.g. Pending, Approved, Rejected
