from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

profile_bp = Blueprint("profile", __name__)   # ✅ name must be profile_bp


@profile_bp.route("/profile")
@login_required
def view_profile():
    return render_template("profile.html")


@profile_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    name  = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name:
        flash("Name cannot be empty.", "danger")
        return redirect(url_for("profile.view_profile"))

    current_user.name  = name
    current_user.phone = phone
    current_user.name_updated = True
    db.session.commit()
    flash("✅ Profile updated successfully!", "success")
    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    old_pw  = request.form.get("old_password")
    new_pw  = request.form.get("new_password")
    confirm = request.form.get("confirm_password")

    if not check_password_hash(current_user.password, old_pw):
        flash("❌ Current password is incorrect.", "danger")
        return redirect(url_for("profile.view_profile"))

    if len(new_pw) < 6:
        flash("❌ New password must be at least 6 characters.", "danger")
        return redirect(url_for("profile.view_profile"))

    if new_pw != confirm:
        flash("❌ Passwords do not match.", "danger")
        return redirect(url_for("profile.view_profile"))

    current_user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash("✅ Password changed successfully!", "success")
    return redirect(url_for("profile.view_profile"))
