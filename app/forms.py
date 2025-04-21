# Example of your form class (make sure it's similar to this)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, FileField
from wtforms.validators import InputRequired, Email, Length

class StudentSignupForm(FlaskForm):
    prn = StringField('PRN', validators=[InputRequired()])
    name = StringField('Full Name', validators=[InputRequired()])
    dob = DateField('Date of Birth', validators=[InputRequired()])
    branch = StringField('Branch', validators=[InputRequired()])
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    mobile = StringField('Mobile', validators=[InputRequired()])
    hostel = StringField('Hostel Name', validators=[InputRequired()])
    photo = FileField('Upload Photo')
