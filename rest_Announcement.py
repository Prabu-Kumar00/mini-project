from app import app
from models import db, Announcement

with app.app_context():
    Announcement.__table__.drop(db.engine)
    db.create_all()
    print("✅ Done!")
