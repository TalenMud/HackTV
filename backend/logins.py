from os import path
import requests
from flask import Blueprint,make_response

from backend.varfile import *

# Creating logins file if it does not exist
if not path.exists(LOGIN_FILE):
    with open(LOGIN_FILE, 'w') as f:
        json.dump({}, f)

## Login functions
def load_logins():
    with open(LOGIN_FILE, 'r') as f:
        return json.load(f)

def save_logins(logins):
    with open(LOGIN_FILE, 'w') as f:
        json.dump(logins, f, indent=4)

####| Routes |#################################

loginsBp= Blueprint("login_routes", __name__)

@loginsBp.route('/api/login', methods=['POST'])
def loginsignup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
    logins = load_logins()

    if username in logins and logins[username] == password:
        response = make_response(jsonify({'status': 'success', 'message': 'Login successful'}))
        response.set_cookie('username', username, max_age=3600, httponly=True, secure=False)
        return response

    return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

@loginsBp.route('/api/signup', methods=['POST'])
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

