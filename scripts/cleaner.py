import pygsheets

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

if __name__ == "__main__":
     print(df_spot_history)
     df_spot_history = df_spot_history.drop_duplicates()
     print(df_spot_history)
     save_spot_history()
     