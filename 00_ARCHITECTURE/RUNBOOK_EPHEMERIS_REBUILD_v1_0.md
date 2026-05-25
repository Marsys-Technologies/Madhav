---
artifact: RUNBOOK_EPHEMERIS_REBUILD_v1_0
canonical_id: RUNBOOK_EPHEMERIS_REBUILD
version: 1.1
status: CURRENT
authored_on: 2026-05-19
amended_on: 2026-05-25
amendment_session: DAR-P6-S21
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
sub_phase: 4B
changelog:
  - v1.1 (2026-05-25, DAR-P6-S21): Added §7 DAR MEAN_NODE Rebuild Operator Guide
    documenting the bootstrap invocation, monitoring, verification, atomic swap,
    and rollback procedure for the Data Asset Reconciliation rebuild.
  - v1.0 (2026-05-19): Initial authoring for Phase 4B derived enrichment campaign.
---

# Runbook — Ephemeris Daily Rebuild for §4.B

## When to run

After merging the §4.B PR. Native triggers; brief does NOT auto-execute.

## What it does

Rebuilds the entire `ephemeris_daily` table (657K rows) with:
- Rahu = MEAN_NODE (was TRUE_NODE) — small longitude shift propagates to sign/nakshatra/pada for dates where true node diverges from mean node
- 6 new derived columns populated inline (dignity_d1, is_combust, combust_orb_deg, vargottama_today, sign_ingress_today, whole_sign_house, graha_yuddha_with)

## Prerequisites

1. Migration `059_ephemeris_derived_columns.sql` applied against target DB.
2. Cloud SQL Auth proxy running (see below).
3. `DATABASE_URL` environment variable set.
4. `pyswisseph>=2.10.0` installed in the python-sidecar venv.

## Steps

### 1. Start Cloud SQL Auth proxy

```bash
platform/scripts/start_db_proxy.sh
# Listens on localhost:5433 by default.
```

### 2. Export DATABASE_URL

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5433/madhav_jis"
```

### 3. Apply migration (if not already applied)

```bash
psql "$DATABASE_URL" -f platform/migrations/059_ephemeris_derived_columns.sql
```

Verify:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name='ephemeris_daily'
  AND column_name IN ('dignity_d1','is_combust','whole_sign_house');
-- Must return 3 rows.
```

### 4. Choose rebuild path

---

### Path A — Full rebuild via staging swap (recommended for production)

Truncates `ephemeris_daily_staging`, recomputes all 657K rows with MEAN_NODE
Rahu + 6 derived columns, then swaps staging → live atomically.

```bash
# Truncate staging
psql "$DATABASE_URL" -c "TRUNCATE ephemeris_daily_staging;"

# Bootstrap into staging
cd platform/python-sidecar
python -m pipeline.bootstrap_ephemeris \
  --build-id "phase-4b-$(date +%Y%m%d)" \
  --skip-csv-check

# Verify count (expect 657,450 = 73,050 days × 9 planets)
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily_staging;"

# Verify derived columns populated
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily_staging WHERE dignity_d1 IS NULL;"
# Must be 0.

# Atomic swap
python -m pipeline.swap_ephemeris_staging
```

**Use Path A when**: you want the MEAN_NODE Rahu fix AND derived columns.
This is the correct production path.

---

### Path B — Enrichment-only (fast, but does NOT fix MEAN_NODE Rahu)

Computes derived columns from existing rows without re-running pyswisseph.
Rahu longitude stays as originally bootstrapped (TRUE_NODE). Use only if the
MEAN_NODE fix is explicitly deferred.

```bash
cd platform/python-sidecar

# Dry-run first — inspect 100 rows
python -m pipeline.enrich_ephemeris_daily --dry-run --limit 100

# Full enrichment
python -m pipeline.enrich_ephemeris_daily
```

**Use Path B when**: you accept TRUE_NODE Rahu for now and only want the 6
derived columns to be available immediately (e.g., to unblock synthesis-layer
development while a full rebuild is scheduled separately).

---

## Verification (post-rebuild)

```sql
-- All rows have derived columns populated (must be 0)
SELECT COUNT(*) FROM ephemeris_daily WHERE dignity_d1 IS NULL;

-- Spot-check native birth day (1984-02-05)
SELECT date, planet, sign, sign_degree, dignity_d1, whole_sign_house
FROM ephemeris_daily WHERE date='1984-02-05' ORDER BY planet;

-- Verify MEAN_NODE fix: Rahu should be retrograde always, speed ≈ -0.053°/day
SELECT date, planet, speed_deg_per_day, is_retrograde
FROM ephemeris_daily
WHERE planet='rahu' AND date='1984-02-05';

-- Spot-check exalted Jupiter (Jupiter exalted in Cancer)
SELECT date, planet, sign, dignity_d1
FROM ephemeris_daily
WHERE planet='jupiter' AND sign='Cancer' AND dignity_d1='exalted'
LIMIT 5;
```

## Rollback

### Path A rollback

Re-bootstrap with prior `build_id` into staging and swap back. Alternatively,
restore from the most recent Cloud SQL backup taken before the rebuild.

### Path B rollback

Clear derived columns to restore pre-4B state (columns are nullable):

```sql
UPDATE ephemeris_daily SET
  dignity_d1=NULL, is_combust=NULL, combust_orb_deg=NULL,
  vargottama_today=NULL, sign_ingress_today=NULL,
  whole_sign_house=NULL, graha_yuddha_with=NULL;
```

## Estimated runtime

- Path A: ~4–6 hours for 73,050 days × 9 planets at ~3 days/second.
- Path B: ~20–40 minutes for 657K UPDATE batches at 500 rows/batch.

## §4 Panchanga Bootstrap (Phase 4C)

Independent of the ephemeris_daily rebuild. ~73,050 rows, ~30 minutes runtime.

### Steps

1. Start Cloud SQL Auth proxy on port 5433.
2. Apply migration:
   ```bash
   psql "$DATABASE_URL" -f platform/migrations/060_panchanga_daily.sql
   ```
3. Bootstrap (writes to staging):
   ```bash
   cd platform/python-sidecar
   python -m pipeline.bootstrap_panchanga --build-id "phase-4c-$(date +%Y%m%d)"
   ```
4. Verify count = 73,050:
   ```sql
   SELECT COUNT(*) FROM panchanga_daily_staging;
   ```
5. Swap atomically:
   ```sql
   BEGIN;
   TRUNCATE panchanga_daily;
   INSERT INTO panchanga_daily SELECT * FROM panchanga_daily_staging;
   COMMIT;
   ```
6. Spot-check known dates:
   ```sql
   -- Native birth day panchanga
   SELECT date, tithi_name, vara, moon_nakshatra, yoga, karana
   FROM panchanga_daily WHERE date = '1984-02-05';
   -- Next Purnima from a known reference
   SELECT date, tithi_name FROM panchanga_daily
   WHERE date >= '2026-05-19' AND tithi = 15 ORDER BY date ASC LIMIT 1;
   ```

### Rollback

```sql
TRUNCATE panchanga_daily;
DROP TABLE IF EXISTS panchanga_daily, panchanga_daily_staging;
-- then re-run migration to recreate empty tables
```

---

---

## §5 Transit Search Sidecar Endpoint (Phase 4D)

No bootstrap or precompute needed. The `/transit_search` POST endpoint is
live-compute via Swiss Ephemeris. It depends on the sidecar service being
running and reachable from the web tier.

### Verification post-merge

1. Confirm sidecar deployment includes the new router:

```bash
curl -s -X POST ${SIDECAR_URL}/transit_search \
  -H "x-api-key: ${PYTHON_SIDECAR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "conjunction",
    "planet_a": "Jupiter",
    "planet_b": "Saturn",
    "start_date": "2026-05-19",
    "end_date": "2027-05-19",
    "orb_deg": 1.0
  }' | jq length
```

Expect: a JSON array (likely empty or 1-2 events for that window). A `404`
or `500` means the router was not registered — check `main.py` imports.

2. Latency expectations:
   - Aspect/conjunction searches over 2-year windows: ~500ms–2s (bisection
     over ~730 day-steps per planet pair).
   - Ingress and station queries hit Postgres directly via the TS tool: <100ms.

3. Window cap sanity check:

```bash
curl -s -X POST ${SIDECAR_URL}/transit_search \
  -H "x-api-key: ${PYTHON_SIDECAR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "conjunction",
    "planet_a": "Jupiter",
    "planet_b": "Saturn",
    "start_date": "2020-01-01",
    "end_date": "2031-01-02"
  }' | jq .detail
```

Expect: `"Window exceeds ±10-year cap"` (HTTP 400).

## References

- Brief (Phase 4B): `00_ARCHITECTURE/BRIEFS/PHASE_4B_DERIVED_ENRICHMENT_BRIEF_v1_0.md`
- Brief (Phase 4C): `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANGA_BRIEF_v1_0.md`
- Brief (Phase 4D): `00_ARCHITECTURE/BRIEFS/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md`
- Derivation module: `platform/python-sidecar/pipeline/ephemeris_derivations.py`
- Panchanga derivation module: `platform/python-sidecar/pipeline/panchanga_derivations.py`
- Bootstrap (ephemeris): `platform/python-sidecar/pipeline/bootstrap_ephemeris.py`
- Bootstrap (panchanga): `platform/python-sidecar/pipeline/bootstrap_panchanga.py`
- Backfill: `platform/python-sidecar/pipeline/enrich_ephemeris_daily.py`

---

## §6 Bhava-Chalit Backfill (Phase 4 §6.6 follow-up)

After migration 061 lands, the `bhava_chalit_house` column is added to
`ephemeris_daily` (nullable, IF NOT EXISTS). Backfill via the enrich script
takes ~5-10 min for 660K rows (pure-Python derivation, no Swiss Ephemeris
recompute — just SELECT longitude_deg + UPDATE bhava_chalit_house).

**Decision: run via Cloud SQL proxy session (Path B below), not a one-shot
Cloud Run job.** The backfill is a single idempotent Python script invocation
with no network I/O beyond the database. Cloud SQL proxy is already the
established operator pattern for DML operations on this project (see §1-§3
above). A one-shot Cloud Run job adds image-build + Cloud Run overhead for a
~10 min task; proxy is faster and simpler. If the backfill needs to be
re-triggered (e.g., after a future full rebuild), the proxy path is equally
convenient.

### Steps

1. Apply migration 061 via Cloud SQL proxy:

   ```bash
   # Start Cloud SQL Auth proxy (if not already running)
   cloud-sql-proxy madhav-marsys:asia-south1:madhav-marsys-pg --port 5433 &

   export DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@localhost:5433/madhav"
   psql "$DATABASE_URL" -f platform/migrations/061_ephemeris_bhava_chalit.sql
   ```

2. Run the backfill (idempotent — only patches rows where `bhava_chalit_house IS NULL`):

   ```bash
   cd platform/python-sidecar
   python -m pipeline.enrich_ephemeris_daily --backfill-bhava-chalit
   ```

   Optional dry-run first to confirm script starts cleanly:

   ```bash
   python -m pipeline.enrich_ephemeris_daily --backfill-bhava-chalit --dry-run
   ```

3. Verify completeness:

   ```sql
   SELECT COUNT(*) AS total,
          COUNT(*) FILTER (WHERE bhava_chalit_house IS NULL) AS still_null
   FROM ephemeris_daily;
   -- Expect: still_null = 0
   ```

4. Spot-check native birth day (1984-02-05). For Aries lagna at 12°25',
   Saturn at Libra 22.43° should be in bhava 7 (both Whole-Sign and
   Bhava-Chalit agree — Saturn is near the DSC, not in sandhi):

   ```sql
   SELECT date, planet, longitude_deg, sign, sign_degree,
          whole_sign_house, bhava_chalit_house
   FROM ephemeris_daily
   WHERE date = '1984-02-05' AND planet IN ('saturn', 'sun', 'moon', 'mars')
   ORDER BY planet;
   -- Expected: saturn whole_sign_house=7, bhava_chalit_house=7
   -- Expected: sun    whole_sign_house=10, bhava_chalit_house=11  ← sandhi case
   ```

5. Verify the index was created:

   ```sql
   SELECT indexname FROM pg_indexes
   WHERE tablename = 'ephemeris_daily' AND indexname = 'idx_ephemeris_bhava_chalit';
   ```

### Native Sripati cusps (canonical project values)

These are the 12 Sripati bhava madhyas (midpoints) for the native's birth chart,
computed by `_compute_native_sripati_cusps` at 1984-02-05T05:13:00 UTC,
Bhubaneswar (20.27021°N, 85.82966°E), Lahiri sidereal:

| Bhava | Madhya (°) | Sign         | Degree |
|-------|-----------|--------------|--------|
|  1    |  12.4189  | Aries        | 12°25' | ← ASC (lagna)
|  2    |  39.2710  | Taurus       |  9°16' |
|  3    |  66.1230  | Gemini       |  6°07' |
|  4    |  92.9750  | Cancer       |  2°58' | ← IC
|  5    | 126.1230  | Leo          |  6°07' |
|  6    | 159.2710  | Virgo        |  9°16' |
|  7    | 192.4189  | Libra        | 12°25' | ← DSC
|  8    | 219.2710  | Scorpio      |  9°16' |
|  9    | 246.1230  | Sagittarius  |  6°07' |
| 10    | 272.9750  | Capricorn    |  2°58' | ← MC
| 11    | 306.1230  | Aquarius     |  6°07' |
| 12    | 339.2710  | Pisces       |  9°16' |

These values are project-defining constants for the native's Bhava-Chalit layer.
M7 multi-native extension will require per-native cusp computation; these
native-specific values become a single row in a future `native_sripati_cusps`
table.

### Rollback

```sql
-- Nullify the column (soft rollback — leaves column in place):
UPDATE ephemeris_daily SET bhava_chalit_house = NULL;

-- Hard rollback (removes column entirely):
ALTER TABLE ephemeris_daily DROP COLUMN bhava_chalit_house;
ALTER TABLE ephemeris_daily_staging DROP COLUMN bhava_chalit_house;
DROP INDEX IF EXISTS idx_ephemeris_bhava_chalit;
```

---

## §7 DAR MEAN_NODE Rebuild — Operator Guide (DAR-P6-S21)

**Context:** The Data Asset Reconciliation (DAR) campaign found `ephemeris_daily` was
populated before the §4.B fix (2026-05-19), meaning live rows use TRUE_NODE for Rahu/Ketu.
FORENSIC v8.0 and Jyotish tradition require MEAN_NODE. This section is the operator guide
for executing the MEAN_NODE rebuild as part of DAR-P6-S22.

**Pre-flight check artifact:**
`00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md`

**Bootstrap script:** `platform/python-sidecar/pipeline/bootstrap_ephemeris.py`
`swe.MEAN_NODE` is hardcoded at line 252 — no flag needed, no `--node-type` argument.

**Expected row count:** 657,450 (73,050 days × 9 planets, 1900-01-01..2100-12-31)

**Estimated runtime:** 4–6 hours (~110,000 rows/hour)

### §7.1 Pre-flight checks

```bash
# Confirm DATABASE_URL is set and psql connects
echo ${DATABASE_URL:-"NOT_SET"}
psql "$DATABASE_URL" -c "SELECT 1;"

# Confirm disk space >= 10 GB free
df -h .

# Confirm Python dependencies
cd platform/python-sidecar
python -c "import swisseph; print('swisseph OK:', swisseph.version)"
python -c "import psycopg2; print('psycopg2 OK')" || python -c "import psycopg; print('psycopg OK')"

# Confirm Swiss Ephemeris data files present
ls platform/python-sidecar/ephe/ | head -5

# Confirm ephemeris_daily_staging is empty (or truncate it)
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily_staging;"
# If > 0 and you want a fresh run:
psql "$DATABASE_URL" -c "TRUNCATE TABLE ephemeris_daily_staging;"

# Record production baseline for audit trail
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily;"
```

### §7.2 Run bootstrap

The standard invocation. No special node-type flag needed — MEAN_NODE is hardcoded.

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar

# Optional dry-run on a small window first
DATABASE_URL="$DATABASE_URL" python -m pipeline.bootstrap_ephemeris \
  --dry-run \
  --start 1984-02-01 \
  --end 1984-02-10
# Expected: 10 days × 9 planets = 90 rows computed (no DB write)

# Full rebuild (writes to ephemeris_daily_staging)
DATABASE_URL="$DATABASE_URL" python -m pipeline.bootstrap_ephemeris \
  --build-id "ephemeris-mean-node-rebuild-$(date +%Y%m%d)" \
  --skip-csv-check
# Use --skip-csv-check unless GCS CSV at gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv is available.
# Idempotent: if interrupted, re-run with the same --build-id to resume.
```

### §7.3 Monitor progress

```bash
# Poll staging row count every 30 minutes
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily_staging;"

# Progress milestones (approximate):
#   1 hour  →  ~110,000 rows
#   2 hours →  ~220,000 rows
#   4 hours →  ~440,000 rows
#   6 hours →  ~657,450 rows (complete)
```

### §7.4 Verify after bootstrap completes

All checks must PASS before atomic swap.

```bash
# §7.4.1 Row count = 657,450
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily_staging;"

# §7.4.2 Spot-check Rahu at native birth date (1984-02-05)
# FORENSIC v8.0: Rahu in Gemini. MEAN_NODE Rahu at 1984-02-05 ≈ 67–68° (Gemini).
# TRUE_NODE would show same sign but slightly different longitude.
psql "$DATABASE_URL" -c "
  SELECT date, planet, longitude_deg, sign, sign_degree, nakshatra
  FROM ephemeris_daily_staging
  WHERE date = '1984-02-05' AND planet IN ('rahu','ketu')
  ORDER BY planet;"
# PASS: rahu sign = 'Gemini'; ketu sign = 'Sagittarius'

# §7.4.3 Rahu always retrograde (MEAN_NODE convention)
psql "$DATABASE_URL" -c "
  SELECT COUNT(*) FROM ephemeris_daily_staging
  WHERE planet = 'rahu' AND is_retrograde = false;"
# PASS: count = 0

# §7.4.4 No duplicate (date, planet) pairs
psql "$DATABASE_URL" -c "
  SELECT date, planet, COUNT(*) AS cnt
  FROM ephemeris_daily_staging
  GROUP BY date, planet HAVING COUNT(*) > 1 LIMIT 5;"
# PASS: 0 rows

# §7.4.5 All 9 planets present
psql "$DATABASE_URL" -c "
  SELECT planet, COUNT(*) AS day_count
  FROM ephemeris_daily_staging GROUP BY planet ORDER BY planet;"
# PASS: 9 rows, each day_count = 73050
```

### §7.5 Atomic swap

Execute only after all §7.4 checks PASS.

```bash
psql "$DATABASE_URL" << 'SQL'
BEGIN;
DELETE FROM ephemeris_daily;
INSERT INTO ephemeris_daily SELECT * FROM ephemeris_daily_staging;
DO $$
DECLARE cnt INTEGER;
BEGIN
  SELECT COUNT(*) INTO cnt FROM ephemeris_daily;
  IF cnt <> 657450 THEN
    RAISE EXCEPTION 'Swap verification failed: expected 657450 rows, got %', cnt;
  END IF;
END $$;
TRUNCATE TABLE ephemeris_daily_staging;
COMMIT;
SQL

# Confirm live table
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily;"
# Expected: 657,450
```

### §7.6 Post-swap smoke test

```bash
# Final spot-check on live table
psql "$DATABASE_URL" -c "
  SELECT date, planet, longitude_deg, sign, nakshatra
  FROM ephemeris_daily
  WHERE date = '1984-02-05' AND planet IN ('rahu','ketu')
  ORDER BY planet;"
# PASS: rahu in Gemini; ketu in Sagittarius

# Rahu always retrograde in live table
psql "$DATABASE_URL" -c "
  SELECT COUNT(*) FROM ephemeris_daily
  WHERE planet = 'rahu' AND is_retrograde = false;"
# PASS: count = 0
```

### §7.7 Rollback

Production `ephemeris_daily` is untouched until the swap in §7.5.

**Pre-swap rollback (bootstrap failed):**
```bash
psql "$DATABASE_URL" -c "TRUNCATE TABLE ephemeris_daily_staging;"
# Fix the issue, then re-run §7.2 with a new build-id.
```

**Post-swap rollback:** Restore from Cloud SQL backup taken before the rebuild began.

### §7.8 Audit log entry (append after completion)

Append to `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CONDUCTOR_LOG.md`:
```
DAR-P6-S22 | EPHEMERIS MEAN_NODE REBUILD | COMPLETE
  build_id: ephemeris-mean-node-rebuild-<YYYYMMDD>
  rows_written: 657450
  rahu_spot_check_1984-02-05: Gemini <longitude>° PASS
  swap_completed: <timestamp>
```
