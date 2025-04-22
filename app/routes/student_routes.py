# app/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms import StudentSignupForm
from app.models import db, LeaveRequest
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

stud_bp = Blueprint("stud", __name__)


@stud_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user
    student = user.student_profile
    faculty = user.faculty_profile

    if request.method == "POST":
        # Update User (common) fields
        user.name = request.form["name"]
        dob_str = request.form["dob"]
        user.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        user.username = request.form["username"]
        user.email = request.form["email"]
        user.mobile = request.form["mobile"]

        if request.form["password"]:
            user.password =  generate_password_hash(request.form["password"], method='pbkdf2:sha256')

        # Update Student-specific fields
        if student:
            student.branch = request.form["branch"]
            student.hostel = request.form["hostel"]
        elif faculty :
            faculty.role = request.form["role"]
            faculty.department = request.form["department"]

        # Photo upload
        if "photo" in request.files:
            photo = request.files["photo"]
            if photo and photo.filename != "":
                filename = f"{user.id}_{photo.filename}"
                photo.save(os.path.join("static/profile", filename))  
                user.photo = filename

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("stud.profile"))

    return render_template("profile.html", student=student, user=user, faculty=faculty)


@stud_bp.route("/leave_req", methods=["GET", "POST"])
@login_required
def leave_req():
    # POST - Submit leave request
    if request.method == "POST":
        leave_type = request.form["leave_type"]
        subject = request.form["subject"]
        description = request.form["description"]
        parent_name = request.form["parent_name"]
        parent_contact = request.form["parent_contact"]
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()

        leave = LeaveRequest(
            student_id=current_user.student_profile.id,
            type=leave_type,
            subject=subject,
            description=description,
            starting_date=start_date,
            ending_date=end_date,
            parents_number=parent_contact,
            parents_name=parent_name,
            approvedby_teacher="Pending",
            approvedby_hod="Pending",
            approvedby_warden="Pending",
            final_status="Pending",
        )

        db.session.add(leave)
        db.session.commit()
        flash("Leave request submitted successfully!", "success")
        return redirect(url_for("stud.student_dashboard"))

    # GET - View a specific leave request
    leave_id = request.args.get("leave_id")
    if leave_id:
        leave = LeaveRequest.query.get_or_404(leave_id)
        # Optional: Ensure the student can only view their own leave
        if leave.student_id != current_user.student_profile.id:
            flash("Unauthorized access to leave request.", "danger")
            return redirect(url_for("stud.student_dashboard"))
        return render_template("student/leave_request_view.html", leave=leave)

    return render_template("student/leave_request.html")



# Student Dashboard Route
@stud_bp.route('/student_dashboard', methods=['GET'])
def student_dashboard():
    # Fetch leave requests for the current student
    leave_requests = LeaveRequest.query.filter_by(student_id=current_user.student_profile.id).all()

    return render_template('dashboard/student_dashboard.html', leave_requests=leave_requests)


@stud_bp.route('/cancel_leave/<int:leave_id>', methods=['POST'])
def cancel_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)

    if leave.final_status == 'Pending':
        db.session.delete(leave)
        db.session.commit()
        flash('Leave request cancelled successfully.', 'success')
    else:
        flash('Only pending leave requests can be cancelled.', 'warning')

    return redirect(url_for('stud.student_dashboard'))  # Replace with your actual view name
