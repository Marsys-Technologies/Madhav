# python-sidecar

Python build pipeline sidecar for MARSYS-JIS. Contains orchestrator writers (`ga_*`, `bo_*`, etc.) and supporting services.

## Build Path

All builds must go through the orchestrator via the cockpit `runs` API.
Direct runner scripts (`run_*_prod.py`) are **RETIRED** as of 2026-06-23.

Use: `POST /api/cockpit/runs` with `{ chart_id, scope, scope_target, action }`.

Example for a single-asset rebuild:
```json
{
  "chart_id": "<uuid>",
  "scope": "asset",
  "scope_target": "bo_laksana",
  "action": "rebuild"
}
```

This dispatches via `invokeRunJob` → `brahma-build-pipeline-job` (Cloud Run Job, region `asia-south1`), building the target asset and all transitive downstream in topo order. Build state is tracked in `build_runs` / `build_run_assets` and visible in the cockpit.
