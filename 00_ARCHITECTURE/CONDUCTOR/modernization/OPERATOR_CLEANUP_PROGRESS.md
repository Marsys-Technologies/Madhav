---
artifact: OPERATOR_CLEANUP_PROGRESS
plan: OPERATOR_CLEANUP_PLAN_v1_0.md
plan_version: 1.1
kickoff: OPERATOR_CLEANUP_KICKOFF.md
kickoff_version: 1.1
status: IN_PROGRESS
started_at: 2026-05-28T17:00:00+05:30
seal_tag: platform-modernization-sealed-v1.0
seal_commit: ab7e1a9509e8a6b426975e53803229303ea86ef4
---

# Operator Cleanup — Progress Log

Live cursor for the post-seal cleanup run. Updated after each phase close.
Co-runs with `OPERATOR_CLEANUP_HALT_LOG.md` (written only on halt).

## Phase 0 — Remediation + Re-Verify

| R# | Check | Result | Notes |
|---|---|---|---|
| R1 | Commit Phase D correction edits | PASS | commit 9e5eb801 on main; push OK |
| R2 | Wipe partial terraform init residue | PASS | 4 stale `.terraform/` dirs removed (cloud_tasks, iam, memorystore, scheduler) |
| R3 | GCS state bucket `gs://madhav-astrology-tf-state` | PASS | Created at `asia-south1` with uniform BLA + 7d soft delete (was missing) |
| R4a | `infra/cloud_tasks/apply.sh plan` | PASS | 4 to add (queue, SA, run-invoker, jobsExecutor) |
| R4b | `infra/memorystore/apply.sh plan` | PASS | 1 to add (REDIS_7_2 BASIC, allkeys-lru) |
| R4c | `infra/scheduler/apply.sh plan` | PASS | 2 to add (amjis-mv-refresh, amjis-pending-stream-reaper) |
| R4d | `infra/edge/apply.sh plan` | PASS | 8 to add (CDN backend, armor policy + 5 rules, URL map) |
| R4e | `infra/iam/apply.sh plan` | PASS | 22 to add (4 runtime SAs + IAM bindings + WIF) |
| R5 | Smoke env vars (`SMOKE_CHART_ID`, `SMOKE_SESSION_COOKIE`) | PASS | Cookie minted via `mint_session_cookie.ts` (930 chars JWT); env persisted to `/tmp/madhav-cleanup/env.sh` (chmod 600) |
| R6 | Cloud SQL quota probe | PASS | Project CPU 32, regional CPU 100, regional N2 200 — all 0 used; 4 vCPU Phase J target fits with headroom; current instance `db-g1-small / ZONAL / 10 GB` in asia-south1-c |
| R7 | Final Phase 0 verification | _pending_ | |

## Subsequent Phases

| Phase | Status | Notes |
|---|---|---|
| A — Tag confirm + Phase 0 close | _pending_ | |
| B — Migrations 081–090 prep | _pending_ | |
| C1 — Pre-flight grep + mig 090 cutover | _pending_ | |
| D — IaC apply (5 modules) | _pending_ | |
| E — Cloud Run env-var cleanup | _pending_ | |
| F — answer:eval live baseline | _pending_ | |
| G — BUILD_TRIGGER flag flip | _pending_ | |
| H — amjis-tracker delete | _pending_ | |
| I — amjis-db-password rotate | _pending_ | |
| J — Cloud SQL scale + HA + partitioning | _pending_ | quota: GREEN per R6 |
| K — depth-selector native review | _pending_ | |
| L — engine hygiene (OPTIONAL) | _pending_ | |
| M — Final seal of cleanup arc | _pending_ | |
