from app import app
from models import db, Staff
from werkzeug.security import generate_password_hash

with app.app_context():
    staff_accounts = [

        # ── Academic Coordinators ──
        Staff(name='Lavanya Gangadharan',       email='lavanya.gangadharan@srec.ac.in',        password=generate_password_hash('coord123'), role='coordinator', department='BME'),
        Staff(name='Radhika Senthil',           email='radhika.senthil@srec.ac.in',            password=generate_password_hash('coord123'), role='coordinator', department='BME'),
        Staff(name='Dhiviyalakshmi',            email='dhiviyalakshmi.lakshmipathy@srec.ac.in',password=generate_password_hash('coord123'), role='coordinator', department='BME'),

        # ── HODs — All Departments ──
        # email format: faculty-dept@srec.ac.in → routes to that dept HOD
        Staff(name='HOD CSE',                   email='faculty-cse@srec.ac.in',                password=generate_password_hash('hod123'),   role='hod', department='CSE'),
        Staff(name='HOD ECE',                   email='faculty-ece@srec.ac.in',                password=generate_password_hash('hod123'),   role='hod', department='ECE'),
        Staff(name='HOD EEE',                   email='faculty-eee@srec.ac.in',                password=generate_password_hash('hod123'),   role='hod', department='EEE'),
        Staff(name='HOD Mechanical',            email='faculty-mech@srec.ac.in',               password=generate_password_hash('hod123'),   role='hod', department='MECH'),
        Staff(name='HOD IT',                    email='faculty-it@srec.ac.in',                 password=generate_password_hash('hod123'),   role='hod', department='IT'),
        Staff(name='HOD EIE',                   email='faculty-eie@srec.ac.in',                password=generate_password_hash('hod123'),   role='hod', department='EIE'),
        Staff(name='HOD Biomedical',            email='faculty-bme@srec.ac.in',                password=generate_password_hash('hod123'),   role='hod', department='BME'),
        Staff(name='HOD Civil',                 email='faculty-civil@srec.ac.in',              password=generate_password_hash('hod123'),   role='hod', department='CIVIL'),
        Staff(name='HOD Aeronautical',          email='faculty-aero@srec.ac.in',               password=generate_password_hash('hod123'),   role='hod', department='AERO'),
        Staff(name='HOD Robotics & Automation', email='faculty-ra@srec.ac.in',                 password=generate_password_hash('hod123'),   role='hod', department='RA'),
        Staff(name='HOD AIDS',                  email='faculty-aids@srec.ac.in',               password=generate_password_hash('hod123'),   role='hod', department='AIDS'),
        Staff(name='HOD MTech CSE',             email='faculty-pg@srec.ac.in',                 password=generate_password_hash('hod123'),   role='hod', department='PG'),
        Staff(name='HOD Management Studies',    email='faculty-mba@srec.ac.in',                password=generate_password_hash('hod123'),   role='hod', department='MBA'),
        Staff(name='HOD Nano Science',          email='faculty-nano@srec.ac.in',               password=generate_password_hash('hod123'),   role='hod', department='NANO'),

        # ── Red Cells — Special Departments ──
        Staff(name='Librarian',                 email='librarian@srec.ac.in',                  password=generate_password_hash('lib123'),    role='hod', department='Library'),
        Staff(name='Admin Office',              email='adminoffice@srec.ac.in',                password=generate_password_hash('admin123'),  role='admin', department=None),
        Staff(name='CMC',                       email='cmc@srec.ac.in',                        password=generate_password_hash('cmc123'),    role='hod', department='CMC'),
        Staff(name='COE Office',                email='coe@srec.ac.in',                        password=generate_password_hash('coe123'),    role='hod', department='COE'),
        Staff(name='Book Depot',                email='bookdepot@srec.ac.in',                  password=generate_password_hash('book123'),   role='hod', department='BookDepot'),
        Staff(name='Anti Drug Committee',       email='antidrug@srec.ac.in',                   password=generate_password_hash('drug123'),   role='discipline', department=None),
        Staff(name='Anti Ragging Committee',    email='antiragging@srec.ac.in',                password=generate_password_hash('ragging123'),role='discipline', department=None),
        Staff(name='SREC COIN',                 email='coin@srec.ac.in',                       password=generate_password_hash('coin123'),   role='hod', department='COIN'),
        Staff(name='ICC',                       email='icc@srec.ac.in',                        password=generate_password_hash('icc123'),    role='discipline', department=None),
        Staff(name='WEC',                       email='wec@srec.ac.in',                        password=generate_password_hash('wec123'),    role='discipline', department=None),
        Staff(name='SAC',                       email='sac@srec.ac.in',                        password=generate_password_hash('sac123'),    role='hod', department='SAC'),
        Staff(name='Grievance Redressal Committee', email='grc@srec.ac.in',                   password=generate_password_hash('grc123'),    role='hod', department='GRC'),
        Staff(name='Research Committee',        email='researchcommittee@srec.ac.in',          password=generate_password_hash('res123'),    role='hod', department='Research'),
        Staff(name='Discipline & Welfare',      email='discipline@srec.ac.in',                 password=generate_password_hash('disc123'),   role='discipline', department=None),
        Staff(name='NSS',                       email='nss@srec.ac.in',                        password=generate_password_hash('nss123'),    role='hod', department='NSS'),
        Staff(name='Hostel Warden',             email='hostel@srec.ac.in',                     password=generate_password_hash('hostel123'), role='hod', department='Hostel'),
    ]

    for s in staff_accounts:
        existing = Staff.query.filter_by(email=s.email).first()
        if not existing:
            db.session.add(s)
            print(f"✅ Created: {s.name} ({s.role}) — {s.email}")
        else:
            print(f"⏭️  Skipped: {s.email}")

    db.session.commit()
    print("\n🎉 All staff accounts ready in Neon DB!")
