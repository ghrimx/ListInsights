import pandas as pd

def days(df):
    df[['start_date','end_date']] = df[['start_date','end_date']].apply(pd.to_datetime)