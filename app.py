from flask import Flask, render_template   # ✅ added render_template
from flask_login import LoginManager
from flask_mail import Mail
from models import db, Student, Staff
from routes.auth import auth
from routes.student import student
from routes.coordinator import coordinator
from routes.admin import admin
from routes.community import community
from dotenv import load_dotenv
load_dotenv() 
import config, os

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

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("s_"):
        return db.session.get(Student, int(user_id[2:]))
    elif user_id.startswith("f_"):
        return db.session.get(Staff, int(user_id[2:]))
    return None

# ✅ Homepage route — serves index.html
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

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
