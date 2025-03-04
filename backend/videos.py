from .varfile import *
from .functions import *
from flask import Blueprint 
import uuid
from datetime import datetime

## creating videos file if it does not exist 
if not path.exists(VIDEOS_JSON):
    with open(VIDEOS_JSON, 'w') as f:
        json.dump([], f)

## loading videos 
with open(VIDEOS_JSON, 'r') as f:
    videos = json.load(f)

## Fixing issues with videos 
for video in videos:
    if 'comments' not in video:
        video['comments'] = []
    if 'likes' not in video:
        video['likes'] = 0
    if 'liked_by' not in video:
        video['liked_by'] = []

with open(VIDEOS_JSON, 'w') as f:
    json.dump(videos, f, indent=2)

#### Routes #################################

videosBp= Blueprint("videos_routes", __name__)

@videosBp.route('/video')
def video():
    url_param = request.args.get('url', '')
    with open(VIDEOS_JSON, 'r') as f:
        videos = json.load(f)
    title = "Some cool video"
    desc = "Some cool description"
    thumbUrl = "test.com/test.img"
    duration="00:00"

    for i in videos:
        print(i['url'])
        if i['url'] == url_param:
            title = i['title'].replace("\n","\\n")
            desc = i['desc'].replace("\n","") 
            thumbUrl = i['url_thumb']
            duration=i['duration']
            print("Found a match!:")
            print(title)
            print(desc)
            print(thumbUrl)
    if url_param:
        clean_url = url_param.replace('/embed', '')
    else:
        clean_url=url_param

    context={
            "videoUrl":clean_url,
            "thumbUrl":thumbUrl,
            "title":title,
            "desc":desc,
            "duration":duration
            }

    return render_template('watch.html', user=session.get("user"),**context)


@videosBp.route('/create-video', methods=['POST'])
def create_video():
    for i in ['title', 'url', 'desc', 'thumb-url']:
        if i not in request.form:
            flash('Missing required fields', 'error')
            return redirect(url_for('create_video'))

    title = request.form['title']
    desc = request.form['desc']
    url = request.form['url']
    url_thumb = request.form['thumb-url']
    duration = request.form['video-duration']
    video_id = str(uuid.uuid4())
    video_data = {
        'id': video_id,
        'title': title,
        'desc': desc,
        'url': url,
        'url_thumb': url_thumb,
        'upload_date': datetime.now().isoformat(),
        'comments': [],
        'likes': 0,
        'duration':formatSeconds(duration),
        'liked_by': []
    }
    with open(VIDEOS_JSON, 'r') as f:
        videos = json.load(f)
    videos.append(video_data)
    with open(VIDEOS_JSON, 'w') as f:
        json.dump(videos, f, indent=2)
    flash('Video stream created successfully!', 'success')
    return redirect(url_for('create_video'))

@videosBp.route('/get-videos', methods=['GET'])
def get_videos():
    try:
        with open(VIDEOS_JSON, 'r') as f:
            videos = json.load(f)
        return jsonify({'status': 'success', 'videos': videos})
    except FileNotFoundError:
        return jsonify({'status': 'success', 'videos': []})
    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': 'Error reading video data'}), 500

@videosBp.route('/stream/<video_id>')
def stream_video(video_id):
    try:
        with open(VIDEOS_JSON, 'r') as f:
            videos = json.load(f)
        video = next((v for v in videos if v['id'] == video_id), None)
        if video:
            return jsonify({'status': 'success', 'video': video})
        return jsonify({'status': 'error', 'message': 'Video not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

