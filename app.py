from flask import Flask, render_template, url_for, redirect

#create app
app = Flask(__name__, template_folder="templates")


#index function map with default route (/)
@app.route ('/')
def index ():
    return render_template("document.html")

#go to other page/route connected to web, <> is a variable, can be added in function
@app.route('/redirect_endpoint')
def redirect_endpoint():
    return redirect (url_for("test"))

#run app with local host (0.0.0.0) and port 5555, set debug to true, does not have to reset app everytime theres error
if __name__ == "__main__":
    app.run (host="0.0.0.0", port=5555, debug=True)