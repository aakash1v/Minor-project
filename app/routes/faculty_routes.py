# app/routes/faculty_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import LeaveRequest, db, Faculty
from app.mail_utils import send_rejection_email, send_approval_email
from datetime import datetime
import pytz
IST = pytz.timezone('Asia/Kolkata')
current_ist_time = datetime.now(IST)
from app.models import Student, User


faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/faculty_dashboard')
@login_required
def faculty_dashboard():
    department_filter = request.args.get('department')
    hostel_filter = request.args.get('hostel')

    query = LeaveRequest.query.join(Student).join(User)

    if department_filter:
        query = query.filter(Student.branch == department_filter)

    if hostel_filter:
        query = query.filter(Student.hostel == hostel_filter)

    leave_requests = query.order_by(LeaveRequest.id.desc()).all()

    # For dropdown options (optional: deduplicate)
    departments = [s.branch for s in Student.query.distinct(Student.branch)]
    hostels = [s.hostel for s in Student.query.distinct(Student.hostel)]

    return render_template(
        'dashboard/faculty_dashboard.html',
        leave_requests=leave_requests,
        departments=departments,
        hostels=hostels,
        selected_department=department_filter,
        selected_hostel=hostel_filter
    )


@faculty_bp.route('/approve/<int:leave_id>', methods=['POST'])
@login_required
def approve_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()

    if not faculty:
        flash('Faculty profile not found.', 'danger')
        return redirect(url_for('faculty.faculty_dashboard'))

    if leave.type.lower() == "emergency":
        leave.final_status = "Approved"
        leave.issue_date = current_ist_time
        send_approval_email(leave.student.user.email,leave.student.user.name, leave.subject)

    if faculty.role == 'teacher':
        leave.approvedby_teacher = 'Approved'
    elif faculty.role == 'hod':
        leave.approvedby_hod = 'Approved'
    elif faculty.role == 'warden':
        leave.approvedby_warden = 'Approved'
    else:
        flash('Invalid faculty role.', 'danger')
        return redirect(url_for('faculty.faculty_dashboard'))

    # Check if all approvals are done to mark final status
    if all([
        leave.approvedby_teacher == 'Approved',
        leave.approvedby_hod == 'Approved',
        leave.approvedby_warden == 'Approved'
    ]):
        leave.final_status = 'Approved'
        leave.issue_date = current_ist_time
        send_approval_email(leave.student.user.email, leave.student.user.name,  leave.subject)

    db.session.commit()
    flash('Leave approved successfully.', 'success')
    return redirect(url_for('faculty.faculty_dashboard'))


@faculty_bp.route('/reject/<int:leave_id>', methods=['POST'])
@login_required
def reject_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.approvedby_teacheder = current_user.name
    leave.issue_date = current_ist_time
    leave.final_status = 'Rejected'
    send_rejection_email(leave.student.user.email, leave.student.user.name,  leave.subject)
    db.session.commit()
    flash('Leave rejected.', 'danger')
    return redirect(url_for('faculty.faculty_dashboard'))



@faculty_bp.route('/view_student/<int:leave_id>')
@login_required
def view_student(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    student = leave.student
    user = student.user

    return render_template('faculty/view_student.html', leave=leave, student=student, user=user)