from flask import Flask, render_template, url_for, request, redirect, flash, session
import re
import uuid
import os
import secrets
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime, timezone
from config import Config
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from typing import Dict
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.middleware.proxy_fix import ProxyFix



app = Flask(__name__, template_folder="templates", static_folder="static/uploads")
db= SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
socketio = SocketIO()

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://athirah:Tiya071!@localhost/CareerTrack_Database"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=15)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logger = logging.getLogger(__name__)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
with app.app_context():
    db.create_all()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    image_file= db.Column(db.String(20), nullable=False, default='default.jpg')
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('new_job.id', ondelete='CASCADE'), nullable=False)
    reminder_date = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(255))
    is_done = db.Column(db.Boolean, default=False)

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

def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)
    bcrypt.init_app(app)
    app.config.from_object(Config)
    mail = Mail()
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"


    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=15)
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    print("SECRET_KEY:", app.config.get("SECRET_KEY"))
    print("DATABASE_URL:", app.config.get("SQLALCHEMY_DATABASE_URI"))
    print("MAIL_USERNAME:", app.config.get("MAIL_USERNAME"))
    print("MAIL_PASSWORD:", app.config.get("MAIL_PASSWORD"))

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_app_password'
    app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'
    
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

        full_time = NewJob.query.filter_by(user_id=current_user.id, job_type='Full-Time').all()

        part_time = NewJob.query.filter_by(user_id=current_user.id, job_type='Part-Time').all()

        intern = NewJob.query.filter_by(user_id=current_user.id, job_type='Intern/Trainee').all()

        all_jobs = full_time + part_time + intern

        job_dates = {}

        for job in all_jobs:
            job_dates[job.id] = []

            for d in job.dates:
                job_dates[job.id].append({
                    "date_type": d.date_type,
                    "date_value": d.date_value.strftime("%Y-%m-%dT%H:%M")
                })

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            full_time=full_time,
            part_time=part_time,
            intern=intern,
            job_dates=job_dates
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
                    return redirect(url_for('login'))
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

            if not errors:
                user = User.query.filter_by(email=email).first()

            if not user or not check_password_hash(user.password_hash, password):
                errors.append("Invalid password or email")

            else:

                remember_me = request.form.get("remember") == "1"

                login_user(user, remember=remember_me)
                return redirect(url_for("dashboard"))
            

        return render_template('login.html', errors=errors)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))
 
    @app.route('/add_job', methods=['POST'])
    @login_required
    def add_job():
        application_date = request.form.get("application_date")

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

        if application_date:
            app_date_obj = datetime.strptime(application_date, "%Y-%m-%d")

            reminder = Reminder(
                user_id=current_user.id,
                job_id=job.id,
                reminder_date=app_date_obj - timedelta(days=1),
                message="Upcoming application deadline"
            )
            db.session.add(reminder)

        date_types = request.form.getlist('date_type[]')
        date_values = request.form.getlist('date_value[]')

        for dtype, dvalue in zip(date_types, date_values):
            if dvalue:
                date_obj = datetime.strptime(dvalue, "%Y-%m-%dT%H:%M")

                job_date = JobDate(
                    job_id=job.id,
                    date_type=dtype,
                    date_value=date_obj.date()
                )
                db.session.add(job_date)

                reminder = Reminder(
                    user_id=current_user.id,
                    job_id=job.id,
                    reminder_date=date_obj,
                    message = f"{dtype.title()} – {job.job_position} at {job.company_name}"
                )
                db.session.add(reminder)

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

            print("DEBUG reset_id:", new_password_reset_id.reset_id)

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
        docs = Document.query.order_by(Document.filename.asc()).all()
        return render_template("document.html", docs=docs)  

    @app.route('/edit_job/<int:id>', methods=['POST'])
    @login_required
    def edit_job(id):

        job = NewJob.query.get_or_404(id)

        job.company_name = request.form.get("company_name")
        job.job_position = request.form.get("job_position")
        job.location = request.form.get("location")
        job.job_status = request.form.get("job_status")
        job.job_type = request.form.get("job_type")

        date_types = request.form.getlist("date_type[]")
        date_values = request.form.getlist("date_value[]")

        JobDate.query.filter_by(job_id=id).delete()

        Reminder.query.filter_by(job_id=id).delete()

        for t, v in zip(date_types, date_values):

            if v:
                parsed_date = datetime.fromisoformat(v)

                new_date = JobDate(
                    job_id=id,
                    user_id=current_user.id,
                    date_type=t,
                    date_value=datetime.fromisoformat(v)
                )
                db.session.add(new_date)

                reminder = Reminder(
                    user_id=current_user.id,
                    job_id=id,
                    reminder_date=parsed_date,
                    message = f"{t.title()} - {job.job_position} at {job.company_name}"
                )

                db.session.add(reminder)

        db.session.commit()

        return redirect(url_for("dashboard"))

    @app.route('/delete_job/<int:id>', methods=['POST'])
    @login_required
    def delete_job(id):
        job = NewJob.query.get_or_404(id)

        db.session.delete(job)
        db.session.commit()
        return redirect(url_for('dashboard'))

    @app.route('/reminders')
    @login_required
    def reminders():

        reminders = Reminder.query.filter_by(
            user_id=current_user.id
        ).order_by(Reminder.reminder_date).all()

        now = datetime.now()

        upcoming_reminders = []
        past_reminders = []

        for reminder in reminders:
            if reminder.reminder_date >= now:
                upcoming_reminders.append(reminder)
            else:
                past_reminders.append(reminder)

        return render_template(
            "reminders.html",
            upcoming_reminders=upcoming_reminders,
            past_reminders=past_reminders
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
        results = db.session.query(NewJob.job_status, func.count(NewJob.job_status)).filter(NewJob.user_id == current_user.id).group_by(NewJob.job_status).all()

        stats_dict = {status: count for status, count in results}
    
        total_count = sum(stats_dict.values())

        return render_template('statistic.html', 
                           status_data=results, 
                           stats=stats_dict, 
                           total=total_count)
        
    def save_picture(form_picture):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
        form_picture.save(picture_path)

        return picture_fn

    @app.route("/account", methods=["POST", "GET"])
    @login_required
    def account():
        form = UpdateAccountForm()
        if form.validate_on_submit():
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
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            form.full_name.data = current_user.full_name 
            form.phone_number.data = current_user.phone_number 
            form.about_me.data = current_user.about_me 

        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('account.html', title='Account', image_file=image_file, form=form)

    @app.route("/chat")
    @login_required
    def chat():
        logger.info(f"User {current_user.username} entered the chat session")
        rooms = ChatRoom.query.all()


        return render_template(
            'chat.html',
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

    with app.app_context():
        db.create_all()
        return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
