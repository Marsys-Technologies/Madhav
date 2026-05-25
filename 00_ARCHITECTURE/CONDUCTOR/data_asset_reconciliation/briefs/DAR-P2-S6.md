---
session_id: DAR-P2-S6
phase: 2
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-HG-1]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md  # create
  - 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
must_not_touch:
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/
  - platform/src/
---

# DAR-P2-S6: DB baseline state report

## Context

HG-1 is complete — migrations 116 and 117 have been applied to production. This session
queries the production DB to capture baseline state before the MSR pipeline cascade begins.
The report is the gate for Phase 3 sessions (DAR-P3-S8 depends on knowing DB state).

## Steps

Run each query via `psql "$DATABASE_URL"` and record all results in
`00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md`.

1. MSR signals source and count:
   ```sql
   SELECT source_file, COUNT(*) as cnt FROM msr_signals GROUP BY source_file;
   SELECT source_file, COUNT(*) as cnt FROM l25_msr_signals GROUP BY source_file;
   ```

2. MSR rag chunks:
   ```sql
   SELECT source_version, COUNT(*) as cnt FROM rag_chunks
   WHERE canonical_id = 'MSR' GROUP BY source_version;
   ```

3. Migration 116 verification:
   ```sql
   SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name='query_trace_steps' AND column_name='mcp_tool';
   ```

4. Migration 117 verification:
   ```sql
   SELECT pg_get_constraintdef(oid) FROM pg_constraint
   WHERE conname='mcp_api_keys_audience_tier_check';
   ```

5. chart_facts count:
   ```sql
   SELECT COUNT(*) FROM chart_facts;
   ```

6. school_signal_coverage:
   ```sql
   SELECT COUNT(*) FROM school_signal_coverage;
   ```

7. ephemeris_daily:
   ```sql
   SELECT COUNT(*), node_type FROM ephemeris_daily GROUP BY node_type;
   ```

8. bhava_chalit null check:
   ```sql
   SELECT COUNT(*) FROM ephemeris_daily WHERE bhava_chalit_house IS NULL;
   ```

Format `DB_BASELINE_REPORT.md` as:
```yaml
# DB Baseline Report — DAR Phase 2 S6
# Generated: [timestamp]

migration_116: CONFIRMED  # or NOT_APPLIED
migration_117: CONFIRMED  # or NOT_APPLIED
msr_signals_source: MSR_v3_0.md  # or MSR_v5_0.md — whatever the query returns
msr_signals_count: <N>
l25_msr_signals_source: <source_file>
l25_msr_signals_count: <N>
msr_rag_chunks_count: <N>
msr_rag_chunks_source_version: <version>
chart_facts_count: <N>
school_signal_coverage_count: <N>
ephemeris_daily_count: <N>
ephemeris_node_type: <MEAN_NODE or TRUE_NODE>
bhava_chalit_null_count: <N>
```

Update `00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md` to add rows for 116 and 117 if not already present.

9. Commit:
   ```
   dar: P2-S6 DB baseline state report — pre-cascade snapshot
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md` → TRUE
- `grep 'migration_116: CONFIRMED' DB_BASELINE_REPORT.md` → match
- `grep 'migration_117: CONFIRMED' DB_BASELINE_REPORT.md` → match
- `grep 'msr_signals_source:' DB_BASELINE_REPORT.md` → match
