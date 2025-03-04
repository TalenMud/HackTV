from os import getenv,path
from dotenv import load_dotenv

## Other common imports
from flask import request,jsonify,redirect,render_template_string,render_template,session,url_for,flash
import json
import psycopg2

load_dotenv()

## Getting all environment variables
SLACK_CLIENT_ID = getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = getenv("SLACK_REDIRECT_URI")
DATABASE_URL = getenv("DATABASE_URL")
ALLOWED_SLACK_IDS = getenv("ALLOWED_SLACK_IDS", "").split(",")
FLASK_KEY=getenv("FLASK_SECRET_KEY")
SLACK_HOOK_URL = "https://hooks.slack.com/triggers/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"

LOGIN_FILE = 'logins.json'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
VIDEOS_JSON = 'videos.json'

current_image = None
streams_data = "Test.Test:Test2.Test"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)
