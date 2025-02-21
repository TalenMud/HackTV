import os
import requests
from flask import Flask, send_file, request, redirect, url_for, session, flash, render_template
from dotenv import load_dotenv
import random

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

#get allowed users from .env
ALLOWED_SLACK_IDS = os.getenv("ALLOWED_SLACK_IDS").split(",")
@app.route("/explore")
def explore():
    return send_file("explore.html")

@app.route("/getad") # Get an ad from the ad list
def getad():
    ads = [
        {
            "ad": "Put the you in CPU today",
            "image": "https://hackclub.com/stickers/inside.png",
            "url": "https://www.cpu.land"
        },
        {
            "ad": "A Game about Love & Graphing, Made By Hack Clubbers",
            "image": "https://sinerider.com/Assets/Images/loading-screen.png",
            "url": "https://sinerider.com/"
        },
        {
            "ad": "Free Linux VPS for Hack Club Members",
            "image": "https://hackclub.com/stickers/nest_hatched_smolpheus.png",
            "url": "https://hackclub.com/nest"
        },
        {
            "ad": "OnBoard to PCB Design",
            "image": "https://hackclub.com/stickers/orpheus-skateboarding-PCB.png",
            "url": "https://hackclub.com/onboard/"
        },
        {
            "ad": "HCB: Start a Non-Profit",
            "image": "https://hackclub.com/stickers/hcb_(dark).png",
            "url": "https://hackclub.com/fiscal-sponsorship/"
        },
        {
            "ad": "YS: A Game, WS: A Console (A Sprig)",
            "image": "https://hackclub.com/stickers/sprig.svg", 
            "url": "https://sprig.hackclub.com/"
        },
        {
            "ad": "Blot: Online Drawing Machine",
            "image": "https://hackclub.com/stickers/Blot.png", 
            "url": "https://blot.hackclub.com/editor"
        },
        {
            "ad": "Design your own 3D printer, Get a Grant to Build It, then get flown to a Hack Club event!",
            "image": "https://infill.hackclub.com/_astro/houston.CZZyCf7p_Z2wV2f.webp", 
            "url": "https://infill.hackclub.com/"
        },
        {
            "ad": "Build a IOS App, Get $100 to Ship it to the App Store",
            "image": "https://cider.hackclub.com/logo.svg",
            "url": "https://cider.hackclub.com/"
        }
    ]
    
    selected_ad = random.choice(ads)
    return selected_ad

@app.route("/")
def home():
    return send_file("index.html")
@app.route("/login")
def login():
    """redirects user to Slack OAuth login"""
    slack_auth_url = (
        f"https://slack.com/oauth/v2/authorize?"
        f"client_id={SLACK_CLIENT_ID}&"
        "scope=profile&"
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
    access_token = token_response["authed_user"]["access_token"]
    user_response = requests.get(
        "https://slack.com/api/users.identity",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    if not user_response.get("ok"):
        return f"error: {user_response.get('error')}"
    
    user_info = user_response["user"]
    slack_user_id = user_info["id"]

    #check if user is allowed
    if slack_user_id not in ALLOWED_SLACK_IDS:
        return "womp womp. access denied."

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
    return render_template("search.html", search_keywords=keywords)

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
