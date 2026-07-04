from app import create_app, send_reminders

app = create_app()

if __name__ == "__main__":
    send_reminders(app)