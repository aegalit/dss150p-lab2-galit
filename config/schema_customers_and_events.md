# Logical Schema

## customers

| Field | Logical Type | Nullable | Key Role | Definition |
|---|---|---|---|---|
| customer_id | string | No | Primary key (candidate) | Unique identifier for a customer. Note: 3 duplicate values found in source, violating intended uniqueness. |
| first_name | string | No | - | Customer's given name. |
| last_name | string | No | - | Customer's family name. |
| email | string | Yes | - | Customer's contact email address. Missing in 3 records. |
| city | string | Yes | - | City associated with the customer's address. Missing in 2 records. |
| signup_date | date | No | - | Date the customer registered. Arrives as text in the source CSV but represents a calendar date logically. |
| customer_segment | string (categorical) | No | - | Business segment the customer belongs to (e.g. Retail, Professional, Student, SME). |

## api_events

| Field | Logical Type | Nullable | Key Role | Definition |
|---|---|---|---|---|
| event_id | string | No | Candidate key (pre-dedup) | Identifier for an event. Intentionally repeated for some events in the source API; deduplication required to use as a true key. |
| customer_id | string | No | Foreign key (references customers) | Identifies which customer the event belongs to. |
| event_type | string (categorical) | No | - | Type of event (e.g. page_view, checkout, payment, add_to_cart, support). |
| amount | float | No | - | Monetary value associated with the event. |
| updated_at | timestamp | No | Watermark field | Arrives as ISO 8601 text; represents a timestamp logically. Used to track the latest state of a record for incremental ingestion. |
| metadata.channel | string (categorical) | No | - | Nested field indicating the channel the event originated from (web, mobile, partner). |
| metadata.campaign | string (categorical) | No | - | Nested field indicating the marketing campaign associated with the event, if any. |