---
artifact: STATE_D-5
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-5 — Gochara-Chitra
updated_at: 2026-07-19T18:35:00Z
---

```yaml
wave: D-5
lifecycle_step: 6  # REBUILD in progress — all 5 lanes merged+deployed; a two-part live bug discovered, fix cycle 2 in flight
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
  - {lane: G-4, branch: wave/D-5/G-4 (deleted, merged), status: merged_fix_in_progress, receipt_ref: "PR #627 (095a2bc1), ACCEPT-WITH-FINDINGS at Phase-1 (small-scale live test, legitimately passed — not a REJECT). REBUILD-time re-open, attempt 2 of 3 (protocol §2.3): production-scale execution surfaced incident #1 (fixed, PR #631, independently re-verified live), whose own fix immediately surfaced incident #2 (see rebuild_incident_2) — both within this same re-open cycle, not two separate attempts. Fix #2 in progress on wave/D-5/fix-savepoint-rollback. If this does not resolve cleanly, the NEXT re-open would be attempt 3/3 before PARK."}
  - {lane: G-5, branch: wave/D-5/G-5 (deleted, merged), status: merged, receipt_ref: "PR #629 (f1d8e339), ACCEPT-WITH-FINDINGS, 5841 tests green, both live filing directions (accept+reject) independently verified. DR-16 persistence gap carried (see carried_findings). Worktree+branch cleaned up."}
deploy: {done: true, sha: "amjis_web=f1d8e339, amjis_mcp=095a2bc1, amjis_sidecar=095a2bc1, brahma_build_pipeline_job=14b82dae (post incident-#1 fix, live-SHA verified 2026-07-19T17:53Z)"}
rebuild:
  scope: "asset_set: [ka_gochara_resonance, ka_gochara_sweep], per BIND_D-5 §6 minimal-cascade ruling — no full-layer trigger identified"
  abhisek_build_id: "29b8c805... (attempt 1, FAILED, incident #1) → 9d2f0a16... (attempt 2, FAILED, incident #2) → ef3d3004-bd30-4a91-a920-f5607dad9710 (attempt 3, FAILED, incident #3 — clean 30-min writer_timeout_seconds watchdog kill, ZERO transaction-abort errors this run, confirming incident #2's fix genuinely holds) — ka_gochara_resonance completes clean on every attempt; only the sweep substep is affected"
  status: fix_merged_awaiting_deploy_then_attempt_4
rebuild_incident_1:
  what: "Cloud Run job execution brahma-build-pipeline-job-kb4zr (started 2026-07-19T16:29:35Z): ka_gochara_sweep's kakshya_cell_crossing primitive hit 'current transaction is aborted' within ~2s of the substep starting. Root cause (live-diagnosed): _fetch_av_gate_rows's untyped NULL SQL placeholder → IndeterminateDatatype, poisoning the shared connection for every subsequent query in that substep."
  disposition: "FIXED, PR #631 (14b82dae) — placeholder cast + safe_rollback() hardening added at 4 call boundaries in gochara_grammar/primitives.py. Independently re-verified live (exact original trigger reproduced, confirmed fixed) before merge."
rebuild_incident_2:
  what: "Re-dispatched rebuild (build_run 9d2f0a16..., job brahma-build-pipeline-job-lq8w4, 2026-07-19T18:12Z): ka_gochara_resonance completed clean again, but ka_gochara_sweep crashed differently this time — 'InvalidSavepointSpecification: savepoint \"writer_exec\" does not exist' at the orchestrator's own RELEASE SAVEPOINT call, then a secondary InFailedSqlTransaction trying to record the error. Root cause (conductor-diagnosed, pending agent verification): incident #1's own fix is the culprit — _dbutil.safe_rollback() calls a bare conn.rollback() (FULL transaction rollback), which is safe in G-3's standalone no-orchestrator context it was designed for, but destroys ALL savepoints — including the orchestrator's own per-substep SAVEPOINT writer_exec (FROZEN contract, asset_runner.py._drive_substeps) — when reached via gochara_grammar/primitives.py from WITHIN an orchestrator-driven G-4 substep. A violation of the FROZEN contract's 'writer never commits/rollbacks ctx.db_conn' rule, introduced indirectly by importing a helper across an execution-context boundary it wasn't designed for."
  disposition: "Cloud Run execution completed cleanly at the process level (orchestrator handled the worker crash without hanging); build_runs row auto-marked failed correctly this time. asset_throughput reset to state=error with honest last_error. Proper fix (SAVEPOINT-scoped, not a bare rollback, safe in both G-3-standalone and G-4-orchestrator-driven contexts) dispatched to wave/D-5/fix-savepoint-rollback, explicitly briefed NOT to touch FROZEN asset_runner.py — any apparent orchestrator-core robustness gap (mark_asset_error not defensive against an already-aborted transaction) is to be reported for native review, not fixed in-lane."
  counts_as: "Both incidents fall within G-4's REBUILD-time re-open attempt 2/3 (protocol §2.3) — a genuine, non-obvious production-scale interaction (FROZEN-contract-adjacent) that neither the small-scale Phase-1 live test nor incident #1's own live re-verification surfaced, since neither ran inside the orchestrator's actual SAVEPOINT lifecycle."
rebuild_incident_3:
  what: "Re-dispatched rebuild (build_run ef3d3004..., job brahma-build-pipeline-job-5csdp, 2026-07-19T20:17Z): ka_gochara_resonance completed clean; ka_gochara_sweep ran for the full 1800s writer_timeout_seconds budget with ZERO transaction-abort/savepoint errors (confirming incident #2's fix genuinely resolved the connection-poisoning class of bug), but committed ZERO rows before the orchestrator's watchdog killed it: 'TIMEOUT: asset_id=ka_gochara_sweep exceeded writer_timeout_seconds=1800 — marking error'. Root cause: pure chunking-granularity — plan_substeps chunked by DECADE (~3650 days x full primitive/composition/intensity pipeline per day), too coarse to fit one substep in 30 minutes. Not a correctness defect."
  disposition: "FIXED, PR #635 (9b883196) — re-chunked to per-YEAR substeps (100/event_class, 300 total for the 3 populated classes), a straight 10x finer grain; _RESUME_VERSION bumped 1→2 so a stale decade-keyed resumption ledger can never be misread against the new plan. 20/20 sweep tests green incl. live integration test; live-confirmed 300-substep plan for chart 482012f1. Direct single-substep timing was inconclusive (local Cloud SQL proxy connection dropped mid-measurement — a known local-proxy reliability limitation per O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md, not a fix defect); the real Cloud Run job's own dedicated connection is the authoritative environment and is the basis for attempt 4."
  counts_as: "G-4's REBUILD-time re-open attempt 3/3 (protocol §2.3) — final attempt before this specific chunking concern would need a PARK/native-review disposition. Unlike incidents #1/#2, this one carries zero correctness risk (confirmed clean transaction handling); it is purely a throughput/scheduling characteristic of a genuinely heavy, first-of-its-kind 100-year x 3-domain daily-grid computation."
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
