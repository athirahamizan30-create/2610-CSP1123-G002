import sqlite3
import os 
from flask import Flask, request, render_template

app = Flask (__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
@app.route('/')
def index():
    return render_template('document.html')
def upload_file():
    file = request.files['filename']
    filename = file.filename
    
    file.save(f"./uploads/{filename}")
    
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("INSERT INTO files (name) VALUES (?)", (filename,))
    connection.commit()
    connection.close()
    
    return "File uploaded and recorded in SQLite!"

if __name__ == '__main__':
    app.run(debug=True)