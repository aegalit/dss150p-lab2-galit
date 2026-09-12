"""Week 2 starter: profile CSV, JSON, Parquet, API payload, and PostgreSQL table.
Complete the TODOs. Do not hard-code expected counts.
"""
from pathlib import Path
import json, csv
DATA_DIR=Path(__file__).resolve().parents[1]/'data'

def profile_csv(path):
    import pandas as pd
    df = pd.read_csv(path)
    print(f"File: {path.name}")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")

    print("\nMissing values per column:")
    print(df.isnull().sum())

    print(f"\nExact duplicate rows: {df.duplicated().sum()}")
    print(f"Duplicate customer_id values: {df['customer_id'].duplicated().sum()}")
    print(f"customer_id is unique: {df['customer_id'].is_unique}")

    print("\nInferred data types:")
    print(df.dtypes)

def profile_json(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    print(f"\nFile: {path.name}")
    print(f"Record count: {len(data)}")

    first = data[0]
    print(f"Top-level keys: {list(first.keys())}")
    print(f"Nested field: shipping -> {list(first['shipping'].keys())}")

    null_counts = {}
    for record in data:
        for key in first.keys():
            value = record.get(key)
            if value is None:
                null_counts[key] = null_counts.get(key, 0) + 1

    print(f"Null/missing counts by key: {null_counts}")

def profile_parquet(path):
    # TODO: use pandas.read_parquet; report rows/columns/dtypes/nulls and file size
    # Requires pyarrow from requirements.txt
    pass

if __name__=='__main__':
    profile_csv(DATA_DIR/'customers.csv')
    profile_json(DATA_DIR/'orders.json')
    profile_parquet(DATA_DIR/'products.parquet')
