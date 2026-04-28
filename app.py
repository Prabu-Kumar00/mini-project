from flask import Flask, render_template   
from flask_login import LoginManager
from flask_mail import Mail
from models import db, Student, Staff
from routes.auth import auth
from routes.student import student
from routes.coordinator import coordinator
from routes.admin import admin
from routes.community import community
from routes.profile import profile_bp
from models import db, Student, Staff, Announcement
from dotenv import load_dotenv
import config, os


load_dotenv() 


app = Flask(__name__)
app.config.from_object(config)
os.makedirs("static/uploads", exist_ok=True)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'grievanceaisrec@gmail.com'
app.config['MAIL_PASSWORD'] = 'yjzzujisfyprmdbf'
app.config['MAIL_DEFAULT_SENDER'] = 'grievanceaisrec@gmail.com'

mail = Mail(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# ─── ANNOUNCEMENTS CONTEXT PROCESSOR ───
@app.context_processor
def inject_announcements():

    def get_announcements():
        from flask_login import current_user
        from models import Announcement
        from sqlalchemy import or_

        if not current_user.is_authenticated:
            return []

        # Only show to students
        if current_user.role == "student":
            anns = Announcement.query.filter(
                Announcement.is_active == True,
                or_(
                    Announcement.target_dept == "ALL",
                    Announcement.target_dept == current_user.department
                )
            ).order_by(Announcement.posted_at.desc()).limit(3).all()

            return anns

        return []

    return {"get_announcements": get_announcements}


# ─── FLASK LOGIN USER LOADER ───
@login_manager.user_loader
def load_user(user_id):
    from models import Student, Staff

    if user_id.startswith("s_"):
        return Student.query.get(int(user_id[2:]))

    if user_id.startswith("f_"):
        return Staff.query.get(int(user_id[2:]))

    return None

# ═══ SEO: robots.txt ═══
@app.route("/robots.txt")
def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /dashboard
Disallow: /admin
Disallow: /coordinator
Disallow: /status
Disallow: /profile
Disallow: /test-gemini
Sitemap: https://greivanceinfo.in/sitemap.xml
"""
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}


# ═══ SEO: sitemap.xml ═══
@app.route("/sitemap.xml")
def sitemap_xml():
    from datetime import date
    today = date.today().isoformat()
    base  = "https://greivanceinfo.in"
    pages = [
        {"loc": "/",               "priority": "1.0", "changefreq": "weekly"},
        {"loc": "/login",          "priority": "0.9", "changefreq": "monthly"},
        {"loc": "/register",       "priority": "0.8", "changefreq": "monthly"},
        {"loc": "/forgot-password","priority": "0.4", "changefreq": "yearly"},
    ]
    urls = ""
    for page in pages:
        urls += f"""
  <url>
    <loc>{base}{page['loc']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{page['changefreq']}</changefreq>
    <priority>{page['priority']}</priority>
  </url>"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}
</urlset>"""
    return xml, 200, {"Content-Type": "application/xml"}


# ═══ Homepage route — serves index.html ═══
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/test-gemini")
def test_gemini():
    try:
        from gemini_helper import client
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say hello in one word."
        )
        return f"✅ Gemini working: {response.text}"
    except Exception as e:
        return f"❌ Gemini error: {str(e)}"

app.register_blueprint(auth)
app.register_blueprint(student)
app.register_blueprint(coordinator)
app.register_blueprint(admin)
app.register_blueprint(community)
app.register_blueprint(profile_bp)

with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables verified.")
    except Exception as e:
        print(f"⚠️  db.create_all() failed (DB may be cold-starting): {e}")

if __name__ == "__main__":
    app.run(debug=True)
