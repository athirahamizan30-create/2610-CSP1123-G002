from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="N&j@1209",
        database="add_job"
    )

@app.route('/')
def home():
    return render_template('job.html')

@app.route('/dashboard')
def dashboard():
    db = get_db_connection()
    cursor = db.cursor(buffered=True, dictionary=True)

    cursor.execute("""
        SELECT n.*, d.date_type, d.date_value
        FROM new_job n
        LEFT JOIN job_dates d ON n.id = d.job_id
    """)

    rows = cursor.fetchall()

    jobs = {}

    for row in rows:
        job_id = row['id']

        if job_id not in jobs:
            jobs[job_id] = {
                'id': job_id,
                'company_name': row['company_name'],
                'job_position': row['job_position'],
                'location': row['location'],
                'job_status': row['job_status'],
                'job_type': row['job_type'],
                'dates': []
            }

        if row['date_type']:
            jobs[job_id]['dates'].append({
                'date_type': row['date_type'],
                'date_value': row['date_value']
            })

    cursor.close()
    db.close()

    all_jobs = list(jobs.values())

    full_time = [j for j in all_jobs if j['job_type'] == 'Full-Time']
    part_time = [j for j in all_jobs if j['job_type'] == 'Part-Time']
    intern = [j for j in all_jobs if j['job_type'] == 'Intern/Trainee']

    return render_template(
        'dashboard.html',
        full_time=full_time,
        part_time=part_time,
        intern=intern
    )

@app.route('/add_job', methods=['POST'])
def add_job():
    db = get_db_connection()
    cursor = db.cursor()

    company = request.form['company_name']
    position = request.form['job_position']
    location = request.form['location']
    status = request.form['job_status']
    job_type = request.form['job_type']

    cursor.execute("""
        INSERT INTO new_job (company_name, job_position, location, job_status, job_type)
        VALUES (%s, %s, %s, %s, %s)
    """, (company, position, location, status, job_type))

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

    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)