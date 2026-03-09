from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Grievance, Staff
from email_helper import send_grievance_update
from datetime import datetime

coordinator = Blueprint("coordinator", __name__)

# ─── ROLE MAPPING — Gemini route_to → Staff.role in DB ────
ROLE_MAP = {
    "hod":           "hod",
    "coe":           "coe",
    "accounts":      "accounts",
    "admin":         "admin",
    "security":      "security",
    "maintenance":   "maintenance",
    "hostel_warden": "hostel_warden",
    "discipline":    "discipline",
}


def find_staff_for_grievance(route_to, student_dept):
    """Find the right Staff member based on route_to and student's department."""
    role = ROLE_MAP.get(route_to.lower().strip(), "admin")

    # HOD → match by department first
    if role == "hod":
        staff = Staff.query.filter_by(
            role="hod",
            department=student_dept,
            is_active=True
        ).first()
        if staff:
            return staff

    # All other roles → find by role only
    staff = Staff.query.filter_by(role=role, is_active=True).first()

    # Final fallback → admin
    if not staff:
        staff = Staff.query.filter_by(role="admin", is_active=True).first()

    return staff


# ─── ROLE GUARD ───────────────────────────────────────────
def coordinator_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "coordinator":
            flash("Access denied. Coordinators only.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─── COORDINATOR PANEL ────────────────────────────────────
@coordinator.route("/coordinator")
@login_required
@coordinator_required
def panel():
    grievances = Grievance.query.order_by(Grievance.submitted_at.desc()).all()
    return render_template("coordinator/dashboard.html", grievances=grievances)


# ─── COORDINATOR ACTION ───────────────────────────────────
@coordinator.route("/coordinator/action/<int:grievance_id>", methods=["POST"])
@login_required
@coordinator_required
def action(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    decision = request.form.get("decision")
    reason   = request.form.get("reason", "")
    student  = g.student

    if decision == "forward":
        # ✅ Find correct Staff based on AI route + student department
        assigned_staff = find_staff_for_grievance(
            g.route_to or "admin",
            student.department
        )

        g.status               = "Approved"
        g.forwarded_to         = assigned_staff.name if assigned_staff else (g.route_to or "Admin")
        g.assigned_to_staff_id = assigned_staff.id if assigned_staff else None
        g.action_by            = current_user.name
        g.action_note          = f"Forwarded to {g.forwarded_to}"
        g.action_at            = datetime.utcnow()
        db.session.commit()

        send_grievance_update(
            student_email   = student.email,
            student_name    = student.name,
            staff_name      = current_user.name,
            grievance_title = g.description or (g.text[:60] if g.text else "Grievance"),
            action          = "forwarded",
            forwarded_to    = g.forwarded_to
        )
        flash(f"✅ Grievance forwarded to {g.forwarded_to} ({(g.route_to or '').upper()}). Student notified.", "success")

    elif decision == "decline":
        g.status      = "Rejected"
        g.action_by   = current_user.name
        g.action_note = reason
        g.action_at   = datetime.utcnow()
        db.session.commit()

        send_grievance_update(
            student_email   = student.email,
            student_name    = student.name,
            staff_name      = current_user.name,
            grievance_title = g.description or (g.text[:60] if g.text else "Grievance"),
            action          = "declined",
            reason          = reason
        )
        flash("Grievance declined. Student notified via email.", "warning")

    return redirect(url_for("coordinator.dashboard"))
