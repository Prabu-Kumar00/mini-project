from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, CommunityPost, CommunityReply, PostUpvote, ReplyUpvote, Announcement
from datetime import datetime

community = Blueprint("community", __name__)


# ───────────────── COMMUNITY FEED ─────────────────

@community.route("/community")
@login_required
def index():

    category = request.args.get("category", "all")
    search   = request.args.get("search", "")

    query = CommunityPost.query

    if category != "all":
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            CommunityPost.title.ilike(f"%{search}%") |
            CommunityPost.content.ilike(f"%{search}%")
        )

    posts = query.order_by(CommunityPost.created_at.desc()).all()

    return render_template(
        "community/index.html",
        posts=posts,
        category=category,
        search=search
    )


# ───────────────── CREATE POST ─────────────────

@community.route("/community/new", methods=["GET", "POST"])
@login_required
def new_post():

    if request.method == "POST":

        title   = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "General")

        is_anonymous = request.form.get("is_anonymous") == "on"

        if not title or not content:
            flash("Title and content are required!", "danger")
            return redirect(url_for("community.new_post"))

        post = CommunityPost(
            title=title,
            content=content,
            category=category,
            student_id=current_user.id,
            is_anonymous=is_anonymous
        )

        db.session.add(post)
        db.session.commit()

        flash("✅ Post created successfully!", "success")

        return redirect(url_for("community.index"))

    return render_template("community/new_post.html")


# ───────────────── VIEW POST ─────────────────

@community.route("/community/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def view_post(post_id):

    post = CommunityPost.query.get_or_404(post_id)

    if request.method == "POST":

        content = request.form.get("content", "").strip()
        is_anonymous = request.form.get("is_anonymous") == "on"

        if not content:
            flash("Reply cannot be empty!", "danger")
            return redirect(url_for("community.view_post", post_id=post_id))

        reply = CommunityReply(
            content=content,
            post_id=post_id,
            student_id=current_user.id,
            is_anonymous=is_anonymous
        )

        db.session.add(reply)
        db.session.commit()

        flash("✅ Reply added!", "success")

        return redirect(url_for("community.view_post", post_id=post_id))


    upvoted_post = PostUpvote.query.filter_by(
        post_id=post_id,
        student_id=current_user.id
    ).first()

    upvoted_reply_ids = {
        u.reply_id for u in ReplyUpvote.query.filter_by(
            student_id=current_user.id
        ).all()
    }

    return render_template(
        "community/view_post.html",
        post=post,
        upvoted_post=upvoted_post,
        upvoted_reply_ids=upvoted_reply_ids
    )


# ───────────────── POST UPVOTE ─────────────────

@community.route("/post/<int:post_id>/upvote", methods=["POST"])
@login_required
def upvote_post(post_id):

    if not hasattr(current_user, "department") or current_user.role != "student":
        flash("Only students can upvote posts.", "warning")
        return redirect(url_for("community.index"))

    post = CommunityPost.query.get_or_404(post_id)

    existing = PostUpvote.query.filter_by(
        post_id=post_id,
        student_id=current_user.id
    ).first()

    # Toggle vote
    if existing:
        db.session.delete(existing)
        post.upvotes -= 1
        db.session.commit()

        flash("Upvote removed.", "info")

        return redirect(url_for("community.index"))

    vote = PostUpvote(
        post_id=post_id,
        student_id=current_user.id
    )

    db.session.add(vote)

    post.upvotes += 1

    db.session.commit()

    flash("Post upvoted!", "success")

    return redirect(url_for("community.index"))


# ───────────────── REPLY UPVOTE ─────────────────

@community.route("/community/upvote/reply/<int:reply_id>", methods=["POST"])
@login_required
def upvote_reply(reply_id):

    reply = CommunityReply.query.get_or_404(reply_id)

    existing = ReplyUpvote.query.filter_by(
        reply_id=reply_id,
        student_id=current_user.id
    ).first()

    if existing:
        flash("⚠️ You already upvoted this reply!", "warning")
        return redirect(url_for("community.view_post", post_id=reply.post_id))

    vote = ReplyUpvote(
        reply_id=reply_id,
        student_id=current_user.id
    )

    db.session.add(vote)

    reply.upvotes += 1

    db.session.commit()

    return redirect(url_for("community.view_post", post_id=reply.post_id))


# ───────────────── RESOLVE POST ─────────────────

@community.route("/community/resolve/<int:post_id>", methods=["POST"])
@login_required
def resolve_post(post_id):

    post = CommunityPost.query.get_or_404(post_id)

    if post.student_id != current_user.id:
        flash("You can only resolve your own posts!", "danger")
        return redirect(url_for("community.view_post", post_id=post_id))

    post.is_resolved = True

    db.session.commit()

    flash("✅ Post marked as resolved!", "success")

    return redirect(url_for("community.view_post", post_id=post_id))


# ───────────────── DELETE POST ─────────────────

@community.route("/community/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):

    post = CommunityPost.query.get_or_404(post_id)

    if post.student_id != current_user.id:
        flash("You can only delete your own posts!", "danger")
        return redirect(url_for("community.index"))

    db.session.delete(post)

    db.session.commit()

    flash("Post deleted.", "info")

    return redirect(url_for("community.index"))


# ───────────────── ANNOUNCEMENTS ─────────────────

@community.route("/announcements/new", methods=["GET", "POST"])
@login_required
def new_announcement():

    if current_user.role not in ['admin', 'hod', 'coordinator', 'head', 'hostel_warden']:
        flash("Access denied.", "danger")
        return redirect(url_for("community.index"))

    if request.method == "POST":

        from datetime import timedelta

        title = request.form.get("title", "").strip()
        message = request.form.get("content", "").strip()

        target_dept = request.form.get("department") or None
        is_urgent   = request.form.get("is_urgent") == "on"

        days = int(request.form.get("expires_days", 7))

        if not title or not message:
            flash("Title and content required.", "danger")
            return redirect(url_for("community.new_announcement"))

        ann = Announcement(
            title=title,
            message=message,
            target_dept=target_dept,
            is_urgent=is_urgent,
            author_id=current_user.id,
            expires_at=datetime.utcnow() + timedelta(days=days)
        )

        db.session.add(ann)
        db.session.commit()

        flash("✅ Announcement posted!", "success")

        return redirect(url_for("admin.dashboard"))

    return render_template("community/new_announcement.html")


# ───────────────── DELETE ANNOUNCEMENT ─────────────────

@community.route("/announcements/delete/<int:ann_id>", methods=["POST"])
@login_required
def delete_announcement(ann_id):

    ann = Announcement.query.get_or_404(ann_id)

    db.session.delete(ann)

    db.session.commit()

    flash("🗑️ Announcement removed.", "warning")

    return redirect(url_for("admin.dashboard"))