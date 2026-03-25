from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Grievance, Announcement
from gemini_helper import analyze_text, analyze_image  # ✅ fixed import
from email_helper import send_high_priority_alert
from functools import wraps
from datetime import datetime
import os

student = Blueprint("student", __name__)
UPLOAD_FOLDER = "static/uploads"


# ── Role Guard ──
def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(current_user, 'roll_no'):
            flash("Access denied. Students only.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── DASHBOARD ──
@student.route("/dashboard", methods=["GET", "POST"])
@login_required
@student_required
def dashboard():
    if request.method == "POST":
        input_type = request.form.get("input_type")
        result = None
        filename = None

        if input_type == "text":
            text = request.form.get("grievance_text", "").strip()
            if not text:
                flash("Please enter your grievance.", "warning")
                return redirect(url_for("student.dashboard"))
            result = analyze_text(text, current_user.department)
        else:
            file = request.files.get("grievance_image")
            if not file or file.filename == "":
                flash("Please upload an image.", "warning")
                return redirect(url_for("student.dashboard"))
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            result = analyze_image(filepath, current_user.department)

        # ✅ REMOVED: abusive content blocking — faculty can see all student details

        # ── Fix {dept} placeholder ──
        route_to = result.get("route_to", "Admin Office")
        if "{dept}" in route_to:
            route_to = route_to.replace("{dept}", current_user.department)

        grievance = Grievance(
            student_id  = current_user.id,
            text        = request.form.get("grievance_text"),
            image_path  = filename,
            category    = result.get("category"),
            priority    = result.get("priority"),
            route_to    = route_to,
            description = result.get("description"),
            is_abusive  = False
        )
        db.session.add(grievance)
        db.session.commit()

        if grievance.priority == "High":
            send_high_priority_alert(grievance, current_user)

        flash("✅ Grievance submitted successfully!", "success")
        return redirect(url_for("student.status"))

    # ── GET: Load dashboard ──
    now = datetime.utcnow()

    announcements = Announcement.query.filter(
        Announcement.expires_at > now,
        db.or_(
            Announcement.target_dept == None,
            Announcement.target_dept == current_user.department
        )
    ).order_by(Announcement.posted_at.desc()).all()

    dismissed = session.get('dismissed_announcements', [])
    popup_announcements = [
        ann for ann in announcements
        if str(ann.id) not in dismissed
    ]

    return render_template(
        "student/dashboard.html",
        student             = current_user,
        grievances          = Grievance.query.filter_by(
                                  student_id=current_user.id
                              ).order_by(Grievance.submitted_at.desc()).all(),
        announcements       = announcements,
        popup_announcements = popup_announcements,
        now                 = now
    )


# ── STATUS ──
@student.route("/status")
@login_required
@student_required
def status():
    grievances = Grievance.query.filter_by(
        student_id=current_user.id
    ).order_by(Grievance.submitted_at.desc()).all()
    return render_template("student/status.html", grievances=grievances)


# ── VOTE ──
@student.route("/vote/<int:grievance_id>", methods=["POST"])
@login_required
@student_required
def vote(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    if request.form.get("vote") == "yes":
        g.yes_votes += 1
    else:
        g.no_votes += 1
    db.session.commit()
    return redirect(url_for("student.status"))


# ── EDIT GRIEVANCE ──
@student.route("/edit/<int:grievance_id>", methods=["GET", "POST"])
@login_required
@student_required
def edit_grievance(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)

    if g.student_id != current_user.id or g.status != "Pending Approval":
        flash("You cannot edit this grievance.", "danger")
        return redirect(url_for("student.status"))

    if request.method == "POST":
        new_text = request.form.get("grievance_text", "").strip()
        if new_text:
            result = analyze_text(new_text, current_user.department)

            route_to = result.get("route_to", "Admin Office")
            if "{dept}" in route_to:
                route_to = route_to.replace("{dept}", current_user.department)

            g.text        = new_text
            g.category    = result.get("category")
            g.priority    = result.get("priority")
            g.route_to    = route_to
            g.description = result.get("description")
            g.is_abusive  = False  # ✅ always false
            db.session.commit()
            flash("✅ Grievance updated successfully!", "success")
        return redirect(url_for("student.status"))

    return render_template("student/edit.html", grievance=g)


# ── DELETE GRIEVANCE ──
@student.route("/delete/<int:grievance_id>", methods=["POST"])
@login_required
@student_required
def delete_grievance(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)

    if g.student_id != current_user.id or g.status != "Pending Approval":
        flash("You cannot delete this grievance.", "danger")
        return redirect(url_for("student.status"))

    db.session.delete(g)
    db.session.commit()
    flash("🗑️ Grievance deleted.", "success")
    return redirect(url_for("student.status"))
