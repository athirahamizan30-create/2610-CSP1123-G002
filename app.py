from flask import Flask, render_template, request, redirect
import mysql.connector
import re
import uuid
import os
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    print("SECRET_KEY:", app.config.get("SECRET_KEY"))
    print("DATABASE_URL:", app.config.get("SQLALCHEMY_DATABASE_URI"))
    print("MAIL_USERNAME:", app.config.get("MAIL_USERNAME"))
    print("MAIL_PASSWORD:", app.config.get("MAIL_PASSWORD"))

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    mail.init_app(app)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('index.html')
    
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

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)



#satu database and semua table dalam database tu
#kene buang register punyer link kat navbar. 
