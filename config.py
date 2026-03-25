import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')   # ✅ Neon DB
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,     # ✅ fixes connection drops
    "pool_recycle": 280,
    "pool_size": 5,
    "max_overflow": 2,
}
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
UPLOAD_FOLDER = 'static/uploads'
COLLEGE_DOMAIN = 'srec.ac.in'
MAIL_ADDRESS = os.getenv('MAIL_ADDRESS')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
