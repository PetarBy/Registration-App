from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Registration App!"

if __name__ == "__main__":
    # Only used when running 'python app.py'
    app.run(debug=True)
