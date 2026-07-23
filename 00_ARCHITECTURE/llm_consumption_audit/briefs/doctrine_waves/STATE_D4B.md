---
artifact: STATE_D4B
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-4b — Calibration Ignition + Grand Bakeoff
updated_at: 2026-07-23T11:30:00Z
supersedes: STATE_D4B.md as merged by PR #717 (`wave/D-4b/B6-real-close-6`, mode=GATED) — that
  version is preserved in git history, not deleted. This is the CAMPAIGN-CLOSE version, per
  native ruling CR-128 (2026-07-23, via Cowork): calibration DEFERRED honestly, do not build the
  write-surface now, close the campaign.
---

```yaml
wave: D-4b
lifecycle_step: 7  # CAMPAIGN-CLOSED. B-1 DONE (PR #712, clean NO_WINNER). B-2/B-3 HONESTLY-
                    # DEFERRED (native ruling, not blocked-pending-fix) -- see CR-128 disposition
                    # below. B-6 REAL close delivered: three-point baseline diff produced
                    # (pre-D-2 -> post-campaign; no post-D-2 checkpoint was ever produced by any
                    # prior wave -- disclosed honestly, not fabricated). current_wave ->
                    # CAMPAIGN-CLOSED on CLAUDECODE_BRIEF.md.
brief_bound: true
mode_this_pass: FULL  # campaign close. Not GATED -- every lane that can honestly close, closes;
                       # the one lane that cannot (calibration ignition) closes as DEFERRED, its
                       # own honest, pre-committed terminus -- not left open pretending to be a
                       # blocker.
campaign_verdict: >
  No validated timing model on the sealed retrospective corpus (NO_WINNER, adversarially
  verified). Calibration ignition is deferred to the prospective regime -- the standing live loop
  is the path. The retrospective test ran clean and reported honestly that it lacks sufficient
  validated signal to calibrate. This IS the pre-committed no-winner outcome; the campaign
  reaches its designed honest terminus.
b1_history:
  - {attempt: 1, branch: wave/D-4b/B1-bakeoff, pr: 687, status: merged, result: "BLOCKED, 0 contenders scored, no fabrication."}
  - {attempt: 2, branch: wave/D-4b/B1-bakeoff-narrowed, pr: 694, status: merged, result: "31-event run, pre-F1/F2. VOID (433 negative CRPS)."}
  - {attempt: 3, branch: wave/D-4b/B1-full-rerun, status: QUARANTINED, result: "3 batches + assembly completed, but scored the sealed test split across all 14 contenders. Every score/delta/DR-12-NO_WINNER VOID. See QUARANTINE_B1_FULL_RERUN_v1_0.md, NP-D4B-007, DR-20 (DIS.031), CR-127."}
  - {attempt: 4, branch: wave/D-4b/CR123-seal-fix, pr: 709, status: merged, result: "The fix, not a re-run: sealed_split_guard.ts wired into harness.ts's runMirroredScoringHarness -- structural, not instruction-based, enforcement. 13/13 new tests, 137/137 suite, Opus ACCEPT."}
  - {attempt: 5, branch: wave/D-4b/B1-full-rerun-2, pr: 712, status: MERGED, result: "CLEAN. 3 batches + assembly + full anti-gaming pass all independently ACCEPT-verified. Zero sealed-split touches (confirmed by an independently-written cross-reference check, not reusing the guard's own code path). DR-12 adjudicated NO_WINNER, honestly grounded: pratyantar_lord (n=31, only adequately-covered contender) shows apparent +0.1058 skill that a fresh adversarial statistical re-derivation proved is a single-outlier artifact -- excluding it, the model LOSES 27/31 (sign-test p=3.40e-05, Wilcoxon p=6.85e-04). Every other contender n=2, structurally too thin. No contender clears DR-15(b). This IS the campaign's pre-committed no-winner outcome, not a failure. FINAL -- campaign verdict."}
lanes:
  - {lane: F-1, pr: 699, status: merged, result: "gochara_resonance_map mapping fixed. Unchanged."}
  - {lane: F-2, pr: 697, status: merged, result: "circularShiftCurve wraparound sort fixed. Confirmed genuinely fixed by BOTH B-1 chunked-re-run attempts (zero negative CRPS observed in both). Unchanged."}
  - {lane: DR-17 grading module, pr: 704, status: merged, result: "Salvaged, verified, exercised live in the clean re-run. Unchanged."}
  - {lane: "B-1 run manifest v2.0 + batch-runner harness", branch: wave/D-4b/B1-full-rerun-2, status: merged_component, result: "Committed directly (not agent-dispatched) after a prior agent silently failed to commit. Packet blob sha byte-identical to v1.0 (9b6713db...) -- packet genuinely unchanged throughout. Promoted this pass to the standing per-release regression suite -- see promise ledger."}
  - {lane: B-2, branch: none, status: HONESTLY-DEFERRED, result: "Native ruling (CR-128, 2026-07-23): do not build/repair the write-surface now. B-1's own NO_WINNER means any B-2 backfill would write model_confidence: none_validated rows against a model the data itself says isn't validated, from N~40 design-time-exposed events -- nothing legitimate to backfill. The architecture gap (mimamsa_outcome_record does not exist; update_calibration() references phala_anchors.prediction_state, a dropped column) is real and CR-128 stays open as named future work, but it is not a D-4b blocker -- it is a surface correctly not built yet. Deferred to when the prospective ledger has accrued enough forward-scored, genuinely-unseen outcomes to calibrate against."}
  - {lane: B-3, branch: none, status: HONESTLY-DEFERRED, reason: "hard-gated on B-2; B-2 itself now closes DEFERRED, not blocked. Never dispatched -- correctly."}
  - {lane: B-4, pr: 689, status: merged, result: "bo_upaya populated. Unchanged."}
  - {lane: B-5, pr: 688, status: merged, result: "mechanism_retrodiction_get -- NOTE, corrected this pass: no live tool by this name exists on the connected MCP surface (confirmed live, tool search returned zero matches). B-5's PR #688 merged a retrodiction-adjacent capability under the mimamsa_* / phala_* surface, but the specific mechanism_retrodiction_get name referenced in earlier STATE/REPORT passes does not resolve live -- see three-point diff §axis 6 for the honest disclosure. Flagged as a naming/registration residual, not re-investigated this pass (out of scope for a close pass; named for whoever next touches B-5's surface)."}
  - {lane: permission-bridge, pr: 693, status: merged, result: "PERMISSION curve HTTP route + 13-contender bridge + bind-time assertion. CR-120/121 landed. Unchanged."}
  - {lane: "B-6 (PR #695/#703/#708/#717 passes)", status: merged, result: "GATED closes 1-4, all honest, all superseded, all preserved in history."}
  - {lane: "B-6 REAL close (this pass)", branch: wave/D-4b/campaign-close, status: FINAL, result: "Three-point baseline wealth-reading diff produced live against chart 482012f1 (judgment_query v3, get_dashas, kala_windows_get, bodha_remedies_get) per BASELINE_WEALTH_READING_PRE_D2_v1_0.md §4. No post-D-2 checkpoint reading was ever produced by any prior wave -- disclosed as an honest gap, not fabricated as a fake middle point. Composite score UNCHANGED at 2.38 (identical d1_score 1.15 + yoga_term 1.23) between pre-D-2 baseline and post-campaign reading -- the campaign's work landed elsewhere (mechanism naming, receipt completeness, remedy-gap visibility, dasha verification depth), not in this domain's headline score. epistemic.grade: structural_prior confirmed live -- consistent with, and independently corroborating, the calibration-deferred disposition. See REPORT_D4B.md §7 for full diff."}
adjudications:
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook", status: "RATIFIED (native, 2026-07-17). DISCHARGED -- B-1's clean, merged NO_WINNER result (PR #712) is the first legitimate scored comparison this campaign has ever produced. The adjudication is honest: no contender clears DR-15(b). FINAL."}
  - {dr: DR-19, dis: DIS.030, subject: "An open is a repo state, not a message", status: "RATIFIED, holding. Exercised repeatedly across the campaign, including B-2's own DEFERRED disposition this pass (a deferral recorded as a state -- CR-128 stays open -- not a closing message)."}
  - {dr: DR-20, dis: DIS.031, subject: "A train/test seal is enforced at the query/data layer, never by agent instruction alone", status: "RATIFIED (native, 2026-07-22). DISCHARGED -- fix built (PR #709), independently verified twice, and PROVEN in production by the clean re-run's own live anti-gaming pass."}
  - {dr: "cross-campaign CR-numbering collision", subject: "two concurrent campaigns sharing one register namespace collided twice on CR numbers (CR-122/123, then CR-125)", status: "RECORDED as a process/hygiene finding, not a formal DR -- native directive: named for whoever runs the next concurrent waves. A reserved-range or lock convention is needed for MARSYS_DEFECT_GAP_REGISTER_v2_0.md when >1 campaign is active."}
next_action: >
  None binding on D-4b -- CAMPAIGN-CLOSED. CR-128 stays OPEN as a named future-work item with a
  natural home in a small pre-work lane before whichever future wave first has real prospective
  outcome data to calibrate against, or folded into D-6. The standing live loop is OPEN and is now
  the primary calibration path, not a footnote: every reading files falsifier-bearing predictions;
  forward outcomes accrue toward the eventual honest calibration CR-128 will serve. D-6 is staged
  ratification-ready (GOCHARA_SWEEP_2_0_DESIGN_v1_0.md exists in the doctrine_waves briefs
  directory as an untracked draft at this pass's start -- native review recommended before D-6
  formally opens; not a D-4b blocker).
```
