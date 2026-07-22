---
artifact: STATE_D4B
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-4b — Calibration Ignition + Grand Bakeoff
updated_at: 2026-07-23T04:45:00Z
supersedes: STATE_D4B.md as merged by PR #708 (2026-07-22T18:04:49Z, `wave/D-4b/B6-real-close-4`)
  — that version is preserved in git history, not deleted. NOTE: a later, unrelated commit
  (`d1c375d2`, a concurrent campaign's own cross-contamination cleanup) accidentally reverted
  PR #708's content further than intended; this file restores it and adds everything since.
---

```yaml
wave: D-4b
lifecycle_step: 6  # B-1 is DONE — genuinely merged, clean, NO_WINNER (PR #712). B-2 is BLOCKED
                    # on a real architecture gap (CR-127), not a mechanical bug: BRIEF_D4B's
                    # write target does not exist. B-3 correctly SKIPPED (gated on B-2).
                    # current_wave stays D-4b (OPEN) on CLAUDECODE_BRIEF.md.
brief_bound: true
mode_this_pass: GATED  # explicitly not mode=FULL. B-2/B-3 have never run to completion.
b1_history:
  - {attempt: 1, branch: wave/D-4b/B1-bakeoff, pr: 687, status: merged, result: "BLOCKED, 0 contenders scored, no fabrication."}
  - {attempt: 2, branch: wave/D-4b/B1-bakeoff-narrowed, pr: 694, status: merged, result: "31-event run, pre-F1/F2. VOID (433 negative CRPS)."}
  - {attempt: 3, branch: wave/D-4b/B1-full-rerun, status: QUARANTINED, result: "3 batches + assembly completed, but scored the sealed test split across all 14 contenders. Every score/delta/DR-12-NO_WINNER VOID. See QUARANTINE_B1_FULL_RERUN_v1_0.md, NP-D4B-007, DR-20 (DIS.031), CR-126."}
  - {attempt: 4, branch: wave/D-4b/CR123-seal-fix, pr: 709, status: merged, result: "The fix, not a re-run: sealed_split_guard.ts wired into harness.ts's runMirroredScoringHarness -- structural, not instruction-based, enforcement. 13/13 new tests, 137/137 suite, Opus ACCEPT."}
  - {attempt: 5, branch: wave/D-4b/B1-full-rerun-2, pr: 712, status: MERGED, result: "CLEAN. 3 batches + assembly + full anti-gaming pass all independently ACCEPT-verified. Zero sealed-split touches (confirmed by an independently-written cross-reference check, not reusing the guard's own code path). DR-12 adjudicated NO_WINNER, honestly grounded: pratyantar_lord (n=31, only adequately-covered contender) shows apparent +0.1058 skill that a fresh adversarial statistical re-derivation proved is a single-outlier artifact -- excluding it, the model LOSES 27/31 (sign-test p=3.40e-05, Wilcoxon p=6.85e-04). Every other contender n=2, structurally too thin. No contender clears DR-15(b). This IS the campaign's pre-committed no-winner outcome, not a failure."}
lanes:
  - {lane: F-1, pr: 699, status: merged, result: "gochara_resonance_map mapping fixed. Unchanged."}
  - {lane: F-2, pr: 697, status: merged, result: "circularShiftCurve wraparound sort fixed. Confirmed genuinely fixed by BOTH B-1 chunked-re-run attempts (zero negative CRPS observed in both). Unchanged."}
  - {lane: DR-17 grading module, pr: 704, status: merged, result: "Salvaged, verified, exercised live in the clean re-run. Unchanged."}
  - {lane: "B-1 run manifest v2.0 + batch-runner harness", branch: wave/D-4b/B1-full-rerun-2, status: merged_component, result: "Committed directly (not agent-dispatched) after a prior agent silently failed to commit. Packet blob sha byte-identical to v1.0 (9b6713db...) -- packet genuinely unchanged throughout."}
  - {lane: B-2, branch: none, status: BLOCKED, result: "The B-2 build dispatch traced mimamsa_outcome_record (BRIEF_D4B's stated write target) end-to-end and found it does not exist as a table or any live write path -- confirmed independently by this pass via direct pg_tables/information_schema queries. See CR-127. No branch, commit, or write was ever created -- correctly halted rather than fabricate a row count against a mechanism that doesn't exist."}
  - {lane: B-3, branch: none, status: skipped, reason: "hard-gated on B-2. Never dispatched."}
  - {lane: B-4, pr: 689, status: merged, result: "bo_upaya populated. Unchanged."}
  - {lane: B-5, pr: 688, status: merged, result: "mechanism_retrodiction_get live. Unchanged."}
  - {lane: permission-bridge, pr: 693, status: merged, result: "PERMISSION curve HTTP route + 13-contender bridge + bind-time assertion. CR-120/121 landed. Unchanged."}
  - {lane: "B-6 (PR #695/#703/#708 passes)", status: merged, result: "GATED closes 1-3, all honest, all superseded, all preserved in history."}
  - {lane: "B-6 (this pass, #6)", branch: wave/D-4b/B6-real-close-6, status: in_progress_gated, result: "Authored directly by the orchestrating session. Re-lands DR-20/CR-125/CR-126/NP-D4B-007 (originally committed only on the permanently-quarantined branch, never reached main) under fresh numbers after a numbering collision with a concurrent campaign; restores STATE_D4B.md/REPORT_D4B.md content an unrelated campaign's own cleanup revert accidentally rolled back; registers CR-127 (the new B-2 architecture gap) and NP-D4B-008 (process findings, native review requested)."}
adjudications:
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook", status: "RATIFIED (native, 2026-07-17). DISCHARGED this pass -- B-1's clean, merged NO_WINNER result (PR #712) is the first legitimate scored comparison this campaign has ever produced. The adjudication is honest: no contender clears DR-15(b)."}
  - {dr: DR-19, dis: DIS.030, subject: "An open is a repo state, not a message", status: "RATIFIED, holding. Exercised repeatedly this pass too (B-2's own halt began with a DR-19 check)."}
  - {dr: DR-20, dis: DIS.031, subject: "A train/test seal is enforced at the query/data layer, never by agent instruction alone", status: "RATIFIED (native, 2026-07-22). DISCHARGED -- fix built (PR #709), independently verified twice, and PROVEN in production by the clean re-run's own live anti-gaming pass."}
next_action: "Native/Binder decision required on CR-127 (B-2's real architecture gap): repair update_calibration()/phala_anchors's schema mismatch to wire a genuine LEL-event -> calibration pipeline, OR build a new migration for whatever mimamsa_outcome_record was meant to be. B-2/B-3 stay blocked until that ruling. B-1 itself is DONE and requires no further action -- its honest NO_WINNER stands."
```
