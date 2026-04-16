from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sqlalchemy import text


app = Flask(__name__)

db= SQLAlchemy()
login_manager = LoginManager()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.string(120), unique=True, nullable=False)
    password_hash = db.Column(db.string(255), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"
    
    


def create_user_registration():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'user_registration_athirah'
    app.config['SQLALCHEMY_DATABSE_URI'] = "mysql+pymysql://athirah:Tiya071!@localhost/CareerTrack_Database"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init.app(app)
    login_manager.init.app(app)
    login_manager.login_view = "login"

    @app.route('/')

    @app.route('/')
    def index():
        return render_template('index.html')
    

    @app.route('/register')
    def register():
        return render_template('register.html')
    

    @app.route('/register')
    def login():
        return render_template('login.html')
    

    @login_manager.user_loader
    def load_user(user_id):
        return None
    
    with app.app_context():
        db.create_all()
    
    
    
    return app


  




@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)