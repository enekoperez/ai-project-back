from flask import Flask


app = Flask(__name__)
app.config.from_object("config.Config")


@app.get("/")
def index():
    return "Hello, Flask!"


if __name__ == "__main__":
    app.run(debug=True)
