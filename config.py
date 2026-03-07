import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
SQLALCHEMY_DATABASE_URI = "sqlite:///grievance.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UPLOAD_FOLDER = "static/uploads"
COLLEGE_DOMAIN = "@srec.ac.in"
MAIL_ADDRESS = os.getenv("MAIL_ADDRESS")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
