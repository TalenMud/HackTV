# HackTV

**HackTV** is a live streaming platform built by and for Hack Clubbers. Watch and show the time and effort you and other people put into their projects via livestreams!

## Features
 - Slack Authentication: Secure and simple SSO login using Hack Club Slack credentials! No more having to type in an email and password.
 - Stream Discovery: Search functionality with keywords! No windows 10 here.
 - Live Streaming: Stream with ease and have other hack clubbers watch them!
 - Ad System: Hack club style ads! Lets you know of the latest YSWSes!
 - Live Chat: Comments section during streams! If you spam it we will cancel you!

## Tech stack
### Backend:
 - Python/Flask
 - PostgreSQL (no airtable allowed!)
### Frontend:
 - TailwindCSS
 - HTML5
 - JavaScript

## Installation
1. **Prerequisites:**
     - PostgreSQL
     - Python 3.9+
     - Slack workspace with OAuth app configured

2. **Set up database:**
```bash
createdb hacktv
psql hacktv < postgre.sql
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configuration:**
Create an `.env` file with:
```env
FLASK_SECRET_KEY=a_randomly_generated_key
DATABASE_URL=postgresql:///hacktv
SLACK_CLIENT_ID=client_id_of_oauth_bot
SLACK_CLIENT_SECRET=slack_secret_of_oauth_bot
SLACK_REDIRECT_URI=http://localhost:5000/slack/callback
ALLOWED_SLACK_IDS=user_slack_ids
```

## Running the app
```bash
flask run --port 5000
```

## File heirarchy

```heirarchy
hacktv/
├── static/
│   ├── scripts/
|   |   ├── dots.js
|   |   └── script.js
│   ├── styles/
|   |   └── main.css
│   └── main.css
├── templates/
│   ├── explore.html
│   ├── history.html
│   ├── index.html
│   ├── search.html
│   ├── settings.html
│   ├── stream.html
│   └── watch.html
├── .env
├── .gitignore
├── HACK_TV.code-workspace
├── postgre.sql
├── README.md
├── requirements.txt
├── server.py
└── sql.py
```

## Contributing
Feel free to contribute to our code any time! Here's how:
1. Fork the repository to your account
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Add the feature to the readme
4. Commit your changes (`git commit -m 'Add an amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a pull request

*Please make sure that your work has clean, commented code and the commit messages are meaningful.*

## Versions panel
### Version 1.0.?
<!-- Maybe we could put here all the features available on V1 -->

### HackTV was built by these people:
 - Shibam Roy (@Shibam Roy)
 - Marwane (@M_)
 - Ewoud Van Vooren (@Ewoud Tinkerboy)
 - Talen Mudaly (@TalenMud)
 - Matthew F (@GamerC0der)
 - @m5kro
<br>
And others who contributed through PRs! (none yet pls make some)