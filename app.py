import os
from dotenv import load_dotenv
from slack_bolt import App
import pygsheets
import pandas as pd
import re
import logging

'''
TO-DOs
- Option to flag erroneous diversaspots
- command to check current stats 
- command to check leaderboard stats
'''


"""

Environment Setup

"""

logging.basicConfig(level=logging.DEBUG)


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
# Saves spot_history dataframe to google sheets
def save_spot_history():
    '''Saves df_spot_history to excel sheet'''
    global df_spot_history
    sh_spot_history.set_dataframe(
        df=df_spot_history,
        start=(1,1),
        copy_head=True,
        extend=True,
        copy_index=False
    )

def find_all_mentions(msg: str) -> list:
    '''Returns all user_ids mentioned in msg'''
    member_ids = re.findall(r'<@([\w]+)>', msg, re.MULTILINE)
    return member_ids


def count_spots(user: str) -> int:
    '''Counts the number of DiversaSpots 'user' has accumulated'''
    global df_spot_history
    df = df_spot_history
    return len(df[df['SPOTTER'] == user])


"""

Routes

"""

@app.event({
    "type" : "message",
    "subtype" : "file_share"
})
def record_spot(message, client, logger):
    global df_spot_history

    user = message["user"]
    message_ts = message["ts"]
    channel_id = message["channel"]
    logger.debug(message)

    member_ids = find_all_mentions(message["text"])

    if len(member_ids) == 0:
        reply = f"Hey <@{user}>, this DiversaSpot doesn't count because you didn't mention anyone! Try again."
    
    elif message['files'][0]['filetype'] != 'jpg' and message['files'][0]['filetype'] != 'png':
        reply = f"Hiya <@{user}>, This DiversaSpot doesn't count because you didn't attach a JPG or a PNG file! Try again!"

    else:
        df_spot_history = df_spot_history.append(
            {
                'TIME' : message['ts'],
                'SPOTTER' : user,
                'SPOTTED' : member_ids,
                'MESSAGE' : message['text'],
                'IMAGE' : message['files'][0]['url_private']
            },
            ignore_index=True
        )
        save_spot_history()

        reply = f"Hey <@{user}>, you now have {count_spots(user)} DiversaSpots!"

    client.postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=reply
    )


@app.error
def error_logger(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")



if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))