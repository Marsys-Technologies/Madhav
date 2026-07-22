---
artifact: STATE_D4B
type: WAVE STATE LEDGER (protocol §6.1)
wave: D-4b — Calibration Ignition + Grand Bakeoff
updated_at: 2026-07-22T22:45:00Z
supersedes: STATE_D4B.md as merged by PR #703 (2026-07-22T13:57:10Z, `wave/D-4b/B6-real-close`) —
  that version is preserved in git history, not deleted; this file replaces it as the current
  record.
---

```yaml
wave: D-4b
lifecycle_step: 6  # B-lanes IN PROGRESS. B-4/B-5 merged. B-1's original two defects (F-1/F-2) are
                    # both FIXED and merged. The FIRST chunked B-1 re-run attempt crashed with zero
                    # committed progress (infrastructure stall on the manifest step) and was
                    # correctly refused-not-fabricated by two downstream batch dispatches. The
                    # manifest + batch-runner harness were then committed DIRECTLY (not via agent
                    # dispatch) and independently verified before any batch ran. The SECOND
                    # attempt ran all 3 batches + assembly to completion — but the final
                    # anti-gaming verifier found the run had scored the SEALED TEST SPLIT
                    # (events >= 2020-01-01) across all 14 contenders. Per native ruling
                    # (sole-halt-condition disposition), that entire run is QUARANTINED — every
                    # score, delta, and its DR-12 NO_WINNER call are VOID, cited nowhere. Root
                    # cause registered as DR-20 (seal enforcement must be structural, not
                    # instruction-only); fix registered as CR-123. B-2/B-3 correctly SKIPPED
                    # throughout (hard-gated on a merged B-1, which has never existed).
                    # current_wave stays D-4b (OPEN) on CLAUDECODE_BRIEF.md.
brief_bound: true
mode_this_pass: GATED  # explicitly not mode=FULL. The mode=FULL three-point baseline diff
  # (BRIEF_D4B §1 B-6 item 4) has still not been run — no pass has reached it, since B-1 has never
  # produced a legitimate, merged result.
lanes:
  - {lane: B-1 (original 5-contender), branch: wave/D-4b/B1-bakeoff, status: merged, pr: 687, result: "BLOCKED — 0 contenders scored. Unchanged."}
  - {lane: B-1 (narrowed, pre-fix), branch: wave/D-4b/B1-bakeoff-narrowed, status: merged, pr: 694, result: "31-TRAIN-event run predating F-1/F-2. BLOCKED-ON-DEFECT. VOID, superseded-pending-re-run. Unchanged."}
  - {lane: F-1 (fix), branch: wave/D-4b/F1-resonance-map, status: merged, pr: 699, merged_at: "2026-07-22T11:07:19Z", result: "gochara_resonance_map event_class mapping fixed. NP-D4B-006 deviation + retroactive-verifier mitigation, DISCHARGED (Phase 4b retroVerify pass, fresh-context ACCEPT). Unchanged since prior pass."}
  - {lane: F-2 (fix), branch: wave/D-4b/F2-curve-controls, status: merged, pr: 697, merged_at: "2026-07-22T07:03:12Z", result: "circularShiftCurve() wraparound re-sort fixed. Confirmed genuinely fixed by BOTH B-1 chunked-re-run attempts (zero negative CRPS observed across all scored pairs in both). Unchanged."}
  - {lane: DR-17 grading module (salvage), branch: wave/D-4b/dr17-grading, status: merged, pr: 704, result: "Peak/sub_peak/elevated/neutral/contra grading, NP-D4B-001 weights. Salvaged from a crashed B-1 attempt's uncommitted WIP, independently verified (23/23 tests, tsc clean) before commit. Unchanged."}
  - {lane: "B-1 run manifest + batch-runner harness", branch: wave/D-4b/B1-full-rerun, status: merged_component, result: "B1_RUN_MANIFEST_v1_0.json (references the FROZEN packet by git blob sha, not a re-transcription) + b1_batch_artifact_io.ts (idempotent batch I/O, manifest-hash consistency check) — committed DIRECTLY by the orchestrating session after the manifest-build AGENT dispatch silently failed to commit despite returning result text (same infrastructure-stall category CR-122 documents). Verified before commit: 8/8 unit tests, tsc clean. This component is sound and reusable; it is the SCORING that ran on top of it which breached the seal (see below) — the manifest/harness themselves did not."}
  - {lane: "B-1 full re-run attempt #1", branch: wave/D-4b/B1-full-rerun, status: crashed_zero_progress, result: "Manifest-build agent's connection dropped mid-response; result text was returned but no commit ever landed. Two downstream batch-build dispatches (batch1, batch2) both independently checked live repo state and correctly REFUSED to fabricate scores against a manifest that did not exist — see this branch's own preserved BATCH-2-BLOCKED commit (061d4ace). No fabrication occurred; B-6 (PR #703) correctly closed GATED on this state."}
  - {lane: "B-1 full re-run attempt #2 (chunked)", branch: wave/D-4b/B1-full-rerun, status: QUARANTINED, result: "All 3 checkpointed batches ran to completion and were each independently verified ACCEPT (manifest-hash match, live re-derivation of a sampled event, zero negative CRPS spot-check). Assembly completed: manifest-hash consistency confirmed across all 3 batches, DR-12 adjudicated NO_WINNER (pratyantar_lord skill -0.1557, only adequate-coverage contender; all PERMISSION contenders n=3, too thin). The FINAL anti-gaming verifier — the sixth of six required confirmations — found the run had scored the sealed test split: pratyantar_lord scored 20 post-2020 events; every PERMISSION contender + the ensemble scored a 2025 marriage event. Root cause: one batch-build agent, resolving a perceived conflict between its dispatch instruction and the manifest's full-event-set framing, found and cited stale REPORT_D4B.md text characterizing B-1 scoring as a 'gate-runner exception' to the seal — an interpretation-based bypass, proving instruction-only enforcement is not a seal. Merge agent correctly DECLINED on the verdict. Never reached main, B-2, or B-3. QUARANTINED by native ruling: every score/delta/adjudication from this run is VOID, cited nowhere, branch stays permanently unmerged as incident evidence (QUARANTINE_B1_FULL_RERUN_v1_0.md). Full record: NP-D4B-007, DR-20 (DIS.031), CR-123."}
  - {lane: B-2, branch: none, status: skipped, reason: "hard-gated on a merged, legitimate B-1 result, which has never existed (attempt #1 crashed clean, attempt #2 quarantined). Never dispatched."}
  - {lane: B-3, branch: none, status: skipped, reason: "hard-gated on B-2. Never dispatched."}
  - {lane: B-4, branch: wave/D-4b/B4-remedy-join, status: merged, pr: 689, result: "bo_upaya populated. Unchanged."}
  - {lane: B-5, branch: wave/D-4b/B5-retrodiction, status: merged, pr: 688, result: "mechanism_retrodiction_get live, CONFIRMATION-ONLY. Unchanged."}
  - {lane: permission-bridge, branch: wave/D-4b/permission-bridge, status: merged, pr: 693, result: "PERMISSION curve HTTP route + 13-contender bridge + bind-time assertion. CR-120/121 landed. Unchanged."}
  - {lane: ledger-hygiene, branch: wave/D-4b/ledger-hygiene, status: merged, pr: 690, result: "NP-D4B-004/005. Unchanged."}
  - {lane: ledger-f1-deviation, branch: wave/D-4b/ledger-f1-deviation, status: merged, pr: 701, result: "NP-D4B-006. Unchanged."}
  - {lane: "B-6 (PR #695 pass)", branch: wave/D-4b/B6-close, status: merged, pr: 695, result: "First GATED close. Superseded, preserved in history."}
  - {lane: "B-6 (PR #703 pass)", branch: wave/D-4b/B6-real-close, status: merged, pr: 703, result: "Second GATED close, correctly found B-1 attempt #1's crash and zero fabrication. Superseded, preserved in history."}
  - {lane: "B-6 (PR #707, this pass's predecessor)", branch: wave/D-4b/B6-real-close-3, status: closed_stale_not_merged, result: "Written between B-1's assembly completing and the final anti-gaming verifier's REJECT landing — cited the now-VOID NO_WINNER result as legitimate. CLOSED, never merged, superseded by this pass before landing anything incorrect on main."}
  - {lane: "B-6 (this pass)", branch: wave/D-4b/B6-real-close-4, status: in_progress_gated, result: "Authored directly by the orchestrating session (not dispatched, given the precision required after PR #707's staleness) to guarantee accuracy. Full record: REPORT_D4B.md (this pass's version)."}
adjudications:
  - {dr: DR-12, dis: DIS.025, subject: "D-4 peak-model adjudication hook", status: "RATIFIED (native, 2026-07-17) but NOT YET DISCHARGED — B-1 has still not produced a legitimate scored comparison to adjudicate. The quarantined run's NO_WINNER call does not discharge this."}
  - {dr: DR-19, dis: DIS.030, subject: "An open is a repo state, not a message", status: "RATIFIED (native, 2026-07-21). Exercised repeatedly this campaign (B-4/B-5 original refusals; multiple batch-dispatch refusals this pass) — holding."}
  - {dr: DR-20, dis: DIS.031, subject: "A train/test seal is enforced at the query/data layer, never by agent instruction alone", status: "RATIFIED (native, 2026-07-22, sole-halt-condition disposition). NOT YET DISCHARGED — the structural fix (packet-construction-time filtering, harness-level hard exclusion, gate-blocking assertion at every verification altitude) has not yet been built. This is the wave's next lane."}
next_action: "Fix lane (Opus-verified, not a scoring change): implement DR-20's structural seal (packet-construction filtering + harness-level hard exclusion + gate-blocking assertion at per-batch/assembly/final-anti-gaming altitudes). Then ONE clean, chunked/checkpointed B-1 re-run, training-split only, on the fixed harness. Pre-committed outcome: a genuine NO_WINNER on clean data closes B-1 honestly — the campaign does not chase a champion."
```
