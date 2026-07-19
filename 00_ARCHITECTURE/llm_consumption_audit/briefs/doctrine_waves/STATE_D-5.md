---
artifact: STATE_D-5
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-5 — Gochara-Chitra
updated_at: 2026-07-19T15:35:00Z
---

```yaml
wave: D-5
lifecycle_step: 3  # IMPLEMENT ∥ VERIFY, G-1/G-2/G-3/G-4 merged, G-5 next (final lane)
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
  - {lane: G-4, branch: wave/D-5/G-4 (deleted, merged), status: merged, receipt_ref: "PR #627 (095a2bc1), ACCEPT-WITH-FINDINGS, 3852 tests green. Shape-aware output (point/interval/chain) live-verified against real ontology data; peak_basis/DR-10 honesty independently confirmed (DIS.023 genuinely doesn't name a gochara-engine peak model); density_contract populated on all 3 new views. Worktree+branch cleaned up."}
  - {lane: G-5, branch: wave/D-5/G-5, status: pending, receipt_ref: null}
deploy: {done: false, sha: null}
rebuild: {scope: pending, abhisek_build_id: pending}
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
