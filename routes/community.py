from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, CommunityPost, CommunityReply, PostUpvote, ReplyUpvote
from datetime import datetime

community = Blueprint("community", __name__)


@community.route("/community")
@login_required
def index():
    category = request.args.get("category", "all")
    search = request.args.get("search", "")
    query = CommunityPost.query
    if category != "all":
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            CommunityPost.title.ilike(f"%{search}%") |
            CommunityPost.content.ilike(f"%{search}%")
        )
    posts = query.order_by(CommunityPost.created_at.desc()).all()
    return render_template("community/index.html", posts=posts,
                           category=category, search=search)


@community.route("/community/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "General")
        is_anonymous = request.form.get("is_anonymous") == "on"
        if not title or not content:
            flash("Title and content are required!", "danger")
            return redirect(url_for("community.new_post"))
        post = CommunityPost(
            title=title, content=content, category=category,
            student_id=current_user.id, is_anonymous=is_anonymous
        )
        db.session.add(post)
        db.session.commit()
        flash("✅ Post created successfully!", "success")
        return redirect(url_for("community.index"))
    return render_template("community/new_post.html")


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
            content=content, post_id=post_id,
            student_id=current_user.id, is_anonymous=is_anonymous
        )
        db.session.add(reply)
        db.session.commit()
        flash("✅ Reply added!", "success")
        return redirect(url_for("community.view_post", post_id=post_id))

    # Pass already-upvoted post IDs and reply IDs so template can grey out buttons
    upvoted_post = PostUpvote.query.filter_by(
        post_id=post_id, student_id=current_user.id
    ).first()
    upvoted_reply_ids = {
        u.reply_id for u in ReplyUpvote.query.filter_by(student_id=current_user.id).all()
    }
    return render_template("community/view_post.html", post=post,
                           upvoted_post=upvoted_post,
                           upvoted_reply_ids=upvoted_reply_ids)


@community.route("/community/upvote/<int:post_id>", methods=["POST"])
@login_required
def upvote_post(post_id):
    post = CommunityPost.query.get_or_404(post_id)
    already = PostUpvote.query.filter_by(
        post_id=post_id, student_id=current_user.id
    ).first()
    if already:
        flash("⚠️ You already upvoted this post!", "warning")
    else:
        db.session.add(PostUpvote(post_id=post_id, student_id=current_user.id))
        post.upvotes += 1
        db.session.commit()
    return redirect(url_for("community.view_post", post_id=post_id))


@community.route("/community/upvote/reply/<int:reply_id>", methods=["POST"])
@login_required
def upvote_reply(reply_id):
    reply = CommunityReply.query.get_or_404(reply_id)
    already = ReplyUpvote.query.filter_by(
        reply_id=reply_id, student_id=current_user.id
    ).first()
    if already:
        flash("⚠️ You already upvoted this reply!", "warning")
    else:
        db.session.add(ReplyUpvote(reply_id=reply_id, student_id=current_user.id))
        reply.upvotes += 1
        db.session.commit()
    return redirect(url_for("community.view_post", post_id=reply.post_id))


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
