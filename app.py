import os
from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#create app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Database & Upload Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///documents.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Create the upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database Model
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

# Create the database file
with app.app_context():
    db.create_all()

#index function map with default route (/)
@app.route('/')
def index():
    # Fetch all uploaded documents to display them
    docs = Document.query.all()
    return render_template("document.html", docs=docs)

@app.route('/file_upload', methods=["POST"])
def file_upload():
    file = request.files['file']
    if file:
        filename = file.filename
        # 1. Save the physical file to the 'static/uploads' folder
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # 2. Save the metadata (path) to SQLite
        new_doc = Document(filename=filename, file_path=save_path)
        db.session.add(new_doc)
        db.session.commit()

        return redirect(url_for('index'))
    return "Upload Failed"

#run app with local host (0.0.0.0) and port 5555, set debug to true, does not have to reset app everytime theres error
if __name__ == "__main__":
    app.run (host="0.0.0.0", port=5555, debug=True)