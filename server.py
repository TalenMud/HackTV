import os
import requests
from flask import Flask, send_file, request, redirect, url_for, session, flash, render_template
from dotenv import load_dotenv
import io
import random
import psycopg2

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")
streams_data = "Test.Test:Test2.Test"



#get psql connection
DATABASE_URL = os.getenv("DATABASE_URL")

ALLOWED_SLACK_IDS = os.getenv("ALLOWED_SLACK_IDS", "").split(",")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/index.html')
def index():
    return redirect(url_for('home'))

@app.route('/settings')  
def account():
    return render_template("settings.html") 

@app.route('/history')  
def history():
    return render_template("history.html") 

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/stream")
def streams():
    return render_template("stream.html")

@app.route("/getad")
def getad(): #idea: instead of putting all this here, we should get the active yswses from ysws.hackclub.com through api or if there is no api then just scrape the data ;)
    ads = [
        {"ad": "Put the you in CPU today", "image": "https://hackclub.com/stickers/inside.png", "url": "https://www.cpu.land"},
        {"ad": "A Game about Love & Graphing, Made By Hack Clubbers", "image": "https://sinerider.com/Assets/Images/loading-screen.png", "url": "https://sinerider.com/"},
        {"ad": "Free Linux VPS for Hack Club Members", "image": "https://hackclub.com/stickers/nest_hatched_smolpheus.png", "url": "https://hackclub.com/nest"},
        {"ad": "OnBoard to PCB Design", "image": "https://hackclub.com/stickers/orpheus-skateboarding-PCB.png", "url": "https://hackclub.com/onboard/"},
        {"ad": "HCB: Start a Non-Profit", "image": "https://hackclub.com/stickers/hcb_(dark).png", "url": "https://hackclub.com/fiscal-sponsorship/"},
        {"ad": "YS: A Game, WS: A Console (A Sprig)", "image": "https://hackclub.com/stickers/sprig.svg", "url": "https://sprig.hackclub.com/"},
        {"ad": "Blot: Online Drawing Machine", "image": "https://hackclub.com/stickers/Blot.png", "url": "https://blot.hackclub.com/editor"},
        {"ad": "Design your own 3D printer, Get a Grant to Build It, get flown to a Hack Club event!", "image": "https://infill.hackclub.com/_astro/houston.CZZyCf7p_Z2wV2f.webp", "url": "https://infill.hackclub.com/"},
        {"ad": "Build a IOS App, Get $100 to Ship it to the App Store", "image": "https://cider.hackclub.com/logo.svg", "url": "https://cider.hackclub.com/"},
        {"ad": "Juice: Code a game for 100 hours, get a steam grant, get a stipend to the event!", "image": "ADD ME PLEASE ADD ME I BEG YOU", "url": "https://juice.hackclub.com/"}, #incomplete
        {"ad": "Jungle: Code a game, recieve tokens to be spent on assets for your game!", "image": "PLEASE ADD ME I NEED TO BE ADDED PLEASE", "url": "uhh idfk tbh"} #incomplete
    ]
    
    selected_ad = random.choice(ads)
    return selected_ad

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    """redirects user to Slack OAuth login"""
    slack_auth_url = (
        f"https://slack.com/openid/connect/authorize?"
        f"response_type=code&"
        f"client_id={SLACK_CLIENT_ID}&"
        f"scope=openid%20profile%20email&"
        f"redirect_uri={SLACK_REDIRECT_URI}"
    )
    return redirect(slack_auth_url)

@app.route("/slack/callback")
def slack_callback():
    if not (code := request.args.get("code")):
        return "missing auth code", 400
    
    token_response = requests.post(
        "https://slack.com/api/openid.connect.token",
        data={
            "client_id": SLACK_CLIENT_ID,
            "client_secret": SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": SLACK_REDIRECT_URI
        },
    ).json()

    if "access_token" not in token_response:
        return f"error: {token_response.get('error', 'no token recieved')}", 401
    
    #get user info
    user_response = requests.get(
        "https://slack.com/api/openid.connect.userInfo",
        headers={"Authorization": f"Bearer {token_response['access_token']}"}
    ).json()

    if "sub" not in user_response:
        return "unable to get user info", 401

    #authorize user
    if (slack_id := user_response["sub"]) not in ALLOWED_SLACK_IDS:
        return "unauthorized", 403

    #put user in db
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (slack_id, name, email)
                VALUES (%s, %s, %s)
                ON CONFLICT (slack_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email""",
                (slack_id, user_response.get("name", ""), user_response.get("email", ""))
            )
            conn.commit()

    #create user session
    session["user"] = {
        "id": slack_id,
        "name": user_response.get("name", ""),
        "email": user_response.get("email", "")
    }

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        pass
    else:
        return send_file("create.html")

@app.route("/createstream/<stream_name>/<stream_description>", methods=['POST', 'GET'])
def createstream(stream_name, stream_description):
    """stores a new stream in psql"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO streams (name, description) VALUES (%s, %s)",
        (stream_name, stream_description)
    )
    conn.commit()
    cur.close()
    conn.close()
    return "Stream created", 200

@app.route("/search/<keywords>")
def search(keywords):
    #split keywords and create search patterns
    search_terms = keywords.split("+")
    search_patterns = [f'%{term}%' for term in search_terms]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        #search both name and desc, case insensitive
        cur.execute("""
            SELECT name, description
            FROM streams
            WHERE name ILIKE ANY(%s)
                OR description ILIKE ANY(%s)
            ORDER BY name
            LIMIT 50
            """,
            (search_patterns, search_patterns))
        
        results = [{
            'id': row[0],
            'name': row[1],
            'description': row[2]
        } for row in cur.fetchall()]

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        results = []
    finally:
        cur.close()
        conn.close()

    return render_template("search.html",
                           search_keywords=keywords,
                           results=results)

@app.route("/watch/<stream_id>")
def watch(stream_id):
    return render_template("watch.html") #add custom stream id stuff later

@app.route("/stream/<stream_id>")
def stream(stream_id):
    pass

current_image = None

@app.route("/watchtest")
def watchtest():
    return render_template("watchtesting.html")

@app.route('/stream/sendimg', methods=['POST'])
def receive_image():
    global current_image
    if 'image' in request.files:
        current_image = request.files['image'].read()
        return 'Image received', 200
    return 'No image found', 400

@app.route("/activestreams")
def activestreams():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, description FROM streams")
    streams = cur.fetchall()
    cur.close()
    conn.close()
    return {"streams": [{"name": row[0], "description": row[1]} for row in streams]}

@app.route('/stream/getimg', methods=['GET'])
def get_image():
    if current_image:
        return send_file(io.BytesIO(current_image), mimetype='image/jpeg')
    return 'No image available', 200

if __name__ == "__main__":
    app.run(debug=True)