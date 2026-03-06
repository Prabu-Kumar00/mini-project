import smtplib
from email.mime.text import MIMEText
from config import MAIL_ADDRESS, MAIL_PASSWORD

def send_high_priority_alert(grievance, student):
    subject = f"[HIGH PRIORITY] New Grievance - {grievance.category}"
    body = f"""
A high priority grievance has been submitted.

Student: {student.name} ({student.roll_no})
Department: {student.department}
Category: {grievance.category}
Routed To: {grievance.route_to}

Description: {grievance.description}

Please log in to the admin dashboard to review.
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = MAIL_ADDRESS
    msg["To"] = MAIL_ADDRESS  # Replace with authority email lookup

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_ADDRESS, MAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Email failed: {e}")
