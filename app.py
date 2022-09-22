import os
from dotenv import load_dotenv
from slack_bolt import App
import pygsheets
import pandas as pd
import re


"""

Environment Setup

"""

load_dotenv('.env')

app = App(
    token = os.environ.get('SLACK_AUTH_TOKEN'),
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
)

g_client = pygsheets.authorize(service_file='google-credentials.json')

sh = g_client.open('DiversaBot')

sh_spot_history = sh[0]
df_spot_history = sh_spot_history.get_as_df(
    has_header=True,
    index_column=None,
    nuumerize=True,
    include_tailing_empty=False,
    include_tailing_empty_rows=False
)

"""

Helper Functions

"""

def save_spot_history():
    global df_spot_history
    sh_spot_history.set_dataframe(
        df=df_spot_history,
        start=(1,1),
        copy_head=True,
        extend=True,
        copy_index=False
    )

def find_all_mentions(msg: str) -> list:
    member_ids = re.findall(r'<@([\w]+)>', msg, re.MULTILINE)
    return member_ids


def count_spots(user: str) -> int:
    global df_spot_history
    df = df_spot_history
    return len(df[df['SPOTTER'] == user])

"""

Routes

"""


@app.message("")
def record_spot(message, say):
    global df_spot_history
    member_ids = find_all_mentions(message["text"])
    user = message['user']

    if len(member_ids) == 0:
        # say(f"Hey <@{user}>, you didn't mention anyone! Try again.")
        return

    if 'files' not in message:
        say(f"Hey <@{user}>, you didn't attach an image to this message! Delete and try again.")
        return
    
    if message['files'][0]['filetype'] != 'jpg' and message['files'][0]['filetype'] != 'png':
        say(f"Hey <@{user}>, you didn't attach an image of the right type! Delete and try again.")
        return

    df_spot_history = df_spot_history.append(
        {
            'TIME' : message['ts'],
            'SPOTTER' : user,
            'SPOTTED' : member_ids,
            'MESSAGE' : message['text']
        }
    )
    save_spot_history()

    say(f"Hey <@{user}>, you now have {count_spots(user)} DiversaSpots!")


# Health Check
@app.message("diversabot health check")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    msg = message['text']
    print(message)
    say(f"I'm all up and running! Otherwise, let Tommy know.")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))