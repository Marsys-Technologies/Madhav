---
session_id: DAR-P6-S23
phase: 6
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P6-S22]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/
  - platform/src/
  - platform/python-sidecar/pipeline/bootstrap_ephemeris.py
---

# DAR-P6-S23: Post-rebuild ephemeris verification

Context: DAR-P6-S22 ran the full ephemeris bootstrap. This session verifies correctness:
Rahu/Ketu must now be MEAN_NODE in production, the row count must be 657,450, and
the bhava_chalit columns must have no NULLs.

## Steps

### 1. Start DB proxy
  bash /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/start_db_proxy.sh &
  PROXY_PID=$!
  sleep 20

### 2. Check node type in production table
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT rahu_long, ketu_long, node_type \
     FROM ephemeris_daily \
     WHERE date = '1984-02-05' LIMIT 1;"
  
  Record the node_type value (expected: MEAN_NODE or the equivalent column).
  If the table has no node_type column, derive from value comparison with known MEAN_NODE values.

### 3. Spot-check Rahu at native birth date (1984-02-05)
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT date, rahu_long FROM ephemeris_daily WHERE date = '1984-02-05';"
  
  The FORENSIC document records Rahu at ~3°52' Gemini (≈ 63.87°).
  MEAN_NODE and TRUE_NODE differ by ~1.5° at most. Verify the value is in the Gemini range (60–90°).

### 4. Sample 50 random dates and check for anomalies
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT date, rahu_long, ketu_long \
     FROM ephemeris_daily \
     ORDER BY RANDOM() LIMIT 50;" | head -60

### 5. Verify row count
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT COUNT(*) FROM ephemeris_daily;"
  Expected: 657450

### 6. Check bhava_chalit null count
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT COUNT(*) FROM ephemeris_daily \
     WHERE bhava_chalit IS NULL OR bhava_chalit = '{}'::jsonb;"
  Expected: 0

### 7. Write EPHEMERIS_POST_REBUILD_REPORT.md
Write to: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md
  ---
  generated: [ISO timestamp]
  node_type: MEAN_NODE
  birth_date_rahu_spot_check: PASS
  birth_date_rahu_value: [value from step 3]
  row_count: 657450
  bhava_chalit_null_count: 0
  random_sample_anomalies: none
  notes: "Ephemeris rebuilt from bootstrap_ephemeris.py post-commit c63ef9f9 (MEAN_NODE fix)"
  ---

### 8. Stop proxy
  kill $PROXY_PID 2>/dev/null || true
