from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Student, Staff
from config import COLLEGE_DOMAIN
import re

auth = Blueprint("auth", __name__)

def valid_email(email):
    return email.endswith(COLLEGE_DOMAIN)


# ─── INDEX ────────────────────────────────────────────────
@auth.route("/")
def index():
    return render_template("index.html")


# ─── STUDENT LOGIN ────────────────────────────────────────
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = Student.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_blocked:
                flash("Your account has been blocked due to misuse.", "danger")
                return redirect(url_for("auth.login"))
            login_user(user)
            return redirect(url_for("student.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html")


# ─── COORDINATOR LOGIN ────────────────────────────────────
@auth.route("/coordinator/login", methods=["GET", "POST"])
def coordinator_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # ✅ Query Staff model with role=coordinator
        staff = Staff.query.filter_by(email=email, role="coordinator").first()
        if staff and check_password_hash(staff.password, password):
            if not staff.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login") + "?role=coordinator")
            login_user(staff)
            return redirect(url_for("coordinator.dashboard"))
        flash("Invalid coordinator credentials.", "danger")
        return redirect(url_for("auth.login") + "?role=coordinator")
    return redirect(url_for("auth.login") + "?role=coordinator")


# ─── ADMIN / HOD LOGIN ────────────────────────────────────
@auth.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # ✅ Query Staff model with role=admin
        staff = Staff.query.filter_by(email=email, role="admin").first()
        if staff and check_password_hash(staff.password, password):
            if not staff.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login") + "?role=admin")
            login_user(staff)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid admin credentials.", "danger")
        return redirect(url_for("auth.login") + "?role=admin")
    return redirect(url_for("auth.login") + "?role=admin")


# ─── DISCIPLINE LOGIN ─────────────────────────────────────
@auth.route("/discipline/login", methods=["GET", "POST"])
def discipline_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # ✅ Query Staff model with role=discipline
        staff = Staff.query.filter_by(email=email, role="discipline").first()
        if staff and check_password_hash(staff.password, password):
            if not staff.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login") + "?role=discipline")
            login_user(staff)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials.", "danger")
        return redirect(url_for("auth.login") + "?role=discipline")
    return redirect(url_for("auth.login") + "?role=discipline")


# ─── STUDENT REGISTER ─────────────────────────────────────
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        if not valid_email(email):
            flash(f"Please use your college email ({COLLEGE_DOMAIN})", "danger")
            return redirect(url_for("auth.register"))
        if Student.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register"))
        new_student = Student(
            name=request.form.get("name"),
            email=email,
            roll_no=request.form.get("roll_no"),
            department=request.form.get("department"),
            class_name=request.form.get("class_name"),
            section=request.form.get("section"),
            password=generate_password_hash(request.form.get("password"))
        )
        db.session.add(new_student)
        db.session.commit()
        flash("Registered successfully! Please login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


# ─── LOGOUT ───────────────────────────────────────────────
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
