---
artifact: LOCALHOST_PROD_FULL_SYNC_CHECK_v1_0.md
canonical_id: LOCALHOST_PROD_FULL_SYNC_CHECK
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
purpose: >
  Read-only verification that localhost (main) and production are completely in sync across ALL planes:
  code (local==origin), every deployed service (web/sidecar/mcp/job-image) CONTAINS its relevant commits
  (ancestor check, not blind SHA-equality — path-filtered deploys legitimately lag main HEAD), and the
  database (all migrations applied to prod, no pending/failed, no schema drift). Produces a single
  green/red sync verdict. Diagnoses only; fixes are a separate decision.
audience: Claude Code (Antigravity)
---

# localhost == production — full sync check (read-only)

## §0 — What "in sync" correctly means
Images deploy per-service tagged `:${github.sha}` with PATH-FILTERING — a service is NOT redeployed when
a commit didn't touch its paths, so its deployed SHA can lag main HEAD AND THAT IS CORRECT. So the test
is per-service: "does the deployed image CONTAIN every commit that touched THIS service's source paths?"
(ancestor / no-missing-relevant-commit), not "does its SHA == main HEAD." Only a service MISSING a
commit that DID touch its code is real drift.

Deploy facts (from .github/workflows/deploy.yml): services `amjis-web`, `amjis-sidecar`, `amjis-mcp`
(images `asia-south1-docker.pkg.dev/madhav-astrology/amjis/<svc>:${github.sha}`); migrations run in the
deploy-web job via `cd platform && npx tsx scripts/migrate.ts` against `PROD_DATABASE_URL` (push→main
auto-migrates prod). The Cloud Run JOB `brahma-build-pipeline-job` image
(`.../amjis/brahma-pipeline:...`) is built SEPARATELY (its own repo/build), so check it against ITS
source, not this deploy.yml.

## §1 — CODE: local == origin
```
git -C /Users/Dev/Vibe-Coding/Apps/Madhav fetch --all --prune
git rev-parse main origin/main
git status --short          # working tree must be clean
git log --oneline @{u}..HEAD ; git log --oneline HEAD..@{u}   # zero ahead, zero behind
```
PASS = local main SHA == origin/main SHA, clean tree, 0 ahead / 0 behind. Record main HEAD SHA = H.

## §2 — DEPLOYS: each service contains its relevant commits (ancestor check)
For each of amjis-web, amjis-sidecar, amjis-mcp, and brahma-build-pipeline-job:
2.1 — Resolve the deployed image SHA:
```
gcloud run services describe <svc> --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.containers[0].image)'        # → tag = a commit SHA
# job:
gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1 --project=madhav-astrology \
  --format='value(template.template.containers[0].image)'
```
Extract the commit SHA from each image tag → call it Dsvc.
2.2 — Determine each service's source paths (from deploy.yml path-filters + Dockerfile context):
  - web: platform/src, platform/app, platform/package*, platform/next.config*, platform/Dockerfile, etc.
  - sidecar: platform/python-sidecar/**
  - mcp: platform-mcp/**
  - job image: the pipeline source (python-sidecar pipeline/orchestrator/** + ga_writers/** + brahmagyan/**
    — the writers it runs). Confirm which repo/build produces it.
2.3 — The ancestor test per service:
```
# commits that touched THIS service's paths but are NOT in the deployed image:
git log --oneline <Dsvc>..H -- <service paths>
```
  - EMPTY → PASS (deployed image contains every commit affecting it; lag is path-filter-correct).
  - NON-EMPTY → REAL DRIFT: list the missing commits + which files; this service needs a redeploy.
2.4 — SPECIAL: the job image MUST contain every L0–L4 correctness fix (it runs the regeneration).
  Assert `git merge-base --is-ancestor <fix_sha> <Djob>` for the known fixes: ga_positions (731661e0),
  ga_sensitive (cf38e029), B5 ga_sensitive writer guard, ga_nakshatra dict_row, and any sweep fixes once
  they land. Any non-ancestor = job image too old to regenerate safely.

## §3 — DATABASE: migrations applied, no drift
3.1 — List migration files in main vs applied-in-prod:
```
ls platform/<migrations dir>           # the *.sql / migrate.ts manifest in the repo (find the dir)
```
  Read scripts/migrate.ts to learn HOW it tracks applied migrations (a migrations table? a ledger?).
  Then query prod (:5433) for the applied set:
```
# e.g. if migrate.ts uses a _migrations / schema_migrations table:
psql "$PROD_DATABASE_URL" -c "SELECT name FROM <migrations_table> ORDER BY 1;"
```
3.2 — DIFF: every migration file present in main is in prod's applied set. Report:
  - migrations in main NOT applied to prod → PENDING (drift — prod behind code).
  - migrations applied in prod NOT in main → ORPHAN (prod ahead / a deleted migration — investigate).
3.3 — FAILED/partial: any migration recorded as failed or partially applied? Any migration the deploy
  would re-run? (migrate.ts idempotency — does it skip already-applied?)
3.4 — SCHEMA spot-check: for a few tables the recent migrations created/altered (e.g. the latest
  migration's target table/column), confirm prod's actual schema matches (column exists, type matches).
  `psql "$PROD_DATABASE_URL" -c "\d+ <table>"`. This catches a "migration recorded applied but schema
  doesn't match" case.
3.5 — Note (from memory): push→main runs migrate.ts against PROD automatically in deploy-web. So if §1
  is in sync and the last deploy-web job succeeded, migrations SHOULD be current — but VERIFY via the
  applied-set diff, don't assume the job ran clean.

## §4 — BUILD ARTIFACTS (light)
If prod reads pre-built artifacts the code depends on (ephemeris data files, embeddings), confirm the
expected artifact exists/loads in prod (e.g. ephemeris range present, embedding model/version pinned).
Flag any artifact the current code expects that prod lacks. (Skip if none apply.)

## §5 — VERDICT
Single table:
| Plane | Check | Result | Drift? |
| code | local==origin, clean | … | |
| web | contains its commits | … | |
| sidecar | contains its commits | … | |
| mcp | contains its commits | … | |
| job-image | contains its commits + all L0–L4 fixes | … | |
| db-migrations | all main migrations applied, none failed | … | |
| db-schema | spot-check matches | … | |
GREEN = every plane PASS (services may lag main HEAD by SHA, but each contains its relevant commits, and
the job image contains every correctness fix; DB fully migrated, no drift). RED = any real-drift item,
listed with the exact missing commits / pending migrations.

## §6 — Guardrails
- READ-ONLY. No deploys, no migrations, no force-redeploy, no DB writes. This DIAGNOSES sync; fixing
  any RED item is a separate native decision.
- Ancestor semantics, NOT blind SHA-equality — do not flag a path-filter lag as drift.
- The job-image / L0–L4-fixes ancestor check (§2.4) is the one that gates the regeneration; surface it
  prominently.
- If prod DB read needs the proxy, use the :5433 Cloud SQL proxy; never a local Postgres.
DELIVER: the §5 verdict table +, for any RED, the precise missing commits / pending migrations / schema
mismatch. STOP and report.
