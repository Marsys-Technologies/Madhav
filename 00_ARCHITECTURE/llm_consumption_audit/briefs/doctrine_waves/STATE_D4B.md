---
artifact: STATE_D4B
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-4b — Calibration Ignition + Grand Bakeoff
updated_at: 2026-07-22T00:00:00Z
---

```yaml
wave: D-4b
lifecycle_step: 6  # B-lanes IN PROGRESS. B-4/B-5 merged; B-1 BLOCKED-ON-DEFECT (PR #694 open);
                    # B-2/B-3 correctly SKIPPED (hard-gated on B-1); B-6 (this pass) ran GATED —
                    # performed governance duties, did NOT close the wave. current_wave stays
                    # D-4b (OPEN) on CLAUDECODE_BRIEF.md — NOT set to CAMPAIGN-CLOSED.
brief_bound: true
mode_this_pass: GATED  # orchestrator-specified; explicitly not mode=FULL. The mode=FULL
  # three-point baseline diff (BRIEF_D4B §1 B-6 item 4) was NOT run this pass.
lanes:
  - {lane: B-1, branch: wave/D-4b/B1-bakeoff, status: merged, pr: 687, result: "BLOCKED — 0 contenders scored, 1/5 requested contenders even had a callable curve(). DR-19-clean, refused a fabricated cost-projection instruction. No scoring attempted."}
  - {lane: B-1 (narrowed), branch: wave/D-4b/B1-bakeoff-narrowed, status: open_not_merged, pr: 694, result: "Real, live 14-contender x 31-TRAIN-event run (434 calls, 0 errors) against live infra. BLOCKED-ON-DEFECT, not champion/no-winner: (a) gochara_resonance_map event_class mapping gap degrades all 12 PERMISSION contenders; (b) curve_controls.ts circularShiftCurve() wraparound bug corrupts CRPS for every contender's control side. Both named with repro + fix direction. Hit-rate (legacy secondary) reported as trustworthy-where-not-degenerate; CRPS/skill (primary) not trustworthy this run."}
  - {lane: B-2, branch: none, status: skipped, reason: "hard-gated on B-1's adjudication receipt per BRIEF_D4B §1 — never dispatched, no worktree/branch created"}
  - {lane: B-3, branch: none, status: skipped, reason: "hard-gated on B-1's adjudication receipt per BRIEF_D4B §1 — never dispatched, no worktree/branch created"}
  - {lane: B-4, branch: wave/D-4b/B4-remedy-join, status: merged, pr: 689, result: "bo_upaya populated via bodha_rm_dasha_windowed_prescriptions (leverage_index x sadhana history x dasha runway); leverage_index subject=venus false-empty CONFIRMED CLOSED live; NEW finding surfaced (not fixed, out of scope): ga_vichara_writer.py leverage_index embeds a wrong dasha-runway sub-field (years_to_start=0 vs actual chart_dashas ~8.08y) — B-4's own join re-derives fresh rather than propagate it. 26 new tests."}
  - {lane: B-5, branch: wave/D-4b/B5-retrodiction, status: merged, pr: 688, result: "mechanism_retrodiction_get live (registry capability + MCP tool), CONFIRMATION-ONLY, calibration_context_only:true / lel_capable:true (kept out of prashna_ask/planner surfaces). Scoped and merged independently ahead of B-1/B-2/B-3's own merge-order resolution, per its own recorded reasoning."}
  - {lane: permission-bridge (pre-step, not a §1 lane), branch: wave/D-4b/permission-bridge, status: merged, pr: 693, result: "PERMISSION curve HTTP route (/api/compute/permission_curve) + 13-contender TS bridge + bind-time assertion (assertRosterBindable). This is what unblocked B-1-narrowed's bind-time assertion — confirmed GREEN for the full 14-contender roster against live production infra after this merge's own CI/CD deploy completed."}
  - {lane: ledger-hygiene, branch: wave/D-4b/ledger-hygiene, status: merged, pr: 690, result: "Carried NP-D4B-004 (control sample design) into repo state from an uncommitted main-branch edit; recorded NP-D4B-005 (native ruling, B-5 aggregate COUNT(*) near sealed-split boundary — NO BREACH, one-time carve-out) + a process finding (orchestration scripts must pass verifier verdicts through verbatim, never re-narrate into a broader claim)."}
  - {lane: a5-reconciliation, branch: wave/D-4b/a5-reconciliation, status: open_not_merged, pr: 692, result: "Investigation-only. Verdict (b) GATE-RECORD-INTEGRITY-FINDING (narrowly scoped): D-4a REPORT §3 gate table row 5 was a bare PASS against a literal '3 models scored' criterion actually met by only 1/3; (a) PLUMBING-DRIFT definitively ruled out (both model_interface.ts and curve.ts have exactly one commit in their entire history, already stubbed at creation). Correction drafted, NOT applied by this lane (investigation-only charge) — LANDED separately by wave/D-4b/B6-close (this wave, see below)."}
  - {lane: B-6 (this pass), branch: wave/D-4b/B6-close, status: in_progress_gated, result: "Landed the A-5 correction (REPORT_D-4A.md §10 + STATE_D-4A.md pointer, citing PR #692's investigation verbatim). Ran parked-items review, DR ratification sweep (compiled, not self-ratified), register final sweep. Live-checked ka_gochara_sweep materialization: 165/300 substeps (55%), asset_throughput.state=error, last_error=upstream 21600s writer-timeout hit before completion. Did NOT run the mode=FULL three-point baseline diff. Did NOT mark current_wave CAMPAIGN-CLOSED. Full record: REPORT_D4B.md."}
adjudications:
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook (forward-binding from D-3)", status: "RATIFIED (native, 2026-07-17) but NOT YET DISCHARGED — B-1 has not produced a scored midpoint-triangle vs pratyantar-lord vs transit-kernel comparison to adjudicate (midpoint-triangle/transit-kernel remain NotImplementedModelError stubs; only pratyantar_lord is servable)."}
dr_ratification_sweep_this_pass:
  # Compiled for native review, per BRIEF_D4B §1 B-6. None self-ratified by this pass.
  still_queued_for_native_ratification: [DR-6 (DIS.019), DR-7 (DIS.020), DR-8 (DIS.021)]
  already_native_ratified: [DR-9 (DIS.022), DR-10 (DIS.023), DR-11 (DIS.024), DR-12 (DIS.025, ratified-but-undischarged), DR-13 (DIS.026), DR-14 (DIS.027), DR-15 (DIS.028), DR-16 (DIS.029), DR-19 (DIS.030)]
  ratified_in_substance_no_formal_dis_row_yet: [DR-17, DR-18]
  np_d4b_ledger_provisional_pending_native_batch_ratification: [NP-D4B-001, NP-D4B-002, NP-D4B-003, NP-D4B-004]
  np_d4b_ledger_direct_native_ruling_already_final: [NP-D4B-005]
live_materialization_check_this_pass:
  asset: ka_gochara_sweep
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa
  substeps_committed: 165
  substeps_planned: 300  # 3 populated event_classes (career_advancement, major_gain, marriage) x 100 years
  pct: "55%"
  asset_throughput_state: error
  last_error: "BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run; skipped to avoid building on incomplete data"
  most_recent_full_dispatch: {build_run: c9d722d5-2a06-4f4a-a4a2-18009894fe11, started_at: "2026-07-21T16:25:23.529Z", ended_at: "2026-07-21T22:25:28.551Z", duration: "6h00m05s — exactly the 21600s writer_timeout_seconds budget", state: failed}
  new_finding_this_pass: "build_runs row 0a3f15e2-d9e3-43c0-9bca-5a0a0d075ba1 still reads state=running with no ended_at, started 2026-07-21T07:57:49Z (>20h before this check) and predates c9d722d5's own later completion+failure — plausibly a stale orphan-watchdog-uncaught row, same pattern as CR-113. NOT reconciled by this session (no destructive DB write performed); named for a future watchdog pass."
  consequence: "Gates ONLY B-6's own serving assertions per BRIEF_D4B §0 RECONCILIATION, not B-1's event-driven scoring. No B-6 claim in REPORT_D4B.md asserts full materialization."
carried_item_dispositions:
  - {item: "D-2 carried finding #1 (leverage_index subject=venus false-empty)", status: "CLOSED — re-verified live by B-4 (PR #689): 5 rows returned, subject_alias_resolved confirms VEN code resolution working."}
  - {item: "D-2 carried finding #4 (judgment_query v3 oversize baseline)", status: "STILL OPEN — carried through D-3 (untouched) and D-4a (owner: D-4b) to this pass; no D-4b lane touched judgment_query's response-budget path. Flagged again, not silently dropped."}
  - {item: "D-4a A-5 metric disagreement (pratyantar_lord: CRPS/skill red vs hit-rate green)", status: "NOT resolved — this is exactly DR-12's adjudication scope, which requires B-1's own certified scoring run (see adjudications above). Still open."}
  - {item: "CR-113 (orphaned build_runs row 372b5cfa…)", status: "confirmed still CLOSED (unrelated to the NEW stale row this pass found, see live_materialization_check_this_pass above)"}
  - {item: "CR-114 (mcp/sidecar images stale)", status: "re-confirmed POSITIVELY working this pass — permission-bridge's own merge (PR #693) exercised the standing deploy.yml per-path workflow_run trigger successfully, live, this campaign."}
  - {item: "Gate Ś #8 (D-1.6 narrow yoga-signal-class timing residual)", status: "re-verified still non-blocking, no new evidence either way"}
  - {item: "Marriage-specimen residual (D-5 gate_run_3 / DR-17 type-specimen pair)", status: "NOT formally closed by B-3 (B-3 never ran). B-1-narrowed's own §5a direct re-test independently corroborates guru_shani_double_transit firing correctly around 2013-12-11 once event_class is correctly mapped — corroborating evidence only, not B-3's own formal residual-pair mining against the fully-materialized sweep (which is at 55%, not 100%, per live_materialization_check_this_pass)."}
  - {item: "NEW — ga_vichara_writer.py leverage_index dasha-runway sub-field wrong (years_to_start=0 vs true ~8.08y)", status: "OPEN, new this pass (surfaced by B-4). Owner: a future ga_vichara_writer.py lane. Not fabricated-around — B-4's own join re-derives the value fresh from chart_dashas instead."}
close_gate_status:
  # BRIEF_D4B §5's 10 criteria, honest status this pass — this is NOT a gate run, it is B-6's own
  # honest accounting of where each criterion stands. No criterion is claimed PASS if the evidence
  # does not support it.
  - {n: 1, criterion: "materialization-completeness (as reconciled: gates only B-6 serving, not B-1 scoring)", status: "PARTIAL — 165/300 (55%), see live_materialization_check_this_pass"}
  - {n: 2, criterion: "bakeoff complete and honest", status: "NOT MET — BLOCKED-ON-DEFECT, two named defects, no champion/no-winner certified. Honestly reported, not forced green."}
  - {n: 3, criterion: "mimamsa_calibration_get n_observations~40/chart, multipliers evaluating", status: "NOT MET — depends on B-2's backfill, which is SKIPPED (hard-gated on B-1)"}
  - {n: 4, criterion: "discrimination (gain/loss different evidence+grades)", status: "not re-verified this pass — no B-lane touched this surface"}
  - {n: 5, criterion: "negative controls implemented, control delta reported honestly", status: "PARTIAL — implemented and exercised (N=1000 per NP-D4B-004) but the CRPS-side control computation itself has defect §5b (circularShiftCurve), so control deltas from this run are NOT trustworthy for the primary metric"}
  - {n: 6, criterion: "at least one served verdict moved by a calibrated multiplier", status: "NOT MET — no calibration has run (B-2/B-3 skipped)"}
  - {n: 7, criterion: "remedy: bo_upaya wealth resonances != 0, leverage-ranked, subject alias identical", status: "MET — B-4 (PR #689), live-verified"}
  - {n: 8, criterion: "prospective ledger live, >=5 falsifier-bearing predictions", status: "MET at D-4a (A-4, 5 entries incl. 3 named baseline-arc predictions) — not re-verified fresh this pass, no D-4b lane touched the ledger surface"}
  - {n: 9, criterion: "DR-17/18 harness live, grading applied, KUC census committed", status: "NOT MET — DR-17 grading confirmed unbuilt anywhere in the codebase (grep, zero hits, per B1_NARROWED_STATUS_v1_0.md §8)"}
  - {n: 10, criterion: "anti-gaming pass on 1-9 + all prior batteries green, every carried finding dispositioned", status: "PARTIAL — this pass's own parked-items review (REPORT_D4B.md §2) dispositions every carried item honestly; no formal anti-gaming pass run against criteria 1-9 since most are NOT MET or PARTIAL, not green surfaces to gate-check yet"}
next_wave: null  # D-4b stays OPEN. No next wave opens until B-1's two defects are fixed and
  # re-run, B-2/B-3 dispatch against a real adjudication receipt, and a future B-6 pass runs the
  # mode=FULL three-point baseline diff this pass explicitly did not.
```

# STATE_D4B — D-4b Wave State (partial, GATED — this pass does not close the wave)

See `REPORT_D4B.md` for the full narrative. This file is the machine-readable state ledger per
protocol §6.1; `CLAUDECODE_BRIEF.md`'s `current_wave` field is the authoritative "you are here"
pointer and is NOT set to `CAMPAIGN-CLOSED` by this pass.
