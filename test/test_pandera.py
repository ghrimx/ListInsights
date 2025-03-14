import pandas as pd
import pandera as pa
import json
from pathlib import Path

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

    schema = describe("test/sample/data/Book1.xlsx", type="package")
    print(schema)
    schema.to_json('test/sample/book1_schema.json')

def test_validate():
    from frictionless import Schema, validate, Resource, Package
    package = Package("test/sample/datapackage.json")

    resource: Resource
    for resource in package.resources:
        resource.path = "data/sample.csv"
        resource.name = 'sample'
        resource.format = 'csv'

    report_schema = package.validate()
    print(report_schema)

    # report = validate("test/datapackage.json", type='package')

    # print(report.flatten(['rowPosition', 'fieldPosition', 'code', 'message']))
    # print(report["valid"])


