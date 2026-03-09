from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()


class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    roll_no = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    strike_count = db.Column(db.Integer, default=0)
    is_blocked = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default="student")

    def get_id(self):
        return f"s_{self.id}"


class Staff(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    department = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)

    def get_id(self):
        return f"f_{self.id}"


class Grievance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    text = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(10), nullable=True)
    route_to = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_abusive = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(30), default="Pending Approval")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    yes_votes = db.Column(db.Integer, default=0)
    no_votes = db.Column(db.Integer, default=0)

    forwarded_to = db.Column(db.String(100), nullable=True)
    action_by = db.Column(db.String(100), nullable=True)
    action_note = db.Column(db.Text, nullable=True)
    action_at = db.Column(db.DateTime, nullable=True)

    assigned_to_staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    assigned_staff = db.relationship("Staff", backref="assigned_grievances")

    student = db.relationship("Student", backref="grievances")


# ─── COMMUNITY ────────────────────────────────────────────

class CommunityPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=False)
    upvotes = db.Column(db.Integer, default=0)
    is_resolved = db.Column(db.Boolean, default=False)

    student = db.relationship("Student", backref="posts")
    replies = db.relationship("CommunityReply", backref="post",
                               lazy=True, cascade="all, delete-orphan")


class CommunityReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("community_post.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=False)
    upvotes = db.Column(db.Integer, default=0)

    student = db.relationship("Student", backref="replies")


class PostUpvote(db.Model):
    __tablename__ = "post_upvotes"
    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey("community_post.id"), nullable=False)   # ✅ fixed
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)          # ✅ fixed

    __table_args__ = (db.UniqueConstraint("post_id", "student_id"),)


class ReplyUpvote(db.Model):
    __tablename__ = "reply_upvotes"
    id         = db.Column(db.Integer, primary_key=True)
    reply_id   = db.Column(db.Integer, db.ForeignKey("community_reply.id"), nullable=False)  # ✅ fixed
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)          # ✅ fixed

    __table_args__ = (db.UniqueConstraint("reply_id", "student_id"),)
