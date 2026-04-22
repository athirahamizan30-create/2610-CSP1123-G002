from flask import Flask, render_template, url_for, redirect, request
import pandas as pd 

#create app
app = Flask(__name__, template_folder="templates")


#index function map with default route (/)
@app.route ('/')
def index ():
    if request.method == "GET":
        return render_template("document.html")
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

    
@app.route ('/file_upload', methods =["POST"])
def file_upload():
    file = request.files['file']

    if file.content_type == "text/plain":
        return file.read().decode()
    elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or file.content_type == "application/vnd.ms-excel":
        df = pd.read_excel(file)
        return df.to_html()



#run app with local host (0.0.0.0) and port 5555, set debug to true, does not have to reset app everytime theres error
if __name__ == "__main__":
    app.run (host="0.0.0.0", port=5555, debug=True)