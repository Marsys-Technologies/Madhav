---
artifact: STATE_D4B
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-4b — Calibration Ignition + Grand Bakeoff
updated_at: 2026-07-22T13:23:00Z
supersedes: STATE_D4B.md as merged by PR #695 (2026-07-21T23:34:17Z, `wave/D-4b/B6-close`) — that
  version is preserved in git history, not deleted; this file replaces it as the current record.
---

```yaml
wave: D-4b
lifecycle_step: 6  # B-lanes IN PROGRESS. B-4/B-5 merged; B-1's two named defects are now BOTH
                    # FIXED on main (F-1 PR #699 merged 2026-07-22T11:07:19Z, F-2 PR #697 merged
                    # 2026-07-22T07:03:12Z) but NO B-1 re-run has been merged, opened, or completed
                    # — b1.merged=false, independently reproduced (gh pr list, empty). B-2/B-3
                    # correctly SKIPPED (hard-gated on B-1). B-6 (this REAL close pass) ran GATED —
                    # verified state independently, did NOT close the wave. current_wave stays
                    # D-4b (OPEN) on CLAUDECODE_BRIEF.md — NOT set to CAMPAIGN-CLOSED.
brief_bound: true
mode_this_pass: GATED  # orchestrator-specified; explicitly not mode=FULL. The mode=FULL
  # three-point baseline diff (BRIEF_D4B §1 B-6 item 4) was NOT run this pass, same as the prior
  # PR #695 pass.
lanes:
  - {lane: B-1, branch: wave/D-4b/B1-bakeoff, status: merged, pr: 687, result: "BLOCKED — 0 contenders scored, 1/5 requested contenders even had a callable curve(). DR-19-clean, refused a fabricated cost-projection instruction. No scoring attempted. Unchanged since prior pass."}
  - {lane: B-1 (narrowed), branch: wave/D-4b/B1-bakeoff-narrowed, status: merged, pr: 694, result: "Real, live 14-contender x 31-TRAIN-event run (434 calls, 0 errors) against live infra, predating both fixes below. BLOCKED-ON-DEFECT, not champion/no-winner. Superseded-pending-re-run, not deleted. Unchanged since prior pass."}
  - {lane: F-1 (fix, not a §1 lane), branch: wave/D-4b/F1-resonance-map, status: merged, pr: 699, merged_at: "2026-07-22T11:07:19Z", result: "gochara_resonance_map event_class mapping gap fixed. Merged under a documented deviation (NP-D4B-006, PR #701): fresh-context Opus verifier stalled (agent-infra instability), conductor-as-verifier authorized as last resort, every probe live. Retroactive verifier reported (to this pass, by the orchestrating session, not re-run independently here) as VERDICT ACCEPT — mitigation obligation treated as DISCHARGED on that attributed basis. NEW SINCE PR #695 PASS."}
  - {lane: F-2 (fix, not a §1 lane), branch: wave/D-4b/F2-curve-controls, status: merged, pr: 697, merged_at: "2026-07-22T07:03:12Z", result: "curve_controls.ts circularShiftCurve() wraparound re-sort fixed — kills the impossible-negative-CRPS class. Unchanged since prior pass (already merged then)."}
  - {lane: "B-1 full re-run", branch: wave/D-4b/B1-full-rerun, status: not_started_no_pr, result: "NO PR EXISTS (gh pr list --head wave/D-4b/B1-full-rerun --state all returns empty, verified this pass). Local worktree .claude/worktrees/wave-D-4b-B1-full-rerun (base 25e0dc4a) carries only UNCOMMITTED WIP: a new dr17_grading.ts implementation + test file, and an unrelated pnpm-lock.yaml diff. No scoring run, no results artifact, no preregistration-packet bump. THIS IS THE WAVE'S EXACT BLOCKER THIS PASS."}
  - {lane: B-2, branch: none, status: skipped, reason: "hard-gated on B-1's adjudication receipt per BRIEF_D4B §1 — never dispatched, no worktree/branch created. Reconfirmed via gh pr list this pass."}
  - {lane: B-3, branch: none, status: skipped, reason: "hard-gated on B-1's adjudication receipt per BRIEF_D4B §1 — never dispatched, no worktree/branch created. Reconfirmed via gh pr list this pass."}
  - {lane: B-4, branch: wave/D-4b/B4-remedy-join, status: merged, pr: 689, result: "bo_upaya populated via bodha_rm_dasha_windowed_prescriptions (leverage_index x sadhana history x dasha runway); leverage_index subject=venus false-empty CONFIRMED CLOSED live (prior pass). Unchanged this pass — not re-touched, not re-verified live."}
  - {lane: B-5, branch: wave/D-4b/B5-retrodiction, status: merged, pr: 688, result: "mechanism_retrodiction_get live, CONFIRMATION-ONLY. Unchanged this pass."}
  - {lane: permission-bridge (pre-step, not a §1 lane), branch: wave/D-4b/permission-bridge, status: merged, pr: 693, result: "PERMISSION curve HTTP route + 13-contender TS bridge + bind-time assertion. Also landed CR-120/CR-121 (midpoint-triangle/transit-kernel NOT-EVALUABLE dispositions, MARSYS_DEFECT_GAP_REGISTER_v2_0.md v3.10). Unchanged this pass, cited here for the CR-120/121 cross-reference."}
  - {lane: ledger-hygiene, branch: wave/D-4b/ledger-hygiene, status: merged, pr: 690, result: "NP-D4B-004/005. Unchanged this pass."}
  - {lane: a5-reconciliation, branch: wave/D-4b/a5-reconciliation, status: open_not_merged, pr: 692, result: "Investigation-only, correction LANDED separately by PR #695 (B6-close). Unchanged this pass."}
  - {lane: ledger-f1-deviation, branch: wave/D-4b/ledger-f1-deviation, status: merged, pr: 701, merged_at: "2026-07-22T11:30:29Z", result: "NP-D4B-006 — records the conductor-verified-under-infrastructure-duress deviation for F-1 (PR #699), with the binding retroactive-verifier mitigation. NEW SINCE PR #695 PASS."}
  - {lane: "B-6 (PR #695 pass)", branch: wave/D-4b/B6-close, status: merged, pr: 695, merged_at: "2026-07-21T23:34:17Z", result: "First GATED close pass — honest partial status, named B-1's two defects as blocker. SUPERSEDED by this REAL close pass's REPORT_D4B.md/STATE_D4B.md, preserved in git history, not deleted."}
  - {lane: "B-6 (this REAL close pass)", branch: wave/D-4b/B6-real-close, status: in_progress_gated, result: "Independently re-verified every material claim handed to this pass (gh pr list for F-1/F-2/B-1-rerun status; live SQL for mimamsa_multipliers and ka_gochara_sweep materialization) rather than trusting the dispatching session's word. Found: both B-1 defects now fixed on main, but NO B-1 re-run exists in any form beyond an uncommitted WIP scaffold. Did NOT run the mode=FULL three-point baseline diff. Did NOT mark current_wave CAMPAIGN-CLOSED. Full record: REPORT_D4B.md (this pass's version)."}
adjudications:
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook (forward-binding from D-3)", status: "RATIFIED (native, 2026-07-17) but NOT YET DISCHARGED — reconfirmed unchanged this pass. B-1 has not produced a scored comparison to adjudicate."}
dr_ratification_sweep_this_pass:
  # Spot-checked, not a full re-sweep — the PR #695 pass performed the full sweep.
  still_queued_for_native_ratification: [DR-6 (DIS.019), DR-7 (DIS.020), DR-8 (DIS.021)]  # unchanged
  already_native_ratified: [DR-9 (DIS.022), DR-10 (DIS.023), DR-11 (DIS.024), DR-12 (DIS.025, ratified-but-undischarged), DR-13 (DIS.026), DR-14 (DIS.027), DR-15 (DIS.028), DR-16 (DIS.029), DR-19 (DIS.030)]  # unchanged
  ratified_in_substance_no_formal_dis_row_yet: [DR-17, DR-18]  # unchanged
  np_d4b_ledger_provisional_pending_native_batch_ratification: [NP-D4B-001, NP-D4B-002, NP-D4B-003, NP-D4B-004]  # unchanged
  np_d4b_ledger_direct_native_ruling_already_final: [NP-D4B-005]  # unchanged
  np_d4b_ledger_new_this_pass: [NP-D4B-006]  # F-1 conductor-verification deviation record; its
    # retroactive-verifier mitigation reported to this pass as DISCHARGED (attributed, see
    # REPORT_D4B.md §0) — not itself a native-ratification event; still queued for native batch
    # ratification along with 001-004.
live_materialization_check_this_pass:
  asset: ka_gochara_sweep
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa
  substeps_committed: 165  # byte-identical to the PR #695 pass; live-requeried, not assumed
  substeps_planned: 300
  pct: "55%"
  asset_throughput_state: error
  last_error: "BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run; skipped to avoid building on incomplete data"
  last_built_at: "2026-07-21T22:25:23.308Z"  # unchanged — no new dispatch since the prior pass
  consequence: "Gates ONLY B-6's own serving assertions per BRIEF_D4B §0 RECONCILIATION, not B-1's event-driven scoring. No B-6 claim in this pass's REPORT_D4B.md asserts full materialization."
live_calibration_check_this_pass:
  table: mimamsa_multipliers
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa
  total_rows: 9
  rows_with_n_observations_gt_0: 0
  max_n_observations: 0
  consequence: "Structural mode confirmed unchanged — consistent with B-2/B-3 both correctly SKIPPED."
carried_item_dispositions:
  - {item: "D-2 carried finding #1 (leverage_index subject=venus false-empty)", status: "CLOSED — unchanged since prior pass, not re-verified live this pass (no B-4-touching change landed)."}
  - {item: "D-2 carried finding #4 (judgment_query v3 oversize baseline)", status: "STILL OPEN — unchanged, no D-4b lane has touched it."}
  - {item: "D-4a A-5 metric disagreement (pratyantar_lord: CRPS/skill red vs hit-rate green)", status: "NOT resolved — still exactly DR-12's adjudication scope, still blocked on B-1's certified run."}
  - {item: "CR-113 (orphaned build_runs row)", status: "confirmed closed at prior passes; not re-queried this pass."}
  - {item: "CR-114 (mcp/sidecar images stale)", status: "re-confirmed working at prior pass (PR #693); F-1/F-2/NP-D4B-006's own merges each imply the same deploy path fired again, not individually re-inspected this pass."}
  - {item: "Gate Ś #8 (D-1.6 narrow yoga-signal-class timing residual)", status: "unchanged, non-blocking, not re-touched this pass."}
  - {item: "Marriage-specimen residual (D-5 gate_run_3 / DR-17 type-specimen pair)", status: "STRENGTHENED, not closed — retroVerify's live guru_shani_double_transit probe (reported to this pass, event_class=marriage, target_count=23, 19/19 active) corroborates against the now-F-1-merged state. Still requires B-3's own formal residual-pair mining against a fully-materialized sweep (still 55%), which has not run."}
  - {item: "NEW at prior pass — ga_vichara_writer.py leverage_index dasha-runway sub-field wrong", status: "OPEN, unchanged this pass. Owner: a future ga_vichara_writer.py lane."}
  - {item: "CR-120/CR-121 (midpoint-triangle/transit-kernel NotImplementedModelError stubs)", status: "NOW FORMALLY REGISTERED (MARSYS_DEFECT_GAP_REGISTER_v2_0.md v3.10, 2026-07-22) as NOT-EVALUABLE, not open defects — closes a citation gap this pass's own PROMISE_LEDGER_D4B.md draft had flagged."}
close_gate_status:
  # BRIEF_D4B §5's 10 criteria, honest status this pass — no criterion is claimed PASS if the
  # evidence does not support it. Delta from the PR #695 pass named explicitly per row.
  - {n: 1, criterion: "materialization-completeness (as reconciled: gates only B-6 serving, not B-1 scoring)", status: "PARTIAL — 165/300 (55%), unchanged from prior pass (live-requeried, byte-identical)"}
  - {n: 2, criterion: "bakeoff complete and honest", status: "NOT MET — both named defects now FIXED on main (delta from prior pass), but NO re-run exists to certify a champion/no-winner. Honestly reported, not forced green."}
  - {n: 3, criterion: "mimamsa_calibration_get n_observations~40/chart, multipliers evaluating", status: "NOT MET — depends on B-2's backfill, which is SKIPPED (hard-gated on B-1). Live-reconfirmed this pass: 0/9 rows have any observations."}
  - {n: 4, criterion: "discrimination (gain/loss different evidence+grades)", status: "not re-verified this pass — no B-lane touched this surface, unchanged"}
  - {n: 5, criterion: "negative controls implemented, control delta reported honestly", status: "PARTIAL, unchanged in substance — the F-2 fix that repairs the CRPS-side control computation is now merged (delta from prior pass), but it has not been exercised in a fresh run, so no control delta from a certified run exists yet"}
  - {n: 6, criterion: "at least one served verdict moved by a calibrated multiplier", status: "NOT MET — no calibration has run (B-2/B-3 skipped), unchanged"}
  - {n: 7, criterion: "remedy: bo_upaya wealth resonances != 0, leverage-ranked, subject alias identical", status: "MET — B-4 (PR #689), unchanged, not re-verified live this pass"}
  - {n: 8, criterion: "prospective ledger live, >=5 falsifier-bearing predictions", status: "MET at D-4a (A-4, 5 entries) — unchanged, not re-verified fresh this pass"}
  - {n: 9, criterion: "DR-17/18 harness live, grading applied, KUC census committed", status: "NOT MET, unchanged — though a dr17_grading.ts scaffold now sits uncommitted in the B-1-full-rerun WIP worktree, suggesting work toward this has started but not landed"}
  - {n: 10, criterion: "anti-gaming pass on 1-9 + all prior batteries green, every carried finding dispositioned", status: "PARTIAL — this pass's own spot-check (REPORT_D4B.md §2) dispositions every carried item honestly, including the two new-since-prior-pass deltas (F-1 merged, CR-120/121 registered); no formal anti-gaming pass run since most criteria are still NOT MET or PARTIAL"}
next_wave: null  # D-4b stays OPEN. No next wave opens until B-1's full re-run (over the
  # F-1+F-2-repaired substrate) is completed, committed, and certified; B-2/B-3 dispatch against a
  # real adjudication receipt; and a future B-6 pass runs the mode=FULL three-point baseline diff
  # this pass explicitly still does not.
```

# STATE_D4B — D-4b Wave State (partial, GATED — this pass does not close the wave)

See `REPORT_D4B.md` (this pass's version) for the full narrative. This file is the machine-readable
state ledger per protocol §6.1; `CLAUDECODE_BRIEF.md`'s `current_wave` field is the authoritative
"you are here" pointer and is NOT set to `CAMPAIGN-CLOSED` by this pass. This file supersedes the
version merged via PR #695 — that version remains readable in git history at its own merge commit.
