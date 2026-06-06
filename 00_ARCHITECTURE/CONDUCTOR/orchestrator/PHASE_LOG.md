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
**Status:** IN PROGRESS
