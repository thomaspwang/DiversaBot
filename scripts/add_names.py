import os
from dotenv import load_dotenv
from slack_bolt import App
import pygsheets
import pandas as pd
import re
import logging
import random


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
df = sh_spot_history.get_as_df(
    has_header=True,
    index_column=None,
    nuumerize=True,
    include_tailing_empty=False,
    include_tailing_empty_rows=False
)

for i, row in df.iterrows():
    userid = df.at[i, "SPOTTER"]
    response = app.client.users_info(user=userid)
    name = response["user"]["real_name"]
    df.at[i, "NAME"] = name

sh_spot_history.set_dataframe(
    df=df,
    start=(1,1),
    copy_head=True,
    extend=True,
    copy_index=False
)

