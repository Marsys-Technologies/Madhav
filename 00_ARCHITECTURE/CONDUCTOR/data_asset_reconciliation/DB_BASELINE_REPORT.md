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
notes: "Baseline captured before MSR v5.0 DB rebuild. rag_chunks filtered by doc_type='msr_signal' (column source_type does not exist; task brief contained incorrect column name — doc_type is the correct discriminator). Migration 117 SQL file contained a PG12-incompatible reference to pg_constraint.consrc (removed in PG12); fixed in-session to use pg_get_constraintdef(c.oid) — migration SQL file updated with fix annotation."
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

### Source File
```
msr_signals.source_file: MSR_v5_0.md
```

## Anomalies

1. **rag_chunks column mismatch**: Task brief specified `WHERE source_type='msr_signal'` but `source_type` column does not exist. Correct column is `doc_type`. Count via `doc_type='msr_signal'` = 514. This is consistent with `l25_msr_signals` count (514), suggesting rag_chunks MSR entries were sourced from MSR_v3_0.md (confirmed: `source_file = '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'`) — these are stale relative to the current MSR_v5_0.md (573 signals). The DAR rebuild will correct this.

2. **Migration 117 SQL bug**: Original `pg_constraint.consrc` reference fails on PG15. Fixed in-session; migration SQL file updated with fix annotation and corrected DO block.

3. **msr_signals (573) vs rag_chunks msr_signal (514)**: Delta of 59 signals. Rag_chunks reflect MSR_v3_0.md; current canonical is MSR_v5_0.md with 573 signals. Rebuild target: 573 rag_chunks with doc_type=msr_signal post-DAR.
