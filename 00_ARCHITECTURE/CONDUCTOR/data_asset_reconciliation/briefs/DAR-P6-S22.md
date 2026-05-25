---
session_id: DAR-P6-S22
phase: 6
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-HG-3]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md  # create
must_not_touch:
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
---

# DAR-P6-S22: Post-ephemeris rebuild verification

## Context

HG-3 is complete — the operator ran `bootstrap_ephemeris.py` with MEAN_NODE flag.
This session verifies the rebuild is correct: row count, node type, bhava_chalit coverage,
and a FORENSIC spot-check of Rahu at the native's birth date (1984-02-05).

## Steps

1. Total row count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily;"
   ```
   Expected: 657,450 (1800-01-01 to 2600-12-31 at daily granularity).

2. Node type confirmation:
   ```bash
   psql "$DATABASE_URL" -c "SELECT DISTINCT node_type FROM ephemeris_daily;"
   ```
   Expected: `MEAN_NODE` only (no TRUE_NODE rows).

3. bhava_chalit null check:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily WHERE bhava_chalit_house IS NULL;"
   ```
   Expected: 0

4. Rahu spot-check at FORENSIC birth date (1984-02-05):
   ```bash
   psql "$DATABASE_URL" -c "
   SELECT planet, longitude, nakshatra, nakshatra_pada
   FROM ephemeris_daily
   WHERE date = '1984-02-05' AND planet IN ('Rahu', 'Ketu');"
   ```
   Cross-check Rahu nakshatra against `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`
   declaration. They must match (MEAN_NODE Rahu position at 1984-02-05).

5. 50 random-date sanity checks:
   ```bash
   psql "$DATABASE_URL" -c "
   SELECT date, COUNT(*) as planet_count FROM ephemeris_daily
   WHERE date IN (SELECT date FROM ephemeris_daily ORDER BY random() LIMIT 50)
   GROUP BY date HAVING COUNT(*) < 10 ORDER BY date;"
   ```
   Expected: 0 rows (every date should have all planets).

6. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md`:
   ```yaml
   # Ephemeris Post-Rebuild Verification Report
   # Generated: [timestamp]

   row_count: 657450
   node_type_in_db: MEAN_NODE
   bhava_chalit_null_count: 0
   birth_date_rahu_spot_check: PASS  # or FAIL with actual vs expected
   rahu_nakshatra_1984_02_05: <nakshatra name>
   forensic_rahu_nakshatra: <from FORENSIC v8.0>
   random_date_coverage_check: PASS
   rebuild_status: COMPLETE
   ```

7. Commit:
   ```
   dar: P6-S22 ephemeris post-rebuild verification PASS — MEAN_NODE confirmed, 657450 rows
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md` → TRUE
- `grep 'node_type_in_db: MEAN_NODE' EPHEMERIS_POST_REBUILD_REPORT.md` → match
- `grep 'birth_date_rahu_spot_check: PASS' EPHEMERIS_POST_REBUILD_REPORT.md` → match
- `grep 'row_count: 657450' EPHEMERIS_POST_REBUILD_REPORT.md` → match
- `grep 'bhava_chalit_null_count: 0' EPHEMERIS_POST_REBUILD_REPORT.md` → match
