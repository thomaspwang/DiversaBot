import os
from dotenv import load_dotenv
from slack_bolt import App
import pygsheets
import pandas as pd


"""

Environment Setup

"""

load_dotenv('.env')

app = App(
    token = os.environ.get('SLACK_AUTH_TOKEN'),
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
)

# g_client = pygsheets.authorize(service_file='C:\\Users\\tommy\\Desktop\DiversaBot\\diversabot-363300-f4b5abc8a0c8.json')

# sh = g_client.open('DiversaBot')

# sh_spot_history = sh[0]
# df_spot_history = sh_spot_history.get_as_df(
#     has_header=True,
#     index_column=None,
#     nuumerize=True,
#     include_tailing_empty=False,
#     include_tailing_empty_rows=False
# )

# """

# Helper Functions

# """

# def save_spot_history():
#     sh_spot_history.set_dataframe(
#         df=df_spot_history,
#         start=(1,1),
#         copy_head=True,
#         extend=True,
#         copy_index=False
#     )



"""

Routes

"""




# Health Check
@app.message("diversabot health check")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    msg = message['text']
    print(msg)
    say(f"I'm all up and running! Otherwise, let Tommy know.")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))