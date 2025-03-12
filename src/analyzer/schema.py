import pandas as pd
from pandera import DataFrameSchema, Column, Check, Index, Timestamp
from pandera.engines import pandas_engine



MASTER_SCHEMA = DataFrameSchema(
    {
        "CASE_ID": Column(int),
        "INIT_REPT_DATE": Column(dtype=pandas_engine.DateTime(to_datetime_kwargs = {"format":"%Y-%m-%d"}), coerce=True),
        "CASE_TYPE": Column(pd.CategoricalDtype),
        "CREATION_TS": Column(dtype=pandas_engine.DateTime(to_datetime_kwargs = {"format":"%Y-%m-%d %H:%M:%S"}), coerce=True),
    },
    index=Index(int),
    strict='filter',
    coerce=True,
)