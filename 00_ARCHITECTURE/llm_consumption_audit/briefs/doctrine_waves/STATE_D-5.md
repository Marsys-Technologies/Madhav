---
artifact: STATE_D-5
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-5 — Gochara-Chitra
updated_at: 2026-07-19T08:31:47Z
---

```yaml
wave: D-5
lifecycle_step: 2  # SPAWN in progress
brief_bound: true
rollback_pin:
  amjis_web: c8801e17bcd28b503cbeeac16533cc713124a251
  amjis_mcp: 8f3ace3756c219a65fe8d3baee96606092a38913
  amjis_sidecar: e995c4981068eabf987ac40197749177cd91a239
  brahma_build_pipeline_job: e995c4981068eabf987ac40197749177cd91a239
  abhisek_build_id: d2470804-8aba-478a-9407-69ef9b559c68
lanes:
  - {lane: G-1, branch: wave/D-5/G-1, status: pending, receipt_ref: null}
  - {lane: G-2, branch: wave/D-5/G-2, status: pending, receipt_ref: null}
  - {lane: G-3, branch: wave/D-5/G-3, status: pending, receipt_ref: null}
  - {lane: G-4, branch: wave/D-5/G-4, status: pending, receipt_ref: null}
  - {lane: G-5, branch: wave/D-5/G-5, status: pending, receipt_ref: null}
deploy: {done: false, sha: null}
rebuild: {scope: pending, abhisek_build_id: pending}
gate: {run: false, green: [], red: []}
first_actions:
  cr_113: closed  # orphan build_runs row reaped via /api/cockpit/watchdog, deployed connector
  cr_114: dispositioned_non_blocking  # relies on standing deploy.yml per-path trigger, see BIND_D-5 §3
updated_at: 2026-07-19T08:31:47Z
```
