# SESSION a2 — Ephemeris Build Status

Timestamp: 2026-06-05
Stream: postdeploy-a

## Cloud Run Job
`brahmagyan-ephemeris-build` — NOT FOUND in asia-south1 (infrastructure gap, logged in CLOUDRUN_JOB_GAP.md).

## Direct Python Execution
Falling back to direct Python via `brahmagyan/l0_ephemeris.py::build_ephemeris()`.

### Phase 1: Write path verification
- Sample build for 1984-02-05 (native birth date): 9 rows inserted OK
- Sun tropical_longitude=315.874° (Aquarius tropical — correct for Feb 5 1984)
- source_citation, ayanamsha_id columns populated correctly

### Phase 2: Full build 1980-2060
- Attempt 1: batch_size=365 — failed at batch 3 due to Cloud SQL proxy reset (proxy dropped connection after ~20 mins)
  - Rows committed before failure: 6,579 (731 dates × 9 bodies, up to 1984-02-05)
- Attempt 2: batch_size=30 — running as of 15:31 IST
  - Rows at checkpoint: 6,849 (763 dates × 9 bodies, up to 1984-03-06)
  - Build uses ON CONFLICT DO NOTHING — safe to restart/resume at any point

## Target
Volume floor: 29,200 rows (dates × 9 bodies for 1980-2060)
Status: AMBER (in progress, ~2.6% complete as of last check)

## Proxy Reset Issue (Tier-2 Infrastructure Constraint)
The Cloud SQL Auth Proxy repeatedly resets after ~5-10 minutes of activity.
Both batch_size=365 (attempt 1) and batch_size=30 (attempt 2) failed mid-run.

**Pattern**: proxy accepts connection → completes 1-2 batches → closes connection with EOF
**Root cause**: likely Cloud SQL idle connection timeout or proxy reconnect policy
**Rows committed before each proxy reset**:
- Attempt 1: 6,579 rows (1980-01-01 → 1984-02-05)
- Attempt 2: 7,659 rows (1980-01-01 → 1984-06-04) — net +1,080 rows

## Final State (wave-close)
- Rows in ephemeris_daily: **7,659** (851 dates × 9 bodies)
- Date range covered: **1980-01-01 → 1984-06-04** (first 4.4 years of 80-year build)
- Status: AMBER — partial build, well below 29,200 volume floor
- Volume floor: 29,200 dates — needs full 1980-2060 run

## Resolution
Full build requires running `build_ephemeris()` in a context with stable long-lived DB connection.
Options:
1. Cloud Run Job (direct instance connection, no proxy) — recommended
2. Run inside the sidecar container which connects via Unix socket (no proxy timeout)
3. Use a postgres keepalive setting or pgBouncer to prevent proxy resets

Resume command (idempotent, ON CONFLICT DO NOTHING):
```python
from brahmagyan.l0_ephemeris import build_ephemeris
from datetime import date
result = build_ephemeris(start=date(1984, 6, 5), end=date(2060, 12, 31), batch_size=30)
```

## Operator Note
Consider running this build directly inside the Cloud Run sidecar container for stable execution:
```
gcloud run jobs create brahmagyan-ephemeris-build \
  --image=IMAGE_WITH_PYSWISSEPH \
  --region=asia-south1 \
  --set-env-vars="START_DATE=1980-01-01,END_DATE=2060-12-31"
```
