from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from flask_mail import Message
from models import db, Grievance, Student

admin = Blueprint("admin", __name__)

@admin.route("/admin")
@login_required
def dashboard():
    grievances = Grievance.query.filter(
        Grievance.status.in_(["Approved", "In Progress", "Resolved"])
    ).order_by(Grievance.submitted_at.desc()).all()
    return render_template("admin/dashboard.html", grievances=grievances)


@admin.route("/admin/update/<int:grievance_id>", methods=["POST"])
@login_required
def update_status(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    g.status = request.form.get("status")
    db.session.commit()
    flash("Status updated successfully!", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/admin/reply/<int:grievance_id>", methods=["POST"])
@login_required
def reply_student(grievance_id):
    g = Grievance.query.get_or_404(grievance_id)
    custom_msg = request.form.get("reply_message", "")

    try:
        mail = current_app.extensions['mail']
        msg = Message(
            subject=f"Update on Your Grievance — {g.category}",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[g.student.email]
        )
        msg.body = f"""Dear {g.student.name},

Your grievance regarding "{g.category}" has been reviewed.

Status: {g.status}
Message from Admin: {custom_msg}

If you have further concerns, please resubmit through the portal.

Regards,
Admin Team — GrievanceAI
"""
        mail.send(msg)
        flash(f"Email sent to {g.student.name} successfully! ✅", "success")

    except Exception as e:
        print(f"MAIL ERROR: {str(e)}")
        flash(f"Failed to send email: {str(e)}", "danger")

    return redirect(url_for("admin.dashboard"))
