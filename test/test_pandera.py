import pandas as pd
import pandera as pa
import json

from src.analyzer.validator import readSchema
from src.analyzer.schema import MASTER_SCHEMA

sample_file = r"C:\Users\debru\Documents\GitHub\ListInsights\sample\sample.csv"
schema_file  = r"C:\Users\debru\Documents\GitHub\ListInsights\src\analyzer\master_schema.json"

def test_fromJson():
    schema = readSchema(schema_file)

    df = pd.read_csv(sample_file)

    try:
        df = schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        print(json.dumps(e.message, indent=2))

    print(df)
    print(df.dtypes)

def test_fromFrictionJson():
    f = r"C:\Users\debru\Documents\GitHub\ListInsights\test\schema.json"
    schema = readSchema(f)

    df = pd.read_csv(sample_file)

    try:
        df = schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        print(json.dumps(e.message, indent=2))

    print(df)
    print(df.dtypes)


def test_pandera_schema():
    df = pd.read_csv(sample_file)

    try:
        df = MASTER_SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        print(json.dumps(e.message, indent=2))

    print(df)
    print(df.dtypes)

def test_frictionlessdata():
    from frictionless import Schema, describe

    schema = describe("test/sample", type="package")
    print(schema)
    schema.to_yaml('test/schema.yaml')
    schema.to_json('test/schema.json')

def test_validate():
    from frictionless import Schema, validate
    report = validate("test/datapackage.json", type='package')

    print(report.flatten(['rowPosition', 'fieldPosition', 'code', 'message']))
    print(report["valid"])


