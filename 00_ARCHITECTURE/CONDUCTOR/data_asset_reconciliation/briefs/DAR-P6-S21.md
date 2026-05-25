---
session_id: DAR-P6-S21
phase: 6
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md  # create
  - 00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md  # create
must_not_touch:
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
---

# DAR-P6-S21: Ephemeris pre-rebuild verification + runbook

## Context

The DAR audit found `ephemeris_daily` uses TRUE_NODE for Rahu/Ketu but FORENSIC v8.0 and
the Jyotish tradition both use MEAN_NODE. The full rebuild (~4–6h) is a human gate.
This session verifies the current production state and authors the operator runbook
that the human reads at HG-3.

## Steps

1. Query production DB to confirm current node type:
   ```bash
   psql "$DATABASE_URL" -c "SELECT DISTINCT node_type FROM ephemeris_daily LIMIT 1;"
   ```
   Record result.

2. Inspect the bootstrap script to confirm it supports MEAN_NODE mode:
   ```bash
   grep -n 'MEAN_NODE\|TRUE_NODE\|node_type' platform/python-sidecar/pipeline/bootstrap_ephemeris.py | head -20
   ```
   Confirm the flag/env var that controls node type.

3. Check bhava_chalit null coverage:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily WHERE bhava_chalit_house IS NULL;"
   ```
   Record null count.

4. Record total row count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily;"
   ```

5. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md`:
   ```yaml
   # Ephemeris Pre-Rebuild Check
   # Generated: [timestamp]

   current_node_type: <TRUE_NODE or MEAN_NODE>
   current_row_count: <N>
   bhava_chalit_null_count: <N>
   bootstrap_script_node_type: MEAN_NODE  # confirmed by inspecting bootstrap_ephemeris.py
   bootstrap_script_flag: <flag name>
   rebuild_required: true
   ```

6. Create `00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md`:
   - §1: Pre-flight (confirm DB connection, disk space, env vars)
   - §2: Run bootstrap with MEAN_NODE flag (exact command)
   - §3: Monitor progress (tail logs, expected row count per hour)
   - §4: Verify after completion (row count = 657,450; MEAN_NODE present; bhava_chalit null = 0)
   - §5: Signal completion (`touch HG3_COMPLETE`)
   - §6: Rollback (if rebuild fails, production DB is untouched until atomic swap)

7. Commit:
   ```
   dar: P6-S21 ephemeris pre-rebuild check + RUNBOOK_EPHEMERIS_REBUILD_v1_0 authored
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md` → TRUE
- `grep 'bootstrap_script_node_type: MEAN_NODE' EPHEMERIS_PRE_REBUILD_CHECK.md` → match
- `test -f 00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md` → TRUE
