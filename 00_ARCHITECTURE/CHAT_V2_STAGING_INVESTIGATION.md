---
artifact: CHAT_V2_STAGING_INVESTIGATION
title: Chat-v2 §M.3 — Staging Environment Investigation
canonical_id: CHAT_V2_STAGING_INVESTIGATION
version: 1.0
status: CURRENT
authored: 2026-05-16
author: Claude (read-only investigation)
purpose: >
  Determine whether a separate staging environment (DB + app) exists
  for MARSYS-JIS, to inform §M.3 migration application sequencing for
  the Chat-v2 schema work.
---

# Chat-v2 §M.3 — Staging Environment Investigation

## §1 — Separate Cloud SQL Instances

**Command run:**
```
gcloud sql instances list --project=madhav-astrology \
  --format="table(name,region,databaseVersion,state)"
```

**Output:**
```
NAME            REGION       DATABASE_VERSION  STATUS
amjis-postgres  asia-south1  POSTGRES_15       RUNNABLE
```

**Analysis:** Exactly one Cloud SQL instance exists in the project. No instance
carries a `staging`, `stg`, `test`, or `preprod` name fragment.

**Verdict: NO STAGING**

---

## §2 — Separate Cloud Run Services

**Command run:**
```
gcloud run services list --project=madhav-astrology --region=asia-south1 \
  --format="table(metadata.name,status.url)"
```

**Output:**
```
NAME           URL
amjis-sidecar  https://amjis-sidecar-qm256lasva-el.a.run.app
amjis-web      https://amjis-web-qm256lasva-el.a.run.app
```

**Analysis:** Two Cloud Run services exist: `amjis-web` (production Next.js app)
and `amjis-sidecar` (Python sidecar). Neither carries a staging designation.
There is no `amjis-web-staging`, `amjis-web-stg`, or equivalent service. Both
services are production traffic endpoints.

**Verdict: NO STAGING**

---

## §3 — Deploy Workflow Environments

**File read:** `.github/workflows/deploy.yml`

**Key findings:**

| Attribute | Value |
|---|---|
| Trigger | `push` to `main` only + `workflow_dispatch` |
| Number of environments | 1 (production, implicit — no `environment:` key) |
| Branch conditionals | None — all steps run unconditionally on `main` |
| Jobs | `deploy-web` + `deploy-sidecar` — both target production Cloud Run services |
| Instance connection | `INSTANCE_CONNECTION_NAME=madhav-astrology:asia-south1:amjis-postgres` (hardcoded, production) |
| Secrets source | GCP Secret Manager production secrets (`amjis-db-password:latest`, etc.) |

There is no `if: github.ref == 'refs/heads/develop'` style gate, no
`environment: staging` block, no separate job targeting a staging revision or
tag, and no Cloud Run traffic split configuration. Every push to `main`
deploys directly to `amjis-web` (production).

**Verdict: NO STAGING**

---

## §4 — Environment Variable References to Staging

**Commands run:**
```
grep -rn "STAGING\|staging" platform/.env* .env* .github/ 2>/dev/null \
  | grep -v node_modules | head -30

grep -rn "STAGING_DATABASE_URL\|STAGING_URL" . 2>/dev/null \
  | grep -v node_modules | head -20
```

**Output:** Both commands returned empty — zero matches.

**Analysis:** No `STAGING_DATABASE_URL`, `STAGING_URL`, `STAGING_*`, or
`staging` string present in any env file or GitHub Actions configuration.

**Verdict: NO STAGING**

---

## §5 — Codebase Configuration

**Command run:**
```
grep -rn "staging" platform/src/lib/config 2>/dev/null | head -20
```

**Output:** Empty — zero matches.

**Analysis:** No code paths in `platform/src/lib/config` branch on
environment-name `"staging"`. The app has no runtime staging-detection logic.

**Verdict: NO STAGING**

---

## §6 — Migration History (Staging References)

**Directory listing:** `platform/supabase/migrations/` (last visible files)
```
057_school_signal_coverage.sql
058_school_analysis_runs.sql
059_convergence_scores.sql
060_school_disagreements.sql
```

**Grep for "staging" across all migration SQL files:**
```
grep -rn "staging" platform/supabase/migrations/ 2>/dev/null
```

**Output:** Empty — zero matches.

**Analysis:** No migration file contains the word "staging", no migrations
README references a staging-first apply pattern, and no prior migration
documentation describes a two-phase (staging → prod) rollout.

**Verdict: NO STAGING**

---

## §7 — GCP Auth Context

**Commands run:**
```
gcloud config get-value project
gcloud auth list --filter=status:ACTIVE --format="value(account)"
```

**Output:**
```
madhav-astrology
---
mail.abhisek.mohanty@gmail.com
```

**Analysis:** The operator shell is authenticated as the project owner
(`mail.abhisek.mohanty@gmail.com`) against the sole GCP project
`madhav-astrology`. All gcloud queries above reflect the complete, authoritative
state of this project — there is no second project (e.g., `madhav-astrology-stg`)
to inspect.

**Verdict: CONFIRMED — single GCP project, no staging project counterpart**

---

## §8 — DB Proxy Script Behavior

**File read:** `platform/scripts/start_db_proxy.sh`

**Relevant excerpt:**
```bash
source "$ENV_FILE"          # sources .env.rag
cloud-sql-proxy "$INSTANCE_CONNECTION_NAME" --port=5433
```

**Analysis:**

- The script is parameterized: it reads `INSTANCE_CONNECTION_NAME` from
  `.env.rag` at runtime rather than hardcoding the connection string inline.
- However, `.env.rag` in practice points to the single production instance
  `madhav-astrology:asia-south1:amjis-postgres` (confirmed by the deploy.yml
  hardcoded env var, and the single-instance Cloud SQL listing in §1).
- There is no `.env.rag.staging` file or conditional logic to select a
  different instance. The parameterization exists for local-dev convenience
  (overridable), not for a pre-existing staging instance.
- Port 5433 is used (non-default 5432) to avoid colliding with a local
  Postgres if one is running.

**Verdict: NO STAGING** — script is technically parameterizable but
currently hardwired to the production instance via `.env.rag`.

---

## §9 — Consolidated Verdict

| Question | Verdict |
|---|---|
| Separate Cloud SQL staging instance | **NO STAGING** |
| Separate Cloud Run staging service | **NO STAGING** |
| Deploy workflow staging environment | **NO STAGING** |
| STAGING_* env vars | **NO STAGING** |
| Codebase staging code paths | **NO STAGING** |
| Migration staging-first history | **NO STAGING** |
| GCP project isolation | **NO STAGING** (single project) |
| DB proxy parameterized for staging | **NO STAGING** (prod-only in practice) |

**Summary:** MARSYS-JIS operates a single-environment architecture.
There is no staging tier at any layer — no separate Cloud SQL instance,
no separate Cloud Run service, no staging branch, no staging env vars,
and no prior staging-first migration discipline. All migrations apply
directly to the production database (`amjis-postgres`).

---

## §10 — Recommendation for §M.3 Migration Application

Because no staging environment exists, the §M.3 migration sequencing
must use **local Postgres via Docker** as the pre-production verification
step before applying to the live `amjis-postgres` instance.

### Option A — Local Postgres via Docker (Recommended)

This recipe creates an isolated, ephemeral Postgres 15 instance that mirrors
production schema, applies the new Chat-v2 migration, verifies it, and tears
down cleanly. No production risk.

**Step 1 — Start ephemeral Postgres 15:**
```bash
docker run --name amjis-staging-local \
  -e POSTGRES_USER=amjis_app \
  -e POSTGRES_PASSWORD=localtest \
  -e POSTGRES_DB=amjis \
  -p 5434:5432 \
  --rm -d \
  postgres:15
```
Port 5434 avoids collision with the Cloud SQL proxy (5433) and any local
Postgres (5432).

**Step 2 — Apply all existing migrations (baseline):**
```bash
# Wait ~3s for container readiness, then:
DATABASE_URL="postgresql://amjis_app:localtest@127.0.0.1:5434/amjis" \
  npx supabase db push --local 2>/dev/null || \
  psql postgresql://amjis_app:localtest@127.0.0.1:5434/amjis \
    -f platform/supabase/migrations/001_*.sql \
    # ... apply each migration in sequence
```

**Practical note:** The simplest approach is to apply each numbered migration
SQL file in order with `psql`:
```bash
for f in platform/supabase/migrations/*.sql; do
  echo "Applying: $f"
  psql postgresql://amjis_app:localtest@127.0.0.1:5434/amjis -f "$f"
done
```

**Step 3 — Apply the Chat-v2 migration under test:**
```bash
psql postgresql://amjis_app:localtest@127.0.0.1:5434/amjis \
  -f platform/supabase/migrations/<NNN>_chat_v2_schema.sql
```

**Step 4 — Verify schema:**
```bash
psql postgresql://amjis_app:localtest@127.0.0.1:5434/amjis -c "\dt"
psql postgresql://amjis_app:localtest@127.0.0.1:5434/amjis \
  -c "SELECT column_name, data_type FROM information_schema.columns
      WHERE table_name = 'chat_v2_sessions' ORDER BY ordinal_position;"
```
Adjust table name to match the actual Chat-v2 migration target.

**Step 5 — Verify rollback (if migration has a down script):**
```bash
psql postgresql://amjis_app:localtest@127.0.0.1:5434/amjis \
  -f platform/supabase/migrations/<NNN>_chat_v2_schema_down.sql
# Re-apply to confirm idempotency if migration supports it
```

**Step 6 — Tear down:**
```bash
docker stop amjis-staging-local
# --rm flag above ensures automatic removal on stop
```

**Step 7 — Apply to production** (only after local verification passes):
```bash
# Start Cloud SQL proxy (port 5433):
bash platform/scripts/start_db_proxy.sh

# Apply migration:
psql postgresql://amjis_app:<prod_password>@127.0.0.1:5433/amjis \
  -f platform/supabase/migrations/<NNN>_chat_v2_schema.sql
```
`<prod_password>` is in GCP Secret Manager as `amjis-db-password:latest`.
Retrieve with:
```bash
gcloud secrets versions access latest \
  --secret=amjis-db-password --project=madhav-astrology
```

### Option B — Cloud Run Revision Tag (Future)

If a no-downtime staging tier is ever required, the lowest-cost approach
within the existing single-project architecture is:

1. Create `amjis-web-stg` as a second Cloud Run service (no new DB instance).
2. Give it `--no-traffic` and a named tag (`--tag=stg`).
3. Point it at a second Cloud SQL database (not instance) on `amjis-postgres`
   (Cloud SQL supports multiple databases per instance).

This is out of scope for Chat-v2 / §M.3 but documents the path if needed.

---

*Investigation performed 2026-05-16. All commands read-only; no files modified.*
