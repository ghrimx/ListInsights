import pandas as pd
import numpy as np

sample_output = {
  "overreported": {
    "description": "what's over reported case",
    "data": [
      "123",
      "456",
      "678"
    ]
  },
  "underreported": {
    "description": "what's under reported case",
    "data": [
      "321",
      "654",
      "765"
    ]
  }
}

class Result:
    def __init__(self, tagname: str, desc: str, data: list):
        self.tagname = tagname
        self.desc = desc
        self.data = []

serious_cases = []
nonserious_cases = []

df_master = pd.DataFrame()
df_event = pd.DataFrame()
df_assessment = pd.DataFrame()
df_report = pd.DataFrame()

def initialize(_master: pd.DataFrame, _report: pd.DataFrame):
    global df_master
    global df_report
    df_master = _master
    df_report = _report

def preprocessing():
    global serious_cases
    global nonserious_cases
    serious_cases = df_master.loc[df_master['CASE_SERIOUSNESS'] == "Serious",['CASE_ID']].values.tolist()
    nonserious_cases = df_master.loc[df_master['CASE_SERIOUSNESS'] == "Not Serious",['CASE_ID']].values.tolist()
    

def rule_1() -> Result:
    tagname = "Late & Serious"
    description = "Case submitted Late to EV"
    
    #convert columns to datetime
    df_report[['RECEIPT_DATE','EMA_DATE']] = df_report[['RECEIPT_DATE','EMA_DATE']].apply(pd.to_datetime)

    #calculate difference between dates
    df_report['DAYS_TO_EV'] = (df_report['EMA_DATE'] - df_report['EMA_DATE']) / np.timedelta64(1, 'D')

    data = df_report[(df_report['CASE_ID'].isin(serious_cases)) & (df_report['DAYS_TO_EV'] > 15)]["CASE_ID"].values.tolist()

    if len(data) > 0:
        result = Result(tagname, description, data)
    else: 
        result = None

    return result

def rule_2():
    print("rule_2")
    return None

# Register function
rules = [rule_1, 
         rule_2]






