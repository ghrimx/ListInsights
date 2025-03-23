
from src.analyzer.rules import rules, Result, initialize, preprocessing
import pandas as pd


def execute():

    initialize(df_master, df_report)

    preprocessing()

    for fn in rules:
        r: Result = fn()

        print(r)