---
session_id: DAR-P3-S8
phase: 3
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P3-S7, DAR-P2-S6]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md  # create
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/migrations/
  - platform/src/
---

# DAR-P3-S8: Load MSR v5.0 into msr_signals + l25_msr_signals

## Context

Dry-run from S7 confirms 573 signals extract correctly. DB baseline from S6 confirmed
migrations are applied. This session loads MSR v5.0 into both DB tables (migration-009
`msr_signals` and migration-018 `l25_msr_signals`), replacing the stale v3/v4 rows.

## Steps

1. Read `DB_BASELINE_REPORT.md` to understand current state (source file and row count).

2. Truncate `msr_signals` and reload from MSR v5.0:
   ```bash
   cd platform/python-sidecar
   python3 -m pipeline.writers.msr_signals_writer \
     --source ../../025_HOLISTIC_SYNTHESIS/MSR_v5_0.md \
     --table msr_signals \
     --truncate
   ```
   If the writer doesn't support --truncate directly, run:
   ```bash
   psql "$DATABASE_URL" -c "TRUNCATE TABLE msr_signals;"
   python3 -m pipeline.writers.msr_signals_writer \
     --source ../../025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
   ```

3. Verify msr_signals count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT source_file, COUNT(*) FROM msr_signals GROUP BY source_file;"
   ```
   Expected: 1 row — `MSR_v5_0.md | 573`

4. Truncate `l25_msr_signals` and reload:
   ```bash
   psql "$DATABASE_URL" -c "TRUNCATE TABLE l25_msr_signals;"
   python3 -m pipeline.writers.msr_signals_writer \
     --source ../../025_HOLISTIC_SYNTHESIS/MSR_v5_0.md \
     --table l25_msr_signals
   ```
   (Adapt command to actual writer interface — check the writer's argparse or main() signature.)

5. Verify l25_msr_signals count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT source_file, COUNT(*) FROM l25_msr_signals GROUP BY source_file;"
   ```
   Expected: 1 row — `MSR_v5_0.md | 573`

6. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md`:
   ```yaml
   # MSR v5.0 DB Load Report
   # Generated: [timestamp]

   source_file: MSR_v5_0
   msr_signals_count: 573
   l25_msr_signals_count: 573
   msr_signals_source: MSR_v5_0.md
   l25_msr_signals_source: MSR_v5_0.md
   load_status: COMPLETE
   ```

7. Commit:
   ```
   dar: P3-S8 load MSR v5.0 into msr_signals + l25_msr_signals (573 rows each)
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md` → TRUE
- `grep 'msr_signals_count: 573' MSR_DB_LOAD_REPORT.md` → match
- `grep 'l25_msr_signals_count: 573' MSR_DB_LOAD_REPORT.md` → match
- `grep 'source_file: MSR_v5_0' MSR_DB_LOAD_REPORT.md` → match
