from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Grievance
from email_helper import send_grievance_update
from datetime import datetime

coordinator = Blueprint("coordinator", __name__)


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
def dashboard():
    grievances = Grievance.query.filter(
        Grievance.status.in_(["Pending Approval", "Approved", "Rejected"])
    ).order_by(Grievance.submitted_at.desc()).all()
    return render_template("coordinator/dashboard.html", grievances=grievances)


# ─── COORDINATOR ACTION ───────────────────────────────────
@coordinator.route("/coordinator/action/<int:grievance_id>", methods=["POST"])
@login_required
@coordinator_required
def action(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    decision    = request.form.get("decision")       # "forward" / "decline"
    reason      = request.form.get("reason", "")     # decline reason
    forward_to  = request.form.get("forward_to", "") # HOD / Admin / Discipline

    student = g.student  # get related student

    if decision == "forward":
        # ✅ Update grievance
        g.status       = "Approved"
        g.forwarded_to = forward_to
        g.action_by    = current_user.name
        g.action_note  = f"Forwarded to {forward_to}"
        g.action_at    = datetime.utcnow()
        db.session.commit()

        # ✅ Send email to student
        send_grievance_update(
            student_email  = student.email,
            student_name   = student.name,
            staff_name     = current_user.name,
            grievance_title= g.description or g.text[:60],
            action         = "forwarded",
            forwarded_to   = forward_to
        )
        flash(f"Grievance forwarded to {forward_to}. Student notified via email.", "success")

    elif decision == "decline":
        # ✅ Update grievance
        g.status    = "Declined"
        g.action_by = current_user.name
        g.action_note = reason
        g.action_at = datetime.utcnow()
        db.session.commit()

        # ✅ Send email to student
        send_grievance_update(
            student_email  = student.email,
            student_name   = student.name,
            staff_name     = current_user.name,
            grievance_title= g.description or g.text[:60],
            action         = "declined",
            reason         = reason
        )
        flash("Grievance declined. Student notified via email.", "warning")

    return redirect(url_for("coordinator.dashboard"))
