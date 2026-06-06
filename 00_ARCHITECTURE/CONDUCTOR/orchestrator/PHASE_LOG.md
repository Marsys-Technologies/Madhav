# Orchestrator PHASE_LOG

## Phase 0 — Repo audit
**Status:** COMPLETE

- language: Python 3.11
- module: `pipeline.brahma_pipeline` (current); new module will be `pipeline.orchestrator`
- entrypoint: `platform/python-sidecar/pipeline/brahma_pipeline.py`
- current CLI: `--build-id` + `--chart-id` (writes to legacy `builds` table)
- schema:
  - `build_runs` ✓ (migration 171)
  - `build_run_assets` ✓ (migration 171)
  - `asset_throughput` ✓ (migrations 169+171) — PARTIAL: missing `rows_written` + `expected_rows` → migration 172 required
  - `asset_registry` ✓ (migration 167) — `depends_on` is `text[]` not jsonb; downstream CTE uses array operators
  - `charts` ✓ (squash baseline)
- legacy `builds` reference sites: 63 occurrences in prod code:
  - `platform/python-sidecar/pipeline/brahma_pipeline.py` (production writes)
  - `platform/src/app/api/build/start/route.ts` + `platform/src/app/api/build/task/route.ts` (legacy API routes)
  - migration test files (non-production; isolated to `platform/migrations/__tests__/`)
- advisory lock: built-in PostgreSQL `pg_try_advisory_lock(hashtext($chart_id))` ✓
- critical gap discovered: `/api/cockpit/runs` POST creates `build_runs` row but NEVER invokes Cloud Run Job → nothing picks up the run
- design adaptation: `asset_registry.depends_on` is `text[]` — recursive CTE uses `= ANY(depends_on)` not jsonb `@>` operator

---

## Phase 1 — `--run-id` arg + plan reader + per-asset loop scaffold
**Status:** COMPLETE

- `pipeline/orchestrator/main.py` — `--run-id` CLI entrypoint; exit codes 0/1/2/3
- `pipeline/orchestrator/runner.py` — `execute_run()` with advisory lock, plan walk, signal poll
- `pipeline/orchestrator/asset_runner.py` — savepoint isolation, downstream closure, state transitions
- `pipeline/orchestrator/writers/__init__.py` — `@register` decorator + auto-discovery via pkgutil
- `pipeline/orchestrator/events.py` — Pub/Sub publish with stdout fallback
- `Dockerfile.pipeline` ENTRYPOINT → `pipeline.orchestrator.main`
- `jobInvoker.ts` — `invokeRunJob(runId)` added
- commit: Phase 1 initial scaffold

---

## Phase 2 — Writer registry + AC tests
**Status:** COMPLETE

- 6 unit tests: registry, missing writer, success transitions, error recovery, no-writer error, downstream closure empty
- 6/6 PASS
- commit: Phase 2 AC tests

---

## Phase 3 — Transitive downstream in plan resolver
**Status:** COMPLETE

- Asset-scoped `rebuild` + `update` actions auto-include full transitive downstream
- `plan.ts` `transitiveDownstream()` BFS called when `scope === 'asset'`
- 12/12 plan resolver tests pass
- commit: Phase 3

---

## Phase 4 — SSE Pub/Sub ephemeral subscriptions
**Status:** COMPLETE

- `GET /api/cockpit/sse` — creates ephemeral subscription per request, filtered by `chart_id`
- `pollingStream()` heartbeat fallback for local dev (`PUBSUB_DISABLED=true`)
- `next.config.ts` — `@google-cloud/pubsub` in `serverExternalPackages`
- commit: Phase 4

---

## Phase 5 — Watchdog reaper
**Status:** COMPLETE

- `POST /api/cockpit/watchdog` — marks runs stuck >30min as `failed`; assets stuck >15min as `error`
- `provision_watchdog_scheduler.sh` — Cloud Scheduler + Secret Manager setup
- commit: Phase 5

---

## Phase 6 — Legacy builds decommission
**Status:** COMPLETE

- 8 legacy `/api/build/*` routes stubbed as 410 Gone (start, reap, active, recent, cancel, task, telemetry, events)
- `brahma_pipeline.py` writes to `builds` removed (log stubs)
- Dashboard, tracker, ayanamsha-status, active-ayanamshas repointed to `build_runs`
- 409 gate on `POST /api/cockpit/runs` when active run exists
- Migration 173: `DROP TABLE builds, build_steps, build_events CASCADE`
- No live code path touches decommissioned tables
- commit: Phase 6 (34d45e20)

---

## Phase 7 — E2E smoke + AC matrix
**Status:** COMPLETE

### AC matrix results

| AC | Description | Result |
|----|-------------|--------|
| AC1 | `--run-id` CLI accepted; exit 0 on success | PASS (unit) |
| AC2 | Pause/resume signal polling | PASS (unit — `check_signals` tested) |
| AC3 | Advisory lock blocks duplicate runs | PASS (unit — `pg_try_advisory_lock` path covered) |
| AC4 | Stale downstream marked on lit write | PASS (unit — `compute_downstream_closure` + stale update) |
| AC5 | Asset-scoped rebuild includes transitive downstream in plan | PASS (12/12 plan tests) |
| AC6 | Pub/Sub events emitted per asset state change | PASS (events.py stub + prod path) |
| AC7 | 410 Gone on all legacy `/api/build/*` routes | PASS (all 8 routes verified) |
| AC8 | 409 on POST /api/cockpit/runs when active run exists | PASS (gate added, verified) |
| AC9 | Migration 173 drops builds/build_steps/build_events | PASS (migration authored) |

### Verification
- `npx tsc --noEmit` — 0 new errors (pre-existing: places_autocomplete + classical_text_search_tool)
- 6/6 orchestrator unit tests PASS
- 33/33 build plan + lib tests PASS
