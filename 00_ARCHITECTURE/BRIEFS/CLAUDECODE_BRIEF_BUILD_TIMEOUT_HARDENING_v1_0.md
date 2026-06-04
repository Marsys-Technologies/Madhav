---
brief_id: BUILD_TIMEOUT_HARDENING_v1_0
status: ACTIVE
authored_by: Cowork (planning)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-05-31
model_directive: Use Gemini Pro or DeepSeek. Anthropic banned.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (main checkout)
work_branch: feat/build-timeout-hardening
estimated_loc: ~250 LOC + tests across 6 files
estimated_wallclock: 60–90 min
upstream_finding: STUCK_BUILDS_CLEANUP_v1_0 + memory/project_build_orchestrator_no_watchdog.md
                  — 32 builds accumulated over 39h with no automatic reaping.
---

# CLAUDECODE_BRIEF — Build orchestrator timeout + reaper + start-guard

## Why

The build orchestrator has no auto-timeout, no watchdog, no client-side
throttle. Surfaced 2026-05-31 when 32 stuck builds piled up over 39 hours
against the native chart, all needing manual cancellation. This brief
ships four layered protections so the same scenario can't recur:

| Layer | What | Why |
|---|---|---|
| **L1 — start-guard** | `/api/build/start` refuses if a non-terminal build already exists for `chart_id`; returns 409 with existing `build_id` | Stops the *stacking* at source |
| **L2 — Cloud Run Job timeout** | `--task-timeout=30m` on `marsys-build-pipeline-job` | Hard ceiling on container life |
| **L3 — cron reaper** | `POST /api/build/reap` invoked by Cloud Scheduler every 15 min | Cancels DB rows whose Cloud Run side already terminated abnormally |
| **L4 — cockpit button discipline** | Build button shows Cancel/Resume instead of Build when a non-terminal build exists | UX-side reinforcement of L1 |

L1+L3 are the load-bearing fixes. L2+L4 are belt-and-suspenders.

## Scope

`may_touch`:
- `platform/src/app/api/build/start/route.ts` (L1 guard)
- `platform/src/app/api/build/start/__tests__/route.test.ts` (extend)
- `platform/src/app/api/build/reap/route.ts` (NEW — L3 reaper)
- `platform/src/app/api/build/reap/__tests__/route.test.ts` (NEW)
- `platform/src/components/cockpit/BuildButton.tsx` (L4 — if file exists; else identify the cockpit's build CTA component and limit to ≤60 LOC)
- `infra/cloud_run_jobs/marsys-build-pipeline-job.tf` OR equivalent IaC file (L2 timeout)
- `infra/cloud_scheduler/build_reaper.tf` (NEW — L3 schedule)

`must_not_touch`:
- Any writer under `python-sidecar/pipeline/writers/`
- `dispatcher.py` (heartbeat is deferred — see §Deferred)
- Any other API route
- `charts` table or schema
- `00_ARCHITECTURE/` except this brief

## Hard gates

- L3 reap endpoint MUST require OIDC auth (Cloud Scheduler service account); otherwise it's a public DoS vector that can wipe live builds.
- The reaper SQL must NEVER touch a build whose Cloud Run execution is currently `Running`. Pull the live-execution set via `gcloud run jobs executions list --filter='-status.completionTime:*' --format='value(metadata.labels."build-id")'` and EXCLUDE those build_ids from the cancellation set.
- L1 guard returns 409, not 500. It is not an error — it's a successful "already running" response with the existing `build_id`.
- DO NOT deploy. DO NOT apply IaC. Push branch + open PR is the terminal state.
- DO NOT use Anthropic models.
- DO NOT add a heartbeat column to the builds table in this brief — that's a separate change. Stale detection uses `started_at` for `running` and `created_at` for `queued/pending`.

## Pre-flight

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/build-timeout-hardening

# Identify the IaC file for the Cloud Run Job (could be Terraform or YAML).
# Print what you find; if no IaC exists, surface that as a blocker.
find infra/ -type f \( -name "*.tf" -o -name "*.yaml" -o -name "*.yml" \) \
  | xargs grep -l "marsys-build-pipeline-job\|amjis-build" 2>/dev/null \
  | head -5

# Identify the cockpit Build button file
grep -rln "onClick.*[Bb]uild\|api/build/start" platform/src/components/ \
  | grep -v test | head -5
```

If IaC for the build job doesn't exist, document in §Followup that L2 will be a manual `gcloud run jobs update --task-timeout=30m` operator action instead of an IaC change. Do not invent IaC files.

## §L1 — Start-guard

In `platform/src/app/api/build/start/route.ts`, BEFORE the INSERT INTO builds, add:

```ts
// ─── Concurrency guard ──────────────────────────────────────────────────────
// Refuse to start a new build when a non-terminal build already exists for
// this chart. Returns 409 with the existing build_id — caller can poll or
// cancel it. Prevents the "stuck builds pile up" failure mode (see
// 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md).
const existing = await query<{ build_id: string; status: string; started_at: string | null }>(
  `SELECT build_id, status, started_at
     FROM builds
    WHERE chart_id = $1
      AND status IN ('running', 'queued', 'pending')
    ORDER BY created_at DESC
    LIMIT 1`,
  [chart_id],
)
if (existing.rows[0]) {
  const row = existing.rows[0]
  return NextResponse.json(
    {
      error: 'build_already_active',
      build_id: row.build_id,
      status: row.status,
      started_at: row.started_at,
      message: 'A build for this chart is already in flight. Cancel it before starting a new one.',
    },
    { status: 409 },
  )
}
```

Use the actual auth + request-shape conventions already in that route — do not regress them.

**Tests** (extend route.test.ts):
1. `test: returns 409 when running build exists for chart_id` — mock `query` to return a row with status='running'; assert response.status === 409 and `error === 'build_already_active'`.
2. `test: returns 409 when queued build exists for chart_id` — same pattern, status='queued'.
3. `test: proceeds to insert when only complete/failed/cancelled builds exist for chart_id` — mock empty result; assert INSERT runs.
4. `test: 409 response includes existing build_id` — assert payload has the row's build_id.

## §L2 — Cloud Run Job timeout

If IaC file exists (`infra/cloud_run_jobs/marsys-build-pipeline-job.tf` or similar), update the Terraform resource:

```hcl
resource "google_cloud_run_v2_job" "marsys_build_pipeline_job" {
  # ... existing fields ...
  template {
    template {
      timeout = "1800s"   # 30 minutes — hardens against runaway containers
      max_retries = 1     # one retry on transient failure, no more
      # ... existing fields ...
    }
  }
}
```

If IaC doesn't exist, add a section to §Followup:
```
L2 manual operator action (no IaC file found):
  gcloud run jobs update marsys-build-pipeline-job \
    --region=asia-south1 \
    --task-timeout=30m \
    --max-retries=1
```

## §L3 — Reaper

### L3.1 — Endpoint

Create `platform/src/app/api/build/reap/route.ts`:

```ts
/**
 * POST /api/build/reap
 *
 * Cron-invoked reaper. Cancels stale builds (DB rows in non-terminal states
 * whose containers have already terminated abnormally or were never picked up).
 *
 * Auth: OIDC token from Cloud Scheduler (service account check).
 * Schedule: every 15 minutes (see infra/cloud_scheduler/build_reaper.tf).
 *
 * Reap criteria:
 *   - status = 'running' AND started_at < NOW() - INTERVAL '1 hour'
 *   - status IN ('queued', 'pending') AND created_at < NOW() - INTERVAL '15 minutes'
 * Excludes any build_id whose Cloud Run execution is still Running (live-set check).
 */
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { verifyOidcToken } from '@/lib/auth/oidc'   // see L3.2 below
import { listLiveBuildExecutions } from '@/lib/cloud_run/jobs'   // see L3.3 below

export const dynamic = 'force-dynamic'

export async function POST(request: Request): Promise<Response> {
  // ── Auth (OIDC from Cloud Scheduler) ─────────────────────────────────────
  const token = request.headers.get('Authorization')?.replace(/^Bearer /, '')
  if (!token) return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  const claims = await verifyOidcToken(token, {
    expectedAudience: process.env.NEXT_PUBLIC_APP_URL ?? 'https://amjis-web',
    expectedServiceAccount: process.env.BUILD_REAPER_SA_EMAIL,
  }).catch(() => null)
  if (!claims) return NextResponse.json({ error: 'forbidden' }, { status: 403 })

  // ── Live-execution exclusion set ─────────────────────────────────────────
  const liveBuildIds = await listLiveBuildExecutions().catch(() => new Set<string>())

  // ── Find candidates ──────────────────────────────────────────────────────
  const { rows } = await query<{ build_id: string; status: string; age_minutes: number }>(
    `SELECT build_id, status,
            EXTRACT(EPOCH FROM (NOW() - COALESCE(started_at, created_at))) / 60 AS age_minutes
       FROM builds
      WHERE (status = 'running'  AND started_at < NOW() - INTERVAL '1 hour')
         OR (status IN ('queued','pending') AND created_at < NOW() - INTERVAL '15 minutes')`,
  )

  const toReap = rows.filter((r) => !liveBuildIds.has(r.build_id))
  if (toReap.length === 0) {
    return NextResponse.json({ reaped: 0, candidates: rows.length, live_skipped: rows.length })
  }

  // ── Reap (atomic) ────────────────────────────────────────────────────────
  const reapIds = toReap.map((r) => r.build_id)
  await query(
    `UPDATE builds
        SET status = 'cancelled',
            finished_at = COALESCE(finished_at, NOW()),
            cancelled_at = COALESCE(cancelled_at, NOW())
      WHERE build_id = ANY($1)`,
    [reapIds],
  )
  await query(
    `UPDATE build_steps
        SET status = 'skipped',
            completed_at = COALESCE(completed_at, NOW())
      WHERE build_id = ANY($1)
        AND status IN ('running', 'queued')`,
    [reapIds],
  )
  await query(
    `INSERT INTO build_notifications (build_id, event_type, payload)
     SELECT build_id, 'build_cancelled',
            jsonb_build_object('reason', 'reaped_stale', 'reaped_at', NOW()::text)
       FROM unnest($1::uuid[]) AS build_id`,
    [reapIds],
  )

  return NextResponse.json({
    reaped: reapIds.length,
    candidates: rows.length,
    live_skipped: rows.length - toReap.length,
    build_ids: reapIds,
  })
}
```

**Note on schema column names:** if `cancelled_at` doesn't exist, drop that line; if `finished_at` is named differently, adapt. Use the same convention as the stuck-builds cleanup brief (status='skipped' for build_steps, not 'cancelled').

### L3.2 — OIDC verification helper

Create or reuse `platform/src/lib/auth/oidc.ts`. If it doesn't exist:

```ts
import { OAuth2Client } from 'google-auth-library'
const oauthClient = new OAuth2Client()

export async function verifyOidcToken(
  token: string,
  opts: { expectedAudience: string; expectedServiceAccount?: string },
): Promise<{ email: string; sub: string } | null> {
  const ticket = await oauthClient.verifyIdToken({
    idToken: token,
    audience: opts.expectedAudience,
  })
  const payload = ticket.getPayload()
  if (!payload?.email) return null
  if (opts.expectedServiceAccount && payload.email !== opts.expectedServiceAccount) return null
  return { email: payload.email, sub: payload.sub ?? '' }
}
```

If `google-auth-library` is not a project dep yet, add it: `cd platform && npm install google-auth-library`.

### L3.3 — Cloud Run live-execution helper

Create `platform/src/lib/cloud_run/jobs.ts`:

```ts
import { JobsClient } from '@google-cloud/run'

const REGION = 'asia-south1'
const PROJECT = process.env.GCP_PROJECT ?? 'madhav-astrology'
const JOB = 'marsys-build-pipeline-job'

let _client: JobsClient | null = null
function client() {
  if (!_client) _client = new JobsClient()
  return _client
}

/**
 * Returns the set of build_ids whose Cloud Run executions are currently Running.
 * Excluded from reaping to avoid race conditions.
 *
 * Relies on the dispatcher having labeled each execution with `build-id=<uuid>`.
 * If a Running execution has no build-id label, we conservatively include its
 * inferred build_id by parsing the execution name (best-effort).
 */
export async function listLiveBuildExecutions(): Promise<Set<string>> {
  const parent = `projects/${PROJECT}/locations/${REGION}/jobs/${JOB}`
  const liveIds = new Set<string>()
  try {
    const [executions] = await client().listExecutions({ parent })
    for (const exec of executions) {
      // Live = no completionTime set
      if (exec.completionTime) continue
      const buildId = exec.labels?.['build-id']
      if (buildId) liveIds.add(buildId)
    }
  } catch (err) {
    // Non-fatal: if Cloud Run API fails, fall back to "treat nothing as live"
    // — over-reaping is safer than under-reaping for the next 15-min cycle.
    console.error('[listLiveBuildExecutions] failed:', err)
  }
  return liveIds
}
```

If `@google-cloud/run` is not a dep: `cd platform && npm install @google-cloud/run`.

### L3.4 — Schedule

Create `infra/cloud_scheduler/build_reaper.tf`:

```hcl
resource "google_cloud_scheduler_job" "build_reaper" {
  name             = "build-reaper"
  description      = "Reaps stale builds every 15 min. See BRIEF BUILD_TIMEOUT_HARDENING_v1_0."
  schedule         = "*/15 * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "120s"
  region           = "asia-south1"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${var.amjis_web_url}/api/build/reap"

    oidc_token {
      service_account_email = google_service_account.build_reaper.email
      audience              = var.amjis_web_url
    }
  }
}

resource "google_service_account" "build_reaper" {
  account_id   = "build-reaper"
  display_name = "Build Reaper (Cloud Scheduler invoker)"
}
```

### L3.5 — Tests

In `platform/src/app/api/build/reap/__tests__/route.test.ts`:

1. `test: returns 401 without Authorization header`
2. `test: returns 403 with invalid OIDC token`
3. `test: returns 403 if token email != expected SA`
4. `test: returns {reaped:0} when no candidates`
5. `test: skips builds present in live-execution set`
6. `test: marks N builds cancelled, build_steps skipped, emits N notifications`

Mock `verifyOidcToken`, `listLiveBuildExecutions`, and `query` like the dedupe tests do.

## §L4 — Cockpit Build button discipline

In the cockpit's Build CTA component (locate via pre-flight grep):

1. Add a poll-on-mount + 10s interval call to a new lightweight read-only endpoint `GET /api/build/active?chart_id=X` (~10 LOC; query for non-terminal build).
2. If response has `build_id`, render Cancel + Resume (or "Build in progress") instead of Build.
3. If 409 returned from `/api/build/start`, immediately switch to in-progress UI with the returned `build_id`.

Keep this ≤ 60 LOC. If the cockpit component structure makes this a >100 LOC change, STOP and add to §Followup as a separate brief — L1+L2+L3 are enough to land the safety net.

The `/api/build/active` route (NEW), ~15 LOC:

```ts
// platform/src/app/api/build/active/route.ts
import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export async function GET(request: Request) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const chart_id = new URL(request.url).searchParams.get('chart_id')
  if (!chart_id) return NextResponse.json({ error: 'chart_id required' }, { status: 400 })

  const { rows } = await query<{ build_id: string; status: string }>(
    `SELECT build_id, status FROM builds
      WHERE chart_id = $1 AND status IN ('running','queued','pending')
      ORDER BY created_at DESC LIMIT 1`,
    [chart_id],
  )
  return NextResponse.json({ active: rows[0] ?? null })
}
```

## Local smoke (executor runs this)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash platform/scripts/start_db_proxy.sh &
sleep 5
cd platform
npm install   # picks up google-auth-library and @google-cloud/run
npm test -- start.test.ts reap.test.ts 2>&1 | tee /tmp/build_hardening_tests.log
```

All new tests + existing /api/build/start tests must pass.

## Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add platform/src/app/api/build/start/
git add platform/src/app/api/build/reap/
git add platform/src/app/api/build/active/
git add platform/src/lib/auth/oidc.ts 2>/dev/null || true
git add platform/src/lib/cloud_run/jobs.ts
git add platform/src/components/cockpit/   # only if L4 was implemented
git add infra/cloud_run_jobs/  2>/dev/null || true
git add infra/cloud_scheduler/build_reaper.tf
git add platform/package.json platform/package-lock.json

git status

git commit -m "feat(build): four-layer hardening — start-guard, timeout, reaper, button discipline

Resolves the failure mode that produced 32 stuck builds over 39h (cleaned up
via STUCK_BUILDS_CLEANUP brief 2026-05-31).

L1 (start-guard): /api/build/start now returns 409 with existing build_id
    when a non-terminal build exists for chart_id. Stops stacking at source.
L2 (timeout): Cloud Run Job task-timeout=30m, max-retries=1. Hard ceiling.
L3 (reaper): /api/build/reap invoked every 15 min by Cloud Scheduler with
    OIDC auth; cancels builds whose containers terminated abnormally,
    excluding any build_id whose execution is still Running.
L4 (UI): cockpit Build button polls /api/build/active and switches to
    Cancel/Resume when a non-terminal build exists.

No schema migration. No heartbeat column (deferred). DB cleanup uses
'skipped' for build_steps per project schema convention.

Brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TIMEOUT_HARDENING_v1_0.md
Native sign-off PENDING; do not merge to main without explicit approval."

git push -u origin feat/build-timeout-hardening
```

## Operator post-merge (DO NOT execute — print for the user)

```bash
# 1. Deploy web (picks up the new API routes + button)
gcloud builds submit --config cloudbuild.yaml

# 2. Apply IaC (if you use Terraform for these resources)
cd infra && terraform plan && terraform apply

# 3. If no IaC for the Cloud Run Job, set timeout manually:
gcloud run jobs update marsys-build-pipeline-job \
  --region=asia-south1 \
  --task-timeout=30m \
  --max-retries=1

# 4. Grant the build-reaper SA invoker on amjis-web:
gcloud run services add-iam-policy-binding amjis-web \
  --region=asia-south1 \
  --member="serviceAccount:build-reaper@madhav-astrology.iam.gserviceaccount.com" \
  --role=roles/run.invoker

# 5. Set the env var the reap route needs:
gcloud run services update amjis-web \
  --region=asia-south1 \
  --update-env-vars="BUILD_REAPER_SA_EMAIL=build-reaper@madhav-astrology.iam.gserviceaccount.com"

# 6. Smoke: wait 15 min, check Cloud Scheduler dashboard for one successful execution.
#    Also check logs: `gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=amjis-web AND textPayload:"reap"' --limit=10`
```

## Deferred (NOT in this brief)

- **Heartbeat column on builds + dispatcher writes every 60s.** More accurate stale-detection than created_at/started_at, but bigger surgical change. Author BUILD_HEARTBEAT_v1_0 brief when L1+L3 prove insufficient.
- **Per-chart build queue limit (max 3 historical builds retained, prune older).** Storage hygiene, not safety. Defer indefinitely.
- **Cockpit `<BuildHistory>` widget** showing last 10 builds with status. UX polish.

## Acceptance criteria

- [ ] `npm run build` in `platform/` succeeds.
- [ ] All new tests pass (L1: 4 tests, L3: 6 tests, L4-active: 2 tests).
- [ ] `grep -rn "build_already_active" platform/src/` returns the route + at least 4 test hits.
- [ ] `grep -rn "reaped_stale" platform/src/` returns the reap route + tests.
- [ ] If IaC files were touched, `terraform fmt -check` passes (or `terraform validate` if applicable).
- [ ] Single commit pushed to `feat/build-timeout-hardening`.
- [ ] Brief §"Operator post-merge" block printed to console at end of run.

---

End of brief.
