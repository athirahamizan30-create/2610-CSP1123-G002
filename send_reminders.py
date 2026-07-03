import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app import create_app, db
from app import Reminder, JobDate, User, Notification

app = create_app()

def send_reminders():

    with app.app_context():

        MY = ZoneInfo("Asia/Kuala_Lumpur")

        print("CRON STARTED")

        now = datetime.now(timezone.utc)

        reminders = Reminder.query.filter(Reminder.reminder_date <= now).all()

        print("REMINDERS FOUND:", len(reminders))

        for reminder in reminders:

            user = db.session.get(User, reminder.user_id)

            if not user:
                continue

            job_date = JobDate.query.filter_by(job_id=reminder.job_id).first()

            already_sent = Notification.query.filter_by(
                reminder_id=reminder.id,
                status="sent"
            ).first()

            if already_sent:
                continue

            if reminder.reminder_type == "applied":
                timing_text = "Your application has been submitted successfully."
                email_body_text = f"""
Hello {user.username},

{timing_text}

{reminder.message}
"""
            else:
                timing_text = {
                    "2_days_before": "This event is coming up in 2 days.",
                    "1_hour_before": "This event starts in 1 hour."
                }.get(reminder.reminder_type, "You have an upcoming event.")

                email_body_text = f"""
Hello {user.username},

{timing_text}

{reminder.message}

Event Date:
{job_date.date_value.astimezone(MY).strftime('%d %b %Y %I:%M %p')}
"""

            print("TRY SEND TO:", user.email)

            try:
                msg = MIMEText(email_body_text)
                msg["Subject"] = "CareerTrack Reminder"
                msg["From"] = os.getenv("MAIL_USERNAME")
                msg["To"] = user.email

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()

                    server.login(
                        os.getenv("MAIL_USERNAME"),
                        os.getenv("MAIL_PASSWORD")
                    )

                    server.send_message(msg)

                print("Email sent:", user.email)

            except Exception as e:
                print("EMAIL FAILED:", str(e))
                continue

            notification = Notification(
                reminder_id=reminder.id,
                sent_at=datetime.now(timezone.utc),
                status="sent",
                email=user.email
            )

            db.session.add(notification)

            db.session.commit()


if __name__ == "__main__":
    send_reminders()