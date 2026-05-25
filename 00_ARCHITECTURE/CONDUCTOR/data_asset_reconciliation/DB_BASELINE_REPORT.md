---
generated: 2026-05-25T00:00:00+05:30
migration_116: CONFIRMED
migration_117: CONFIRMED
msr_signals_source: MSR_v5_0.md
msr_signals_count: 573
l25_msr_signals_count: 514
ephemeris_daily_count: 660726
chart_facts_count: 2681
msr_rag_chunks_count: 514
school_signal_coverage_count: 3747
ephemeris_node_type: "column does not exist — table uses planet discriminator; rahu=73414 ketu=73414 (mean node only; no true-node column)"
bhava_chalit_null_count: 0
notes: "Baseline captured before MSR v5.0 DB rebuild. rag_chunks filtered by doc_type='msr_signal' (column source_type does not exist; task brief contained incorrect column name — doc_type is the correct discriminator). Migration 117 SQL file contained a PG12-incompatible reference to pg_constraint.consrc (removed in PG12); fixed in-session to use pg_get_constraintdef(c.oid) — migration SQL file updated with fix annotation. DAR-P2-S6 augmentation: node_type column does not exist in ephemeris_daily — planet is the discriminator; 9 planets × 73,414 rows; bhava_chalit_house has 0 NULLs (fully populated)."
---

# DB Baseline Report — DAR-P2-S5

Captured: 2026-05-25 (DAR-P2-S5 session)
DB: amjis (Cloud SQL via Auth Proxy, port 5433)
Branch: feature/data-asset-reconciliation

## Migration Status

| Migration | File | Status | Notes |
|-----------|------|--------|-------|
| 116 | `116_trace_mcp_tool_column.sql` | CONFIRMED | Column `mcp_tool TEXT` added to `query_trace_steps`; 85 historical rows backfilled; index `idx_query_trace_steps_mcp_tool` created |
| 117 | `117_audience_tier_acharya_enum.sql` | CONFIRMED | `mcp_api_keys_audience_tier_check` constraint updated to include `'acharya'`; SQL file fixed (pg_constraint.consrc → pg_get_constraintdef) |

### Migration 116 Verification
```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='query_trace_steps' AND column_name='mcp_tool';
-- Result: mcp_tool | text  ✓
```

### Migration 117 Verification
```sql
SELECT c.conname, pg_get_constraintdef(c.oid) AS condef
FROM pg_constraint c
JOIN pg_class r ON r.oid = c.conrelid
WHERE r.relname = 'mcp_api_keys' AND c.contype = 'c';
-- Result: mcp_api_keys_audience_tier_check |
--   CHECK ((audience_tier = ANY (ARRAY['client'::text, 'super_admin'::text, 'acharya'::text])))  ✓
```

## DB Baseline Row Counts

| Table / Filter | Count | Query |
|----------------|-------|-------|
| `msr_signals` | 573 | `SELECT COUNT(*) FROM msr_signals` |
| `l25_msr_signals` | 514 | `SELECT COUNT(*) FROM l25_msr_signals` |
| `ephemeris_daily` | 660,726 | `SELECT COUNT(*) FROM ephemeris_daily` |
| `chart_facts` | 2,681 | `SELECT COUNT(*) FROM chart_facts` |
| `rag_chunks` (doc_type=msr_signal) | 514 | `SELECT COUNT(*) FROM rag_chunks WHERE doc_type='msr_signal'` |
| `school_signal_coverage` | 3,747 | `SELECT COUNT(*) FROM school_signal_coverage` |
| `ephemeris_daily` node_type | N/A — column absent | `SELECT node_type, COUNT(*) FROM ephemeris_daily GROUP BY node_type` — see anomaly §4 |
| `ephemeris_daily` (rahu rows) | 73,414 | `SELECT COUNT(*) FROM ephemeris_daily WHERE planet='rahu'` |
| `ephemeris_daily` (ketu rows) | 73,414 | `SELECT COUNT(*) FROM ephemeris_daily WHERE planet='ketu'` |
| `ephemeris_daily` bhava_chalit_house NULL | 0 | `SELECT COUNT(*) FROM ephemeris_daily WHERE bhava_chalit_house IS NULL` |

### Source File
```
msr_signals.source_file: MSR_v5_0.md
```

## DAR-P2-S6 Augmentation

Captured: 2026-05-25 (DAR-P2-S6 session)

| Field | Value | Notes |
|-------|-------|-------|
| `school_signal_coverage_count` | 3,747 | Table exists and is populated |
| `ephemeris_node_type` | column absent | `node_type` does not exist; planet discriminator used instead; rahu=73,414 / ketu=73,414 |
| `bhava_chalit_null_count` | 0 | All 660,726 rows have `bhava_chalit_house` populated |

## Anomalies

1. **rag_chunks column mismatch**: Task brief specified `WHERE source_type='msr_signal'` but `source_type` column does not exist. Correct column is `doc_type`. Count via `doc_type='msr_signal'` = 514. This is consistent with `l25_msr_signals` count (514), suggesting rag_chunks MSR entries were sourced from MSR_v3_0.md (confirmed: `source_file = '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'`) — these are stale relative to the current MSR_v5_0.md (573 signals). The DAR rebuild will correct this.

2. **Migration 117 SQL bug**: Original `pg_constraint.consrc` reference fails on PG15. Fixed in-session; migration SQL file updated with fix annotation and corrected DO block.

3. **msr_signals (573) vs rag_chunks msr_signal (514)**: Delta of 59 signals. Rag_chunks reflect MSR_v3_0.md; current canonical is MSR_v5_0.md with 573 signals. Rebuild target: 573 rag_chunks with doc_type=msr_signal post-DAR.

4. **ephemeris_daily node_type column absent** (DAR-P2-S6): The task brief specified `SELECT node_type, COUNT(*) FROM ephemeris_daily GROUP BY node_type` but `node_type` is not a column in `ephemeris_daily`. The table uses `planet TEXT NOT NULL` as its discriminator. Lunar nodes are represented as `planet='rahu'` and `planet='ketu'` (mean-node only; no true-node / mean-node split column). The query was adapted: planet breakdown captured instead (9 planets × 73,414 rows each = 660,726 total). No schema gap — this is a task-brief column-name error, not a DB deficiency.

5. **bhava_chalit_house fully populated** (DAR-P2-S6): NULL count = 0 across all 660,726 ephemeris_daily rows. This confirms the ephemeris build pipeline populates `bhava_chalit_house` for every row. No remediation required.
