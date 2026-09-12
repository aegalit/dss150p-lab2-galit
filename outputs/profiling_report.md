# Source Profiling Report

## 1. Source Inventory

| Source | Type | Rows/Records | Key | Update Pattern | Quality Findings |
|---|---|---:|---|---|---|
| customers.csv | CSV | 250 | customer_id (not unique) | Unknown / file-based | 3 missing emails, 2 missing cities, 2 exact duplicate rows, 3 duplicate customer_id values |
| orders.json | JSON | 250 | order_id | Unknown / file-based | No explicit nulls found; nested `shipping` object present |
| products.parquet | Parquet | 200 | product_id | Unknown / file-based | No missing values; types preserved natively (float64, int32) |
| Local REST API (events) | REST API | 122 (before dedup) | event_id (not unique pre-dedup) | Incremental via `updated_after` | 2 intentionally duplicated event_id values with newer timestamps |
| support_tickets (PostgreSQL) | Database table | 250 | ticket_id | Unknown / possible timestamp-CDC in future | 4 tickets with no assigned_agent |

## 2. Schema Findings

- **customers.csv**: 7 columns (`customer_id`, `first_name`, `last_name`, `email`, `city`, `signup_date`, `customer_segment`). All columns are read by pandas as generic strings, including `signup_date`, which is logically a date but arrives as plain text in the CSV.
- **orders.json**: 9 top-level fields, including a nested `shipping` object with two sub-fields (`region`, `method`). `order_timestamp` is logically a timestamp but arrives as ISO-formatted text.
- **products.parquet**: 7 columns. Unlike the CSV and JSON sources, Parquet preserves actual data types natively — `unit_price` and `weight_kg` are stored as `float64`, and `stock_quantity` as `int32`, without needing type inference.
- **API events**: 6 top-level fields plus a nested `metadata` object (`channel`, `campaign`). `updated_at` is the field used for incremental watermarking.
- **support_tickets**: 8 columns including `ticket_id` (integer, primary key), `customer_id`, `category`, `priority`, `assigned_agent` (nullable), `opened_at`, `resolved_at`, and `status`.

## 3. Data Quality Findings

1. `customers.csv` has 3 duplicate `customer_id` values, violating the intended uniqueness of the field.
2. `customers.csv` has 2 exact duplicate rows.
3. `customers.csv` has 3 missing `email` values and 2 missing `city` values.
4. The REST API intentionally contains 2 repeated `event_id` values with newer `updated_at` timestamps, requiring deduplication logic that keeps the most recent version of each record.
5. `support_tickets` has 4 rows with a null `assigned_agent`, meaning some tickets are currently unassigned.
6. Across all file-based sources, timestamp/date fields (`signup_date`, `order_timestamp`) arrive as plain text and require explicit parsing to be used as true date/timestamp types.

## 4. Recommended Acquisition Method

- **customers.csv, orders.json, products.parquet**: Full file copy on each run, using SHA-256 content hashing to detect whether a file has actually changed. This avoids reprocessing unchanged files while still catching real content updates, even if a filename stays the same.
- **REST API events**: Incremental paginated retrieval using the `updated_after` parameter, combined with a persisted watermark (the greatest successfully-processed `updated_at` value). This avoids re-fetching the entire event history on every run.
- **support_tickets (PostgreSQL)**: Inspection only in this lab, using small, bounded queries (row counts, limited row samples, filtered counts) to avoid placing load on the source system. A production extension would require either an `updated_at`-style column or database-native CDC tooling to support real incremental extraction.

## 5. Risks and Assumptions

- It is assumed that `customer_id` duplicates in `customers.csv` are a genuine data-quality issue in the source system, not an intentional design choice (unlike the API's intentional `event_id` duplicates).
- It is assumed the local REST API's pagination and `updated_after` filtering behavior are representative of how a real production API would behave, though a real API may have additional constraints (rate limits, authentication, inconsistent pagination behavior).
- The watermark strategy assumes `updated_at` values are fine-grained enough to avoid frequent exact ties; if the source produced many records with the exact same timestamp, some records could be missed at the watermark boundary (see `config/watermark_explanation.md` for further discussion).
- No assumption was made about the meaning of missing `email`/`city` values in `customers.csv` — they were left as-is and simply reported, per the lab's constraint not to repair source data.