from flask import Flask, request, make_response

#create app
app = Flask(__name__)


#index function map with default route (/)
@app.route ('/')
def index ():
    return "<h1>Hello Word</h1>"

#go to other page/route connected to web, <> is a variable, can be added in function
@app.route('/greet/<int:num1>/<int:num2>')
def greet(num1, num2):
    return f"{num1} + {num2} = {num1 + num2}"

#run app with local host (0.0.0.0) and port 5555, set debug to true, does not have to reset app everytime theres error
if __name__ == "__main__":
    app.run (host="0.0.0.0", port=5555, debug=True)