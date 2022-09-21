import os
from dotenv import load_dotenv
from slack_bolt import App

load_dotenv('.env')

app = App(token = os.environ.get('SLACK_AUTH_TOKEN'), signing_secret = os.environ.get('SLACK_SIGNING_SECRET'))


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))