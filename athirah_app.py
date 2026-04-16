from flask import Flask, render_template, url_for

app = Flask(__name__)


def create_user_registration():
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app




@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)