import os
from dotenv import load_dotenv
import slack
from flask import Flask

load_dotenv()

SLACK_TOKEN = os.environ.get('SLACK_AUTH_TOKEN')
SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')

app = Flask(__name__)

# slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)
client = slack.WebClient(token = SLACK_TOKEN)
# client.chat_postMessage(channel='#diversaspotting',text='Get ready slayers.')

@app.route("/")
def start_message():
    return "DiversaConnected!"

if __name__ == "__main__":
    app.run(debug=True)