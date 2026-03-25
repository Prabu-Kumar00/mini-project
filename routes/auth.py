from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Student, Staff
from config import COLLEGE_DOMAIN
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message

auth = Blueprint("auth", __name__)

def valid_email(email):
    return email.endswith(COLLEGE_DOMAIN)

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


# ─── INDEX ────────────────────────────────────────────────
@auth.route("/")
def index():
    return render_template("index.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        # 🚨 FIRST check if this email belongs to staff
        staff = Staff.query.filter_by(email=email).first()
        if staff:
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        # Now check student table
        user = Student.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            if user.is_blocked:
                flash("Your account has been blocked due to misuse.", "danger")
                return render_template("auth/login.html")

            login_user(user)
            return redirect(url_for("student.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")
# ─── COORDINATOR LOGIN ────────────────────────────────────
@auth.route("/coordinator/login", methods=["GET", "POST"])
def coordinator_login():
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")
        staff    = Staff.query.filter_by(email=email, role="coordinator").first()
        if staff and check_password_hash(staff.password, password):
            if not staff.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login") + "?role=coordinator")
            login_user(staff)
            return redirect(url_for("coordinator.dashboard"))
        flash("Invalid coordinator credentials.", "danger")
        return redirect(url_for("auth.login") + "?role=coordinator")
    return redirect(url_for("auth.login") + "?role=coordinator")


# ─── ADMIN / HOD / DISCIPLINE LOGIN ──────────────────────
@auth.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        staff = Staff.query.filter_by(email=email).first()

        if staff and check_password_hash(staff.password, password):

            # account disabled
            if not staff.is_active:
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("auth.login") + "?role=admin")

            # 🚨 BLOCK coordinator login here
            if staff.role == "coordinator":
                flash("Invalid credentials.", "danger")
                return redirect(url_for("auth.login") + "?role=admin")

            login_user(staff)

            return redirect(url_for("admin.dashboard"))

        flash("Invalid credentials.", "danger")
        return redirect(url_for("auth.login") + "?role=admin")

    return redirect(url_for("auth.login") + "?role=admin")
# ─── DISCIPLINE LOGIN ─────────────────────────────────────
@auth.route("/discipline/login", methods=["GET", "POST"])
def discipline_login():
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")
        staff    = Staff.query.filter_by(email=email, role="discipline").first()
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
            name       = request.form.get("name"),
            email      = email,
            roll_no    = request.form.get("roll_no"),
            department = request.form.get("department"),
            class_name = request.form.get("class_name"),
            section    = request.form.get("section"),
            password   = generate_password_hash(request.form.get("password"))
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


# ─── FORGOT PASSWORD ──────────────────────────────────────
@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        # ✅ Check both Student and Staff tables
        user = Student.query.filter_by(email=email).first() or \
               Staff.query.filter_by(email=email).first()

        if user:
            s     = get_serializer()
            token = s.dumps(email, salt="password-reset")
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            try:
                mail = current_app.extensions['mail']
                msg  = Message(
                    subject  = "Reset Your GrievanceAI Password",
                    sender   = current_app.config['MAIL_ADDRESS'],
                    recipients = [email]
                )
                msg.body = f"""Hello,

You requested a password reset for your GrievanceAI account.

Click the link below to reset your password (valid for 30 minutes):

{reset_url}

If you did not request this, please ignore this email.

Regards,
GrievanceAI — Sri Ramakrishna Engineering College
"""
                mail.send(msg)
            except Exception as e:
                print(f"MAIL ERROR: {e}")

        # ✅ Always show same message — prevents email enumeration
        flash("If that email exists, a reset link has been sent. Check your inbox.", "info")
        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/forgot_password.html")


# ─── RESET PASSWORD ───────────────────────────────────────
@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = get_serializer()
    try:
        # ✅ Token expires after 30 minutes
        email = s.loads(token, salt="password-reset", max_age=1800)
    except SignatureExpired:
        flash("⏰ Reset link has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("❌ Invalid reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_pw  = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if len(new_pw) < 6:
            flash("❌ Password must be at least 6 characters.", "danger")
            return redirect(request.url)

        if new_pw != confirm:
            flash("❌ Passwords do not match.", "danger")
            return redirect(request.url)

        # ✅ Update in whichever table the user exists
        user = Student.query.filter_by(email=email).first() or \
               Staff.query.filter_by(email=email).first()

        if user:
            user.password = generate_password_hash(new_pw)
            db.session.commit()
            flash("✅ Password reset successfully! Please login.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
