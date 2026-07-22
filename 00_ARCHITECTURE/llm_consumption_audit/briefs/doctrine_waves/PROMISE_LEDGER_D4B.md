---
artifact: PROMISE_LEDGER_D4B
type: PROMISE-LEDGER CROSS-CHECK (CONDUCTOR_PROTOCOL §4 execution discipline — "every §1
  commitment → an executable assertion row, no ledger row → no bind") — B-6 REAL close pass
wave: D-4b — Calibration Ignition + Grand Bakeoff
version: 2.0 — supersedes the uncommitted v1.0 draft left in this worktree by an earlier,
  interrupted attempt at this same pass (written when the worktree was 12 commits behind current
  `origin/main` and F-1/PR #699 was still open). That draft's central claim — "F-1 has a
  green-CI, zero-review, unmerged PR (#699) open against main" — is now STALE: PR #699 merged
  2026-07-22T11:07:19Z, confirmed via `gh pr list` this pass. Every row below is re-derived fresh
  against `origin/main` at `0d607d2c` (this pass's fetch), not copied from the stale draft.
status: OPEN — GATED. Cross-checks BRIEF_D4B.md §1 (every lane's stated commitments) against live,
  verified evidence. No row is marked MET without a citable artifact or a live query/`gh` result
  quoted in this pass. Wave stays OPEN — see REPORT_D4B.md §0.
this_pass: 2026-07-22, wave/D-4b/B6-real-close, mode=GATED
authored_by: Claude Code (Sonnet 5), B-6 REAL close pass
---

# PROMISE_LEDGER_D4B — every BRIEF_D4B.md §1 commitment, cross-checked against live evidence

Legend: **MET** (evidence-backed, live-verified) · **PARTIAL** (some sub-commitments met, named) ·
**NOT MET** (attempted, evidence says no) · **BLOCKED** (cannot be attempted yet — hard-gated on
an unmet upstream commitment, not itself a failure) · **NOT YET REACHED** (correctly never
dispatched, per its own gating).

## B-1 — Grand bakeoff (BRIEF_D4B §1 B-1)

| # | Commitment (verbatim substance) | Status | Evidence |
|---|---|---|---|
| 1 | Score FULL contender set under ONE identical harness (midpoint-triangle, pratyantar-lord, transit-kernel, 12 D-5 PERMISSION standalones, hierarchical ENSEMBLE) | **NOT MET** | `midpointTriangleModel()`/`transitKernelModel()` remain `NotImplementedModelError` stubs — reconfirmed live this pass via `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-120/CR-121 (added 2026-07-22, D-4b permission-bridge lane): both dispositioned **NOT-EVALUABLE** (coverage gap, not a retirement); midpoint-triangle's mandatory-baseline role formally reassigned to the shuffled-birth negative control (native ruling, this campaign); transit-kernel's D-3 RED result stands `NOT-RE-EVALUATED-ON-REPAIRED-SUBSTRATE`, deferred to a named D-6-era "2.0 sweep engine" candidate. The only run to date (PR #694, NARROWED, merged) scored 14 of the named contenders (pratyantar_lord + 12 PERMISSION + ensemble), not the full named set. |
| 2 | Identical everything: same event set, same DR-13 scoring semantics, same coverage span, thresholds, DR-15(c) controls | **BOTH NAMED DEFECTS NOW FIXED ON MAIN — NEITHER FIX HAS BEEN EXERCISED IN A FRESH RUN** | (a) `gochara_resonance_map` `event_class` mapping gap: fixed by F-1, **PR #699, MERGED 2026-07-22T11:07:19Z** (`gh pr list` this pass). (b) `curve_controls.ts` `circularShiftCurve()` wraparound non-resort: fixed by F-2, **PR #697, MERGED 2026-07-22T07:03:12Z** (`gh pr list` this pass, unchanged from prior pass). Both fixes are live on `main` as of this pass. **No B-1 re-run has consumed either fix**: `gh pr list --head wave/D-4b/B1-full-rerun` returns empty (no PR opened, merged or otherwise); the local worktree `.claude/worktrees/wave-D-4b-B1-full-rerun` (base commit `25e0dc4a`) carries only uncommitted WIP — a `dr17_grading.ts` implementation + its test file, and an unrelated `pnpm-lock.yaml` diff — no scoring run, no results file, no preregistration-packet version bump. |
| 3 | Pre-registered before first scoring run (packet committed) | **MET (for the narrowed run; not yet re-done for a full re-run)** | `D4B_PREREGISTRATION_PACKET_v1_0.md` v1.2, `status: FROZEN`, committed 2026-07-21 — unchanged this pass, not re-verified live (no packet-touching commit since the prior pass). A full re-run consuming F-1+F-2 has not itself been pre-registered as a fresh packet version. |
| 4 | CRPS primary (DR-15(b)); hit-rate retained as legacy secondary | **STILL VOID for the only run that exists** | The one committed scoring run (`B1_NARROWED_TRAIN_SUMMARY_v1_0.json`, PR #694) predates F-1 and F-2 both — its CRPS numbers remain invalidated by defect (b) exactly as the prior pass found; nothing has changed this fact, because no new run has happened. |
| 5 | Per-model per-event table persisted as first-class committed artifact | **MET (for the narrowed, defect-affected run only)** | Same artifacts as prior pass (`bakeoff_results/B1_NARROWED_TRAIN_PER_EVENT_v1_0.json`, `B1_NARROWED_TRAIN_SUMMARY_v1_0.json`, PR #694) — unchanged, still superseded-pending-re-run, not deleted. |
| 6 | No-winner branch pre-committed, no forced champion ever | **HELD, still not exercised** | No champion or no-winner verdict exists anywhere in the repo for this wave — reconfirmed via `gh pr list --state all` (no merged/open PR claims a B-1 disposition beyond PR #694's own BLOCKED-ON-DEFECT framing) and `git log` on `bakeoff_results/`. The discipline continues to hold: both known defects are now fixed, and still no champion has been fabricated to close the wave early. |
| 7 | DR-12 adjudicated HERE (peak-model selection doctrine) | **BLOCKED, unchanged** | `DISAGREEMENT_REGISTER_v1_0.md` DIS.025: "RATIFIED (native, 2026-07-17) but NOT YET DISCHARGED" — reconfirmed live this pass (grep, no new DIS row past DIS.030). Discharge requires a certified scored comparison, which still does not exist. |
| 8 | Anti-gaming verifier on the whole battery | **NOT YET REACHED** | No certified battery exists yet to run an anti-gaming pass against — unchanged. |

**What is new since the PR #695 pass, named plainly:** F-1 is now merged (it was open at that
pass). That closes defect (a). Defect (b) (F-2) was already merged at that pass. **Both defects
that blocked B-1 are now fixed on `main` — but the fix has not yet been exercised**: no B-1 run has
happened against the repaired substrate. The wave's blocker has moved from "two known defects" to
"the fixes exist but the re-run that would certify a champion or no-winner has not been done." A
`dr17_grading.ts` scaffold sits uncommitted in a WIP worktree, suggesting a re-run was started but
not carried to a scored, committed result this pass.

## B-2 — One-shot backfill (BRIEF_D4B §1 B-2)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Hard-gated on B-1's adjudication receipt | **CORRECTLY HELD** | No B-2 branch/worktree/PR exists — `gh pr list --state all` this pass shows no `B-2`/`backfill` head ref beyond what was already on record. |
| 2 | Scores all 57 LEL events, batch-writes outcome rows, flips n_observations 0→~40/chart | **NOT MET — correctly not attempted** | Live query this pass: `SELECT count(*), count(*) FILTER (WHERE n_observations > 0), max(n_observations) FROM mimamsa_multipliers WHERE chart_id='482012f1-…'` → **9 rows total, 0 rows with `n_observations > 0`, max = 0**. Identical to the prior pass's finding — no drift, structural mode unchanged. |
| 3 | Shrinkage honesty; structural-mode exit criterion | **N/A — not reached** | No calibration has run to test this criterion against. |

## B-3 — Hierarchical calibration (BRIEF_D4B §1 B-3)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Event-class-level weights, chart-level shrunk; every multiplier carries n_observations + control delta + calibration_state | **NOT MET — correctly not attempted** | Same live query as B-2 above: all 9 `mimamsa_multipliers` rows for 482012f1 at `n_observations = 0`. No B-3 branch exists. |
| 2 | Residual-pair mining (marriage specimen, chara_karaka vs guru_shani_double_transit) | **NOT MET — carried, not closed** | Unchanged: `ka_gochara_sweep` materialization for 482012f1 is still 165/300 substeps (55%), `asset_throughput.state='error'`, `last_built_at=2026-07-21T22:25:23Z` — live-requeried this pass, byte-identical to the prior pass's finding (no new dispatch has run since). B-3's formal mining against a fully-materialized sweep still cannot happen. |

## B-4 — Remedy-leverage join (BRIEF_D4B §1 B-4)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | `bo_upaya` populated via leverage_index × sādhanā history × dasha runway | **MET** | PR #689, merged 2026-07-21T19:31:39Z — unchanged, not touched this pass (no `bo_upaya`/`bodha_rm_dasha_windowed_prescriptions` file in this pass's diff). |
| 2 | Wealth resonances ≠ 0; `leverage_index` subject=venus/VEN identical | **MET (carried, not re-verified live this pass)** | Confirmed live in the prior GATED pass (5 rows, `subject_alias_resolved` VEN). Not re-queried this pass — no B-4-touching change has landed since (confirmed via `git log -- '*bo_upaya*' '*leverage*'` showing no new commits), so re-verification would be redundant DB load without new information. |
| 3 | Closes carried `leverage_index` `subject=venus` false-empty item | **MET** | Same evidence as above. |

## B-5 — mechanism_retrodiction surface (BRIEF_D4B §1 B-5)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | LEL events joined to mechanism, served as CONFIRMATION only, never as prediction input | **MET** | PR #688, merged 2026-07-21T19:03:42Z — unchanged, not touched this pass. |

## B-6 — Campaign close (BRIEF_D4B §1 B-6) — this lane's own commitments

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Parked-items review | **CARRIED FROM PRIOR PASS, spot-checked this pass, no drift** | `REPORT_D4B.md` (PR #695, prior version) §2 performed the full review. This pass spot-checked the two items most likely to have moved (B-1's defect status, CR-113/CR-114) and found no change beyond the F-1/F-2 merge delta itself, which is this pass's own headline. |
| 2 | DR ratification sweep (DR-6 through DR-18 + NP-D4B ledger) | **CARRIED FROM PRIOR PASS; re-spot-checked this pass** | `DISAGREEMENT_REGISTER_v1_0.md` grep this pass: highest entry is still `DIS.030`; DR-6/7/8 (DIS.019–021) still read `status: resolved ... native ratification queued at campaign close`; DR-17/18 still lack a formal DIS row (DIS.030's own note, unchanged). NP-D4B-006 (new since the prior pass, PR #701, merged) is folded into this pass's NATIVE_PROXY_LEDGER_D4B.md summary section below. |
| 3 | Register final sweep | **CARRIED FROM PRIOR PASS, spot-checked this pass** | `DISAGREEMENT_REGISTER_v1_0.md`, `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` unchanged in substance. `CAPABILITY_MANIFEST.json`'s `generated_at` has advanced to `2026-07-22T06:50:04.573Z` (was `2026-06-27T18:27:38Z` at the prior pass) — a regeneration has happened since, but no D-4b doctrine-wave artifact is a canonical_id the manifest tracks, so this is noted, not treated as drift against this wave. |
| 4 | Master regression suite becomes the standing per-release regression suite — confirm actually wired | **NOT ACTIONED — mode=FULL item, correctly deferred** | This session's dispatch is mode=GATED; this remains a named open commitment, not silently dropped. |
| 5 | Three-point baseline diff (pre-D-2 → post-D-2 → post-campaign, BASELINE_WEALTH_READING_PRE_D2 §4) | **NOT ACTIONED — mode=FULL item, correctly deferred** | Same as above; unchanged from the prior pass. |
| 6 | Standing live loop declared OPEN | **NOT YET DECLARED — conditioned on a real close** | Unchanged from the prior pass's reasoning — this is a campaign-close action, and the campaign is not closing this pass. |

## Summary

**What changed since PR #695's GATED pass:** F-1 (PR #699) merged 2026-07-22T11:07:19Z, closing
the resonance-map mapping defect. NP-D4B-006 (PR #701, merged) recorded the conductor-verified
deviation that got F-1 merged under agent-infrastructure duress, with a binding retroactive-
verification obligation — see NATIVE_PROXY_LEDGER_D4B.md's summary section, appended this pass,
for that obligation's discharge status. **Both of B-1's two named defects are now fixed on `main`.**

**What did NOT change:** no B-1 re-run exists — merged, open, or even committed to a branch beyond
an uncommitted `dr17_grading.ts` scaffold. B-2/B-3 remain correctly un-dispatched. `mimamsa_multipliers`
is still at 0 observations for every one of its 9 rows (live-requeried this pass). `ka_gochara_sweep`
materialization is still 165/300 (55%), byte-identical to the prior pass. B-4/B-5 are untouched and
still MET.

**Net effect on the wave's blocker:** the blocker has narrowed from "two known defects block a
trustworthy B-1 result" to "both fixes are on `main`, unexercised — B-1 has not been re-run to a
certified champion/no-winner disposition." This is still, by BRIEF_D4B §1 B-1's own no-forced-
champion rule and this session's own dispatch terms, a genuine blocker: **b1.merged = false**. B-2
and B-3 remain correctly `skipped` — hard-gated on a receipt that does not yet exist. **No
commitment in this ledger is marked MET without a citable PR, commit, or live query result named in
this document.**
