from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Grievance
from gemini_helper import analyze_text, analyze_image
from email_helper import send_high_priority_alert
import os

student = Blueprint("student", __name__)
UPLOAD_FOLDER = "static/uploads"

@student.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        if current_user.is_blocked:
            flash("Your account is blocked.", "danger")
            return redirect(url_for("student.dashboard"))

        input_type = request.form.get("input_type")  # "text" or "image"
        result = None

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

        # Handle abusive content
        if result.get("is_abusive"):
            current_user.strike_count += 1
            if current_user.strike_count >= 3:
                current_user.is_blocked = True
                flash("Account blocked due to repeated misuse.", "danger")
            else:
                flash(f"Warning ({current_user.strike_count}/3): Abusive content detected.", "warning")
            db.session.commit()
            return redirect(url_for("student.dashboard"))

        grievance = Grievance(
            student_id=current_user.id,
            text=request.form.get("grievance_text"),
            image_path=filename if input_type == "image" else None,
            category=result.get("category"),
            priority=result.get("priority"),
            route_to=result.get("route_to"),
            description=result.get("description"),
            is_abusive=False
        )
        db.session.add(grievance)
        db.session.commit()

        if grievance.priority == "High":
            send_high_priority_alert(grievance, current_user)

        flash("Grievance submitted successfully!", "success")
        return redirect(url_for("student.status"))

    return render_template("student/dashboard.html", student=current_user)

@student.route("/status")
@login_required
def status():
    grievances = Grievance.query.filter_by(student_id=current_user.id).order_by(Grievance.submitted_at.desc()).all()
    return render_template("student/status.html", grievances=grievances)

@student.route("/vote/<int:grievance_id>", methods=["POST"])
@login_required
def vote(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    if request.form.get("vote") == "yes":
        g.yes_votes += 1
    else:
        g.no_votes += 1
    db.session.commit()
    return redirect(url_for("student.status"))
