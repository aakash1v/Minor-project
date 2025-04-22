# app/routes/faculty_routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import LeaveRequest, db, Faculty
from app.mail_utils import send_rejection_email, send_approval_email
from datetime import datetime
import pytz
IST = pytz.timezone('Asia/Kolkata')
current_ist_time = datetime.now(IST)


faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/faculty_dashboard')
@login_required
def faculty_dashboard():
    # Show all pending and reviewed requests (modify filter as per role)
    leave_requests = LeaveRequest.query.order_by(LeaveRequest.id.desc()).all()
    return render_template('dashboard/faculty_dashboard.html', leave_requests=leave_requests)

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