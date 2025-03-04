def formatSeconds(s):
    try:
        secs=int(s)
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60
        ifhr=""
        if hours>0:
            ifhr=":"
        return f"{hours}{ifhr}{minutes}:{seconds}"
    except:
        return s

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
