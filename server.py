import os
import requests
from flask import Flask, jsonify, send_file, request, redirect, url_for, session, flash, render_template
from dotenv import load_dotenv
import io
import random
import psycopg2
import yaml

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
    if "user" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user"]["id"]

    if request.method == 'POST':
        #update ad prefrence
        ads_enabled = 'ads_enabled' in request.form
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE users
                SET settings = JSONB_SET(
                    COALESCE(settings, '{}'::jsonb),
                    '{ads_enabled}',
                    %s::jsonb)
                )
                WHERE slack_id = %s
            """, (str(ads_enabled).lower(), user_id))
            conn.commit()
            flash("Settings updated", "success")
        except psycopg2.Error as e:
            flash("failed to update settings", "error")
        finally:
            cur.close()
            conn.close()
    
    #get current settings
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COALESCE(settings->>'ads_enabled', 'true')::boolean
            FROM users
            WHERE slack_id = %s
        """, (user_id,))
        ads_enabled = cur.fetchone()[0]
    except psycopg2.Error as e:
        ads_enabled = True #default to true if error occurs
    finally:
        cur.close()
        conn.close()

    return render_template("settings.html", ads_enabled=ads_enabled)

@app.route('/history')  
def history():
    return render_template("history.html") 

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/stream")
def streams():
    return render_template("stream.html")

def fetch_ysws_ads():
    try:
        response = requests.get("https://ysws.hackclub.com/data.yml", timeout=5)
        response.raise_for_status()
        data = yaml.safe_load(response.content)

        ads = []
        #process limited time yswses
        for entry in data.get('limitedTime', []):
            if entry.get('status', '') == 'active':
                ads.append({
                    "ad": entry['name'],
                    "description": entry['description'],
                    "url": entry.get('website', '#'),
                    "image": "https://hackclub.com/stickers/orpheus.png" #default image, there is no image url in the yaml :(
                })

        #process indefinite yswses
        for entry in data.get('indefinite', []):
            if entry.get('status', '') == 'active':
                ads.append({
                    "ad": entry['name'],
                    "description": entry['description'],
                    "url": entry.get('website', '#'),
                    "image": "https://hackclub.com/stickers/orpheus.png" #default image
                })

        return ads
    except Exception as e:
        print(f"error fetching ysws data: {e}")
        return None

@app.route("/getad")
def getad():
    #check if user has ads disabled
    if "user" in session:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COALESCE(settings->>'ads_enabled', 'true')::boolean
                FROM users
                WHERE slack_id = %s
            """, (session["user"]["id"],))
            ads_enabled = cur.fetchone()[0]
            if not ads_enabled:
                return '', 204 #no content
        finally:
            cur.close()
            conn.close()

    #fetch ysws ads
    ysws_ads = fetch_ysws_ads()

    #use default ads if ysws ads in the yaml are not available
    ads = ysws_ads if ysws_ads else [
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
                """INSERT INTO users (slack_id, name, email, settings)
                VALUES (%s, %s, %s, "{ads_enabled: true}"::jsonb)
                ON CONFLICT (slack_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email""",
                (slack_id, user_response.get("name", ""), user_response.get("email", ""))
            )
            user_id = cur.fetchone()[0]
            conn.commit()

    #create user session
    session["user"] = {
        "db_id": user_id,
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
        "INSERT INTO streams (name, description, likes, dislikes) VALUES (%s, %s, 0, 0)",
        (stream_name, stream_description)
    )
    conn.commit()
    cur.close()
    conn.close()
    return "Stream created", 200

@app.route("/search/<keywords>")
def search(keywords):
    search_terms = keywords.split("+")
    search_patterns = [f'%{term}%' for term in search_terms]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT name, description
            FROM streams
            WHERE name ILIKE ANY(%s)
                OR description ILIKE ANY(%s)
            ORDER BY name
            LIMIT 50
        """, (search_patterns, search_patterns))
        
        results = []
        for row in cur.fetchall():
            if len(row) == 2:  
                results.append({
                    'name': row[0] if row[0] is not None else '',
                    'description': row[1] if row[1] is not None else ''
                })

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        results = []
    finally:
        cur.close()
        conn.close()

    print("Results before rendering:", results)

    return render_template("search.html", search_keywords=keywords, results=results)

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

@app.route('/activestreams')
def active_streams():
    category_id = request.args.get('category_id')
    conn = get_db_connection()
    cur = conn.cursor()

    if category_id:
        cur.execute("SELECT streams.name, streams.description, streams.likes, streams.dislikes FROM streams WHERE category_id = %s", (category_id,))
    else:
        cur.execute("SELECT streams.name, streams.description, streams.likes, streams.dislikes FROM streams")

    streams = [{"name": row[0], "description": row[1], "likes": row[2], "dislikes": row[3]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({"streams": streams})

@app.route('/stream/getimg', methods=['GET'])
def get_image():
    if current_image:
        return send_file(io.BytesIO(current_image), mimetype='image/jpeg')
    return 'No image available', 200

#likes/dislikes route
@app.route("/stream/<int:stream_id>/like", methods=['POST'])
def handle_vote(stream_id):
    if "user" not in session:
        return "unauthorized", 401
    
    vote_type = request.form.get("type")
    if vote_type not in ("like", "dislike"):
        return "invalid vote type", 400
    
    user_id = session["user"]["id"]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        #record vote
        cur.execute("""
            INSERT INTO votes (user_id, stream_id, vote_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, stream_id) DO UPDATE SET vote_type = EXCLUDED.vote_type
            """, (user_id, stream_id, vote_type))
        
        #update stream vote count
        cur.execute("""
            UPDATE streams SET
                    likes = (SELECT COUNT(*) FROM votes WHERE stream_id = %s AND vote_type = "like"),
                    dislikes = (SELECT COUNT(*) FROM votes WHERE stream_id = %s AND vote_type = "dislike")
            WHERE id = %s
        """), (stream_id, stream_id, stream_id)

        conn.commit()
        return "vote recorded", 200
    
    except psycopg2.Error as e:
        conn.rollback()
        return f"database error: {e}", 500
    finally:
        cur.close()
        conn.close()

@app.route("/stream/<int:stream_id>/votes")
def get_votes(stream_id):
    """get current vote counts"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT likes, dislikes FROM streams WHERE id = %s
        """, (stream_id,))
        result = cur.fetchone()
        return {
            "likes": result[0] if result else 0,
            "dislikes": result[1] if result else 0
        }
    finally:
        cur.close()
        conn.close()
    




@app.route('/categories')
def get_categories():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM categories")
    categories = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({"categories": categories})

if __name__ == "__main__":
    app.run(debug=True)
