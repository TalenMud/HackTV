import os
import requests
from flask import Flask, send_file, request, redirect, url_for, session, flash
from dotenv import load_dotenv

#load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

#get slack creds from .env
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

#get airtable creds from .env
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT") #personal access token (tf why is airtable api key deprecated)
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json",
}

@app.route("/")
def home():
    if "user" in session:
        return f"Welcome {session['user']['name']}! <a href='/logout'>Logout</a>"
    return '<a href="/login">Login with Slack</a>'

@app.route("/login")
def login():
    """redirects user to Slack OAuth login"""
    slack_auth_url = (
        f"https://slack.com/oauth/v2/authorize?"
        f"client_id={SLACK_CLIENT_ID}&"
        f"scope=identity.basic,identity.email,identity.team&"
        f"redirect_uri={SLACK_REDIRECT_URI}"
    )
    return redirect(slack_auth_url)

@app.route("/slack/callback")
def slack_callback():
    """slack 0auth callback"""
    code = request.args.get("code")
    if not code:
        return "error: no code provided"
    
    #exchange code for token
    token_response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": SLACK_CLIENT_ID,
            "client_secret": SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": SLACK_REDIRECT_URI
        },
    ).json()

    if not token_response.get("ok"):
        return f"error: {token_response.get('error')}"
    
    #get user info
    acces_token = token_response[authed_user][access_token]
    user_response = requests.get(
        "https://slack.com/api/users.identity",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    if not user_response.get("ok"):
        return f"error: {user_response.get('error')}"
    
    user_info = user_response["user"]
    session["user"] = {
        "id": user_info["id"],
        "name": user_info["name"],
        "email": user_info.get["email", ""],
    }

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    """logs out user by clearing session"""
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")

        if not name or not email:
            flash("Name and email are required!", "error")
            return redirect(url_for("signup"))
        
        #check if user already exists in airtable db
        response = requests.get(AIRTABLE_URL, headers=HEADERS)
        users = response.json().get("records", [])

        for user in users:
            if user["fields"].get("email") == email:
                flash("User already exists!", "error")
                return redirect(url_for("signup"))
            
        #add user to airtable db
        data = {"fields": {"Name": name, "Email": email}}

        response = requests.post(AIRTABLE_URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            flash("User created successfully! You can now sign in.", "success")
        else:
            flash("Something went wrong! Please try again.", "error")

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
