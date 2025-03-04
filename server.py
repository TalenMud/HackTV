from flask import Flask,Blueprint,send_from_directory
from os import path

# local modules
from backend.varfile import *
from backend.backend_routes import *
from backend.frontend_routes import *
from backend.logins import *
from backend.videos import *

## initialising flask application
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = FLASK_KEY

## configuring application
app.config['UPLOAD_FOLDER'] = path.join(app.root_path, 'uploads', 'videos')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

## Routes #####################################

#Registering routes
app.register_blueprint(loginsBp)
app.register_blueprint(backendBp)
app.register_blueprint(frontendBp)
app.register_blueprint(videosBp)

@app.route('/videos/<filename>')
def get_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)

###| unused code |##############################################################

# @app.route("/login")
# def login():
#     slack_auth_url = (
#         f"https://slack.com/openid/connect/authorize?"
#         f"response_type=code&"
#         f"client_id={SLACK_CLIENT_ID}&"
#         f"scope=openid%20profile%20email&"
#         f"redirect_uri={SLACK_REDIRECT_URI}"
#     )
#     return redirect(slack_auth_url)

# @app.route("/slack/callback")
# def slack_callback():
#     if not (code := request.args.get("code")):
#         return "missing auth code", 400
#     token_response = requests.post(
#         "https://slack.com/api/openid.connect.token",
#         data={
#             "client_id": SLACK_CLIENT_ID,
#             "client_secret": SLACK_CLIENT_SECRET,
#             "code": code,
#             "redirect_uri": SLACK_REDIRECT_URI
#         },
#     ).json()
#     if not token_response.get("ok", False):
#         return f"error: {token_response.get('error', 'no token recieved')}", 401
#     user_response = requests.get(
#         "https://slack.com/api/openid.connect.userInfo",
#         headers={"Authorization": f"Bearer {token_response['access_token']}"}
#     ).json()
#     if not user_response.get("ok", False):
#         return "unable to get user info", 401
#     user_info = user_response.get("https://slack.com/user_id")
#     if not user_info or (slack_id := user_info.get("sub")) not in ALLOWED_SLACK_IDS:
#         return "unauthorized", 403
#     with get_db_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 """INSERT INTO users (slack_id, name, email, settings)
#                 VALUES (%s, %s, %s, "{ads_enabled: true}"::jsonb)
#                 ON CONFLICT (slack_id) DO UPDATE SET
#                 name = EXCLUDED.name,
#                 email = EXCLUDED.email
#                 RETURNING id""",
#                 (slack_id, user_response.get("name", ""), user_response.get("email", ""))
#             )
#             user_id = cur.fetchone()[0]
#             conn.commit()
#     session["user"] = {
#         "db_id": user_id,
#         "id": slack_id,
#         "name": user_response.get("name", ""),
#         "email": user_response.get("email", "")
#     }
#     return redirect(url_for("home"))

# @app.route("/stream", methods=["POST", "GET"])
# def streams():
#     if request.method == "POST":
#         title = request.form['stream-title']
#         description = request.form['stream-desc']
#         data = {"title": title, "desc": description, "streamer": True}
#         return render_template("watch.html", data=data)
#     data = {"title": None, "desc": None, "streamer": False}
#     return render_template("stream.html", data=data, user=session.get("user"))


# @app.route("/create", methods=['POST', 'GET'])
# def create():
#     if request.method == 'POST':
#         if 'user' not in session:
#             flash("Login to create streams", "error")
#             return redirect(url_for("login"))
#         stream_name = request.form.get('stream_name')
#         stream_description = request.form.get('stream_description')
#         video_file = request.files.get('video')
#         if not all([stream_name, stream_description, video_file]):
#             flash('all fields are required', 'error')
#             return redirect(url_for('create'))
#         if not allowed_file(video_file.filename):
#             flash('invalid file type', 'error')
#             return redirect(url_for('create'))
#         filename = secure_filename(video_file.filename)
#         unique_filename = f"{uuid.uuid4().hex}_{filename}"
#         save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
#         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#         try:
#             video_file.save(save_path)
#         except Exception as e:
#             flash('error saving video', 'error')
#             return redirect(url_for('create'))
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute(
#                 """INSERT INTO streams
#                 (name, description, video_filename, likes, dislikes)
#                 VALUES (%s, %s, %s, 0, 0)""",
#                 (stream_name, stream_description, unique_filename)
#             )
#             conn.commit()
#         except psycopg2.Error as e:
#             flash('database error: could not create stream', 'error')
#             return redirect(url_for('create'))
#         finally:
#             cur.close()
#             conn.close()
#         flash('stream created successfully', 'success')
#         return redirect(url_for('home'))
#     return render_template("create.html", user=session.get("user"))

# @app.route("/createstream", methods=['POST'])
# def createstream():
#     stream_name = request.form.get('stream-title')
#     stream_description = request.form.get('stream-desc')
#     if not stream_name or not stream_description:
#         return jsonify({"success": False, "message": "Stream name and description are required."}), 400
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute(
#         "INSERT INTO streams (name, description, likes, dislikes) VALUES (%s, %s, 0, 0)",
#         (stream_name, stream_description)
#     )
#     conn.commit()
#     cur.close()
#     conn.close()
#     return jsonify({"success": True, "message": "Stream created successfully!"}), 200
# @app.route("/watch/<int:stream_id>")
# def watch(stream_id):
#     conn = get_db_connection()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             SELECT name, description, video_filename
#             FROM streams WHERE id = %s
#         """, (stream_id,))
#         stream_data = cur.fetchone()
#         if not stream_data:
#             return "Stream not found", 404
#         return render_template("watch.html",
#             stream_name=stream_data[0],
#             description=stream_data[1],
#             video_url=url_for('get_video', filename=stream_data[2]))
#     finally:
#         cur.close()
#         conn.close()

# @app.route('/stream/sendimg', methods=['POST'])
# def receive_image():
#     global current_image
#     if 'image' in request.files:
#         current_image = request.files['image'].read()
#         return 'Image received', 200
#     return 'No image found', 400

# @app.route('/activestreams')
# def active_streams():
#     category_id = request.args.get('category_id')
#     conn = get_db_connection()
#     cur = conn.cursor()
#     if category_id:
#         cur.execute("SELECT streams.name, streams.description, streams.likes, streams.dislikes FROM streams WHERE category_id = %s", (category_id,))
#     else:
#         cur.execute("SELECT streams.name, streams.description, streams.likes, streams.dislikes FROM streams")
#     streams = [{"name": row[0], "description": row[1], "likes": row[2], "dislikes": row[3]} for row in cur.fetchall()]
#     cur.close()
#     conn.close()
#     return jsonify({"streams": streams})
#
# @app.route('/stream/getimg', methods=['GET'])
# def get_image():
#     if current_image:
#         return send_file(io.BytesIO(current_image), mimetype='image/jpeg')
#     return 'No image available', 200
#
# @app.route("/stream/<int:stream_id>/like", methods=['POST'])
# def handle_vote(stream_id):
#     if "user" not in session:
#         return "unauthorized", 401
#     vote_type = request.form.get("type")
#     if vote_type not in ("like", "dislike"):
#         return "invalid vote type", 400
#     user_id = session["user"]["id"]
#     conn = get_db_connection()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             INSERT INTO votes (user_id, stream_id, vote_type)
#             VALUES (%s, %s, %s)
#             ON CONFLICT (user_id, stream_id) DO UPDATE SET vote_type = EXCLUDED.vote_type
#             """, (user_id, stream_id, vote_type))
#         cur.execute("""
#             UPDATE streams SET
#                     likes = (SELECT COUNT(*) FROM votes WHERE stream_id = %s AND vote_type = "like"),
#                     dislikes = (SELECT COUNT(*) FROM votes WHERE stream_id = %s AND vote_type = "dislike")
#             WHERE id = %s
#         """), (stream_id, stream_id, stream_id)
#         conn.commit()
#         return "vote recorded", 200
#     except psycopg2.Error as e:
#         conn.rollback()
#         return f"database error: {e}", 500
#     finally:
#         cur.close()
#         conn.close()
#
# @app.route("/stream/<int:stream_id>/votes")
# def get_votes(stream_id):
#     conn = get_db_connection()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             SELECT likes, dislikes FROM streams WHERE id = %s
#         """, (stream_id,))
#         result = cur.fetchone()
#         return {
#             "likes": result[0] if result else 0,
#             "dislikes": result[1] if result else 0
#         }
#     finally:
#         cur.close()
#         conn.close()

# @app.route('/categories')
# def get_categories():
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("SELECT id FROM categories")
#     categories = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
#     cur.close()
#     conn.close()
#     return jsonify({"categories": categories})

