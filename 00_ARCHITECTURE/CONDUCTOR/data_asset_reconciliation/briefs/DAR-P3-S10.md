---
session_id: DAR-P3-S10
phase: 3
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P3-S8]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md  # create
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/migrations/
---

# DAR-P3-S10: Rebuild four registers + school_signal_coverage + refresh school_convergence_index MV

## Context

`msr_signals` now has 573 rows from MSR v5.0. Four derived registers and the
`school_signal_coverage` join table are stale (built against 514 or 420 signals).
The `school_convergence_index` materialized view must also be refreshed.
Target: `school_signal_coverage` = 4,011 rows (573 signals × 7 schools).

## Steps

1. Rebuild `contradiction_register`:
   ```bash
   cd platform/python-sidecar
   python3 -m pipeline.writers.contradiction_register_writer --rebuild
   ```
   Verify: `SELECT COUNT(*) FROM contradiction_register;` — record count.

2. Rebuild `cluster_register`:
   ```bash
   python3 -m pipeline.writers.cluster_register_writer --rebuild
   ```
   Verify row count.

3. Rebuild `pattern_register`:
   ```bash
   python3 -m pipeline.writers.pattern_register_writer --rebuild
   ```
   Verify row count.

4. Rebuild `resonance_register`:
   ```bash
   python3 -m pipeline.writers.resonance_register_writer --rebuild
   ```
   Verify row count.

5. Rebuild `school_signal_coverage` (573 signals × 7 schools = 4,011 rows):
   ```bash
   python3 -m pipeline.writers.school_signal_coverage_writer --rebuild
   ```
   Verify:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM school_signal_coverage;"
   ```
   Expected: 4,011

6. Refresh the `school_convergence_index` materialized view:
   ```bash
   psql "$DATABASE_URL" -c "REFRESH MATERIALIZED VIEW school_convergence_index;"
   ```
   Verify: `SELECT COUNT(*) FROM school_convergence_index;`

7. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md`:
   ```yaml
   # Registers Rebuild Report — Phase 3 S10
   # Generated: [timestamp]

   contradiction_register: REBUILT
   contradiction_register_count: <N>
   cluster_register: REBUILT
   cluster_register_count: <N>
   pattern_register: REBUILT
   pattern_register_count: <N>
   resonance_register: REBUILT
   resonance_register_count: <N>
   school_signal_coverage_count: 4011
   school_convergence_index: REFRESHED
   school_convergence_index_count: <N>
   ```

8. Commit:
   ```
   dar: P3-S10 rebuild 4 registers + school_signal_coverage (4011) + refresh school_convergence_index MV
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md` → TRUE
- `grep 'school_signal_coverage_count: 4011' REGISTERS_REBUILD_REPORT.md` → match
- `grep 'contradiction_register: REBUILT' REGISTERS_REBUILD_REPORT.md` → match
- `grep 'school_convergence_index: REFRESHED' REGISTERS_REBUILD_REPORT.md` → match
