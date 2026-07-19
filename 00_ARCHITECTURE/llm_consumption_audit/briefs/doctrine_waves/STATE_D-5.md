---
artifact: STATE_D-5
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-5 — Gochara-Chitra
updated_at: 2026-07-19T16:50:00Z
---

```yaml
wave: D-5
lifecycle_step: 6  # REBUILD in progress — all 5 lanes merged+deployed; rebuild blocked on a live-discovered bug, fix cycle in flight (G-4 attempt 2/3)
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
  - {lane: G-3, branch: wave/D-5/G-3 (deleted, merged), status: merged, receipt_ref: "PR #625 (1bdec728), ACCEPT-WITH-FINDINGS, 3853 tests green incl. live PERMISSION multi-system independent re-derivation. Both cross-lane findings fixed same-cycle (PR #624 G-2 dasha_data; own enrichment.py fix in #625). Worktree+branch cleaned up."}
  - {lane: G-4, branch: wave/D-5/G-4 (deleted, merged), status: merged_fix_in_progress, receipt_ref: "PR #627 (095a2bc1), ACCEPT-WITH-FINDINGS at Phase-1 (small-scale live test). REBUILD-time discovery (attempt 2/3, protocol §2.3): a real production-scale run against chart 482012f1 hit a transaction-abort cascade — see rebuild_incident below. Fix in progress on wave/D-5/fix-sweep-transaction-abort."}
  - {lane: G-5, branch: wave/D-5/G-5 (deleted, merged), status: merged, receipt_ref: "PR #629 (f1d8e339), ACCEPT-WITH-FINDINGS, 5841 tests green, both live filing directions (accept+reject) independently verified. DR-16 persistence gap carried (see carried_findings). Worktree+branch cleaned up."}
deploy: {done: true, sha: "amjis_web=f1d8e339, amjis_mcp=095a2bc1, amjis_sidecar=095a2bc1, brahma_build_pipeline_job=095a2bc1 (all live-SHA verified 2026-07-19T16:20Z)"}
rebuild:
  scope: "asset_set: [ka_gochara_resonance, ka_gochara_sweep], per BIND_D-5 §6 minimal-cascade ruling — no full-layer trigger identified"
  abhisek_build_id: "29b8c805-6d8e-4b7b-b921-0aa1510f16b5 (FAILED — see rebuild_incident; ka_gochara_resonance itself completed clean within this run before the sweep substep hit the bug)"
  status: blocked_on_fix
rebuild_incident:
  what: "Cloud Run job execution brahma-build-pipeline-job-kb4zr (started 2026-07-19T16:29:35Z) ran ka_gochara_resonance to completion cleanly, then ka_gochara_sweep's kakshya_cell_crossing primitive hit 'current transaction is aborted, commands ignored until end of transaction block' within ~2s of the substep starting — a query earlier in the shared connection genuinely failed and nothing rolled back, poisoning every subsequent DB-dependent primitive call for the rest of the substep (silent near-empty output, not a crash — last_built_at never advanced in 15+ min)."
  disposition: "Conductor cancelled the stuck execution (gcloud run jobs executions cancel), reconciled build_runs row 29b8c805... to state=failed with an honest last_error, reset ka_gochara_sweep's asset_throughput to dormant. Root-cause diagnosis + fix dispatched to wave/D-5/fix-sweep-transaction-abort (mirrors G-3's own gochara_intensity/_dbutil.safe_rollback pattern, which ka_gochara_sweep never adopted). Re-dispatch of the real rebuild will follow once fixed+verified+merged."
  counts_as: "G-4 verification attempt 2 of 3 (protocol §2.3) — a genuine production-scale defect the small-scale Phase-1 live test did not surface."
gate: {run: false, green: [], red: []}
first_actions:
  cr_113: closed  # orphan build_runs row reaped via /api/cockpit/watchdog, deployed connector
  cr_114: dispositioned_non_blocking  # relies on standing deploy.yml per-path trigger, see BIND_D-5 §3
carried_findings:
  - "G-2: Sarvatobhadra (CR-21) vedha-pair grid is an honestly-flagged algorithmic approximation (uncited_extension=true) — no classical grid data exists live anywhere in the DB (archived migrations 140/144 have zero rows, tables never applied). Real classical grid population is open future work, not a G-5 blocker."
  - "G-1/G-2/G-3/G-4: live re-derivation of the 3 named specimens (Sarvatobhadra ~2025-05, windfall 2010-07→2011-03, marriage double-transit 2013-12-11) and the mini-retrodiction check vs A-5 baseline — G-4 has already live-verified shape-correct rows AT the windfall interval and marriage-date specimens for chart 482012f1; full gate-time re-derivation (fresh, at verification time) still owed per BRIEF_D5 §2."
  - "Pre-existing, out of D-5 scope: ka_avadhi.py's older _DASHA_SYSTEMS tuple (7 entries) is also stale vs live chart_dashas.system_id, same root cause class as the G-2 fix (PR #624) but a different, pre-existing file — flagged for a future hygiene pass, not fixed in D-5."
  - "G-4: muhurta_finder re-pointing (BRIEF_D5's stated intent) explicitly deferred as a separate, riskier change to an already-live tool — open item for a future lane, not silently dropped."
  - "G-4: birth-year anchor for chart 482012f1 resolves to 1950 (not literal 1984) due to a pre-existing 840-row multi-cycle chart_dashas substrate — inherited from the already-sealed ka_sangam.py pattern, not a G-4-introduced regression, footnoted for the close report."
resolved_findings:
  - "G-2's dasha_data.DASHA_SYSTEMS staleness: FIXED, PR #624 (0b60739c)."
  - "G-3's enrichment.py graha fact_subject mismatch: FIXED in G-3's own PR #625."
updated_at: 2026-07-19T15:35:00Z
```
