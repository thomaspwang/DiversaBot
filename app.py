import os
from dotenv import load_dotenv
from slack_bolt import App

load_dotenv('.env')

app = App(
    token = os.environ.get('SLACK_AUTH_TOKEN'),
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
)


# Health Check
@app.message("diversabot health check")
def message_hello(say):
    # say() sends a message to the channel where the event was triggered
    say(f"I'm all up and running! Otherwise, let Tommy know.")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))