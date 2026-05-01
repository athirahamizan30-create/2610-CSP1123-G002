from flask import Flask, render_template, url_for, request, redirect, flash
import mysql.connector
import re
import uuid
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime, timezone
from config import Config
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

app = Flask(__name__, template_folder="templates", static_folder="static")
db= SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
import re
import uuid

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
app = Flask(__name__, template_folder="templates", static_folder="static")

app.config['SECRET_KEY'] = 'user_registration_athirah'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://athirah:Tiya071!@localhost/CareerTrack_Database"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=15)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Document(db.Model):
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
    
def get_db_connection():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    password="N&j@1209",
    database="add_job"
    )

def create_app():

    app = Flask(__name__)
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

    mail.init_app(app)

    @app.route('/', methods=['GET', 'POST'])
    def index():
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
                return render_template("index.html", errors=errors)
            return f"Received data - {email}"
        return render_template('index.html', errors=errors)
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
    
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
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)


class NewJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255))
    job_position = db.Column(db.String(255))
    location = db.Column(db.String(255))
    job_status = db.Column(db.String(50))
    job_type = db.Column(db.String(50))

    dates = db.relationship('JobDate', backref='job', cascade="all, delete")


class JobDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('new_job.id'))
    date_type = db.Column(db.String(50))
    date_value = db.Column(db.Date)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            errors.append("Passwords do not match")

        if not errors:
            try:
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                errors.append("User already exists")

    return render_template('register.html', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            errors.append("Invalid email or password")
        else:
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html', errors=errors)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template(
        'dashboard.html',
        active_page='dashboard',
        full_time=NewJob.query.filter_by(job_type='Full-Time').all(),
        part_time=NewJob.query.filter_by(job_type='Part-Time').all(),
        intern=NewJob.query.filter_by(job_type='Intern/Trainee').all()
    )


@app.route('/add_job', methods=['POST'])
@login_required
def add_job():
    job = NewJob(
        company_name=request.form.get('company_name'),
        job_position=request.form.get('job_position'),
        location=request.form.get('location'),
        job_status=request.form.get('job_status'),
        job_type=request.form.get('job_type')
    )

    db.session.add(job)
    db.session.commit()

    date_types = request.form.getlist('date_type[]')
    date_values = request.form.getlist('date_value[]')

    for dtype, dvalue in zip(date_types, date_values):
        if dvalue:  # ignore empty dates
            job_date = JobDate(
                job_id=job.id,
                date_type=dtype,
                date_value=datetime.strptime(dvalue, "%Y-%m-%d").date()
            )
            db.session.add(job_date)

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
    def document():
        docs = Document.query.order_by(Document.filename.asc()).all()
        return render_template("document.html", docs=docs)
@app.route('/edit_job/<int:id>', methods=['POST'])
@login_required
def edit_job(id):
    job = NewJob.query.get_or_404(id)
    
    job.company_name = request.form.get('company_name')
    job.job_position = request.form.get('job_position')
    job.location = request.form.get('location')
    job.job_status = request.form.get('job_status')
    job.job_type = request.form.get('job_type')

    db.session.commit()
    return redirect(url_for('dashboard'))
  
  @app.route('/file_upload', methods=["POST"])
    def file_upload():
        file = request.files['file']
        if file:
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)
        
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            return redirect(url_for('document'))
        return "Upload Failed"

      
    @app.route('/add_job', methods=['GET', 'POST'])
    def add_job():
        if request.method == 'POST':

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
    today = datetime.today().date()

    dates = JobDate.query.filter(
        JobDate.date_value >= today
    ).order_by(JobDate.date_value).all()

    return render_template('reminders.html', active_page='reminders', dates=dates)

@app.route('/document')
@login_required
def document():
    docs = Document.query.all()
    return render_template("document.html", docs=docs)


@app.route('/file_upload', methods=["POST"])
@login_required
def file_upload():
    file = request.files.get('file')

    if file:
        filename = file.filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

    @app.route('/delete_file/<int:doc_id>')
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
        db.session.add(Document(filename=filename, file_path=path))
        db.session.commit()

    return redirect(url_for('document'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)



#satu database and semua table dalam database tu
#kene buang register punyer link kat navbar. 
    app.run(debug=True)
