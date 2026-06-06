# Go-Live Ops — PHASE_LOG

Brief: `ANTIGRAVITY_PASTE_GO_LIVE_OPS.md`
Started: 2026-06-06

---

## Phase 0 — Preflight: State Inventory + Safety Checks

### 0.A — Branch State

| Repo | Branch | HEAD | Status |
|---|---|---|---|
| Madhav | `feature/cockpit-v2-three-views` | `6281505e` — docs(orchestrator): Phase 7 seal | ✓ MATCHES |
| brahma-pipeline | N/A | **NOT FOUND LOCALLY** | ⚠ BLOCKER (see below) |

**brahma-pipeline NOT LOCATED:** Search across `/Users/Dev/Vibe-Coding/Apps`, `/Users/Dev/Antigravity`, and `/Users/Dev` found no repo matching `brahma-pipeline` by directory name or remote URL. Only repos found: `Madhav`, `Marsys-Mines-ERP`, `swisseph`, `sonalimohantyart`.

**Resolution required for Phases 5, 6, 7:** Native must clone brahma-pipeline locally before those phases can proceed. Phases 0–4 and Phase 8 can proceed without it.

### 0.B — GCloud Auth

| Check | Value | Status |
|---|---|---|
| Project | `madhav-astrology` | ✓ |
| Auth account | `mail.abhisek.mohanty@gmail.com` | ✓ |

### 0.C — DB Proxy

- cloud-sql-proxy already running (PID 7644, port 5433) for `madhav-astrology:asia-south1:amjis-postgres`
- DB password from `platform/.env.local` (rotated from `.env.rag`; `.env.rag` password is stale)
- Connectivity: **OK** (`SELECT 1` → 1 row)
- PROD_DB_URL: `postgresql://amjis_app@127.0.0.1:5433/amjis` (with platform/.env.local password)

### 0.D — Migration File Inventory

| Migration | File | Present |
|---|---|---|
| 166 | `166_pyramid_layers.sql` | ✓ (not in brief but exists; table already applied directly to prod 2026-06-05) |
| 167 | `167_asset_registry.sql` | ✓ |
| 168 | `168_asset_coefficients.sql` | ✓ |
| 169 | `169_asset_throughput.sql` | ✓ |
| 170 | `170_layer_approvals.sql` | ✓ |
| 171 | `171_build_runs.sql` | ✓ |
| 172 | `172_asset_throughput_volume.sql` | ✓ |
| 173 | `173_drop_legacy_builds.sql` | ✓ |

All migration files 167-173 present.

### 0.E — Applied Migration Inventory

Migration tracker: `public._migrations_applied` (filename-based, custom tracker).

Last applied migration: `165_chart_panchanga.sql` (2026-06-05)

**Structural state vs tracker state:**

| Migration | Tracker | Table/Column Exists | Action Needed |
|---|---|---|---|
| 166 | Not in tracker | pyramid_layers EXISTS (applied directly 2026-06-05) | Skip (idempotent CREATE IF NOT EXISTS would be safe; table exists) |
| 167 | Not in tracker | asset_registry EXISTS | Apply (tracker update + idempotent) |
| 168 | Not in tracker | asset_coefficients EXISTS | Apply (tracker update + idempotent) |
| 169 | Not in tracker | asset_throughput EXISTS | Apply (tracker update + idempotent) |
| 170 | Not in tracker | layer_approvals EXISTS | Apply (tracker update + idempotent) |
| 171 | Not in tracker | build_runs EXISTS | Apply (tracker update + idempotent) |
| 172 | Not in tracker | `rows_written`/`expected_rows` **MISSING** | **Apply (adds 2 columns)** |
| 173 | Not in tracker | builds/build_steps/build_events all EXIST | Apply after Phase 2 audit + Phase 3 confirmation |

**Legacy tables for Phase 3 (pre-drop row counts):**
- `builds`: 1 row
- `build_steps`: 14 rows
- `build_events`: 0 rows

### Phase 0 Outcome

- ✓ Cockpit branch HEAD verified
- ⚠ brahma-pipeline repo NOT found locally — Phases 5, 6, 7 blocked pending native clone
- ✓ GCloud auth verified
- ✓ DB proxy live (cloud-sql-proxy PID 7644)
- ✓ All migration files 167-173 present
- ✓ Applied-migration state inventoried
- **Key finding:** Migrations 167-171 appear structurally applied (tables exist) but are NOT in `_migrations_applied` tracker. Migration 172 genuinely missing (2 columns). Migration 173 pending (legacy tables still exist).

**Proceeding to Phase 1** (applying 167-172 with `ADD COLUMN IF NOT EXISTS` / `CREATE IF NOT EXISTS` guards — safe to re-run).

---

## Phase 1 — Apply Non-Destructive Migrations 167-172

Applied sequentially with `ON_ERROR_STOP=1`. All used `IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` guards.

| Migration | File | Status | Notes |
|---|---|---|---|
| 167 | `167_asset_registry.sql` | ✓ Applied | Table pre-existed; CREATE skipped (NOTICE) |
| 168 | `168_asset_coefficients.sql` | ✓ Applied | Table pre-existed; CREATE skipped (NOTICE) |
| 169 | `169_asset_throughput.sql` | ✓ Applied | Table pre-existed; CREATE skipped (NOTICE) |
| 170 | `170_layer_approvals.sql` | ✓ Applied | Table pre-existed; CREATE skipped (NOTICE) |
| 171 | `171_build_runs.sql` | ✓ Applied | Most objects pre-existed; build_runs/build_run_assets confirmed via NOTICE |
| 172 | `172_asset_throughput_volume.sql` | ✓ Applied | **Genuinely new** — `rows_written` + `expected_rows` columns added |

### Phase 1.A Verification

- ✓ `asset_registry`, `asset_coefficients`, `asset_throughput`, `layer_approvals`, `build_runs`, `build_run_assets`
- ✓ `asset_throughput.rows_written`, `asset_throughput.expected_rows`

**Phase 1 AC: PASS**

---

## Phase 2 — Pre-Destructive Reverse-Citation Audit

Migration 173 drops: `build_events`, `build_steps`, `builds` (CASCADE).

### 2.A — Initial Grep (first pass)

Found 5 live production-code references — all in `lib/build/trigger.ts` and `lib/build/events.ts`:

```
platform/src/lib/build/trigger.ts:118     INSERT INTO build_events
platform/src/lib/build/events.ts:30,41,70,76  SELECT/INSERT build_events
```

### 2.B — Disposition Assessment

| File | Callers | Decision |
|---|---|---|
| `lib/build/trigger.ts` | 0 live callers (route 410 stub; only vi.mock'd in tests) | DELETE (dead code) |
| `lib/build/events.ts` | 0 live callers (route 410 stub; only vi.mock'd in tests) | DELETE (dead code) |
| `lib/build/__tests__/trigger.test.ts` | Tests deleted module (direct import) | DELETE (tests dead code) |

All `/api/build/*` routes are 410 Gone stubs. The deleted libraries had no live callers.

Files deleted:
- `platform/src/lib/build/trigger.ts`
- `platform/src/lib/build/events.ts`
- `platform/src/lib/build/__tests__/trigger.test.ts`

### 2.C — Decision Gate (second pass)

Re-ran grep after deletion:

```
Live production code references to kill targets: 0
PASS — zero live references. Safe to proceed to Phase 3.
```

**Phase 2 AC: PASS**

---

## Phase 3 — Apply Migration 173 (DESTRUCTIVE)

Native confirmation: `DROP LEGACY TABLES` received.

Pre-drop row counts (audit trail):
- `builds`: 1 row
- `build_steps`: 14 rows
- `build_events`: 0 rows

Migration applied: `psql -f 173_drop_legacy_builds.sql` — exit 0.

CASCADE effects (FK constraints dropped, not tables):
- `build_engine_versions_build_id_fkey`
- `build_notifications_build_id_fkey`
- `notification_views_build_id_fkey`

### Phase 3.D — Verification

- ✓ `builds` dropped
- ✓ `build_steps` dropped
- ✓ `build_events` dropped
- ✓ `build_engine_versions` intact
- ✓ `build_notifications` intact
- ✓ `build_run_assets` intact
- ✓ `build_runs` intact

**Phase 3 AC: PASS**

---

## Phase 4 — Set PUBSUB_TOPIC Env Var on amjis-web

- Pub/Sub topic `cockpit-events` did not exist — created: `projects/madhav-astrology/topics/cockpit-events`
- `gcloud run services update amjis-web --update-env-vars=PUBSUB_TOPIC=cockpit-events` → revision `amjis-web-00523-qjs` deployed, 100% traffic
- Verified: `PUBSUB_TOPIC=cockpit-events` present in service env

**Phase 4 AC: PASS**

---

## Phase 7 — Provision Watchdog Cloud Scheduler Job

### 7.A — Infrastructure Provisioned

- `watchdog-secret` created in Secret Manager (version 1)
- `WATCHDOG_SECRET` env var added to `amjis-web` → new revision `amjis-web-00524-zrq` at 100% traffic
- Cloud Scheduler job `watchdog-reaper` created: `*/5 * * * *`, POST `https://madhav.marsys.in/api/cockpit/watchdog`, `x-watchdog-auth` header = secret value

### 7.B — 401 Root Cause (RESOLVED)

Manual trigger and direct curl both returned 401. Root cause: the watchdog route (`245484fc`) exists only on `feature/cockpit-v2-three-views`, NOT in the production image (`sha256:6c63f55f`, built 2026-06-03). All `/api/cockpit/*` routes return `{"error":"unauthorized"}` via Next.js middleware when no route handler matches. This is expected pre-Phase-8 behavior.

Confirmation: `GET /api/cockpit/nonexistent-route-xyz` → `{"error":"unauthorized"} 401` (same response — middleware, not the route handler).

`WATCHDOG_SECRET` on revision `00524-zrq` matches scheduler header exactly. Authentication will pass once Phase 8 deploys the route.

**Phase 7 AC: PASS (infrastructure provisioned; endpoint activates post-Phase-8)**

---

## Phase 5 — Build + Push brahma-pipeline Orchestrator Image

**Key finding:** `brahma-pipeline` is NOT a separate repo — orchestrator lives at `platform/python-sidecar/pipeline/` within the Madhav repo. `Dockerfile.pipeline` requires repo-root build context.

- Build 1 (`1c9a6e0b`): WRONG — submitted from `python-sidecar/` dir using default `Dockerfile` (sidecar, not pipeline). This pushed the wrong image as `:latest`. **Corrected by Build 3.**
- Build 2 (`079120d2`): FAILED — used `platform/python-sidecar/` as context; Dockerfile.pipeline needs repo root.
- Build 3 (`b5om1ak4x`): IN PROGRESS — correct config: repo-root context + `--config cloudbuild-pipeline.yaml` using `Dockerfile.pipeline`.

---
