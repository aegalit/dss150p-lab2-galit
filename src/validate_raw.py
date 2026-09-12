"""Starter validation checks for raw outputs."""
from pathlib import Path
from datetime import datetime
import json
ROOT=Path(__file__).resolve().parents[1]

def main():
    errors = []

    raw_files_dir = ROOT / 'raw' / 'files'
    expected_files = ['customers.csv', 'orders.json', 'products.parquet', 'manifest.json']
    for filename in expected_files:
        if not (raw_files_dir / filename).exists():
            errors.append(f"Missing expected raw file: {filename}")

    api_path = ROOT / 'raw' / 'api' / 'events.jsonl'
    if not api_path.exists():
        errors.append("Missing raw API output: raw/api/events.jsonl")
    else:
        lines = api_path.read_text(encoding='utf-8').splitlines()
        records = [json.loads(line) for line in lines if line.strip()]

        event_ids = [r['event_id'] for r in records]
        if len(event_ids) != len(set(event_ids)):
            errors.append("Duplicate event_id values found in raw API output")

        required_fields = ['event_id', 'customer_id', 'event_type', 'amount', 'updated_at', '_ingested_at', '_source']
        for i, record in enumerate(records):
            for field in required_fields:
                if field not in record:
                    errors.append(f"Record {i} missing required field: {field}")

        for record in records:
            try:
                datetime.fromisoformat(record['updated_at'])
            except (ValueError, KeyError):
                errors.append(f"Unparseable updated_at value: {record.get('updated_at')}")

        watermark_path = ROOT / 'state' / 'api_watermark.json'
        if watermark_path.exists() and records:
            watermark_value = json.loads(watermark_path.read_text())['updated_at']
            max_updated_at = max(r['updated_at'] for r in records)
            if watermark_value != max_updated_at:
                errors.append(f"Watermark ({watermark_value}) does not match max updated_at in raw output ({max_updated_at})")

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} issue(s) found")
        for e in errors:
            print(f"  - {e}")
    else:
        print("VALIDATION PASSED: all checks succeeded")
    
if __name__=='__main__': main()
