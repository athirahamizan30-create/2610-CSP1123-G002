from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)

db= SQLAlchemy()
login_manager = LoginManager()


def create_user_registration():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'user_registration_athirah'
    app.config['SQLALCHEMY_DATABSE_URI'] = "mysql+pymysql://athirah:Tiya071!@localhost/my_database"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init.app(app)
    login_manager.init.app(app)
    login_manager.login_view = "login"

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
    
    
    
    return app


  




@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)