---
canonical_id: RUNBOOK_EPHEMERIS_REBUILD
version: 1.0
status: CURRENT
authored_on: 2026-05-19
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
sub_phase: 4B
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

## References

- Brief (Phase 4B): `00_ARCHITECTURE/BRIEFS/PHASE_4B_DERIVED_ENRICHMENT_BRIEF_v1_0.md`
- Brief (Phase 4C): `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANGA_BRIEF_v1_0.md`
- Derivation module: `platform/python-sidecar/pipeline/ephemeris_derivations.py`
- Panchanga derivation module: `platform/python-sidecar/pipeline/panchanga_derivations.py`
- Bootstrap (ephemeris): `platform/python-sidecar/pipeline/bootstrap_ephemeris.py`
- Bootstrap (panchanga): `platform/python-sidecar/pipeline/bootstrap_panchanga.py`
- Backfill: `platform/python-sidecar/pipeline/enrich_ephemeris_daily.py`
