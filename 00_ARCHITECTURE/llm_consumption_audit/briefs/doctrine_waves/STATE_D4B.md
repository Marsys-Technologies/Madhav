---
artifact: STATE_D4B
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-4b — Calibration Ignition + Grand Bakeoff
updated_at: 2026-07-22T17:29:44Z
supersedes: STATE_D4B.md as merged by PR #703 (2026-07-22T13:57:10Z, `wave/D-4b/B6-real-close`),
  which itself superseded STATE_D4B.md as merged by PR #695 (2026-07-21T23:34:17Z,
  `wave/D-4b/B6-close`). Both preserved in git history, not deleted; this file replaces both as the
  current record.
---

```yaml
wave: D-4b
lifecycle_step: 6  # B-lanes IN PROGRESS. B-4/B-5 merged; B-1's two named defects were fixed at the
                    # PR #703 pass (F-1 PR #699, F-2 PR #697). SINCE THAT PASS: B-1's full re-run
                    # has been COMPLETED and PUSHED to origin (wave/D-4b/B1-full-rerun @ 0aa69c06)
                    # -- 14 contenders scored, manifest-hash-consistent (independently re-verified
                    # this pass), DR-12 discharged NO_WINNER -- but ZERO PR has ever been opened for
                    # it (gh pr list, empty, all states). b1.merged=false, independently reproduced.
                    # B-2/B-3 correctly SKIPPED (hard-gated on a MERGED receipt, which does not yet
                    # exist). B-6 (this REAL close pass #4) ran GATED -- verified state
                    # independently, did NOT close the wave. current_wave stays D-4b (OPEN) on
                    # CLAUDECODE_BRIEF.md — NOT set to CAMPAIGN-CLOSED.
brief_bound: true
mode_this_pass: GATED  # orchestrator-specified; explicitly not mode=FULL. The mode=FULL
  # three-point baseline diff (BRIEF_D4B §1 B-6 item 4) has NOT been run by any pass to date
  # (#695, #703, or this one).
lanes:
  - {lane: B-1, branch: wave/D-4b/B1-bakeoff, status: merged, pr: 687, result: "BLOCKED — 0 contenders scored, 1/5 requested contenders even had a callable curve(). DR-19-clean, refused a fabricated cost-projection instruction. No scoring attempted. Unchanged since prior pass."}
  - {lane: B-1 (narrowed), branch: wave/D-4b/B1-bakeoff-narrowed, status: merged, pr: 694, result: "Real, live 14-contender x 31-TRAIN-event run (434 calls, 0 errors) against live infra, predating both fixes below. BLOCKED-ON-DEFECT, not champion/no-winner. Superseded-pending-re-run, not deleted. Unchanged since prior pass."}
  - {lane: F-1 (fix, not a §1 lane), branch: wave/D-4b/F1-resonance-map, status: merged, pr: 699, merged_at: "2026-07-22T11:07:19Z", result: "gochara_resonance_map event_class mapping gap fixed. Merged under a documented deviation (NP-D4B-006, PR #701). Unchanged since PR #703 pass."}
  - {lane: F-2 (fix, not a §1 lane), branch: wave/D-4b/F2-curve-controls, status: merged, pr: 697, merged_at: "2026-07-22T07:03:12Z", result: "curve_controls.ts circularShiftCurve() wraparound re-sort fixed. Unchanged since PR #695 pass."}
  - {lane: "DR-17 grading module", branch: wave/D-4b/dr17-grading, status: merged, pr: 704, merged_at: "2026-07-22T13:47:46Z", result: "dr17_grading.ts (peak/sub_peak/elevated/neutral/contra + double-weighted anti-hit, per NP-D4B-001), salvaged from the crashed B-1 re-run attempt the PR #703 pass found as an uncommitted scaffold. NEW SINCE PR #703 PASS; imported (not reimplemented) by every B-1-full-rerun batch driver."}
  - {lane: "B-1 full re-run", branch: wave/D-4b/B1-full-rerun, status: complete_but_unmerged_no_pr, result: "COMPLETE AND PUSHED, ZERO PR EVER OPENED (gh pr list --head wave/D-4b/B1-full-rerun --state all returns empty, verified this pass). origin/wave/D-4b/B1-full-rerun @ 0aa69c06 = local worktree HEAD, identical, verified. 6 commits since the PR #703 pass: manifest (ab054da9), CR-122 batch-artifact-io harness (fc6ead96, 8/8 tests per dispatch terms, imported not reimplemented), 3 batch-driver commits (c6f319d9/19ac5b81/8cb6bef8) scoring 14 contenders x 54 events, ASSEMBLY commit (0aa69c06) concatenating the 3 batches + discharging DR-12 NO_WINNER. Manifest-hash consistency INDEPENDENTLY RE-VERIFIED this pass (re-ran checkManifestHashConsistency/hashManifestFile fresh, imported from the committed harness, not reimplemented): consistent=true, hash 91dc0c3e20...b37603, byte-identical to the ASSEMBLY_REPORT's own citation. pratyantar_lord (n=54, the only adequately-sampled contender): CRPS skill -0.1557 vs shuffled-birth control (underperforms; beats control 9/54). All 12 PERMISSION contenders + hierarchical_ensemble constrained to n=3 each (career_advancement TOTALLY unresolved, 0/54 events, a disclosed recurrence of F-1's design limit, not a new defect). No contender beats its control at a meaningful sample size. THIS IS THE WAVE'S EXACT BLOCKER THIS PASS: the run is done and honest, but it has never been merged, reviewed, or even opened as a PR. The ASSEMBLY step itself also has no independent verifier pass cited beyond the 3 underlying batches' own individual ACCEPT receipts -- a gap this pass names as a precondition for the eventual merge PR, not a defect in the batches."}
  - {lane: B-2, branch: none, status: skipped, reason: "hard-gated on B-1's MERGED adjudication receipt per BRIEF_D4B §1 — never dispatched, no worktree/branch created. Reconfirmed via gh pr list this pass. A completed-but-unmerged B-1 result does not satisfy this gate."}
  - {lane: B-3, branch: none, status: skipped, reason: "hard-gated on B-1's MERGED adjudication receipt per BRIEF_D4B §1 — never dispatched, no worktree/branch created. Reconfirmed via gh pr list this pass."}
  - {lane: B-4, branch: wave/D-4b/B4-remedy-join, status: merged, pr: 689, result: "bo_upaya populated via bodha_rm_dasha_windowed_prescriptions (leverage_index x sadhana history x dasha runway); leverage_index subject=venus false-empty CONFIRMED CLOSED live (prior pass). Unchanged this pass — not re-touched, not re-verified live."}
  - {lane: B-5, branch: wave/D-4b/B5-retrodiction, status: merged, pr: 688, result: "mechanism_retrodiction_get live, CONFIRMATION-ONLY. Unchanged this pass."}
  - {lane: permission-bridge (pre-step, not a §1 lane), branch: wave/D-4b/permission-bridge, status: merged, pr: 693, result: "PERMISSION curve HTTP route + 13-contender TS bridge + bind-time assertion. Also landed CR-120/CR-121 (midpoint-triangle/transit-kernel NOT-EVALUABLE dispositions, MARSYS_DEFECT_GAP_REGISTER_v2_0.md v3.10). Unchanged this pass, cited here for the CR-120/121 cross-reference."}
  - {lane: ledger-hygiene, branch: wave/D-4b/ledger-hygiene, status: merged, pr: 690, result: "NP-D4B-004/005. Unchanged this pass."}
  - {lane: a5-reconciliation, branch: wave/D-4b/a5-reconciliation, status: open_not_merged, pr: 692, result: "Investigation-only, correction LANDED separately by PR #695 (B6-close). Unchanged this pass. Still-open A-5 metric disagreement carried below."}
  - {lane: ledger-f1-deviation, branch: wave/D-4b/ledger-f1-deviation, status: merged, pr: 701, merged_at: "2026-07-22T11:30:29Z", result: "NP-D4B-006 — conductor-verified-under-infrastructure-duress deviation record for F-1 (PR #699). Unchanged since PR #703 pass."}
  - {lane: "B-6 (PR #695 pass)", branch: wave/D-4b/B6-close, status: merged, pr: 695, merged_at: "2026-07-21T23:34:17Z", result: "First GATED close pass — honest partial status, named B-1's two defects as blocker. SUPERSEDED, preserved in git history."}
  - {lane: "B-6 (PR #703 pass)", branch: wave/D-4b/B6-real-close, status: merged, pr: 703, merged_at: "2026-07-22T13:57:10Z", result: "Second GATED close pass — found both B-1 defects fixed on main but no re-run beyond an uncommitted dr17_grading.ts scaffold. SUPERSEDED by this REAL close pass #4's REPORT_D4B.md/STATE_D4B.md, preserved in git history, not deleted."}
  - {lane: "B-6 (this REAL close pass #4)", branch: wave/D-4b/B6-real-close-3, status: in_progress_gated, result: "DR-19 caught a worktree/branch mismatch at dispatch (host harness pinned this session to .claude/worktrees/wave-D-4b-B1-full-rerun, a B-1 scoring branch, not the dispatched B-6 close branch -- neither of which existed on disk or origin at session start); created the dispatched worktree/branch fresh from origin/main before any governance artifact was touched. Independently re-verified every material claim (gh pr list for all named PRs; live re-run of checkManifestHashConsistency/hashManifestFile against the B-1-full-rerun ASSEMBLY artifacts; live SQL for mimamsa_multipliers and ka_gochara_sweep materialization) rather than trusting any prior session's word. Found: B-1's full re-run is COMPLETE, ASSEMBLED, manifest-hash-consistent, DR-12 discharged NO_WINNER -- but has ZERO PR, ever, and is therefore unmerged. Did NOT run the mode=FULL three-point baseline diff. Did NOT mark current_wave CAMPAIGN-CLOSED. Full record: REPORT_D4B.md (this pass's version)."}
adjudications:
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook (forward-binding from D-3)", status: "RATIFIED (native, 2026-07-17); DISCHARGE now exists (B-1-full-rerun ASSEMBLY, NO_WINNER, applying the already-ratified doctrine to real scored data) but is NOT YET ON main -- DISAGREEMENT_REGISTER_v1_0.md DIS.025 still literally reads 'NOT YET DISCHARGED', now stale relative to the unmerged branch. This pass does not edit DIS.025 itself (a register-maintenance action that belongs with the merge)."}
dr_ratification_sweep_this_pass:
  # Spot-checked, not a full re-sweep.
  still_queued_for_native_ratification: [DR-6 (DIS.019), DR-7 (DIS.020), DR-8 (DIS.021)]  # unchanged
  already_native_ratified: [DR-9 (DIS.022), DR-10 (DIS.023), DR-11 (DIS.024), DR-12 (DIS.025, ratified; discharge exists unmerged, see adjudications above), DR-13 (DIS.026), DR-14 (DIS.027), DR-15 (DIS.028), DR-16 (DIS.029), DR-19 (DIS.030)]  # unchanged
  ratified_in_substance_no_formal_dis_row_yet: [DR-17, DR-18]  # unchanged
  np_d4b_ledger_provisional_pending_native_batch_ratification: [NP-D4B-001, NP-D4B-002, NP-D4B-003, NP-D4B-004]  # NP-D4B-001 (DR-17 grading weights) now genuinely EXERCISED by the unmerged B-1-full-rerun batches (was "not exercised, scaffold only" at the PR #703 pass); NP-D4B-004 (control design) re-exercised on the F-1+F-2-repaired substrate. Neither change is on main yet.
  np_d4b_ledger_direct_native_ruling_already_final: [NP-D4B-005]  # unchanged
  np_d4b_ledger_new_this_pass: []  # no new NP-D4B entry issued this pass -- compilation only, see
    # NATIVE_PROXY_LEDGER_D4B.md's addendum appended this pass.
live_materialization_check_this_pass:
  asset: ka_gochara_sweep
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa
  substeps_committed: 165  # byte-identical to both prior passes; live-requeried, not assumed
  substeps_planned: 300
  pct: "55%"
  asset_throughput_state: error
  last_error: "BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run; skipped to avoid building on incomplete data"
  last_built_at: "2026-07-21T22:25:23.308Z"  # unchanged — no new dispatch since the PR #695 pass
  consequence: "Gates ONLY B-6's own serving assertions per BRIEF_D4B §0 RECONCILIATION, not B-1's event-driven scoring -- confirmed again this pass: the full B-1 run scored successfully without full materialization. No B-6 claim in this pass's REPORT_D4B.md asserts full materialization."
live_calibration_check_this_pass:
  table: mimamsa_multipliers
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa
  total_rows: 9
  rows_with_n_observations_gt_0: 0
  max_n_observations: 0
  consequence: "Structural mode confirmed unchanged — consistent with B-2/B-3 both correctly SKIPPED (hard-gated on a merged receipt that still does not exist)."
carried_item_dispositions:
  - {item: "D-2 carried finding #1 (leverage_index subject=venus false-empty)", status: "CLOSED — unchanged since prior passes, not re-verified live this pass (no B-4-touching change landed)."}
  - {item: "D-2 carried finding #4 (judgment_query v3 oversize baseline)", status: "STILL OPEN — unchanged, no D-4b lane has touched it."}
  - {item: "D-4a A-5 metric disagreement (pratyantar_lord: CRPS/skill red vs hit-rate green)", status: "NOT resolved by merge, but the unmerged B-1-full-rerun ASSEMBLY reproduces the same pattern on the repaired substrate: pratyantar_lord's CRPS skill is negative (-0.1557) while its hit-rate (51.9%) and DR-17 weighted mean (0.407) read more favorably -- the same CRPS-vs-hit-rate divergence A-5 named, now on real full-corpus data instead of the pre-fix NARROWED run. Still exactly DR-12's adjudication scope; still not on main."}
  - {item: "CR-113 (orphaned build_runs row)", status: "confirmed closed at prior passes; not re-queried this pass."}
  - {item: "CR-114 (mcp/sidecar images stale)", status: "re-confirmed working at PR #695 pass; not individually re-inspected since."}
  - {item: "Gate Ś #8 (D-1.6 narrow yoga-signal-class timing residual)", status: "unchanged, non-blocking, not re-touched this pass."}
  - {item: "Marriage-specimen residual (D-5 gate_run_3 / DR-17 type-specimen pair)", status: "STRENGTHENED, not closed — the marriage LEL event (EVT.2013.12.11.01) is one of only 3 events resolving to a populated event_class in the unmerged B-1-full-rerun run, per the ASSEMBLY_REPORT's own §5 disclosure. Still requires B-3's own formal residual-pair mining against a fully-materialized sweep (still 55%) AND a merged B-1 receipt -- neither exists yet."}
  - {item: "ga_vichara_writer.py leverage_index dasha-runway sub-field wrong", status: "OPEN, unchanged this pass. Owner: a future ga_vichara_writer.py lane."}
  - {item: "CR-120/CR-121 (midpoint-triangle/transit-kernel NotImplementedModelError stubs)", status: "Registered (MARSYS_DEFECT_GAP_REGISTER_v2_0.md v3.10) as NOT-EVALUABLE, unchanged since PR #703 pass."}
  - {item: "CR-122 (checkpointed-batching artifact-I/O harness, b1_batch_artifact_io.ts)", status: "NEW THIS PASS -- named in the fc6ead96 commit message but has ZERO hits in MARSYS_DEFECT_GAP_REGISTER_v2_0.md (grep, this pass). Flagged as an open registration gap; not resolved by this pass (adding register rows for another lane's infra is out of B-6's own bounded scope)."}
close_gate_status:
  # BRIEF_D4B §5's 10 criteria, honest status this pass — no criterion is claimed PASS if the
  # evidence does not support it. Delta from the PR #703 pass named explicitly per row.
  - {n: 1, criterion: "materialization-completeness (as reconciled: gates only B-6 serving, not B-1 scoring)", status: "PARTIAL — 165/300 (55%), unchanged from both prior passes (live-requeried, byte-identical)"}
  - {n: 2, criterion: "bakeoff complete and honest", status: "NOT MET, but the substance now exists unmerged -- DELTA FROM PRIOR PASS: the full 14-contender x 54-event run is ASSEMBLED, manifest-hash-consistent, and DR-12 was discharged NO_WINNER honestly, per the pre-committed no-winner branch. It is not yet on main, so it cannot yet be the campaign's certified record. Honestly reported, not forced green, not treated as MET on the strength of an unmerged branch."}
  - {n: 3, criterion: "mimamsa_calibration_get n_observations~40/chart, multipliers evaluating", status: "NOT MET — depends on B-2's backfill, which is SKIPPED (hard-gated on a merged B-1 receipt). Live-reconfirmed this pass: 0/9 rows have any observations."}
  - {n: 4, criterion: "discrimination (gain/loss different evidence+grades)", status: "not re-verified this pass — no merged B-lane change touches this surface, unchanged"}
  - {n: 5, criterion: "negative controls implemented, control delta reported honestly", status: "PARTIAL — the F-2 fix is merged and now genuinely EXERCISED in the unmerged B-1-full-rerun run (negative_crps_check.total_negative_crps_found sums to 0 across all 3 batches, per the ASSEMBLY_REPORT), demonstrating the fix holds at full scale. Still not on main, so no certified control delta exists yet."}
  - {n: 6, criterion: "at least one served verdict moved by a calibrated multiplier", status: "NOT MET — no calibration has run (B-2/B-3 skipped), unchanged"}
  - {n: 7, criterion: "remedy: bo_upaya wealth resonances != 0, leverage-ranked, subject alias identical", status: "MET — B-4 (PR #689), unchanged, not re-verified live this pass"}
  - {n: 8, criterion: "prospective ledger live, >=5 falsifier-bearing predictions", status: "MET at D-4a (A-4, 5 entries) — unchanged, not re-verified fresh this pass"}
  - {n: 9, criterion: "DR-17/18 harness live, grading applied, KUC census committed", status: "PARTIAL -- DELTA FROM PRIOR PASS: dr17_grading.ts is now MERGED (PR #704) and genuinely applied to every contender in the unmerged B-1-full-rerun run (grade distributions reported per-contender in the ASSEMBLY_REPORT). Not yet on main as part of a certified B-1 record, and no formal KUC census artifact beyond the per-contender grade counts has been separately committed."}
  - {n: 10, criterion: "anti-gaming pass on 1-9 + all prior batteries green, every carried finding dispositioned", status: "PARTIAL — this pass's own spot-check (REPORT_D4B.md §3) dispositions every carried item honestly, including this pass's own new delta (B-1 ASSEMBLED-but-unmerged, CR-122 registration gap); no formal anti-gaming pass run since most criteria are still NOT MET or PARTIAL, and the ASSEMBLY step itself still lacks its own independent verifier pass (REPORT_D4B.md §2)."}
next_wave: null  # D-4b stays OPEN. No next wave opens until B-1's already-complete NO_WINNER run
  # is opened as a PR, independently verified at the ASSEMBLY level, and merged; B-2/B-3 dispatch
  # against that real, merged receipt; and a future B-6 pass runs the mode=FULL three-point
  # baseline diff this pass explicitly still does not.
```

# STATE_D4B — D-4b Wave State (partial, GATED — this pass does not close the wave)

See `REPORT_D4B.md` (this pass's version) for the full narrative. This file is the machine-readable
state ledger per protocol §6.1; `CLAUDECODE_BRIEF.md`'s `current_wave` field is the authoritative
"you are here" pointer and is NOT set to `CAMPAIGN-CLOSED` by this pass. This file supersedes the
versions merged via PR #703 and PR #695 — both remain readable in git history at their own merge
commits.
