from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)