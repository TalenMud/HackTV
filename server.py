from flask import Flask, send_file, request, redirect

app = Flask(__name__)

@app.route("/")
def home():
    return send_file("index.html")

# Need to make these pages
@app.route("/login", methods=['POST', 'GET'])

# ewoud will do the slack app sso
# Maybe use HC slack as sso instead of creating our own login system
def login():
    if request.method == 'POST':
        # Check if user exists in database (need one first)
        # If user exists, redirect to home page
        # If user does not exist, redirect to signup page
        pass
    else:
        return send_file("login.html")

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        # Add user to database (need one first)
        # Redirect to home page
        pass
    else:
        return send_file("signup.html")

@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        # Create a stream
        pass
    else:
        return send_file("create.html")

@app.route("/search/<keywords>")
def search(keywords):
    # Search for streams with the given keywords
    return send_file("search.html")

@app.route("/watch/<stream_id>")
def watch(stream_id):
    # Check if stream exists
    # If stream exists, return watch page with the correct info for the stream
    return send_file("watch.html")

@app.route("/stream/<stream_id>")
def stream(stream_id):
    # Need to implement some way to send video stream, ideally without writing to disk first
    pass

if __name__ == "__main__":
    app.run(debug=True)
