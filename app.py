import os
from dotenv import load_dotenv
from slack_bolt import App
import pygsheets
import pandas as pd
import re
import logging
import random
from datetime import date

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
    numerize=False,
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

def random_greeting() -> str:
    '''Returns a random greeting'''
    greetings = [
        "Hey",
        "Hi",
        "What's schlaying",
        "What poppin'",
        "Greetings",
        "DiversaHi",
        "Attention",
        "DiversaSLAY",
        "Howdy"
    ]
    return random.choice(greetings)


def spotter_leaderboard():
    '''
    Returns a leaderboard dataframe for the most spots
    columns = ['COUNT', 'RANK']
    indexed by SPOTTER, NAME
    '''
    global df_spot_history

    df_spot_history = df_spot_history[df_spot_history["FLAGGED"] == "FALSE"]
    counts = df_spot_history.groupby(['SPOTTER', 'NAME']).count()
    counts.rename(columns={'SPOTTED':'COUNT'}, inplace=True)
    counts = counts[['COUNT']]
    counts['RANK'] = counts['COUNT'].rank(ascending=False, method='dense')
    counts.sort_values(by='COUNT', inplace=True, ascending=False)
    return counts

def spotter_leaderboard_position_text(user: str) -> str:
    '''Return text describing the leaderboard position of the user for number of spots, and the person you're right behind.'''
    leaderboard = spotter_leaderboard()
    user_rank = leaderboard.loc[user]['RANK']

    if int(user_rank) == 1:
        return "Woohoo, you're 1st on the leaderboard." 

    user_in_front_id = leaderboard.index[leaderboard['RANK'] == int(user_rank) - 1].tolist()[0][0]
    return f"You're currently #{int(user_rank)} on the leaderboard, right behind <@{user_in_front_id}>."


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

    if message_ts in df_spot_history['TIME'].values:
        logger.warn("DUPLICATE: ", message_ts)
        return

    if len(member_ids) == 0:
        reply = f"{random_greeting()} <@{user}>, this DiversaSpot doesn't count because you didn't mention anyone! Delete and try again."
    
    elif message['files'][0]['filetype'] != 'jpg' and message['files'][0]['filetype'] != 'png':
        reply = f"{random_greeting()} <@{user}>, This DiversaSpot doesn't count because you didn't attach a JPG or a PNG file! Delete and try again."

    else:
        response = app.client.users_info(user=user)
        name = response["user"]["real_name"]
        df_spot_history = df_spot_history.append(
            {
                'TIME' : str(message['ts']),
                'SPOTTER' : user,
                'SPOTTED' : member_ids,
                'MESSAGE' : message['text'],
                'IMAGE' : message['files'][0]['url_private'],
                'FLAGGED' : 'FALSE',
                'NAME' : name
            },
            ignore_index=True
        )
        save_spot_history()

        reply = f"{random_greeting()} <@{user}>, you now have {count_spots(user)} DiversaSpots! {spotter_leaderboard_position_text(user)}"

    client.chat_postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=reply
    )


@app.message("diversabot leaderboard")
def post_leaderboard(message, client):
    leaderboard = spotter_leaderboard()
    leaderboard = leaderboard.reset_index()
    message_text = ""
    for i in range(10):
        row = leaderboard.iloc[i]
        message_text += f"*#{i + 1}: {row['NAME']}* with {row['COUNT']} spots \n"
    
    channel_id = message["channel"]

    blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": ":trophy:  DiversaSpot Leaderboard  :trophy:"
			}
		},
		{
			"type": "context",
			"elements": [
				{
					"text": f"*{date.today()}*",
					"type": "mrkdwn"
				}
			]
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": message_text
			}
		},
        {
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": "To see your individual stats, type 'diversabot stats'!"
				}
			]
		}
	]

    client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )

@app.message("diversabot stats")
def post_leaderboard(message, client):
    leaderboard = spotter_leaderboard()
    leaderboard = leaderboard.reset_index()
    user = message["user"]
    name = "None"
    message_text = ""
    rank = leaderboard.index[leaderboard['SPOTTER']==user].tolist()[0]
    for i in range(max(0, rank - 4), rank + 5):
        row = leaderboard.iloc[i]
        if row['SPOTTER'] == user:
            message_text += f"_*#{i + 1}: {row['NAME']} with {row['COUNT']} spots*_ \n"
            name = row['NAME']
        else:
            message_text += f"#{i + 1}: {row['NAME']} with {row['COUNT']} spots \n"
    
    channel_id = message["channel"]

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":trophy:  DiversaSpot Stats for {name} :trophy:"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "text": f"*{date.today()}*",
                    "type": "mrkdwn"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message_text
            }
        }
    ]

    client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )

@app.message("diversabot flag")
def flag_spot(message, client, logger):
    logger.warn(message)
    flagger = message['user']
    channel_id = message["channel"]

    if 'thread_ts' not in message:
        reply = f"{random_greeting()} <@{flagger}>, to flag a spot, you have to reply 'diversaspot flag' in the thread of the spot that you'd like to flag."
        message_ts = message['ts']
    else:
        spot_ts = message['thread_ts']
        message_ts = spot_ts
        if spot_ts not in df_spot_history['TIME'].values:
            reply = f"{random_greeting()} <@{flagger}>, this is not a valid DiversaSpot to flag!"
        else:
            spotter = df_spot_history.loc[df_spot_history['TIME'] == spot_ts, 'SPOTTER'].values[0]
            df_spot_history.loc[df_spot_history['TIME'] == spot_ts, 'FLAGGED'] = "TRUE"
            save_spot_history()
            reply = f"{random_greeting()} <@{spotter}>, this spot has been flagged by <@{flagger}> as they believe it is in violation of the \
                    official DiversaSpotting rules and regulations. \n \n \
                    If you would like to review the official DiversaSpotting rules and regulations, you can type 'diversabot rules' \n \n \
                    If you would like to dispute this flag, please @ Thomas Wang in this thread."
    
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=reply
    )


# @app.event("reaction_added")
# def flag_spot(event, client, logger):
#     global df_spot_history
#     logger.debug(event)

#     if event['reaction'] != "triangular_flag_on_post":
#         return

#     spot_user = event['item_user']
#     spot_ts = event["item"]["ts"]

#     df_spot_history.loc[df_spot_history['TIME'] == spot_ts, "FLAGGED"] = "TRUE"
#     logger.warn(df_spot_history.loc[df_spot_history['TIME'] == spot_ts, "FLAGGED"])
#     save_spot_history()

#     reply = f"{random_greeting()} <@{spot_user}>! This DiversaSpot is flagged and as a result, it is currently not being counted. Please remove all flags for this spot to be counted again."

#     channel_id = event["item"]["channel"]
#     client.chat_postMessage(
#         channel=channel_id,
#         thread_ts=spot_ts,
#         text=reply
#     )


@app.error
def error_logger(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")



if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))