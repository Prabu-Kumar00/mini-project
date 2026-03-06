from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from models import db, Grievance, Student

admin = Blueprint("admin", __name__)

@admin.route("/admin")
@login_required
def dashboard():
    grievances = Grievance.query.filter_by(status="Approved").order_by(Grievance.submitted_at.desc()).all()
    return render_template("admin/dashboard.html", grievances=grievances)

@admin.route("/admin/update/<int:grievance_id>", methods=["POST"])
@login_required
def update_status(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    g.status = request.form.get("status")
    db.session.commit()
    return redirect(url_for("admin.dashboard"))
