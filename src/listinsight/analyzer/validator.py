from pathlib import Path
import pandas as pd
from pandera import DataFrameSchema, Column, Check, Index, Timestamp

from pandera.io import from_frictionless_schema


def readSchema(file: str) -> DataFrameSchema:
    file_path = Path(file)

    if not file_path.exists():
        return

    schema = from_frictionless_schema(file_path)
    return schema








