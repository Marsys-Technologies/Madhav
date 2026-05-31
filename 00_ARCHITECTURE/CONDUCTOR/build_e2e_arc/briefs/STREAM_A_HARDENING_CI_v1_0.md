---
brief_id: STREAM_A_HARDENING_CI_v1_0
status: ACTIVE
arc_id: build_e2e_arc
stream: A
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI
branch: feat/hardening-ci
base: main
sessions: 9
estimated_loc: ~700 across 14 files
---

# Stream A — Build orchestrator hardening + full CI/CD automation

Ships the safety net (L1 guard, L2 timeout, L3 reaper, L4 button polish)
AND extends deploy.yml so every main-branch push auto-deploys + auto-migrates
+ auto-applies IaC + auto-smokes + auto-promotes traffic.

## Cross-cuts read first

- `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md` (the master playbook — non-negotiable)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md` (the original L1-L4 brief — this stream subsumes it)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_STUCK_BUILDS_CLEANUP_v1_0.md` (context for why the reaper matters)

## Hard gates

- NO Anthropic models.
- NO direct prod DB writes from inside agent sessions. Migrations only via deploy.yml.
- NO `gcloud builds submit` / `gcloud run deploy` invoked from inside agent sessions. Deploy is GitHub-Actions-only.
- NO touching files outside Stream A's owned paths (see STREAM_COORDINATION §9).
- Reaper endpoint MUST require OIDC auth. Public reaper = DoS vector.
- Reaper SQL MUST exclude builds whose Cloud Run execution is currently Running (live-set check via `@google-cloud/run`).
- Migration runner MUST be idempotent and transactional. Apply-then-track or track-then-apply must roll back on partial failure.
- `builds.status` CHECK constraint allows: `running, queued, complete, failed, cancelled, cancelling`. NOT `pending`. Non-terminal set for guards/reapers = `('running', 'queued', 'cancelling')`. Verified empirically 2026-05-31 ship.
- `build_steps.status` CHECK constraint allows: `queued, running, complete, failed, skipped`. NOT `cancelled` or `pending` or `cancelling`. Use `skipped` for cancellation paths on STEPS.
- `builds.cancelled_at` exists. `cancel_reason` does NOT exist. Don't reference it.

**Pre-completed scope — DO NOT REDO:**
The standalone BUILD_TIMEOUT_HARDENING brief was executed by an Antigravity
session pre-Conductor (commit `5ef88415` on `feat/build-timeout-hardening`).
That branch ships:
- A-S1 (L1 start-guard) ✓
- A-S2 (L3 reaper endpoint + OIDC + Cloud Run helper) ✓
- A-S3 (L3 reaper tests, 6/6 green) ✓
- A-S4 (L4 button discipline — BuildButton.tsx 57 LOC EXISTS but **not yet wired into clients/[id]/build/page.tsx**; that page was outside the standalone brief's may_touch)
- A-S6 (Cloud Scheduler IaC) ✓

Stream A's effective work in this arc:
- B-S1 (merge feat/build-timeout-hardening into feat/hardening-ci) ← NEW first session
- A-S5 (Cloud Run Job timeout — manual gcloud, no terraform exists)
- A-S7 (migration runner)
- A-S8 (deploy.yml CI/CD extension)
- A-S9 (cherry-pick to main + watch first auto-deploy)
- COORDINATION: Stream C wires BuildButton.tsx into the cockpit page during its visual implementation (note added to Stream C brief).

## §A-S1 — L1 start-guard on POST /api/build/start

In `platform/src/app/api/build/start/route.ts`, BEFORE the INSERT INTO builds,
add a pre-INSERT lookup that returns 409 with the existing build_id if a
non-terminal build exists for this chart_id. Full spec lives in the
BUILD_TIMEOUT_HARDENING brief §L1 — reuse it verbatim, do not re-derive.

Add 4 tests in `platform/src/app/api/build/start/__tests__/route.test.ts`:
running blocks, queued blocks, only-terminal proceeds, 409 includes build_id.

Gate: `cd platform && npm test -- start.test.ts` → green.

## §A-S2 — L3 reaper endpoint + OIDC helper + Cloud Run helper

Create:
- `platform/src/app/api/build/reap/route.ts` — full spec in BUILD_TIMEOUT_HARDENING §L3.1
- `platform/src/lib/auth/oidc.ts` — verifyOidcToken (spec §L3.2)
- `platform/src/lib/cloud_run/jobs.ts` — listLiveBuildExecutions (spec §L3.3)

Install deps: `cd platform && npm install google-auth-library @google-cloud/run`.

Gate: `cd platform && npm run build` → green.

## §A-S3 — L3 reaper tests

6 tests per BUILD_TIMEOUT_HARDENING §L3.5 in
`platform/src/app/api/build/reap/__tests__/route.test.ts`.

Gate: `cd platform && npm test -- reap.test.ts` → green.

## §A-S4 — L4 button discipline + /api/build/active route

Create `platform/src/app/api/build/active/route.ts` (15 LOC, spec in
BUILD_TIMEOUT_HARDENING §L4 inline code).

Cockpit Build button discipline: locate via
`grep -rln "api/build/start" platform/src/components | grep -v test`.
Add poll-on-mount + 10s interval to /api/build/active. When response has
build_id, render Cancel/Resume; on 409 from /start, switch to in-progress.
60-LOC cap; if would exceed, halt and tag the L4 button work for a
follow-up brief (this happens, it's expected).

Add 2 tests for /api/build/active in `__tests__/active.test.ts`:
returns active build, returns null when none.

Gate: `cd platform && npm test -- active.test.ts` → green.

## §A-S5 — IaC: Cloud Run Job timeout + max-retries

Locate the IaC for `marsys-build-pipeline-job`:
```bash
find infra/ -type f \( -name "*.tf" -o -name "*.yaml" \) -exec grep -l "marsys-build-pipeline-job" {} \;
```

If terraform exists: add `timeout = "1800s"` + `max_retries = 1` to the
job template. If only gcloud-shell config exists: add to deploy.yml's
step 5 the command `gcloud run jobs update marsys-build-pipeline-job
--region=asia-south1 --task-timeout=30m --max-retries=1`.

Gate: `cd infra && terraform fmt -check` (if terraform) OR yaml lint.

## §A-S6 — IaC: Cloud Scheduler reaper + build-reaper SA

Create `infra/cloud_scheduler/build_reaper.tf` per
BUILD_TIMEOUT_HARDENING §L3.4. Also create the
`google_service_account` resource for `build-reaper`.

Gate: `cd infra && terraform validate` (with init if needed).

## §A-S7 — Migration runner

Create `platform/scripts/migrate.ts`:

```typescript
/**
 * Idempotent migration runner.
 * - Reads platform/migrations/*.sql and platform/supabase/migrations/*.sql
 * - Tracks applied migrations in _migrations_applied (id, filename, applied_at, sha256)
 * - For each unapplied migration in lexical order:
 *     BEGIN; <SQL>; INSERT INTO _migrations_applied; COMMIT;
 *   On any error: ROLLBACK and exit non-zero
 * - --dry-run flag: lists what would be applied; no writes
 * - --target <filename> flag: stops after that migration
 *
 * Connection: DATABASE_URL env var (Cloud SQL Auth Proxy in CI via WIF).
 */
```

Tracker table bootstrap (idempotent):
```sql
CREATE TABLE IF NOT EXISTS _migrations_applied (
  id SERIAL PRIMARY KEY,
  filename TEXT UNIQUE NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sha256 TEXT NOT NULL
);
```

Tests in `platform/scripts/__tests__/migrate.test.ts`:
- bootstrap creates tracker
- skips already-applied
- applies new in order
- rolls back on failure
- dry-run makes no writes

Gate: `cd platform && npm test -- migrate.test.ts` → green.

## §A-S8 — Extend .github/workflows/deploy.yml

**This session absorbs all 4 remaining operator actions from PR #174's
merge note** — they all become deploy.yml steps so future deploys are
fully self-contained:

1. `gcloud run jobs update marsys-build-pipeline-job --task-timeout=30m --max-retries=1` (was operator action #1)
2. `cd infra && terraform apply -auto-approve` (was operator action #2 — applies the cloud_scheduler module)
3. `gcloud run services add-iam-policy-binding amjis-web ... --role=roles/run.invoker --member="serviceAccount:build-reaper@..."` (was operator action #3 — OR migrate to a `google_cloud_run_service_iam_member` terraform resource and let step 2 handle it)
4. `gcloud run deploy amjis-web --update-env-vars="APP_URL=...,BUILD_REAPER_SA_EMAIL=build-reaper@madhav-astrology.iam.gserviceaccount.com" ...` (was operator action #4 — bake into the deploy command so every deploy reasserts them)

Once A-S8 lands, the operator has zero manual deploy steps for the
hardening arc.

Add post-build steps. Approximate shape:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
          service_account: ${{ secrets.GCP_DEPLOY_SA }}
      - name: Build amjis-web
        run: gcloud builds submit --config cloudbuild.yaml --quiet
      - name: Build amjis-sidecar
        run: gcloud builds submit --config platform-sidecar/cloudbuild.yaml --quiet
      - name: Start Cloud SQL proxy
        run: ./.github/scripts/start_proxy_ci.sh &
      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
        run: cd platform && npx tsx scripts/migrate.ts
      - name: Terraform apply
        run: cd infra && terraform init && terraform apply -auto-approve
      - name: Deploy web (no traffic)
        run: gcloud run deploy amjis-web --no-traffic ...
      - name: Deploy sidecar (no traffic)
        run: gcloud run deploy amjis-sidecar --no-traffic ...
      - name: Post-deploy smoke
        run: bash scripts/operator/end_to_end_smoke.sh
      - name: Promote traffic
        if: success()
        run: gcloud run services update-traffic amjis-web --to-latest --region=asia-south1
```

Create `scripts/operator/end_to_end_smoke.sh`:
- curl /api/health on both services with retries
- (optional) hit /api/build/active with a known chart_id
- exit non-zero on any failure

Gate: `yamllint .github/workflows/deploy.yml` (or basic YAML parse).

## §A-S9 — Final commit + cherry-pick to main

Per STREAM_COORDINATION §5. The cherry-pick of A-S8 triggers the FIRST
auto-deploy run. Watch CI; if it fails, the deploy.yml has bugs to fix
inline before B/C/D's commits start arriving.

If A-S8's cherry-pick triggers an auto-deploy that fails halfway through
the new step chain (e.g. migration runner has a bug), the agent reads
the failed step output and patches it in a hotfix commit per CI auto-fix
policy (5 attempts).

Gate: `git log origin/main..HEAD --oneline` returns 0 (everything is upstream).

---

End of Stream A brief.
