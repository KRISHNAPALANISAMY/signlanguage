from flask import Flask

# create Flask app
app = Flask(__name__)

# define route
@app.route("/")
def hello():
    return "Hello, World!"

# run app
if __name__ == "__main__":
    app.run(debug=True)
