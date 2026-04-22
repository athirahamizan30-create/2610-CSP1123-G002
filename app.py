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

@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':

        db = get_db_connection()
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

app.run(debug=True)