from flask import Blueprint
from backend.varfile import *

frontendBp= Blueprint("frontend_bp", __name__)

@frontendBp.route("/")
def home():
    return render_template("index.html", user=session.get("user"))

@frontendBp.route('/settings', methods=['GET', 'POST']) 
def account():
    return render_template("settings.html", ads_enabled=True, user="Test")

@frontendBp.route('/history')  
def history():
    return render_template("history.html", user=session.get("user")) 

@frontendBp.route("/myvideos")
def myvids():
    return render_template("myvids.html",user=session.get("user"))


@frontendBp.route("/explore")
def explore():
    return render_template("explore.html", user=session.get("user"))

@frontendBp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        email = request.form.get('email')
        message = request.form.get('message')
        
        payload = {
            "email": email,
            "feedback": message,
        }
        
        response = requests.post(SLACK_HOOK_URL, json=payload)
        
        if response.status_code == 200:
            flash('Thank you for your feedback!', 'success')
        else:
            flash('There was an error sending your feedback. Please try again later.', 'error')
        
        return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@frontendBp.route("/user/<username>")
def user(username):
    return render_template("user.html", username=username)


@frontendBp.route("/loginorsignup")
def loginorsignup():
    return render_template("login.html")

@frontendBp.route("/search/<keywords>")
def search(keywords):
    return render_template("search.html", search_keywords=keywords)

@frontendBp.route("/create", methods=['POST', 'GET'])
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

# unused/not required
# @app.route('/index.html')
# def index():
#     return redirect(url_for('home'))

# @frontendBp.route('/beta/stream')  
# def newstream():
#     return render_template("newstream.html", user=session.get("user")) 
