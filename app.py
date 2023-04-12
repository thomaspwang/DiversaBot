import os
from dotenv import load_dotenv
from slack_bolt import App
import pygsheets
import pandas as pd
import re
import logging
import random
from datetime import date
import ast

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
    columns = ['SPOTTER', 'COUNT', 'RANK', 'NAME']
    indexed by number
    '''
    global df_spot_history

    df_spot_history = df_spot_history[df_spot_history["FLAGGED"] == "FALSE"]
    counts = df_spot_history.groupby('SPOTTER').count()
    counts.rename(columns={'SPOTTED':'COUNT'}, inplace=True)
    counts = counts[['COUNT']]
    counts.sort_values(by='COUNT', inplace=True, ascending=False)
    counts['RANK'] = counts['COUNT'].rank(ascending=False, method='first')
    counts = counts.reset_index()
    counts['NAME'] = counts['SPOTTER'].apply(find_name)
    return counts

def spotter_leaderboard_position_text(user: str) -> str:
    '''Return text describing the leaderboard position of the user for number of spots, and the person you're right behind.'''
    leaderboard = spotter_leaderboard()
    user_rank = int(leaderboard[leaderboard['SPOTTER'] == user]['RANK'].iloc[0])

    if user_rank == 1:
        return "Woohoo, you're 1st on the leaderboard." 

    user_in_front_id = leaderboard[leaderboard['RANK'] == user_rank - 1]['SPOTTER'].iloc[0]
    return f"You're currently #{user_rank} on the leaderboard, right behind *{find_name(user_in_front_id)}*"

def find_name(user_id : str) -> str:
    global app

    return app.client.users_profile_get(user=user_id)['profile']['real_name']

def eval_string_to_list(str_lst):
    #str could be a string or a list, idk it's a bug this is a lazy fix
    if type(str_lst) == str:
        return eval(str_lst)
    else:
        return str_lst


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
@app.message("diversabot team leaderboard")
def post_team_leaderboard(message, client):
    leaderboard = spotter_leaderboard()

    teams = {
        "Checkr" : [
            "Emily Zhang",
            "Priya Kamath",
            "James Reyna",
            "Andrew Crawley",
            "Kaylene Son",
            "Serah Almeyda",
            "Nick Melamed",
            "Evan Quan",
            "Alba Joy",
            "Marden Escobar Deleon"
        ],
        "Hi-Five" : [
            "Sharon Jihn",
            "Urvi Dhala",
            "Thien-Kim Dang",
            "Lily Yang",
            "Trishala Jain",
            "Bradley Tian",
            "Ira Puri",
            "Sera Goksal",
            "Oliver Johansson",
            "Gigi Huang"
        ],
        "Indoxi" : [
            "Emily Xiao",
            "Ruofu Li",
            "Joanna Huynh",
            "Enya Do",
            "Patrick Zhu",
            "No longer Prez",
            "Soph Ma",
            "Justin Li",
            "Clara Tu",
            "Rachel Hua"
        ],
        "Fabletics" : [
            "Derrick Cai",
            "Eileen Chang",
            "Joshua Chuang",
            "Ria Nakahara",
            "Daewon Kwon",
            "Joseph Schull",
            "Dylan Huynh",
            "Sameen Shah",
            "Daniel Jiang",
            "Caleb Kim",
            "Manuel Neumayer"
        ],
        "Exec" : [
            "Thomas Wang",
            "Isabela Moise",
            "Chloe Kim",
            "Jeremy Li",
            "Aidan Curran",
            "Hanson Li",
            "Michelle Tran"
        ],
        "Account Managers" : [
            "Daniel Yao",
            "Luke Wu",
            "Joshua Paul"
        ]
    }
    
    people = {}
    for ID in pd.unique(leaderboard["SPOTTER"]):
        name = find_name(ID)
        for team in teams:
            if name in teams[team]:
                people[ID] = team

    
    team_points = {
        "Account Managers" : 0,
        "Exec" : 0,
        "Fabletics" : 0,
        "Checkr" : 0,
        "Indoxi" : 0,
        "Hi-Five" : 0
    }

    for p, t in people.items():
        points = int(leaderboard[leaderboard['SPOTTER'] == p]["COUNT"])
        team_points[t] += points

    team_points = dict(sorted(team_points.items(), key=lambda item: item[1], reverse = True))

    message_text = ""
    for team, points in team_points.items():
        message_text += f"*{team}*: {points} spots \n\n"

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
				},
                {
					"type": "mrkdwn",
					"text": "To see the individual leaderboard, type 'diversabot leaderboard!'"
				}
			]
		}
	]

    channel_id = message["channel"]
    client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )



@app.message("diversabot leaderboard")
def post_leaderboard(message, client):
    leaderboard = spotter_leaderboard()
    message_text = ""
    size = len(leaderboard)
    for i in range(min(size, 10)):
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
def post_stats(message, client):
    global df_spot_history
    user = message["user"]
    message_text = ""
    name = find_name(user)

    # Leaderboard
    if user not in df_spot_history['SPOTTER'].values:
        message_text = "You have not spotted anyone yet :("
    else:
        leaderboard = spotter_leaderboard()
        rank = int(leaderboard[leaderboard['SPOTTER']==user]['RANK'].iloc[0])
        size = len(leaderboard)
        for i in range(max(0, rank - 5), min(size, rank + 4)):
            row = leaderboard.iloc[i]
            if row['SPOTTER'] == user:
                message_text += f"_*#{i + 1}: {row['NAME']} with {row['COUNT']} spots*_ \n"
                name = row['NAME']
            else:
                message_text += f"#{i + 1}: {row['NAME']} with {row['COUNT']} spots \n"

    # Spot stats
    df = df_spot_history[df_spot_history["FLAGGED"] == "FALSE"]
    df['SPOTTED'] = df['SPOTTED'].apply(eval_string_to_list)
    df = df.explode('SPOTTED')
    df = df[df['SPOTTED'] == user]

    num_spots = len(df)

    df = df.groupby('SPOTTER').count()

    if len(df) == 0:
        message_text_2 = ":camera_with_flash: No one has spotted you yet ... so sneaky of you!"

    else:
        max_spotter_id = df.idxmax()['TIME']
        max_spotter_count = df.loc[max_spotter_id]['TIME']
        message_text_2 = f":camera_with_flash: You've been spotted a total of {num_spots} times!\n\n:heart_eyes: *{find_name(max_spotter_id)}* has spotted you the most with {max_spotter_count} spots."

    
    channel_id = message["channel"]


    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":chart_with_upwards_trend: DiversaSpot Stats for {name} :chart_with_upwards_trend:"
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
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message_text_2
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
            reply = f"{random_greeting()} <@{spotter}>, this spot has been flagged by <@{flagger}> as they believe it is in violation of the official DiversaSpotting rules and regulations. If you would like to review the official DiversaSpotting rules and regulations, you can type 'diversabot rules'. If you would like to dispute this flag, please @ Thomas Wang in this thread with a relevant explanation."
    
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=message_ts,
        text=reply
    )

@app.message("diversabot miss")
def post_miss(message, client):
    global df_spot_history
    user = message["user"]
    tagged = find_all_mentions(message['text'])
    channel_id = message['channel']
    message_ts = message['ts']

    if len(tagged) == 0:
        message_text = "Please tag someone to use this command!"
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=message_ts,
            text=message_text
        )
    elif len(tagged) > 1:
        message_text = "Please tag only one person to use this command!"
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=message_ts,
            text=message_text
        )
    else:
        tagged_user = tagged[0]

        df = df_spot_history[df_spot_history["FLAGGED"] == "FALSE"]
        df['SPOTTED'] = df['SPOTTED'].apply(eval_string_to_list)
        df = df.explode('SPOTTED')
        df = df[df['SPOTTED'] == tagged_user]

        message_text = f"Aww ... you miss {find_name(tagged_user)}? :pleading_face::point_right::point_left:"

        if (len(df) == 0):
            image_url = "Too bad ... they're too elusive and haven't been spotted yet :("
        else:
            image_url = df.iloc[random.randint(0, len(df))]['IMAGE']

        blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message_text
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "It's okay, here's a picture of them to remind you <3"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": image_url
                    }
                }
                # {
                #     "type": "image",
                #     "image_url": image_url,
                #     "alt_text": "picture of your fav person"
                # }
            ]

        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks
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

@app.message("diversabot help")
def post_help(message, client):
    blocks = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Hi there! 👋 I'm DiversaBot. \n\nHere are some things I can do:"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*📸 DiversaSpotting:* Found the DiversaFam in the wild? Upload a picture of them along and tag them in the #diversaspotting channel to secure those delicious points."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*🚩 Flag:* Detected an illegal DiversaSpot? Reply *diversabot flag* in the thread."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*🏆 Leaderboard:* If you want to see the top 10 DiversaSpotters, type *diversaspot leaderboard*."
			}
		},
        {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*🏆 Team Leaderboard:* If you want how teams are stacking against one another, type *diversaspot team leaderboard*."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*📈 Stats:* If you want to view your own stats, type *diversabot stats*."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*🥺 Miss:* Miss anyone? I'll give you a random photo of them if type *diversabot miss @ThatPerson*."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*📖 Rules:* Need a refresh on DiversaSpotting rules? Type *diversabot rules*."
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": "❓ View my commands anytime by typing *diversabot help*!"
				}
			]
		}
	]
    channel_id = message["channel"]
    client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )

@app.message("diversabot rules")
def post_rules(message, client):
    blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "DiversaSpot Official Rules & Regulations"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "It is everyone’s responsability to hold everyone accountable for following the rules! If you see a post that violates any of the following rules and regulations, you should reply ‘diversabot flag’ in the thread. Please use this command in good faith!"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Rule 1:* The person being spotted must be identifiable. Some ambiguity is allowed (i.e their back is turned but we can tell it’s them, half their face is showing, etc), but total ambiguity is not (i.e the image is completely blurry, they’re too small to discern, their back is turned but they could literally be any asian dude with a black hoodie, etc)."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Rule 2:* Spotting multiple DT members in the same group or vicinity counts a 1 spot. Specifically, you cannot get multiple points from spotting the same group."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Rule 3:* You cannot get multiple points for spotting individuals or groups at the same function. For example, you cannot spot a project team meeting at Moffitt and then spot them again an hour later. As another example, if you’re hanging out with DT member(s), you cannot spot them more than once just because you moved locations. In cognition that this rule is subjective and ambiguous, it is recommended to post a spot anyways if you’re unsure whether it violates this rule."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Rule 4:* In the case of a spotting duel where two (or more) people are attempting to spot one another, the winner is the first person to successfully post their spot in the slack channel, and everyone else’s spots do not count."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Rule 5:* The project team with the most combined DiversaSpot will be rewarded with ... TBD"
			}
		}
	]
    channel_id = message["channel"]
    client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )

@app.error
def error_logger(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")



if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))