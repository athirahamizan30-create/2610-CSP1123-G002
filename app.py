from flask import Flask, render_template, url_for, request, redirect, flash, session, jsonify, make_response
import requests
import re, uuid, os, secrets, logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime, timezone
from config import Config
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, and_ , or_
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from typing import Dict
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from collections import defaultdict
import resend
import json
import urllib.request


db= SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
bcrypt = Bcrypt()
socketio = SocketIO()
load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")


logger = logging.getLogger(__name__)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    image_file= db.Column(db.String(100), nullable=False, default='default.jpg')
    full_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    about_me = db.Column(db.Text, nullable=True)


    password_reset_ids = db.relationship(
        "PasswordResetId",
        backref="user",
        cascade="all, delete-orphan"
    )

class PasswordResetId(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    reset_id = db.Column(
        db.String(36),
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def is_expired(self):
        now = datetime.now(timezone.utc)
        base_time = self.created_at
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=timezone.utc)
        expires_at = base_time + timedelta(minutes=10)
        return now > expires_at
    
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)    

class NewJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(255))
    job_position = db.Column(db.String(255))
    location = db.Column(db.String(255))
    job_status = db.Column(db.String(50))
    job_type = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dates = db.relationship('JobDate', backref='job', cascade="all, delete")
    reminders = db.relationship('Reminder', backref='job', cascade="all, delete-orphan", passive_deletes=True)

class JobDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('new_job.id'))
    date_type = db.Column(db.String(50))
    date_value = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reminder(db.Model):
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('new_job.id', ondelete='CASCADE'), nullable=False)

    reminder_date = db.Column(db.DateTime, nullable=False)

    reminder_type = db.Column(db.String(50))
    message = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Reminder {self.reminder_date}>"

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    
    full_name = StringField('Full Name')
    phone_number = StringField('Phone Number')
    about_me = TextAreaField('About Me')

    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80),nullable=False)
    room = db.Column(db.String(150),nullable=False)
    message = db.Column(db.Text,nullable=False)
    is_private = db.Column(db.Boolean,default=False)
    timestamp = db.Column(db.DateTime,default=datetime.utcnow)

class ChatRoom(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    reminder_id = db.Column(
        db.Integer,
        db.ForeignKey('reminders.id'),
        nullable=False
    )

    sent_at = db.Column(db.DateTime)

    status = db.Column(
        db.String(20),
        default='pending'
    )

    email = db.Column(db.String(120))

    error_message = db.Column(db.Text)

def send_reminders(app):
    with app.app_context():

        MY = ZoneInfo("Asia/Kuala_Lumpur")
        now = datetime.now(MY)

        print("NOW:", now)

        reminders = Reminder.query.filter(Reminder.reminder_date <= now).all()
        
        all_reminders = Reminder.query.all()
        for r in all_reminders:
            print("DB:", r.reminder_date)

        print("FOUND:", reminders)

        for reminder in reminders:

            if reminder.reminder_type == "applied":
                timing_text = "Your application has been submitted successfully."

            elif reminder.reminder_type == "2_days_before":
                timing_text = "This event is coming up in 2 days."

            elif reminder.reminder_type == "1_hour_before":
                timing_text = "This event starts in 1 hour."

            else:
                timing_text = "You have an upcoming event."

            job_date = JobDate.query.filter_by(job_id=reminder.job_id).first()

            already_sent = Notification.query.filter_by(
                reminder_id=reminder.id,
                status="sent"
            ).first()

            if already_sent:
                continue

            user = db.session.get(User, reminder.user_id)

            msg = Message(
                subject='Reminder Notification',
                sender=app.config['MAIL_USERNAME'],
                recipients=[user.email]
            )

            if reminder.reminder_type == "applied":

                msg.body = f"""
            Hello {user.username},

            {timing_text}

            {reminder.message}
            """

            else:

                msg.body = f"""
            Hello {user.username},

            {timing_text}

            {reminder.message}

            Event Date:
            {job_date.date_value.strftime('%d %b %Y %I:%M %p')}
            """
            print("TRY SEND TO:", user.email)

            mail.send(msg)
            notification = Notification(
                reminder_id=reminder.id,
                sent_at=datetime.now(),
                status="sent",
                email=user.email
            )

            db.session.add(notification)

            if reminder.reminder_type == "applied":
                db.session.delete(reminder)

            db.session.commit()

def create_app():
    app = Flask(__name__)
    load_dotenv()

    app.config.from_object(Config)
    bcrypt.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secretley')
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://athirah:Tiya071!@localhost/CareerTrack_Database"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=15)
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    profile_pics_folder = os.path.join(app.config['UPLOAD_FOLDER'],'profile_pics')
    os.makedirs(profile_pics_folder, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    mail.init_app(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"),
        logger=False,
        engineio_logger=False
    )

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():

        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        query = NewJob.query.filter_by(user_id=current_user.id)

        if search:
            query = query.filter(
                or_(
                    NewJob.company_name.ilike(f"%{search}%"),
                    NewJob.job_position.ilike(f"%{search}%"),
                    NewJob.location.ilike(f"%{search}%"),
                    NewJob.job_status.ilike(f"%{search}%")
                )
            )

        if status:
            query = query.filter(NewJob.job_status == status)

        jobs = query.all()

        full_time = [job for job in jobs if job.job_type == "Full-Time"]
        part_time = [job for job in jobs if job.job_type == "Part-Time"]
        intern = [job for job in jobs if job.job_type == "Intern/Trainee"]

        job_date = {}

        for job in jobs:
            job_date[job.id] = [
                {
                    "date_type": d.date_type,
                    "date_value": d.date_value.strftime("%Y-%m-%dT%H:%M")
                }
                for d in job.dates
            ]

        profile_image = url_for('static', filename='uploads/profile_pics/' + current_user.image_file)

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            full_time=full_time,
            part_time=part_time,
            intern=intern,
            job_dates=job_date,
            image_file=profile_image,
        )
    
    @app.route('/register', methods=["GET", "POST"])
    def register():
        errors = []

        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            email = (request.form.get("email")or "").strip()
            password = request.form.get("password")or ""
            confirm = request.form.get("confirm_password")or ""

            if not (3 <= len(username) <= 80):
                errors.append("Username must be between 3 and 80 characters")

            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                errors.append("Please enter a valid email address")

            if len(password) < 6:
                errors.append("Password needs to be atleast 6 characters")

            if password != confirm:
                errors.append("Password don't match")

            if not errors:
                
                try:
                    pw_hash = generate_password_hash(password)
                    user = User(username=username, email=email, password_hash=pw_hash)
                    db.session.add(user)
                    db.session.commit()
                    return redirect(url_for('index'))
                except IntegrityError:
                    db.session.rollback()
                    errors.append("that username or email is already registered")
            if errors:
                return render_template("register.html", errors=errors)
            return f"Received data - {email}"
        
        return render_template('register.html', errors=errors)

    @app.route('/login', methods=["POST", "GET"])
    def login():
        errors = []

        if request.method == "POST":
            email = (request.form.get("email") or "").strip()
            password = request.form.get("password") or ""

            if not email:
                errors.append("Email is required")

            if not password:
                errors.append("Password is required")

            user = None

            if not errors:
                user = User.query.filter_by(email=email).first()

            if not user or not check_password_hash(user.password_hash, password):
                errors.append("Invalid password or email")

            else:

                remember_me = request.form.get("remember") == "1"

                print("Remember value:", request.form.get("remember"))
                print("Remember me:", remember_me)

                login_user(user, remember=remember_me)
                return redirect(url_for("dashboard"))
            

        return render_template('login.html', errors=errors)
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route('/logout')
    def logout():
        logout_user()
        response = make_response(redirect(url_for("index")))
        response.delete_cookie("remember_token")
        return response
 
    @app.route('/add_job', methods=['POST'])
    @login_required
    def add_job():

        date_types = request.form.getlist('date_type[]')
        date_values = request.form.getlist('date_value[]')

        date_dict = {}

        for dtype, dvalue in zip(date_types, date_values):
            if dtype and dvalue:
                dt = datetime.strptime(dvalue, "%Y-%m-%dT%H:%M")

                if dtype not in date_dict:
                    date_dict[dtype] = dt

        print(date_dict)

        applied = date_dict.get("applied")
        offer = date_dict.get("offer")

        print("Applied =", applied)
        print("Offer =", offer)

        if applied and offer:
            print("Comparison:", offer < applied)

        applied = date_dict.get("applied")
        stage1 = date_dict.get("stage1")
        stage2 = date_dict.get("stage2")
        interview = date_dict.get("interview")
        offer = date_dict.get("offer")
        deadline = date_dict.get("deadline")

        errors = []

        if stage1 and applied and stage1 < applied:
            errors.append("Stage 1 cannot be earlier than Applied")

        if stage2 and stage1 and stage2 < stage1:
            errors.append("Stage 2 cannot be earlier than Stage 1")

        if interview and stage2 and interview < stage2:
            errors.append("Interview cannot be earlier than Stage 2")

        if offer and interview and offer < interview:
            errors.append("Offer cannot be earlier than Interview")

        if offer and applied and offer < applied:
            errors.append("Offer cannot be earlier than Applied")

        if errors:
            flash(" | ".join(errors))
            return redirect(url_for('dashboard'))

        job = NewJob(
            user_id=current_user.id,
            company_name=request.form.get('company_name'),
            job_position=request.form.get('job_position'),
            location=request.form.get('location'),
            job_status=request.form.get('job_status'),
            job_type=request.form.get('job_type')
        )

        db.session.add(job)
        db.session.commit()

        for dtype, dvalue in zip(date_types, date_values):

            if dvalue:
                event_time = datetime.strptime(dvalue, "%Y-%m-%dT%H:%M")

                job_date = JobDate(
                    user_id=current_user.id,
                    job_id=job.id,
                    date_type=dtype,
                    date_value=event_time
                )

                db.session.add(job_date)

                if dtype.lower() == "applied":

                    reminder = Reminder(
                        user_id=current_user.id,
                        job_id=job.id,
                        reminder_date=datetime.now(),
                        reminder_type="applied",
                        message=f"You have applied for {job.job_position} at {job.company_name}"
                    )

                    db.session.add(reminder)

                else:

                    reminder_2days = Reminder(
                        user_id=current_user.id,
                        job_id=job.id,
                        reminder_date=event_time - timedelta(days=2),
                        reminder_type="2_days_before",
                        message=f"{dtype.title()} - {job.job_position} at {job.company_name}"
                    )

                    reminder_1hour = Reminder(
                        user_id=current_user.id,
                        job_id=job.id,
                        reminder_date=event_time - timedelta(hours=1),
                        reminder_type="1_hour_before",
                        message=f"{dtype.title()} - {job.job_position} at {job.company_name}"
                    )

                    db.session.add(reminder_2days)
                    db.session.add(reminder_1hour)

        db.session.commit()

        return redirect(url_for('dashboard'))

    @app.route('/forgot_password', methods=['POST', 'GET'])
    def forgot_password():

        if request.method == 'POST':
            email = request.form.get("email")

            user = db.session.scalar(
                select(User).where(User.email == email)
            )

            if not user:
                flash("No user with that email found", "error")
                return redirect(url_for("forgot_password"))
            
            user.password_reset_ids.clear()

            new_password_reset_id = PasswordResetId(user_id=user.id)
            db.session.add(new_password_reset_id)
            db.session.flush()

            password_reset_link = url_for("reset_password", reset_id=new_password_reset_id.reset_id , _external=True)
            db.session.commit()


            msg = Message(
                subject = "Reset your password",
                recipients = [email],
                body = f"Reset your password using the link below\n\n{password_reset_link}"
            )
            try:
                mail.send(msg)

                context = {
                    "reset_sent": True,
                    "email": email
                }

                return render_template("forgot_password.html", **context)
            except Exception as e:
                print(f"Error: {e}")

        return render_template("forgot_password.html")
    
    @app.route('/reset_password/<reset_id>', methods=['POST', 'GET'])
    def reset_password(reset_id):

            reset_id_object = db.session.scalar(
                select(PasswordResetId).where(PasswordResetId.reset_id == reset_id)
            )

            if not reset_id_object:
                flash('Invalid reset link', "error")
                return redirect(url_for("forgot_password"))
            
            if reset_id_object.is_expired():
                db.session.delete(reset_id_object)
                db.session.commit()

                flash("Expired reset link", "error")
                return redirect(url_for('forgot_password'))
            
            if request.method == "POST":

                password = request.form.get("password")
                confirm_password = request.form.get("confirm_password")

                if len(password) < 5:
                    flash("Password must be at least 5 characters long", "error")
                    return redirect(url_for('reset_password', reset_id=reset_id))
                
                if password != confirm_password:
                    flash("Passwords do not match", "error")
                    return redirect(url_for('reset_password', reset_id=reset_id))
                
                user = User.query.get(reset_id_object.user_id)
                if user:
                    user.password_hash = generate_password_hash(password)
                    db.session.delete(reset_id_object)
                    db.session.commit()
                    flash("Password changed successfully. Login", "success")
                    return redirect(url_for('login'))
                else:
                    flash("User not found", "error")

            return render_template("reset_password.html")
    
    @app.route('/document')
    @login_required
    def document():
        docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.filename.asc()).all()
    
        return render_template("document.html",active_page="document", docs=docs)

    @app.route('/edit_job/<int:id>', methods=['POST'])
    @login_required
    def edit_job(id):

        date_types = request.form.getlist('date_type[]')
        date_values = request.form.getlist('date_value[]')

        date_dict = {}

        for dtype, dvalue in zip(date_types, date_values):
            if dtype and dvalue:
                dt = datetime.strptime(dvalue, "%Y-%m-%dT%H:%M")

                if dtype not in date_dict:
                    date_dict[dtype] = dt

        applied = date_dict.get("applied")
        stage1 = date_dict.get("stage1")
        stage2 = date_dict.get("stage2")
        interview = date_dict.get("interview")
        offer = date_dict.get("offer")
        deadline = date_dict.get("deadline")

        errors = []

        if stage1 and applied and stage1 < applied:
            errors.append("Stage 1 cannot be earlier than Applied")

        if stage2 and stage1 and stage2 < stage1:
            errors.append("Stage 2 cannot be earlier than Stage 1")

        if interview and stage2 and interview < stage2:
            errors.append("Interview cannot be earlier than Stage 2")

        if offer and interview and offer < interview:
            errors.append("Offer cannot be earlier than Interview")

        if offer and applied and offer < applied:
            errors.append("Offer cannot be earlier than Applied")

        if errors:
            flash(" | ".join(errors))
            return redirect(url_for('dashboard'))

        job = NewJob.query.get_or_404(id)

        job.company_name = request.form.get("company_name")
        job.job_position = request.form.get("job_position")
        job.location = request.form.get("location")
        job.job_status = request.form.get("job_status")
        job.job_type = request.form.get("job_type")

        date_types = request.form.getlist("date_type[]")
        date_values = request.form.getlist("date_value[]")

        print(date_types)
        print(date_values)

        JobDate.query.filter_by(job_id=id).delete()

        Reminder.query.filter_by(job_id=id).delete()

        for t, v in zip(date_types, date_values):

            if v:
                parsed_date = datetime.fromisoformat(v)

                new_date = JobDate(
                    job_id=id,
                    user_id=current_user.id,
                    date_type=t,
                    date_value=parsed_date
                )
                db.session.add(new_date)

                if t.lower() == "applied":

                    reminder = Reminder(
                        user_id=current_user.id,
                        job_id=job.id,
                        reminder_date=datetime.now(),
                        reminder_type="applied",
                        message=f"You have applied for {job.job_position} at {job.company_name}"
                    )

                    db.session.add(reminder)

                else:

                    reminder_2days = Reminder(
                        user_id=current_user.id,
                        job_id=job.id,
                        reminder_date=parsed_date - timedelta(days=2),
                        reminder_type="2_days_before",
                        message=f"{t.title()} - {job.job_position} at {job.company_name}"
                    )

                    reminder_1hour = Reminder(
                        user_id=current_user.id,
                        job_id=job.id,
                        reminder_date=parsed_date - timedelta(hours=1),
                        reminder_type="1_hour_before",
                        message=f"{t.title()} - {job.job_position} at {job.company_name}"
                    )

                    db.session.add(reminder_2days)
                    db.session.add(reminder_1hour)

        db.session.commit()

        return redirect(url_for("dashboard"))

    @app.route('/delete_job/<int:id>', methods=['POST'])
    @login_required
    def delete_job(id):
        job = NewJob.query.get_or_404(id)

        Reminder.query.filter_by(job_id=job.id).delete()

        db.session.delete(job)
        db.session.commit()

        return redirect(url_for('dashboard'))

    @app.route('/reminders')
    @login_required
    def reminders():

        events = JobDate.query.filter_by(
            user_id=current_user.id
        ).order_by(JobDate.date_value).all()

        upcoming_events = []
        past_events = []

        now = datetime.now()

        for event in events:

            if event.date_value >= now:
                upcoming_events.append(event)
            else:
                past_events.append(event)

            job = db.session.get(NewJob, event.job_id)

            if job:
                event.title = (
                    f"{event.date_type} - "
                    f"{job.job_position} at "
                    f"{job.company_name}"
                )
            else:
                event.title = event.date_type

        return render_template(
            "reminders.html",
            active_page="reminders",
            upcoming_events=upcoming_events,
            past_events=past_events
        )

    @app.route('/file_upload', methods=["POST"])
    @login_required
    def file_upload():
        file = request.files['file']
        if file:
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)

            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            new_doc = Document(filename=filename, file_path=save_path, user_id=current_user.id)
            db.session.add(new_doc)
            db.session.commit()

            return redirect(url_for('document'))
        return "Upload Failed"

    @app.route('/delete_file/<int:doc_id>')
    @login_required
    def delete_file(doc_id):
        doc = Document.query.get_or_404(doc_id)

        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)

            if os.path.exists(file_path):
                os.remove(file_path)

            db.session.delete(doc)
            db.session.commit()
        
            return redirect(url_for('document')) # Redirect back to your files page

        except Exception as e:
            print(f"Error: {e}")
            return "There was a problem deleting that file."

    @app.route('/statistic')
    def statistic():
        selected_status = request.args.get('status', '').strip()
        date_range = request.args.get('date_range', '').strip()

        cards_query = db.session.query(NewJob.job_status, func.count(NewJob.id)).filter(NewJob.user_id == current_user.id)
        chart_query = db.session.query(NewJob.job_status, func.count(NewJob.id)).filter(NewJob.user_id == current_user.id)

        if date_range in ['7', '30']:
            days_to_subtract = int(date_range)
            date_threshold = datetime.now() - timedelta(days=days_to_subtract)
        
            cards_query = cards_query.filter(NewJob.created_at >= date_threshold)
            chart_query = chart_query.filter(NewJob.created_at >= date_threshold)

        all_results = cards_query.group_by(NewJob.job_status).all()
        stats_dict = {status: count for status, count in all_results}
        total_count = sum(stats_dict.values())

        if selected_status:
            chart_query = chart_query.filter(NewJob.job_status == selected_status)
    
        chart_results = chart_query.group_by(NewJob.job_status).all()

        return render_template(
            'statistic.html', 
            active_page="statistic",
            status_data=chart_results,
            stats=stats_dict,          
            total=total_count)
        
    def save_picture(form_picture):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)

        picture_fn = random_hex + f_ext

        upload_dir = os.path.join(
        app.root_path,
        'static',
        'uploads',
        'profile_pics'
        )

        picture_path = os.path.join(upload_dir, picture_fn)
        form_picture.save(picture_path)

        return picture_fn

    @app.route("/account", methods=["POST", "GET"])
    @login_required
    def account():
        form = UpdateAccountForm()
        if form.validate_on_submit():

            try:    
                if form.picture.data:
                    picture_file = save_picture(form.picture.data)
                    current_user.image_file = picture_file

                current_user.username = form.username.data
                current_user.email = form.email.data
                current_user.full_name = form.full_name.data
                current_user.phone_number = form.phone_number.data
                current_user.about_me = form.about_me.data

                db.session.commit()
                flash("your account has been updated!", 'success')
                return redirect(url_for('account'))

            except Exception as e:
                print("ACCOUNT UPDATE ERROR:", e)
                db.session.rollback()
                raise

        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            form.full_name.data = current_user.full_name 
            form.phone_number.data = current_user.phone_number 
            form.about_me.data = current_user.about_me 

        image_file = url_for('static',filename='uploads/profile_pics/' +current_user.image_file)
        return render_template('account.html',active_page="account", title='Account', image_file=image_file, form=form)

    @app.route("/chat")
    @login_required
    def chat():
        logger.info(f"User {current_user.username} entered the chat session")
        rooms = ChatRoom.query.all()


        return render_template(
            'chat.html',
            active_page="chat",
            username=current_user.username,
            rooms=rooms
        )

    active_users = {}
    @socketio.event
    def connect():
        try:
            if 'username' not in session:
                session['username'] = current_user.username

            active_users[request.sid] = {
                'username':session['username'],
                'connected_at': datetime.now().isoformat()
            }

            unique_users = list(set(
                user['username']
                for user in active_users.values()
            ))

            emit('active_users', {
                'users': unique_users
            }, broadcast=True)

            logger.info({f"User connected {session['username']}"})

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
        
    #disconnect from session
    @socketio.event
    def disconnect():
        try:
            if request.sid in active_users:
                username= active_users[request.sid]['username']
                del active_users[request.sid]

            unique_users = list(set(
                user['username']
                for user in active_users.values()
            ))

            emit('active_users', {
                'users': unique_users
            }, broadcast=True)

            logger.info({f"User disconnected: {'username'}"})

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")

    @socketio.on('join')
    def on_join(data:dict):
        try:
            username = current_user.username
            room = data['room']

            room_exists = (ChatRoom.query.filter_by(name=room).first())
            if not room_exists:
                return
            
            join_room(room)
            active_users[request.sid]['room'] = room

            emit('status', {
                'msg' : f"{username} has joined the room",
                'type' : 'join',
                'timestamp' : datetime.now().isoformat()
            }, room=room)

            logger.info(f"User {username} has joined {room}")

        except Exception as e:
            logger.error(str(e))

    @socketio.on('leave')
    def on_leave(data:dict):
        try:
            username = session['username']
            room = data['room']

            leave_room(room)
            if request.sid in active_users:
                active_users[request.sid].pop('room', None)

            emit('status', {
                    'msg' : f"{username} has left the room",
                    'type' : 'leave',
                    'timestamp' : datetime.now().isoformat()
                }, room=room)

            logger.info(f"User {username} has left the room")

        except Exception as e:
            logger.error(str(e))

    @socketio.on('message')
    def handle_message(data:dict):
        try:
            username = current_user.username
            room = data.get('room', "General")
            msg_type = data.get("type", 'message')
            message = data.get('msg', "").strip()

            if not message:
                return
            timestamp = datetime.now().isoformat()
            
            if msg_type == 'private':
                target_user = data.get('target')
                if not target_user:
                    return

                private_room = create_private_room(
                    username,
                    target_user
                )

                new_message = ChatMessage(sender=username,room=private_room,message=message,is_private=True)

                db.session.add(new_message)
                db.session.commit()

               
                receiver = User.query.filter_by(username=target_user).first()

                is_online = any(user_data["username"] == target_user for user_data in active_users.values())

                if receiver and not is_online:
                    msg = Message( subject="You have a new private message", recipients=[receiver.email])
                    msg.body = f"""
                Hello {receiver.username},
                You have received a new private message from {username}.

                Message:
                "{message}"

                Log in to CareerTrack to reply.

                Regards,
                CareerTrack
                """
                    try:
                        mail.send(msg)
                    except Exception as e:
                        print("Email failed:", e)

                emit('message', {'msg': message,'username': username,'room': private_room,'timestamp': timestamp,'private': True}, room=private_room)

            else:
                room_exists = (ChatRoom.query.filter_by(name=room).first())
                if not room_exists:
                    return
                
                new_message = ChatMessage(sender=username,room=room,message=message,is_private=False)

                db.session.add(new_message)
                db.session.commit()

                emit('message', {
                            'msg': message,
                            'username':username,
                            'room':room,
                            'timestamp':timestamp,
                        }, room=room)
        except Exception as e:
            logger.error(str(e))       

    def create_private_room(user1, user2):
        users = sorted([user1, user2])
        return f"dm_{users[0]}_{users[1]}"    

    @socketio.on('join_private')
    def join_private(data):
        try:
            target_user = data.get('target')

            if not target_user:
                return

            username = current_user.username

            private_room = create_private_room(
                username,
                target_user
            )

            join_room(private_room)

            emit('status', {
                'msg': f"Private chat with {target_user}",
                'type': 'system'
            }, room=request.sid)

        except Exception as e:
            logger.error(str(e))

    @app.route('/get_messages/<room>')
    @login_required
    def get_messages(room):
        messages = ChatMessage.query.filter_by(
            room=room
        ).order_by(ChatMessage.timestamp.asc()).all()

        return {
            "messages": [
                {
                    "sender": msg.sender,
                    "message": msg.message,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ]
        }

    @app.route('/create-room', methods=['POST'])
    @login_required
    def create_room():

        room_name = request.form.get( "room_name").strip()

        if not room_name:
            flash("Room name required","danger")
            return redirect(url_for("chat"))

        existing_room = ( ChatRoom.query.filter_by(name=room_name).first())

        if existing_room:
            flash("Room already exists", "warning")
            return redirect(url_for("chat"))

        new_room = ChatRoom(name=room_name,created_by=current_user.id)
        db.session.add(new_room)
        db.session.commit()

        flash("Chatroom created!","success")
        return redirect(url_for("chat"))

    @app.route('/private_chats')
    @login_required
    def private_chats():

        username = current_user.username
        messages = ChatMessage.query.filter(ChatMessage.is_private == True,ChatMessage.room.contains(username)).all()
        chats = set()

        for msg in messages:
            room_parts = msg.room.replace('dm_','').split('_')
            other_user = (
                room_parts[0]
                if room_parts[1] == username
                else room_parts[1]
            )

            chats.add(other_user)
        return {"chats": list(chats)}

    @app.route('/get_profile/<username>')
    @login_required
    def get_profile(username):

        user = User.query.filter_by(
            username=username
        ).first_or_404()

        image_file = url_for(
            'static',
            filename=f'uploads/profile_pics/{user.image_file}'
        )

        return jsonify({
            "username":
                user.username,

            "full_name":
                user.full_name,

            "email":
                user.email,

            "phone":
                user.phone_number,

            "about_me":
                user.about_me,

            "image":
                image_file
        })
    
    @app.route('/enquiry', methods=['GET', 'POST'])
    def enquiry():
        if request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"success": False, "message": "No data provided"}), 400

                visitor_name = data.get('name')
                visitor_email = data.get('email')
                message_content = data.get('message')

                if not visitor_name or not visitor_email or not message_content:
                    return jsonify({"success": False, "message": "All fields are required."}), 400

                # Safely get your verified email address from the Flask Config object
                recipient_email = app.config.get('MAIL_USERNAME')

                # 1. Fetch and verify the API key string exists
                api_key = os.getenv("BREVO_API_KEY")
                if not api_key:
                    if 'logger' in globals():
                        logger.error("Inquiry failed: BREVO_API_KEY environment variable is missing!")
                    else:
                        print("Inquiry failed: BREVO_API_KEY environment variable is missing!")
                    return jsonify({"success": False, "message": "Server mail configuration error."}), 500

                # --- BREVO HTTP API SENDING VIA BUILT-IN URLLIB ---
                api_url = "https://api.brevo.com/v3/smtp/email"
                
                headers = {
                    "Accept": "application/json",
                    "api-key": api_key,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    # Ensure email matches your authenticated Brevo sender profile
                    "sender": {"name": "CareerTrack Inquiry", "email": recipient_email},
                    "to": [{"email": recipient_email}],
                    "subject": f"New Inquiry from {visitor_name}",
                    "htmlContent": f"""
                    <h3>New Inquiry Received</h3>
                    <p><strong>From:</strong> {visitor_name} ({visitor_email})</p>
                    <p><strong>Message:</strong></p>
                    <p>{message_content}</p>
                    """
                }

                # Convert data to bytes safely
                jsondata = json.dumps(payload).encode('utf-8')
                
                # Build the network request
                req = urllib.request.Request(api_url, data=jsondata, headers=headers, method="POST")
                
                # Execute the request avoiding gevent/eventlet monkey-patches
                with urllib.request.urlopen(req) as response:
                    status_code = response.getcode()
                    
                if status_code in [200, 201]:
                    return jsonify({"success": True, "message": "Inquiry sent successfully!"}), 200
                else:
                    return jsonify({"success": False, "message": "Failed to send via API."}), 500

            except Exception as e:
                if 'logger' in globals():
                    logger.error(f"Inquiry submission failed: {str(e)}")
                else:
                    print(f"Inquiry submission failed: {str(e)}")

                return jsonify({"success": False, "message": "Server error. Could not send email."}), 500

        return render_template('enquiry.html')

    with app.app_context():
        db.create_all()
        return app

if __name__ == '__main__':
    app = create_app()
    scheduler = BackgroundScheduler(job_defaults={'coalesce': True, 'misfire_grace_time': 60})
    scheduler.add_job(func=send_reminders, trigger='interval', minutes=1, args=[app])
    scheduler.start()

    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)


