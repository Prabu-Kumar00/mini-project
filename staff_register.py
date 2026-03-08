from app import app
from models import db, Staff
from werkzeug.security import generate_password_hash

with app.app_context():
    staff_accounts = [
        Staff(name="Dr. Meena", email="coordinator@srec.ac.in",
              password=generate_password_hash("coord123"), role="coordinator"),
        Staff(name="Dr. Rajesh Kumar", email="admin@srec.ac.in",
              password=generate_password_hash("admin123"), role="admin"),
        Staff(name="Dr. Priya", email="discipline@srec.ac.in",
              password=generate_password_hash("disc123"), role="discipline"),
    ]

    for s in staff_accounts:
        db.session.add(s)
    db.session.commit()
    print("✅ Staff accounts created successfully!")