import re
import uuid
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
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
    
    def is_expired(self):
        expires_at = self.created_at + timedelta(minutes=10)
        return datetime.now(timezone.utc) > expires_at

    

    

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

    

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))





    with app.app_context():
        db.create_all()
    
    return app




   






if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)



    #landing page - index.html
    #connect database dgn page
    #flask working
    #database nnti share je ngan org laen, nnti bagi org laen download kat clickup
    #tkyah tambah yg feature nk tambah kat storyboard
    #bole pkai java nnti tambah kat click up
    
















