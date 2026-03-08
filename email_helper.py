import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import MAIL_ADDRESS, MAIL_PASSWORD


# ─── EXISTING FUNCTION (unchanged) ───────────────────────
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
    msg["To"] = MAIL_ADDRESS

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_ADDRESS, MAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Email failed: {e}")


# ─── NEW FUNCTION (add below) ─────────────────────────────
def send_grievance_update(student_email, student_name,
                           staff_name, grievance_title,
                           action, reason=None, forwarded_to=None):

    subject_map = {
        "forwarded":  "Your Grievance Has Been Forwarded — GrievanceAI",
        "declined":   "Your Grievance Has Been Declined — GrievanceAI",
        "resolved":   "Your Grievance Has Been Resolved — GrievanceAI",
        "inprogress": "Your Grievance Is In Progress — GrievanceAI",
    }

    body_map = {
        "forwarded": f"""
        <p>Dear <b>{student_name}</b>,</p>
        <p>Your grievance titled <b>"{grievance_title}"</b> has been reviewed by
        <b>Coordinator {staff_name}</b> and forwarded to <b>{forwarded_to}</b> for further action.</p>
        <p>Status: <b>Forwarded ➡️</b></p>
        <p>You will receive another update once it is resolved.</p>
        """,
        "declined": f"""
        <p>Dear <b>{student_name}</b>,</p>
        <p>Your grievance titled <b>"{grievance_title}"</b> has been reviewed and
        <b>declined</b> by Coordinator <b>{staff_name}</b>.</p>
        <p>Reason: <b>{reason or 'Not specified'}</b></p>
        <p>Status: <b>Declined ❌</b></p>
        <p>If you believe this is wrong, please resubmit with more details.</p>
        """,
        "resolved": f"""
        <p>Dear <b>{student_name}</b>,</p>
        <p>Great news! Your grievance titled <b>"{grievance_title}"</b>
        has been <b>resolved</b> by <b>{staff_name}</b>.</p>
        <p>Resolution: <b>{reason or 'Issue has been addressed'}</b></p>
        <p>Status: <b>Resolved ✅</b></p>
        """,
        "inprogress": f"""
        <p>Dear <b>{student_name}</b>,</p>
        <p>Your grievance titled <b>"{grievance_title}"</b> is currently
        <b>being reviewed</b> by <b>{staff_name}</b>.</p>
        <p>Status: <b>In Progress 🔄</b></p>
        <p>You will receive another update soon.</p>
        """,
    }

    subject = subject_map.get(action, "Grievance Update — GrievanceAI")
    body    = body_map.get(action, "<p>Your grievance status has been updated.</p>")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="color:#4f8ef7;margin:0">🛡️ GrievanceAI</h2>
        <p style="color:#a0aec0;margin:4px 0 0">SRCC College Grievance Management System</p>
      </div>
      <div style="background:#f9f9f9;padding:24px;border-radius:0 0 8px 8px;border:1px solid #e0e0e0">
        {body}
        <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0">
        <p style="color:#999;font-size:12px">This is an automated message from GrievanceAI.
        Please do not reply to this email.</p>
      </div>
    </body></html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = MAIL_ADDRESS
        msg["To"]      = student_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_ADDRESS, MAIL_PASSWORD)
            server.sendmail(MAIL_ADDRESS, student_email, msg.as_string())

        print(f"✅ Email sent to {student_email}")
        return True

    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        return False
