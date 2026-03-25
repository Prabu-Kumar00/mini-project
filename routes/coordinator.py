from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Grievance, Staff
from email_helper import send_grievance_update
from datetime import datetime
from functools import wraps

coordinator = Blueprint("coordinator", __name__)


# ─── STAFF FINDER ───
def find_staff_for_grievance(route_to, student_dept):
    route = (route_to or "").strip().lower()
    print(f"🔍 route_to='{route_to}' | normalized='{route}'")

    # ── 1. GRC — check FIRST before HOD fallback ──
    if any(k in route for k in ["grievance redressal", "grc", "no response",
                                  "not resolved", "escalat", "no action"]):
        staff = Staff.query.filter_by(role="head", department="GRC").first()
        print(f"   GRC → {staff}")
        if staff: return staff

    # ── 2. HOD (e.g. "CSE HOD", "ECE HOD") ──
    if "hod" in route:
        dept = route.replace("hod", "").strip().upper()
        if not dept:
            dept = student_dept
        staff = Staff.query.filter_by(role="hod", department=dept).first()
        print(f"   HOD: dept={dept} → {staff}")
        if staff: return staff

    # ── 3. Librarian → role="head", dept="Library" ──
    if "librar" in route:
        staff = Staff.query.filter_by(role="head", department="Library").first()
        print(f"   Librarian → {staff}")
        if staff: return staff

    # ── 4. Hostel Warden → role="hostel_warden" ──
    if "hostel" in route or "warden" in route:
        staff = Staff.query.filter_by(role="hostel_warden").first()
        print(f"   Hostel → {staff}")
        if staff: return staff

    # ── 5. COE → role="hod", dept="COE" ──
    if "controller" in route or "examination" in route or "coe" in route:
        staff = Staff.query.filter_by(role="hod", department="COE").first()
        print(f"   COE → {staff}")
        if staff: return staff

    # ── 6. Computer Maintenance Cell → role="hod", dept="CMC" ──
    if "computer maintenance" in route or "cmc" in route or "computer lab" in route:
        staff = Staff.query.filter_by(role="hod", department="CMC").first()
        print(f"   CMC → {staff}")
        if staff: return staff

    # ── 7. Anti Drug → role="head", dept="AntiDrug" ──
    if "drug" in route:
        staff = Staff.query.filter_by(role="head", department="AntiDrug").first()
        print(f"   AntiDrug → {staff}")
        if staff: return staff

    # ── 8. Anti Ragging → role="head", dept="AntiRagging" ──
    if "ragging" in route:
        staff = Staff.query.filter_by(role="head", department="AntiRagging").first()
        print(f"   AntiRagging → {staff}")
        if staff: return staff

    # ── 9. Discipline → role="discipline" ──
    if "discipline" in route or "welfare" in route:
        staff = Staff.query.filter_by(role="discipline").first()
        print(f"   Discipline → {staff}")
        if staff: return staff

    # ── 10. Research → role="hod", dept="Research" ──
    if "research" in route:
        staff = Staff.query.filter_by(role="hod", department="Research").first()
        print(f"   Research → {staff}")
        if staff: return staff

    # ── 11. Book Depot → role="head", dept="BookDepot" ──
    if "book depot" in route or "depot" in route:
        staff = Staff.query.filter_by(role="head", department="BookDepot").first()
        print(f"   BookDepot → {staff}")
        if staff: return staff

    # ── 12. WEC / ICC → role="head", dept="WEC" ──
    if "women" in route or "wec" in route or "icc" in route or "complaint" in route:
        staff = Staff.query.filter_by(role="head", department="WEC").first()
        print(f"   WEC → {staff}")
        if staff: return staff

    # ── 13. Student Affairs / SAC → role="hod", dept="SAC" ──
    if "student affairs" in route or "sac" in route or "sports" in route or "cultural" in route:
        staff = Staff.query.filter_by(role="hod", department="SAC").first()
        print(f"   SAC → {staff}")
        if staff: return staff

    # ── 14. Admin Office → role="admin" ──
    if "admin" in route or "maintenance" in route or "canteen" in route or "infrastructure" in route:
        staff = Staff.query.filter_by(role="admin").first()
        print(f"   Admin → {staff}")
        if staff: return staff

    # ── 15. Fallback → student's own dept HOD ──
    staff = Staff.query.filter_by(role="hod", department=student_dept).first()
    print(f"   Fallback HOD: dept={student_dept} → {staff}")
    if staff: return staff

    # ── 16. Last resort → Admin ──
    staff = Staff.query.filter_by(role="admin").first()
    print(f"   Last resort Admin → {staff}")
    return staff


# ─── ROLE GUARD ───
def coordinator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "coordinator":
            flash("Access denied. Coordinators only.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─── DASHBOARD ───
@coordinator.route("/coordinator")
@login_required
@coordinator_required
def dashboard():
    grievances = Grievance.query.order_by(Grievance.submitted_at.desc()).all()
    return render_template("coordinator/dashboard.html", grievances=grievances)


# ─── ACTION ───
@coordinator.route("/coordinator/action/<int:grievance_id>", methods=["POST"])
@login_required
@coordinator_required
def action(grievance_id):
    g        = Grievance.query.get_or_404(grievance_id)
    decision = request.form.get("decision")
    reason   = request.form.get("reason", "")
    student  = g.student

    if decision == "forward":
        assigned_staff = find_staff_for_grievance(
            g.route_to,
            student.department
        )

        g.status               = "Approved"
        g.forwarded_to         = assigned_staff.name if assigned_staff else g.route_to
        g.assigned_to_staff_id = assigned_staff.id   if assigned_staff else None
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
        flash(f"✅ Grievance forwarded to {g.forwarded_to}. Student notified.", "success")

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
