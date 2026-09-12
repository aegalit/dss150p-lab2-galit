"""Week 3 starter: rerunnable ingestion to a raw area.
Students implement file ingestion + paginated REST API ingestion + watermark + duplicate prevention.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; RAW=ROOT/'raw'; STATE=ROOT/'state'
API_URL='http://127.0.0.1:8000/api/events'

def utc_now(): return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load_watermark():
    p=STATE/'api_watermark.json'
    if not p.exists(): return None
    return json.loads(p.read_text())['updated_at']

def save_watermark(value):
    STATE.mkdir(exist_ok=True)
    (STATE/'api_watermark.json').write_text(json.dumps({'updated_at':value},indent=2))

def ingest_files():
    RAW_FILES = RAW / 'files'
    RAW_FILES.mkdir(parents=True, exist_ok=True)

    manifest_path = RAW_FILES / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = []

    already_ingested_hashes = {entry['sha256'] for entry in manifest}

    source_files = ['customers.csv', 'orders.json', 'products.parquet']
    for filename in source_files:
        source_path = DATA / filename
        file_hash = sha256_file(source_path)

        if file_hash in already_ingested_hashes:
            print(f"Skipping {filename}: already ingested (hash unchanged)")
            continue

        destination = RAW_FILES / filename
        shutil.copy2(source_path, destination)

        manifest.append({
            'source_file': filename,
            'ingested_at': utc_now(),
            'sha256': file_hash,
            'bytes': source_path.stat().st_size,
        })
        print(f"Ingested {filename} (sha256={file_hash[:8]}...)")

    manifest_path.write_text(json.dumps(manifest, indent=2))

def fetch_api_page(page, per_page=20, updated_after=None):
    params={'page':page,'per_page':per_page}
    if updated_after: params['updated_after']=updated_after
    r=requests.get(API_URL,params=params,timeout=30); r.raise_for_status(); return r.json()

def ingest_api():
    watermark = load_watermark()
    print(f"Starting watermark: {watermark}")

    all_records = []
    page = 1
    while True:
        response = fetch_api_page(page, per_page=20, updated_after=watermark)
        items = response['items']
        all_records.extend(items)
        print(f"Fetched page {page}: {len(items)} records (has_more={response['has_more']})")
        if not response['has_more']:
            break
        page += 1

    print(f"Total records read: {len(all_records)}")

    for record in all_records:
        record['_ingested_at'] = utc_now()
        record['_source'] = 'local_api'

    deduped = {}
    for record in all_records:
        event_id = record['event_id']
        if event_id not in deduped or record['updated_at'] > deduped[event_id]['updated_at']:
            deduped[event_id] = record

    final_records = list(deduped.values())
    duplicates_removed = len(all_records) - len(final_records)
    print(f"Records after dedup: {len(final_records)} (duplicates removed: {duplicates_removed})")

    if not final_records:
        print("No new records to write. Watermark unchanged.")
        return {'records_read': len(all_records), 'records_written': 0, 'duplicates_removed': duplicates_removed, 'watermark_before': watermark, 'watermark_after': watermark}

    RAW_API = RAW / 'api'
    RAW_API.mkdir(parents=True, exist_ok=True)
    final_path = RAW_API / 'events.jsonl'
    temp_path = RAW_API / 'events.jsonl.tmp'

    existing_lines = []
    if final_path.exists():
        existing_lines = final_path.read_text(encoding='utf-8').splitlines()

    new_lines = [json.dumps(record) for record in final_records]
    all_lines = existing_lines + new_lines

    temp_path.write_text('\n'.join(all_lines) + '\n', encoding='utf-8')
    temp_path.replace(final_path)
    print(f"Wrote {len(new_lines)} new records to {final_path}")

    new_watermark = max(record['updated_at'] for record in final_records)
    save_watermark(new_watermark)
    print(f"Watermark advanced to: {new_watermark}")
    return {'records_read': len(all_records), 'records_written': len(new_lines), 'duplicates_removed': duplicates_removed, 'watermark_before': watermark, 'watermark_after': new_watermark}

import csv as csv_module
import uuid

def append_run_log(run_id, started_at, finished_at, status, source, records_read, records_written, duplicates_removed, watermark_before, watermark_after, error_message=''):
    log_path = ROOT / 'templates' / 'pipeline_run_log_template.csv'
    output_path = ROOT / 'outputs' / 'pipeline_run_log.csv'
    output_path.parent.mkdir(exist_ok=True)

    file_exists = output_path.exists()
    with output_path.open('a', newline='', encoding='utf-8') as f:
        writer = csv_module.writer(f)
        if not file_exists:
            writer.writerow(['run_id','started_at','finished_at','status','source','records_read','records_written','duplicates_removed','watermark_before','watermark_after','error_message'])
        writer.writerow([run_id, started_at, finished_at, status, source, records_read, records_written, duplicates_removed, watermark_before, watermark_after, error_message])

if __name__=='__main__':
    RAW.mkdir(exist_ok=True); STATE.mkdir(exist_ok=True)

    run_id = str(uuid.uuid4())
    started_at = utc_now()

    try:
        ingest_files()
        api_result = ingest_api()
        finished_at = utc_now()
        append_run_log(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status='SUCCESS',
            source='files+api',
            records_read=api_result['records_read'],
            records_written=api_result['records_written'],
            duplicates_removed=api_result['duplicates_removed'],
            watermark_before=api_result['watermark_before'],
            watermark_after=api_result['watermark_after'],
        )
        print(f"\nRun {run_id} completed successfully. Logged to outputs/pipeline_run_log.csv")
    except Exception as e:
        finished_at = utc_now()
        append_run_log(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status='FAILED',
            source='files+api',
            records_read=0,
            records_written=0,
            duplicates_removed=0,
            watermark_before=load_watermark(),
            watermark_after=load_watermark(),
            error_message=str(e),
        )
        print(f"\nRun {run_id} FAILED: {e}")
        raise
