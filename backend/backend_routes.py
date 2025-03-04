from flask import Blueprint
from backend.varfile import *
import uuid
from datetime import datetime
from random import choice

backendBp= Blueprint("backend_bp", __name__)

@backendBp.route('/create-comment', methods=['POST'])
def create_comment():
    data = request.get_json()
    video_id = data.get('video_id')
    comment_text = data.get('comment')
    username = data.get('username')

    if not video_id or not comment_text or not username:
        return jsonify({'status': 'error', 'message': 'Video ID, comment, and logged-in user are required'}), 400

    with open(VIDEOS_JSON, 'r') as f:
        videos = json.load(f)

    video = next((v for v in videos if v['id'] == video_id), None)

    if not video:
        return jsonify({'status': 'error', 'message': 'Video not found'}), 404

    comment = {
        'id': str(uuid.uuid4()),
        'username': username,
        'text': comment_text,
        'timestamp': datetime.now().isoformat()
    }

    video['comments'].append(comment)

    with open(VIDEOS_JSON, 'w') as f:
        json.dump(videos, f, indent=2)

    return jsonify({'status': 'success', 'message': 'Comment added successfully', 'comment': comment}), 201

@backendBp.route('/delete-comment', methods=['POST'])
def delete_comment():
    data = request.get_json()
    comment_id = data.get('comment_id')
    if not comment_id:
        return jsonify({'status': 'error', 'message': 'Comment ID is required'}), 400
    
    with open(VIDEOS_JSON, 'r') as f:
        videos = json.load(f)
    
    for video in videos:
        comment_to_delete = next((c for c in video['comments'] if c['id'] == comment_id), None)
        if comment_to_delete:
            video['comments'].remove(comment_to_delete)
            with open(VIDEOS_JSON, 'w') as f:
                json.dump(videos, f, indent=2)
            return jsonify({'status': 'success', 'message': 'Comment deleted successfully'}), 200
    
    return jsonify({'status': 'error', 'message': 'Comment not found'}), 404

@backendBp.route('/toggle-like', methods=['POST'])
def toggle_like():
    data = request.get_json()
    video_id = data.get('video_id')
    username = data.get('username')
    action = data.get('action')

    if not video_id or not username or not action:
        return jsonify({'status': 'error', 'message': 'Video ID, username, and action are required'}), 400
    
    if action not in ['like', 'unlike']:
        return jsonify({'status': 'error', 'message': 'Invalid action'}), 400

    with open(VIDEOS_JSON, 'r') as f:
        videos = json.load(f)

    video = next((v for v in videos if v['id'] == video_id), None)
    if not video:
        return jsonify({'status': 'error', 'message': 'Video not found'}), 404

    liked_by = video.get('liked_by', [])
    likes = video.get('likes', 0)

    if action == 'like' and username not in liked_by:
        liked_by.append(username)
        likes += 1
    elif action == 'unlike' and username in liked_by:
        liked_by.remove(username)
        likes -= 1

    video['liked_by'] = liked_by
    video['likes'] = likes

    with open(VIDEOS_JSON, 'w') as f:
        json.dump(videos, f, indent=2)

    return jsonify({
        'status': 'success',
        'message': 'Like toggled successfully',
        'likes': likes
    }), 200

@backendBp.route("/getad")
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
    ads =  [
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
    selected_ad = choice(ads)
    return selected_ad

@backendBp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))
