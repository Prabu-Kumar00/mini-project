from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from models import db, Grievance, Student, Staff

admin = Blueprint("admin", __name__)

NON_ACADEMIC_DEPTS = ['Library', 'BookDepot', 'GRC', 'Research']


# ── Role Guard ──
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):

        ALLOWED_ROLES = [
            "admin",
            "hod",
            "head",
            "discipline",
            "hostel_warden",
            "accounts",
            "coe"
        ]

        if not current_user.is_authenticated or current_user.role not in ALLOWED_ROLES:
            flash("Access denied.", "danger")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated

# ── DASHBOARD ──
@admin.route("/admin")
@login_required
@admin_required
def dashboard():

    # If user is admin → see everything
    if current_user.role == "admin":
        grievances = Grievance.query.filter(
            Grievance.status.in_(["Approved", "In Progress", "Resolved"])
        ).order_by(Grievance.submitted_at.desc()).all()

    # All department heads / committees → see only assigned grievances
    else:
        grievances = Grievance.query.filter(
            Grievance.status.in_(["Approved", "In Progress", "Resolved"]),
            Grievance.assigned_to_staff_id == current_user.id
        ).order_by(Grievance.submitted_at.desc()).all()

    return render_template(
        "admin/dashboard.html",
        grievances=grievances
    )


# ── UPDATE STATUS ──
@admin.route("/admin/update/<int:grievance_id>", methods=["POST"])
@login_required
@admin_required
def update_status(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    g.status = request.form.get("status")
    db.session.commit()
    flash("Status updated successfully!", "success")
    return redirect(url_for("admin.dashboard"))


# ── REPLY TO STUDENT ──
@admin.route("/admin/reply/<int:grievance_id>", methods=["POST"])
@login_required
@admin_required
def reply_student(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    custom_msg = request.form.get("reply_message", "")

    try:
        mail = current_app.extensions['mail']
        msg = Message(
            subject=f"Update on Your Grievance — {g.category}",
            sender=current_app.config['MAIL_ADDRESS'],
            recipients=[g.student.email]
        )
        msg.body = f"""Dear {g.student.name},

Your grievance regarding "{g.category}" has been reviewed.

Status: {g.status}
Message from {current_user.name}: {custom_msg}

If you have further concerns, please resubmit through the portal.

Regards,
{current_user.name}
{current_user.role.upper()} — GrievanceAI
Sri Ramakrishna Engineering College
"""
        mail.send(msg)
        flash(f"Email sent to {g.student.name} successfully! ✅", "success")

    except Exception as e:
        print(f"MAIL ERROR: {str(e)}")
        flash(f"Failed to send email: {str(e)}", "danger")

    return redirect(url_for("admin.dashboard"))


# ── MANAGE STAFF ──
@admin.route("/admin/staff")
@login_required
@admin_required
def manage_staff():
    # TEMP DEBUG
    print(f">>> dept='{current_user.department}' | can_add={current_user.department not in NON_ACADEMIC_DEPTS}")
    if current_user.role.lower() == "hod":
        staff_list = Staff.query.filter_by(
            role="coordinator",
            department=current_user.department
        ).all()
        can_add = current_user.department not in NON_ACADEMIC_DEPTS
    else:
        staff_list = Staff.query.filter(
            Staff.role.in_(["coordinator", "hod", "coe",
                            "accounts", "hostel_warden", "discipline"])
        ).order_by(Staff.role, Staff.department).all()
        can_add = True

    # Pass list of students in dept so HOD can assign them during coordinator creation
    dept_students = []
    if current_user.role.lower() == "hod":
        dept_students = Student.query.filter_by(
            department=current_user.department
        ).order_by(Student.roll_no).all()

    return render_template(
        "admin/manage_staff.html",
        staff_list=staff_list,
        can_add=can_add,
        dept_students=dept_students
    )


# ── ADD STAFF ──
@admin.route("/admin/staff/add", methods=["POST"])
@login_required
@admin_required
def add_staff():
    if current_user.role == "hod" and current_user.department in NON_ACADEMIC_DEPTS:
        flash("⚠️ Your department does not have Academic Coordinators.", "warning")
        return redirect(url_for("admin.manage_staff"))

    name     = request.form.get("name")
    email    = request.form.get("email")
    password = request.form.get("password", "srec@2024")

    if current_user.role == "hod":
        role       = "coordinator"
        department = current_user.department
    else:
        role       = request.form.get("role", "coordinator")
        department = request.form.get("department")

    existing = Staff.query.filter_by(email=email).first()
    if existing:
        flash(f"⚠️ {email} already exists!", "warning")
        return redirect(url_for("admin.manage_staff"))

    staff = Staff(
        name       = name,
        email      = email,
        password   = generate_password_hash(password),
        role       = role,
        department = department,
        is_active  = True
    )
    db.session.add(staff)
    db.session.commit()

    # ─── Assign selected students as tutees ───
    student_ids = request.form.getlist("student_ids")
    if student_ids:
        for sid in student_ids:
            s = Student.query.get(int(sid))
            if s:
                s.tutor_id = staff.id
        db.session.commit()

    assigned_count = len(student_ids)
    flash(f"✅ {name} added! Email: {email} | Password: {password}" +
          (f" | {assigned_count} student(s) assigned." if assigned_count else ""), "success")
    return redirect(url_for("admin.manage_staff"))


# ── DELETE STAFF ──
@admin.route("/admin/staff/delete/<int:staff_id>", methods=["POST"])
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    flash(f"🗑️ {staff.name} removed.", "warning")
    return redirect(url_for("admin.manage_staff"))


# ── ASSIGN STUDENTS TO COORDINATOR ──
@admin.route("/admin/staff/<int:staff_id>/assign", methods=["GET", "POST"])
@login_required
@admin_required
def assign_students(staff_id):
    staff = Staff.query.get_or_404(staff_id)

    if request.method == "POST":
        # Unassign all students currently linked to this coordinator
        Student.query.filter_by(tutor_id=staff_id).update({"tutor_id": None})
        # Assign newly selected students
        student_ids = request.form.getlist("student_ids")
        for sid in student_ids:
            s = Student.query.get(int(sid))
            if s:
                s.tutor_id = staff_id
        db.session.commit()
        flash(f"✅ Students re-assigned to {staff.name} successfully.", "success")
        return redirect(url_for("admin.manage_staff"))

    # GET: show the assignment page
    dept_students = Student.query.filter_by(
        department=staff.department
    ).order_by(Student.roll_no).all()
    assigned_ids = {s.id for s in Student.query.filter_by(tutor_id=staff_id).all()}

    return render_template(
        "admin/assign_students.html",
        staff=staff,
        dept_students=dept_students,
        assigned_ids=assigned_ids
    )
