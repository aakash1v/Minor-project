from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    type = db.Column(db.String(50))
    description = db.Column(db.Text)
    subject = db.Column(db.String(100))
    starting_date = db.Column(db.Date)
    ending_date = db.Column(db.Date)
    approvedby_teacheder = db.Column(db.String(100))
    approvedby_hod = db.Column(db.String(100))
    approvedby_warden = db.Column(db.String(100))
    final_status = db.Column(db.String(50))
    parents_number = db.Column(db.String(15))
    issue_date = db.Column(db.Date)

class Student(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    prn = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    branch = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    photo = db.Column(db.String(255))
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    class_id = db.Column(db.Integer, db.ForeignKey('class.class_id'))
    hostel = db.Column(db.String(100))
    warden_id = db.Column(db.Integer, db.ForeignKey('warden.id'))
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostel.id'))

    leave_requests = db.relationship('LeaveRequest', backref='student', lazy=True)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    department = db.Column(db.String(100))
    role = db.Column(db.String(50))
    photo = db.Column(db.String(255))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    admin_approved = db.Column(db.Boolean, default=False)
    class_assigned = db.Column(db.Integer, db.ForeignKey('class.class_id'))

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    photo = db.Column(db.String(255))

class Class(db.Model):
    class_id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100))
    student_year = db.Column(db.String(10))
    total_student = db.Column(db.Integer)
    class_teacher = db.Column(db.String(100))

    students = db.relationship('Student', backref='class_', lazy=True)
    faculties = db.relationship('Faculty', backref='class_', lazy=True)

class Hostel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostel_name = db.Column(db.String(100))
    total_student = db.Column(db.Integer)
    present_student = db.Column(db.Integer)
    warden_id = db.Column(db.Integer, db.ForeignKey('warden.id'))

    students = db.relationship('Student', backref='hostel_', lazy=True)

class Warden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    hostel_id = db.Column(db.Integer)
    photo = db.Column(db.String(255))
    admin_approved = db.Column(db.Boolean, default=False)

    students = db.relationship('Student', backref='warden', lazy=True)
    hostels = db.relationship('Hostel', backref='warden', lazy=True)
