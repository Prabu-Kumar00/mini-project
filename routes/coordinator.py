from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Grievance

coordinator = Blueprint("coordinator", __name__)

@coordinator.route("/coordinator")
@login_required
def panel():
    grievances = Grievance.query.filter_by(status="Pending Approval").all()
    return render_template("coordinator/panel.html", grievances=grievances)

@coordinator.route("/coordinator/action/<int:grievance_id>", methods=["POST"])
@login_required
def action(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    decision = request.form.get("decision")
    g.status = "Approved" if decision == "accept" else "Rejected"
    db.session.commit()
    return redirect(url_for("coordinator.panel"))
