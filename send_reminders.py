from app import create_app, send_reminders

app = create_app()

send_reminders(app)