---
artifact: STATE_D-5
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-5 — Gochara-Chitra
updated_at: 2026-07-19T09:40:00Z
---

```yaml
wave: D-5
lifecycle_step: 3  # IMPLEMENT ∥ VERIFY, G-1/G-2 merged, G-3 next
brief_bound: true
rollback_pin:
  amjis_web: c8801e17bcd28b503cbeeac16533cc713124a251
  amjis_mcp: 8f3ace3756c219a65fe8d3baee96606092a38913
  amjis_sidecar: e995c4981068eabf987ac40197749177cd91a239
  brahma_build_pipeline_job: e995c4981068eabf987ac40197749177cd91a239
  abhisek_build_id: d2470804-8aba-478a-9407-69ef9b559c68
lanes:
  - {lane: G-1, branch: wave/D-5/G-1 (deleted, merged), status: merged, receipt_ref: "PR #621 (9a2ec77c), ACCEPT-WITH-FINDINGS, live-verified 80 rows/3 classes/0 citation violations. Worktree+branch cleaned up."}
  - {lane: G-2, branch: wave/D-5/G-2 (deleted, merged), status: merged, receipt_ref: "PR #622 (7b6d7f27), ACCEPT-WITH-FINDINGS, 3770 tests green. Sarvatobhadra classical grid population + live 3-specimen re-derivation carried as open findings to G-4/gate. Worktree+branch cleaned up."}
  - {lane: G-3, branch: wave/D-5/G-3, status: pending, receipt_ref: null}
  - {lane: G-4, branch: wave/D-5/G-4, status: pending, receipt_ref: null}
  - {lane: G-5, branch: wave/D-5/G-5, status: pending, receipt_ref: null}
deploy: {done: false, sha: null}
rebuild: {scope: pending, abhisek_build_id: pending}
gate: {run: false, green: [], red: []}
first_actions:
  cr_113: closed  # orphan build_runs row reaped via /api/cockpit/watchdog, deployed connector
  cr_114: dispositioned_non_blocking  # relies on standing deploy.yml per-path trigger, see BIND_D-5 §3
carried_findings:
  - "G-2: Sarvatobhadra (CR-21) vedha-pair grid is an honestly-flagged algorithmic approximation (uncited_extension=true) — no classical grid data exists live anywhere in the DB (archived migrations 140/144 have zero rows, tables never applied). Real classical grid population is open future work, not a G-5 blocker."
  - "G-1/G-2: live re-derivation of the 3 named specimens (Sarvatobhadra ~2025-05, windfall 2010-07→2011-03, marriage double-transit 2013-12-11) and the mini-retrodiction check vs A-5 baseline deferred to G-3/gate time per BRIEF_D5 §2 (explicitly authorized deferral, not a silent skip)."
updated_at: 2026-07-19T09:40:00Z
```
