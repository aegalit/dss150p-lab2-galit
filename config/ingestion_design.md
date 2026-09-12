# Ingestion Design

| Source | Method | Raw destination | Duplicate key | Incremental state |
|---|---|---|---|---|
| CSV/JSON/Parquet | File copy + manifest | raw/files/ | File SHA-256 | N/A |
| REST API | Paginated GET | raw/api/events.jsonl | event_id | max(updated_at) |
| PostgreSQL | Inspection only in this lab | N/A | ticket_id | Discuss possible timestamp/CDC strategy |

## Notes

- CSV/JSON/Parquet files are ingested via a straight copy into `raw/files/`, with a manifest recording each file's SHA-256 hash so that reruns can detect unchanged files and skip re-copying them.
- The REST API is ingested by paging through all results, deduplicating on `event_id` (keeping the record with the greatest `updated_at`), and tracking an incremental watermark based on the maximum successfully-written `updated_at` value.
- PostgreSQL is inspection-only in this lab (no ingestion pipeline implemented against it). A production extension of this pipeline could use a `updated_at`/`modified_at` column if one existed on `support_tickets`, or database-native Change Data Capture (CDC) tooling, to support incremental extraction without inspection-only bounded queries.