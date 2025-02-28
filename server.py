import os
import requests
from flask import Flask, jsonify, make_response, render_template_string, send_file, request, redirect, url_for, session, flash, render_template, send_from_directory
from dotenv import load_dotenv
import io
import random
import psycopg2
import yaml
import uuid
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from functools import wraps
LOGIN_FILE = 'logins.json'
if not os.path.exists(LOGIN_FILE):
    with open(LOGIN_FILE, 'w') as f:
        json.dump({}, f)

def load_logins():
    with open(LOGIN_FILE, 'r') as f:
        return json.load(f)

def save_logins(logins):
    with open(LOGIN_FILE, 'w') as f:
        json.dump(logins, f, indent=4)

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")
@app.route('/api/login', methods=['POST'])
def loginsignup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400

    logins = load_logins()
    if username in logins and logins[username] == password:
        response = make_response(jsonify({'status': 'success', 'message': 'Login successful'}))
        response.set_cookie('username', username, max_age=3600, httponly=True, secure=False)  # 1-hour cookie, secure=False for local dev
        return response
    return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

@app.route('/api/signup', methods=['POST'])
def signuplogin():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

    logins = load_logins()
    if username in logins:
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 409

    logins[username] = password
    save_logins(logins)
    return jsonify({'status': 'success', 'message': 'Signup successful'})
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400

    logins = load_logins()
    if username in logins:
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 409

    logins[username] = password  
    save_logins(logins)
    return jsonify({'status': 'success', 'message': 'Signup successful'})
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")
streams_data = "Test.Test:Test2.Test"

DATABASE_URL = os.getenv("DATABASE_URL")

ALLOWED_SLACK_IDS = os.getenv("ALLOWED_SLACK_IDS", "").split(",")

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads', 'videos')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

VIDEOS_JSON = 'videos.json'

if not os.path.exists(VIDEOS_JSON):
    with open(VIDEOS_JSON, 'w') as f:
        json.dump([], f)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)



@app.route('/video')
def video():
    url_param = request.args.get('url', '')
    
    if url_param:
        clean_url = url_param.replace('/embed', '')
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script>
                localStorage.setItem('videoUrl', '{{ url }}');
                window.location.href = '/video';
            </script>
        </head>
        <body></body>
        </html>
        ''', url=clean_url)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Player</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #1a1a1a;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .video-container {
                width: 100%;
                max-width: 1200px;
                position: relative;
                background: #000;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }
            video {
                width: 100%;
                height: auto;
                display: block;
            }
            :fullscreen .video-container {
                max-width: none;
                width: 100%;
                height: 100%;
                border-radius: 0;
                box-shadow: none;
            }
            :fullscreen video {
                height: 100%;
                object-fit: contain;
            }
            .controls {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
                padding: 10px 15px;
                opacity: 0;
                transition: opacity 0.3s ease;
                z-index: 2;
            }
            .video-container:hover .controls {
                opacity: 1;
            }
            .control-bar {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .play-btn, .fullscreen-btn {
                background: none;
                border: none;
                color: #fff;
                font-size: 20px;
                cursor: pointer;
                padding: 5px;
                transition: transform 0.2s ease;
            }
            .play-btn:hover, .fullscreen-btn:hover {
                transform: scale(1.1);
            }
            .progress-container {
                flex: 1;
                display: flex;
                align-items: center;
                gap: 10px;
                position: relative;
            }
            .time {
                color: #fff;
                font-family: Arial, sans-serif;
                font-size: 12px;
                min-width: 40px;
            }
            .progress-bar {
                flex: 1;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                position: relative;
                cursor: pointer;
            }
            .progress {
                height: 100%;
                background: #00aaff;
                border-radius: 2px;
                width: 0;
                transition: width 0.1s linear;
            }
            .volume-container {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .volume-btn {
                background: none;
                border: none;
                color: #fff;
                font-size: 16px;
                cursor: pointer;
                padding: 5px;
            }
            .volume-bar {
                width: 60px;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                position: relative;
                cursor: pointer;
            }
            .volume-level {
                height: 100%;
                background: #00aaff;
                border-radius: 2px;
                width: 100%;
            }
            .preview {
                position: absolute;
                bottom: 40px;
                width: 160px;
                height: 90px;
                background: #000;
                border: 1px solid #fff;
                border-radius: 4px;
                display: none;
                pointer-events: none;
                z-index: 3;
            }
        </style>
    </head>
    <body>
        <div class="video-container">
            <video id="videoPlayer">
                <source src="" type="video/mp4">
            </video>
            <div class="controls">
                <div class="control-bar">
                    <button class="play-btn">▶</button>
                    <div class="progress-container">
                        <span class="time current-time">0:00</span>
                        <div class="progress-bar">
                            <div class="progress"></div>
                            <canvas class="preview" width="160" height="90"></canvas>
                        </div>
                        <span class="time duration">0:00</span>
                    </div>
                    <div class="volume-container">
                        <button class="volume-btn">🔊</button>
                        <div class="volume-bar">
                            <div class="volume-level"></div>
                        </div>
                    </div>
                    <button class="fullscreen-btn">⛶</button>
                </div>
            </div>
        </div>
        <script>
            const videoUrl = localStorage.getItem('videoUrl');
            const video = document.getElementById('videoPlayer');
            const playBtn = document.querySelector('.play-btn');
            const progressBar = document.querySelector('.progress-bar');
            const progress = document.querySelector('.progress');
            const currentTime = document.querySelector('.current-time');
            const durationTime = document.querySelector('.duration');
            const volumeBtn = document.querySelector('.volume-btn');
            const volumeBar = document.querySelector('.volume-bar');
            const volumeLevel = document.querySelector('.volume-level');
            const fullscreenBtn = document.querySelector('.fullscreen-btn');
            const preview = document.querySelector('.preview');
            let thumbnails = {};

            if (!videoUrl) {
                document.body.innerHTML = 'No video URL provided';
            } else {
                video.querySelector('source').src = videoUrl;
                video.load();

                video.addEventListener('loadedmetadata', () => {
                    durationTime.textContent = formatTime(video.duration);
                    generateThumbnails();
                });

                playBtn.addEventListener('click', () => {
                    if (video.paused) {
                        video.play();
                        playBtn.textContent = '⏸';
                    } else {
                        video.pause();
                        playBtn.textContent = '▶';
                    }
                });

                video.addEventListener('timeupdate', () => {
                    const percent = (video.currentTime / video.duration) * 100;
                    progress.style.width = percent + '%';
                    currentTime.textContent = formatTime(video.currentTime);
                });

                progressBar.addEventListener('click', (e) => {
                    const rect = progressBar.getBoundingClientRect();
                    const percent = (e.clientX - rect.left) / rect.width;
                    video.currentTime = percent * video.duration;
                });

                progressBar.addEventListener('mousemove', (e) => {
                    const rect = progressBar.getBoundingClientRect();
                    const percent = (e.clientX - rect.left) / rect.width;
                    const time = percent * video.duration;
                    const previewTime = Math.floor(time / 10) * 10;
                    
                    if (thumbnails[previewTime]) {
                        const ctx = preview.getContext('2d');
                        ctx.drawImage(thumbnails[previewTime], 0, 0, 160, 90);
                        preview.style.left = Math.min(
                            Math.max(e.clientX - rect.left - 80, 0),
                            rect.width - 160
                        ) + 'px';
                        preview.style.display = 'block';
                    }
                });

                progressBar.addEventListener('mouseleave', () => {
                    preview.style.display = 'none';
                });

                volumeBtn.addEventListener('click', () => {
                    video.muted = !video.muted;
                    volumeBtn.textContent = video.muted ? '🔇' : '🔊';
                    volumeLevel.style.width = video.muted ? '0%' : (video.volume * 100) + '%';
                });

                volumeBar.addEventListener('click', (e) => {
                    const rect = volumeBar.getBoundingClientRect();
                    const percent = (e.clientX - rect.left) / rect.width;
                    video.volume = percent;
                    video.muted = false;
                    volumeBtn.textContent = '🔊';
                    volumeLevel.style.width = (percent * 100) + '%';
                });

                fullscreenBtn.addEventListener('click', () => {
                    if (!document.fullscreenElement) {
                        document.querySelector('.video-container').requestFullscreen();
                    } else {
                        document.exitFullscreen();
                    }
                });

                function formatTime(seconds) {
                    const mins = Math.floor(seconds / 60);
                    const secs = Math.floor(seconds % 60);
                    return mins + ':' + (secs < 10 ? '0' + secs : secs);
                }

                function generateThumbnails() {
                    const canvas = document.createElement('canvas');
                    canvas.width = 160;
                    canvas.height = 90;
                    const ctx = canvas.getContext('2d');
                    const duration = video.duration;
                    const interval = 10;

                    function capture(time) {
                        video.currentTime = time;
                        video.addEventListener('seeked', function onSeeked() {
                            ctx.drawImage(video, 0, 0, 160, 90);
                            thumbnails[time] = new Image();
                            thumbnails[time].src = canvas.toDataURL();
                            video.removeEventListener('seeked', onSeeked);
                            if (time + interval < duration) {
                                capture(time + interval);
                            }
                        }, { once: true });
                    }
                    capture(0);
                }
            }
        </script>
    </body>
    </html>
    ''', user=session.get("user"))

@app.route('/create-video', methods=['POST'])
def create_video():
    if 'title' not in request.form or 'url' not in request.form:
        flash('Missing required fields', 'error')
        return redirect(url_for('create_video'))

    title = request.form['title']
    url = request.form['url']

    video_id = str(uuid.uuid4())
    video_data = {
        'id': video_id,
        'title': title,
        'url': url,
        'upload_date': datetime.now().isoformat()
    }

    with open(VIDEOS_JSON, 'r') as f:
        videos = json.load(f)

    videos.append(video_data)

    with open(VIDEOS_JSON, 'w') as f:
        json.dump(videos, f, indent=2)

    flash('Video stream created successfully!', 'success')
    return redirect(url_for('create_video'))


@app.route('/get-videos', methods=['GET'])
def get_videos():
    try:
        with open(VIDEOS_JSON, 'r') as f:
            videos = json.load(f)
        return jsonify({
            'status': 'success',
            'videos': videos
        })
    except FileNotFoundError:
        return jsonify({
            'status': 'success',
            'videos': []
        })
    except json.JSONDecodeError:
        return jsonify({
            'status': 'error',
            'message': 'Error reading video data'
        }), 500

@app.route('/stream/<video_id>')
def stream_video(video_id):
    try:
        with open(VIDEOS_JSON, 'r') as f:
            videos = json.load(f)
        video = next((v for v in videos if v['id'] == video_id), None)
        if video:
            return jsonify({
                'status': 'success',
                'video': video
            })
        return jsonify({
            'status': 'error',
            'message': 'Video not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/index.html')
def index():
    return redirect(url_for('home'))

@app.route('/settings', methods=['GET', 'POST']) 
def account():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user"]["id"]

    if request.method == 'POST':
        ads_enabled = 'ads_enabled' in request.form
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE users
                SET settings = JSONB_SET(
                    COALESCE(settings, '{}'::jsonb),
                    '{ads_enabled}',
                    to_jsonb(%s::boolean)
                WHERE slack_id = %s
            """, (ads_enabled, user_id))
            conn.commit()
            flash("Settings updated", "success")
        except psycopg2.Error as e:
            flash("failed to update settings", "error")
        finally:
            cur.close()
            conn.close()
    
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
        ads_enabled = True
    finally:
        cur.close()
        conn.close()

    return render_template("settings.html", ads_enabled=ads_enabled, user=session.get("user"))

@app.route('/history')  
def history():
    return render_template("history.html", user=session.get("user")) 

@app.route('/beta/stream')  
def newstream():
    return render_template("newstream.html", user=session.get("user")) 

@app.route("/explore")
def explore():
    return render_template("explore.html", user=session.get("user"))

@app.route("/feedback")
def feedback():
    return render_template("feedback.html", user=session.get("user"))

@app.route("/stream",methods=["POST","GET"])
def streams():
    if request.method=="POST":
        title=request.form['stream-title']
        description=request.form['stream-desc']
        data={"title":title,"desc":description,"streamer":True}
        return render_template("watch.html",data=data)

    data={"title":None,"desc":None,"streamer":False}
    return render_template("stream.html",data=data, user=session.get("user"))

def fetch_ysws_ads():
    try:
        response = requests.get("https://ysws.hackclub.com/data.yml", timeout=5)
        response.raise_for_status()
        data = yaml.safe_load(response.content)

        ads = []
        for entry in data.get('limitedTime', []):
            if entry.get('status', '') == 'active':
                ads.append({
                    "ad": entry['name'],
                    "description": entry['description'],
                    "url": entry.get('website', '#'),
                    "image": "https://hackclub.com/stickers/orpheus.png"
                })

        for entry in data.get('indefinite', []):
            if entry.get('status', '') == 'active':
                ads.append({
                    "ad": entry['name'],
                    "description": entry['description'],
                    "url": entry.get('website', '#'),
                    "image": "https://hackclub.com/stickers/orpheus.png"
                })

        return ads
    except Exception as e:
        print(f"error fetching ysws data: {e}")
        return None

@app.route("/getad")
def getad():
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
                return '', 204
        finally:
            cur.close()
            conn.close()

    ysws_ads = fetch_ysws_ads()

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
        {"ad": "Juice: Code a game for 100 hours, get a steam grant, get a stipend to the event!", "image": "ADD ME PLEASE ADD ME I BEG YOU", "url": "https://juice.hackclub.com/"},
        {"ad": "Jungle: Code a game, recieve tokens to be spent on assets for your game!", "image": "PLEASE ADD ME I NEED TO BE ADDED PLEASE", "url": "uhh idfk tbh"}
    ]

    selected_ad = random.choice(ads)
    return selected_ad

@app.route("/")
def home():
    return render_template("index.html", user=session.get("user"))

@app.route("/login")
def login():
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

    if not token_response.get("ok", False):
        return f"error: {token_response.get('error', 'no token recieved')}", 401
    
    user_response = requests.get(
        "https://slack.com/api/openid.connect.userInfo",
        headers={"Authorization": f"Bearer {token_response['access_token']}"}
    ).json()

    if not user_response.get("ok", False):
        return "unable to get user info", 401

    user_info = user_response.get("https://slack.com/user_id")
    if not user_info or (slack_id := user_info.get("sub")) not in ALLOWED_SLACK_IDS:
        return "unauthorized", 403

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (slack_id, name, email, settings)
                VALUES (%s, %s, %s, "{ads_enabled: true}"::jsonb)
                ON CONFLICT (slack_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email
                RETURNING id""",
                (slack_id, user_response.get("name", ""), user_response.get("email", ""))
            )
            user_id = cur.fetchone()[0]
            conn.commit()

    session["user"] = {
        "db_id": user_id,
        "id": slack_id,
        "name": user_response.get("name", ""),
        "email": user_response.get("email", "")
    }

    return redirect(url_for("home"))
@app.route("/loginorsignup")
def loginorsignup():
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        if 'user' not in session:
            flash("Login to create streams", "error")
            return redirect(url_for("login"))
        
        stream_name = request.form.get('stream_name')
        stream_description = request.form.get('stream_description')
        video_file = request.files.get('video')

        if not all([stream_name, stream_description, video_file]):
            flash('all fields are required', 'error')
            return redirect(url_for('create'))
        
        if not allowed_file(video_file.filename):
            flash('invalid file type', 'error')
            return redirect(url_for('create'))
        
        filename = secure_filename(video_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        try:
            video_file.save(save_path)
        except Exception as e:
            flash('error saving video', 'error')
            return redirect(url_for('create'))
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO streams
                (name, description, video_filename, likes, dislikes)
                VALUES (%s, %s, %s, 0, 0)""",
                (stream_name, stream_description, unique_filename)
            )
            conn.commit()
        except psycopg2.Error as e:
            flash('database error: could not create stream', 'error')
            return redirect(url_for('create'))
        finally:
            cur.close()
            conn.close()

        flash('stream created successfully', 'success')
        return redirect(url_for('home'))
    
    return render_template("create.html", user=session.get("user"))

@app.route('/videos/<filename>')
def get_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/createstream", methods=['POST'])
def createstream():
    stream_name = request.form.get('stream-title')
    stream_description = request.form.get('stream-desc')
    
    if not stream_name or not stream_description:
        return jsonify({"success": False, "message": "Stream name and description are required."}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO streams (name, description, likes, dislikes) VALUES (%s, %s, 0, 0)",
        (stream_name, stream_description)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"success": True, "message": "Stream created successfully!"}), 200

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

    return render_template("search.html", search_keywords=keywords, results=results, user=session.get("user"))

@app.route("/watch/<int:stream_id>")
def watch(stream_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT name, description, video_filename
            FROM streams WHERE id = %s
        """, (stream_id,))
        stream_data = cur.fetchone()

        if not stream_data:
            return "Stream not found", 404
        
        return render_template("watch.html",
            stream_name=stream_data[0],
            description=stream_data[1],
            video_url=url_for('get_video', filename=stream_data[2]))
    
    finally:
        cur.close()
        conn.close()

current_image = None

@app.route("/watchtest")
def watchtest():
    return render_template("watchtesting.html", user=session.get("user"))

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
        cur.execute("""
            INSERT INTO votes (user_id, stream_id, vote_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, stream_id) DO UPDATE SET vote_type = EXCLUDED.vote_type
            """, (user_id, stream_id, vote_type))
        
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