# Watermark Semantics

**What could go wrong if the watermark is saved before the raw file is successfully written?**
If the pipeline crashes or fails partway through writing the raw output (for example, a network error or a disk failure), the watermark would already reflect data that was never actually persisted. On the next run, the pipeline would request only records *after* that watermark, permanently skipping the records that were supposed to be written but weren't — resulting in silent, unrecoverable data loss.

**What could go wrong if the source allows multiple records with exactly the same timestamp?**
Since the watermark strategy relies on `updated_at > watermark`, any records sharing the exact same `updated_at` as the watermark value would be excluded from the next fetch, even if some of them were never actually retrieved in the current run (for example, if the page size cut off mid-timestamp-group). This can cause records to be silently missed.

**Limitation of this simplified watermark:**
It assumes `updated_at` values are unique enough to draw a clean boundary between "already ingested" and "not yet ingested" records. When ties exist at the exact watermark value, there's no way to distinguish which of those tied records were already processed and which weren't.

**Production-grade mitigation:**
Use a composite watermark — for example, `(updated_at, event_id)` pairs, or a strictly increasing sequence/offset column instead of a timestamp — so that ties can be broken deterministically and no record is skipped or reprocessed incorrectly.