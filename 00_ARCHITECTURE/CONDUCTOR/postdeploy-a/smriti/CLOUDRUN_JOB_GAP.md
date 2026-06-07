# Tier-2 Decision: Cloud Run Jobs Missing

Timestamp: 2026-06-05
Stream: postdeploy-a
Sessions: a2 (ephemeris-build), a3 (remedy-seed)
Decision: INFRASTRUCTURE_GAP

## Finding
Cloud Run Jobs `brahmagyan-ephemeris-build` and `brahmagyan-remedy-seed` do not exist in asia-south1.

Commands checked (with brahma-swarm-bot SA impersonation):
- `gcloud run jobs describe brahmagyan-ephemeris-build --region=asia-south1` → ERROR: Cannot find job
- `gcloud run jobs describe brahmagyan-remedy-seed --region=asia-south1` → ERROR: Cannot find job

## Resolution
Proceeded with direct Python execution via python-sidecar modules:
- `platform/python-sidecar/brahmagyan/l0_ephemeris.py` — has `build_ephemeris()` function
- `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py` — has `seed_remedy_corpus()` function

Full ephemeris build (1980-2060, ~262k rows) requires either:
1. Cloud Run Job provisioning by operator, OR
2. Direct Python execution with DATABASE_URL set (feasible locally via proxy)

Remedy corpus seed (54 rows, hardcoded) is achievable via direct Python execution.

## Action Taken
- a3 (remedy-seed): Executed via direct Python path — 54 rows seeded successfully.
- a2 (ephemeris-build): Full 1980-2060 build is long-running (~262k rows). 
  Attempted sample verification (native birth date 1984-02-05).
  See A2_EPHEMERIS_STATUS.md for details.

## Operator Follow-up Required
For the full ephemeris build covering 1980-2060 (29,221 days × 9 bodies = 263k rows):
- Option A: Provision Cloud Run Job `brahmagyan-ephemeris-build` with pyswisseph image
- Option B: Run `build_ephemeris()` from python-sidecar container with DATABASE_URL
- Option C: Run locally (takes ~30 min with pyswisseph installed)
