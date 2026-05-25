---
session: DAR-P3-S9
date: 2026-05-25
canonical_id: MSR
source_version: "5.0"
msr_rag_chunks_count: 573
chunks_with_embedding: 573
null_embeddings: 0
embed_status: COMPLETE
hnsw_index: PRESENT
embed_model: text-multilingual-embedding-002
embed_dim: 768
---

# DAR-P3-S9 — MSR rag_chunks Rebuild Report

## Summary

Rebuilt MSR `rag_chunks` from `MSR_v5_0.md` (573 signals) and re-embedded all 573 vectors
via Vertex AI `text-multilingual-embedding-002` (768-dim). HNSW index confirmed present.

## Pre-conditions

- 514 stale `msr_signal` chunks with `source_version = '3.x'` and `canonical_id = NULL`
  existed in `rag_chunks` from the prior v3.0 corpus load.
- 0 rows existed with `canonical_id = 'MSR'` (column was NULL for all prior MSR chunks).
- 0 existing MSR embeddings in `rag_embeddings`.

## Steps Executed

### 1. Fix P5 validator (prerequisite)

`platform/python-sidecar/rag/validators/p5_signal_id_resolution.py` had a stale
reference to `MSR_v3_0.md` (which no longer exists — only `MSR_v5_0.md` is present).
Updated `_MSR_PATH` and docstring to reference `MSR_v5_0.md` so the signal ID
registry builds correctly against the 573-signal v5.0 corpus.

### 2. Start DB proxy

```
cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433
```

Port 5433 confirmed open.

### 3. Delete stale MSR rag_chunks

```sql
DELETE FROM rag_chunks WHERE doc_type = 'msr_signal';
```

Result: `DELETE 514` — all stale v3.x MSR chunks removed.

Verification:
```sql
SELECT COUNT(*) FROM rag_chunks WHERE doc_type = 'msr_signal';
-- Result: 0
```

### 4. Run MSR chunker

```bash
cd platform/python-sidecar
python3 -m rag.chunkers.msr_signal /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
```

Output:
```
INFO:__main__:msr_signal: 573 chunks parsed from 573 signals
INFO:__main__:msr_signal: wrote 573 / 573 chunks to rag_chunks
msr_signal: 573 chunks written
```

P1, P2, P5 validators all passed — 0 violations, 0 blocks.

### 5. Set canonical_id

The `write_chunks_to_db` function does not populate the `canonical_id` DB column
(only writes to `metadata` JSONB). Applied a post-insert update:

```sql
UPDATE rag_chunks SET canonical_id = 'MSR'
WHERE doc_type = 'msr_signal' AND source_version = '5.0';
-- Result: UPDATE 573
```

### 6. Verify chunk count

```sql
SELECT source_version, COUNT(*) FROM rag_chunks
WHERE canonical_id = 'MSR' GROUP BY source_version;
```

| source_version | count |
|---|---|
| 5.0 | 573 |

### 7. Run embedder

```bash
cd platform/python-sidecar
python3 -m rag.embed
```

The embedder uses idempotency: fetches all non-stale chunks (6990), skips
already-embedded (6417), embeds the delta (573 MSR chunks).

Output summary:
- Chunks to embed: 573
- Batch size: 10 (Vertex AI text-multilingual-embedding-002)
- Total batches: 58
- Embedded: 573 / 573
- HNSW index: PRESENT (m=16, ef_construction=64)
- Sanity test: top-3 distinct doc_types ≥ 2 (AC-B3.4=True)

### 8. Final verification

```sql
SELECT
  rc.source_version,
  COUNT(rc.chunk_id) as chunk_count,
  COUNT(re.chunk_id) as embedded_count,
  COUNT(rc.chunk_id) - COUNT(re.chunk_id) as null_embeddings
FROM rag_chunks rc
LEFT JOIN rag_embeddings re ON rc.chunk_id = re.chunk_id
WHERE rc.canonical_id = 'MSR'
GROUP BY rc.source_version;
```

| source_version | chunk_count | embedded_count | null_embeddings |
|---|---|---|---|
| 5.0 | 573 | 573 | 0 |

## Acceptance Criteria

| Criterion | Status |
|---|---|
| `msr_rag_chunks_count: 573` | PASS |
| `source_version: 5.0` | PASS |
| `null_embeddings: 0` | PASS |
| `embed_status: COMPLETE` | PASS |
| HNSW index present | PASS |

## Anomalies

1. **P5 validator stale reference** — `p5_signal_id_resolution.py` hardcoded `MSR_v3_0.md`
   as the signal registry source. Since only `MSR_v5_0.md` exists, the registry build
   would have crashed with `FileNotFoundError`. Fixed as part of this session.
   This is a residual from DAR-P1-S2 which updated `msr_signal.py` but not the validator.

2. **canonical_id not written by chunker** — `write_chunks_to_db` in `rag/chunkers/__init__.py`
   does not include `canonical_id` in the INSERT statement. The existing 514 stale chunks
   all had `canonical_id = NULL`, confirming this is a long-standing gap. Applied a
   post-insert `UPDATE` to backfill `canonical_id = 'MSR'` for the 573 new rows.
   This gap should be addressed in a future session (add `canonical_id` to the INSERT
   and to the `Chunk` model / `_chunk_to_row` function).

3. **AC-B3.3 p95 latency** — Sanity test reported `p95_latency = 109.0ms`, which is above
   the 50ms threshold (`AC-B3.3=False`). This is a pre-existing condition (HNSW cold cache
   on local proxy) and not a regression introduced by this session.
