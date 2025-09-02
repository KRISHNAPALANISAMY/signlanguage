from flask import Flask,render_template

# create Flask app
app = Flask(__name__)

# define route
@app.route("/")
def hello():
    return render_template("index.html")

# run app
if __name__ == "__main__":
    app.run(debug=True)