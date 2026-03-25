from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE staff 
            ADD COLUMN IF NOT EXISTS name_updated BOOLEAN DEFAULT FALSE
        """))
        conn.execute(text("""
            ALTER TABLE grievance 
            ADD COLUMN IF NOT EXISTS assigned_to_staff_id INTEGER DEFAULT NULL
        """))
        conn.commit()
    print("✅ Both columns added successfully!")
