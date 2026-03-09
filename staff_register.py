from app import app
from models import db, Staff
from werkzeug.security import generate_password_hash

with app.app_context():
    staff_accounts = [
        # ── Coordinator ──────────────────────────────
        Staff(name="Dr. Meena", email="coordinator@srec.ac.in",
              password=generate_password_hash("coord123"),
              role="coordinator", department=None),

        # ── Admin ────────────────────────────────────
        Staff(name="Dr. Rajesh Kumar", email="admin@srec.ac.in",
              password=generate_password_hash("admin123"),
              role="admin", department=None),

        # ── Discipline ───────────────────────────────
        Staff(name="Dr. Priya", email="discipline@srec.ac.in",
              password=generate_password_hash("disc123"),
              role="discipline", department=None),

        # ── HODs (one per department) ─────────────────
        Staff(name="Dr. Suresh", email="hod.cse@srec.ac.in",
              password=generate_password_hash("hod123"),
              role="hod", department="CSE"),

        Staff(name="Dr. Kavitha", email="hod.ece@srec.ac.in",
              password=generate_password_hash("hod123"),
              role="hod", department="ECE"),

        Staff(name="Dr. Anand", email="hod.mech@srec.ac.in",
              password=generate_password_hash("hod123"),
              role="hod", department="MECH"),

        Staff(name="Dr. Lakshmi", email="hod.civil@srec.ac.in",
              password=generate_password_hash("hod123"),
              role="hod", department="CIVIL"),

        Staff(name="Dr. Venkat", email="hod.eee@srec.ac.in",
              password=generate_password_hash("hod123"),
              role="hod", department="EEE"),

        # ── COE ──────────────────────────────────────
        Staff(name="Dr. Muthukumar", email="coe@srec.ac.in",
              password=generate_password_hash("coe123"),
              role="coe", department=None),

        # ── Accounts ─────────────────────────────────
        Staff(name="Mr. Senthil", email="accounts@srec.ac.in",
              password=generate_password_hash("acc123"),
              role="accounts", department=None),

        # ── Hostel Warden ─────────────────────────────
        Staff(name="Mr. Balu", email="hostel@srec.ac.in",
              password=generate_password_hash("hostel123"),
              role="hostel_warden", department=None),

        # ── Security ──────────────────────────────────
        Staff(name="Mr. Rajan", email="security@srec.ac.in",
              password=generate_password_hash("sec123"),
              role="security", department=None),

        # ── Maintenance ───────────────────────────────
        Staff(name="Mr. Kumar", email="maintenance@srec.ac.in",
              password=generate_password_hash("maint123"),
              role="maintenance", department=None),
    ]

    for s in staff_accounts:
        existing = Staff.query.filter_by(email=s.email).first()
        if not existing:
            db.session.add(s)
            print(f"✅ Created: {s.name} ({s.role})")
        else:
            print(f"⏭️  Skipped (already exists): {s.email}")

    db.session.commit()
    print("\n✅ All staff accounts ready!")
