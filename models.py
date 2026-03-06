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
    role = db.Column(db.String(20), default="student")  # student / coordinator / admin

class Grievance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    text = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(10), nullable=True)      # High / Medium
    route_to = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)         # Gemini-generated summary
    is_abusive = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(30), default="Pending Approval")
    # Pending Approval → Approved → In Progress → Resolved / Rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    yes_votes = db.Column(db.Integer, default=0)
    no_votes = db.Column(db.Integer, default=0)

    student = db.relationship("Student", backref="grievances")
