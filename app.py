from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
import re
import uuid

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

        db.session.add(Document(filename=filename, file_path=path))
        db.session.commit()

    return redirect(url_for('document'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)