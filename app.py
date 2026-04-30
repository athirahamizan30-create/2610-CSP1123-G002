from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import mysql.connector
import re
import uuid
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime, timezone
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
db= SQLAlchemy()
login_manager = LoginManager()

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    password_reset_ids = db.relationship(
        "PasswordResetId",
        backref="User",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>" 
    
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
    
def get_db_connection():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    password="N&j@1209",
    database="add_job"
    )


def create_app():

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'user_registration_athirah'
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://athirah:Tiya071!@localhost/CareerTrack_Database"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=15)
    app.config['UPLOAD_FOLDER'] = 'static/uploads'

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

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

    @app.route("/logout")
    def logout():
        logout_user()
        flash("You have been logged out", "success")
        return redirect(url_for("index"))            
                                     

    @app.route('/forgot_password')
    def forgot_password():
        return render_template('forgot_password.html')
    
    @app.route('/reset_password')
    def reset_password():
        return render_template("reset_password.html")
    
    @app.route('/document')
    def document():
        docs = Document.query.order_by(Document.filename.asc()).all()
        return render_template("document.html", docs=docs)

    @app.route('/file_upload', methods=["POST"])
    def file_upload():
        file = request.files['file']
        if file:
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            new_doc = Document(filename=filename, file_path=save_path)
            db.session.add(new_doc)
            db.session.commit()

            return redirect(url_for('document'))
        return "Upload Failed"
      
    
    @app.route('/add_job', methods=['GET', 'POST'])
    def add_job():
        if request.method == 'POST':

            db = get_db_connection
            cursor = db.cursor()

            company = request.form['company_name']
            position = request.form['job_position']
            location = request.form['location']
            status = request.form['job_status']

            cursor.execute("""
                INSERT INTO new_job (company_name, job_position, location, job_status)
                VALUES (%s, %s, %s, %s)
            """, (company, position, location, status))

            job_id = cursor.lastrowid

            date_types = request.form.getlist('date_type[]')
            date_values = request.form.getlist('date_value[]')

            for date_type, date_value in zip(date_types, date_values):
                if date_value:
                    cursor.execute("""
                        INSERT INTO job_dates (job_id, date_type, date_value)
                        VALUES (%s, %s, %s)
                    """, (job_id, date_type, date_value))

            db.commit()
            cursor.close()
            db.close()

            return redirect('/')

        return render_template('job.html')


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        return app

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://nurin:N%26j%401209@localhost/add_job'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class NewJob(db.Model):
    __tablename__ = 'new_job'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255))
    job_position = db.Column(db.String(255))
    location = db.Column(db.String(255))
    job_status = db.Column(db.String(50))
    job_type = db.Column(db.String(50))

    dates = db.relationship('JobDate', backref='job', lazy=True, cascade="all, delete")


class JobDate(db.Model):
    __tablename__ = 'job_dates'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('new_job.id'))
    date_type = db.Column(db.String(50))
    date_value = db.Column(db.Date)

@app.route('/')
def home():
    return render_template('job.html')

@app.route('/dashboard')
def dashboard():
    full_time = NewJob.query.filter_by(job_type='Full-Time').all()
    part_time = NewJob.query.filter_by(job_type='Part-Time').all()
    intern = NewJob.query.filter_by(job_type='Intern/Trainee').all()

    return render_template(
        'dashboard.html', active_page='dashboard',
        full_time=full_time,
        part_time=part_time,
        intern=intern
    )

@app.route('/add_job', methods=['POST'])
def add_job():
    new_job = NewJob(
        company_name=request.form['company_name'],
        job_position=request.form['job_position'],
        location=request.form['location'],
        job_status=request.form['job_status'],
        job_type=request.form['job_type']
    )

    db.session.add(new_job)
    db.session.commit()

    date_types = request.form.getlist('date_type[]')
    date_values = request.form.getlist('date_value[]')

    for date_type, date_value in zip(date_types, date_values):
        if date_value:
            new_date = JobDate(
                job_id=new_job.id,
                date_type=date_type,
                date_value=datetime.strptime(date_value, "%Y-%m-%d")
            )
            db.session.add(new_date)

    db.session.commit()

    return redirect('/dashboard')

@app.route('/reminders')
def reminders():
    today = datetime.today().date()

    upcoming_dates = JobDate.query.filter(JobDate.date_value >= today).order_by(JobDate.date_value).all()

    return render_template('reminders.html', active_page='reminders', dates=upcoming_dates)

@app.route('/edit_job/<int:id>', methods=['POST'])
def edit_job(id):
    job = NewJob.query.get_or_404(id)

    job.company_name = request.form['company_name']
    job.job_position = request.form['job_position']
    job.location = request.form['location']
    job.job_status = request.form['job_status']
    job.job_type = request.form['job_type']

    db.session.commit()

    return redirect('/dashboard')

@app.route('/delete_job/<int:id>', methods=['POST'])
def delete_job(id):
    job = NewJob.query.get_or_404(id)

    db.session.delete(job)
    db.session.commit()

    return redirect('/dashboard')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
