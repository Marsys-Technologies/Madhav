---
artifact: PROMISE_LEDGER_D4B
type: PROMISE-LEDGER CROSS-CHECK (CONDUCTOR_PROTOCOL §4 execution discipline — "every §1
  commitment → an executable assertion row, no ledger row → no bind") — B-6 REAL close pass #4
wave: D-4b — Calibration Ignition + Grand Bakeoff
version: 4.0 — supersedes v2.0 (merged by PR #703, 2026-07-22T13:57:10Z, `wave/D-4b/B6-real-close`),
  which itself superseded the uncommitted v1.0 draft from an earlier interrupted attempt (never
  merged) and the version merged by PR #695. All prior versions preserved in git history at their
  own merge commits / that pass's worktree. Every row below is re-derived fresh against
  `origin/main` at `2df42b61` (this pass's fetch) plus the unmerged `wave/D-4b/B1-full-rerun` @
  `0aa69c06`, not copied from any prior version without independent re-citation.
status: OPEN — GATED. Cross-checks BRIEF_D4B.md §1 (every lane's stated commitments) against live,
  verified evidence. No row is marked MET without a citable artifact or a live query/`gh` result
  quoted in this pass. Wave stays OPEN — see REPORT_D4B.md §0.
this_pass: 2026-07-22, wave/D-4b/B6-real-close-3, mode=GATED
authored_by: Claude Code (Sonnet 5), B-6 REAL close pass #4
---

# PROMISE_LEDGER_D4B — every BRIEF_D4B.md §1 commitment, cross-checked against live evidence

Legend: **MET** (evidence-backed, live-verified) · **PARTIAL** (some sub-commitments met, named) ·
**NOT MET** (attempted, evidence says no) · **BLOCKED** (cannot be attempted yet — hard-gated on
an unmet upstream commitment, not itself a failure) · **NOT YET REACHED** (correctly never
dispatched, per its own gating).

## B-1 — Grand bakeoff (BRIEF_D4B §1 B-1)

| # | Commitment (verbatim substance) | Status | Evidence |
|---|---|---|---|
| 1 | Score FULL contender set under ONE identical harness (midpoint-triangle, pratyantar-lord, transit-kernel, 12 D-5 PERMISSION standalones, hierarchical ENSEMBLE) | **NOT MET, unchanged** | `midpointTriangleModel()`/`transitKernelModel()` remain `NotImplementedModelError` stubs, registered NOT-EVALUABLE (CR-120/CR-121, `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` v3.10). The unmerged `wave/D-4b/B1-full-rerun` @ `0aa69c06` scored the other 14 named contenders (pratyantar_lord + 12 PERMISSION + ensemble) — the fullest run to date, superseding PR #694's NARROWED run — but is not on `main`, and midpoint-triangle/transit-kernel are still not scored under any run. |
| 2 | Identical everything: same event set, same DR-13 scoring semantics, same coverage span, thresholds, DR-15(c) controls | **BOTH NAMED DEFECTS FIXED AND NOW GENUINELY EXERCISED — BUT ON AN UNMERGED BRANCH** | F-1 (PR #699) and F-2 (PR #697) are both merged to `main`, unchanged since the PR #703 pass. **DELTA THIS PASS:** `wave/D-4b/B1-full-rerun` @ `0aa69c06` (pushed to `origin`, zero PR ever opened — `gh pr list --head wave/D-4b/B1-full-rerun --state all` empty, reconfirmed this pass) consumed both fixes across the full 54-of-56-event corpus and 14 contenders. Manifest-hash consistency independently re-verified this pass (`checkManifestHashConsistency()`, imported not reimplemented): `consistent: true`. `negative_crps_check.total_negative_crps_found` sums to 0 across all 3 committed batches (F-2's fix holds at full scale, per the ASSEMBLY_REPORT, re-read this pass). The exercise is real; it is simply not merged. |
| 3 | Pre-registered before first scoring run (packet committed) | **MET (for the narrowed run and the full re-run alike; the full re-run has not been pre-registered as its OWN fresh packet version)** | `D4B_PREREGISTRATION_PACKET_v1_0.md` v1.2, `status: FROZEN`, unchanged this pass (grep, no new commit). The full re-run consumed the same FROZEN v1.2 packet (per the ASSEMBLY_REPORT's own provenance section) rather than bumping to a distinct version for the re-run itself — worth a native note at merge review, not itself a defect this pass adjudicates. |
| 4 | CRPS primary (DR-15(b)); hit-rate retained as legacy secondary | **NOW COMPUTED ON A DEFECT-REPAIRED, FULL-CORPUS RUN — STILL UNMERGED** | `B1_FULLRERUN_ASSEMBLED_SUMMARY_v1_0.json` reports CRPS skill as primary per contender (`pratyantar_lord`: −0.1557 vs control, n=54) with hit-rate as secondary, exactly per this commitment's shape — re-read live this pass. This supersedes PR #694's NARROWED, pre-fix numbers, but is not part of the campaign's certified record until merged. |
| 5 | Per-model per-event table persisted as first-class committed artifact | **MET, on the unmerged branch** | `bakeoff_results/B1_FULLRERUN_ASSEMBLED_PER_EVENT_v1_0.json` (234KB, all 14 contenders × their assigned events, including honestly-marked `skipped: "unresolved_event_class"` rows) — committed to `wave/D-4b/B1-full-rerun`, verified present this pass. Not yet on `main`. |
| 6 | No-winner branch pre-committed, no forced champion ever | **HELD, and now genuinely EXERCISED on the unmerged branch** | `B1_FULLRERUN_ASSEMBLED_SUMMARY_v1_0.json`'s `verdict` field reads `"NO_WINNER"` (re-read live this pass). The ASSEMBLY_REPORT invokes `BRIEF_D4B.md`'s no-winner branch verbatim and is explicit it "does not name a champion." No champion is fabricated anywhere in the repo, merged or unmerged. |
| 7 | DR-12 adjudicated HERE (peak-model selection doctrine) | **DISCHARGE NOW EXISTS, UNMERGED — `DISAGREEMENT_REGISTER_v1_0.md` STILL STALE** | DIS.025 still literally reads "RATIFIED (native, 2026-07-17) but NOT YET DISCHARGED" (grep, this pass, unchanged text). The unmerged ASSEMBLY session applied that already-ratified DR-12 doctrine to real scored data and reached NO_WINNER — a genuine discharge-by-application — but it is not reflected in the register and not on `main`. This pass does not edit DIS.025 (a register-maintenance action for the merge, not for a GATED report). |
| 8 | Anti-gaming verifier on the whole battery | **NOT YET REACHED, and a narrower gap now visible** | The three underlying batches each carry an individually-reported verifier ACCEPT receipt (per the ASSEMBLY_REPORT). The ASSEMBLY step itself (concatenation + DR-12 discharge) has no independent verifier pass cited in its own report — flagged this pass (REPORT_D4B.md §2) as a precondition for the eventual merge PR, not a defect in the batches themselves. No formal anti-gaming pass has run against any of it. |

**What is new since the PR #703 pass, named plainly:** the B-1 full re-run — which the PR #703
pass found did not exist beyond an uncommitted `dr17_grading.ts` scaffold — has since been
**completed, assembled, and pushed to `origin`**: 14 contenders scored across 54 events,
manifest-hash-consistent, DR-12 discharged `NO_WINNER` per the pre-committed branch. **It has never
been opened as a pull request.** `b1.merged = false`, independently reproduced this pass. The
wave's blocker has narrowed a third time: from "two known defects" (PR #695 pass), to "the fixes
exist but no re-run has happened" (PR #703 pass), to "the re-run exists, is complete and honest, but
has never entered review or merged" (this pass).

## B-2 — One-shot backfill (BRIEF_D4B §1 B-2)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Hard-gated on B-1's adjudication receipt | **CORRECTLY HELD — the unmerged B-1 result does not satisfy this gate** | No B-2 branch/worktree/PR exists — `gh pr list --state all` this pass shows no `B-2`/`backfill` head ref. B-1's ASSEMBLY, though complete and honest, is not a MERGED receipt (§B-1 row 2/6 above), so B-2 correctly continues to hold. |
| 2 | Scores all 57 LEL events, batch-writes outcome rows, flips n_observations 0→~40/chart | **NOT MET — correctly not attempted** | Live query this pass: `SELECT count(*), count(*) FILTER (WHERE n_observations > 0), max(n_observations) FROM mimamsa_multipliers WHERE chart_id='482012f1-…'` → **9 rows total, 0 rows with `n_observations > 0`, max = 0**. Identical to both prior passes' finding — no drift, structural mode unchanged. |
| 3 | Shrinkage honesty; structural-mode exit criterion | **N/A — not reached** | No calibration has run to test this criterion against. |

## B-3 — Hierarchical calibration (BRIEF_D4B §1 B-3)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Event-class-level weights, chart-level shrunk; every multiplier carries n_observations + control delta + calibration_state | **NOT MET — correctly not attempted** | Same live query as B-2 above: all 9 `mimamsa_multipliers` rows for 482012f1 at `n_observations = 0`. No B-3 branch exists. |
| 2 | Residual-pair mining (marriage specimen, chara_karaka vs guru_shani_double_transit) | **NOT MET — carried, not closed; new supporting evidence exists unmerged** | `ka_gochara_sweep` materialization for 482012f1 is still 165/300 substeps (55%), `asset_throughput.state='error'`, `last_built_at=2026-07-21T22:25:23Z` — live-requeried this pass, byte-identical to both prior passes' finding. The unmerged `wave/D-4b/B1-full-rerun` run's ASSEMBLY_REPORT §5 confirms the marriage event (`EVT.2013.12.11.01`) is one of only 3 events resolving to a populated `event_class`, adding context but not itself B-3's own formal mining, which still requires a fully-materialized sweep AND a merged B-1 receipt — neither exists. |

## B-4 — Remedy-leverage join (BRIEF_D4B §1 B-4)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | `bo_upaya` populated via leverage_index × sādhanā history × dasha runway | **MET** | PR #689, merged 2026-07-21T19:31:39Z — unchanged, not touched this pass. |
| 2 | Wealth resonances ≠ 0; `leverage_index` subject=venus/VEN identical | **MET (carried, not re-verified live this pass)** | Confirmed live at the PR #695 pass (5 rows, `subject_alias_resolved` VEN). Not re-queried this pass — no B-4-touching change has landed since. |
| 3 | Closes carried `leverage_index` `subject=venus` false-empty item | **MET** | Same evidence as above. |

## B-5 — mechanism_retrodiction surface (BRIEF_D4B §1 B-5)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | LEL events joined to mechanism, served as CONFIRMATION only, never as prediction input | **MET** | PR #688, merged 2026-07-21T19:03:42Z — unchanged, not touched this pass. |

## B-6 — Campaign close (BRIEF_D4B §1 B-6) — this lane's own commitments

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Parked-items review | **CARRIED, spot-checked this pass, delta named** | `REPORT_D4B.md` (PR #695) §2 performed the full review; PR #703's own §2 spot-checked the F-1/F-2 delta. This pass's spot-check (REPORT_D4B.md §3) is the B-1 ASSEMBLY-but-unmerged delta plus the new CR-122 registration gap. |
| 2 | DR ratification sweep (DR-6 through DR-18 + NP-D4B ledger) | **CARRIED, re-spot-checked this pass** | `DISAGREEMENT_REGISTER_v1_0.md` grep this pass: highest entry still `DIS.030`; DR-6/7/8 (DIS.019–021) still queued; DR-17/18 still lack a formal DIS row; DIS.025 (DR-12) still stale relative to the unmerged discharge. NATIVE_PROXY_LEDGER_D4B.md's addendum (appended this pass) folds in the delta against NP-D4B-001/004. |
| 3 | Register final sweep | **CARRIED, spot-checked this pass** | `CAPABILITY_MANIFEST.json`'s `generated_at` unchanged at `2026-07-22T06:50:04.573Z` since the PR #703 pass. `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`: CR-120/121 unchanged; CR-122 named in a commit message but not yet a register row (new finding this pass). |
| 4 | Master regression suite becomes the standing per-release regression suite — confirm actually wired | **NOT ACTIONED — mode=FULL item, correctly deferred** | This session's dispatch is mode=GATED; this remains a named open commitment, not silently dropped, same as both prior passes. |
| 5 | Three-point baseline diff (pre-D-2 → post-D-2 → post-campaign, BASELINE_WEALTH_READING_PRE_D2 §4) | **NOT ACTIONED — mode=FULL item, correctly deferred** | Same as above; unchanged since the PR #695 pass — no pass to date has run this. |
| 6 | Standing live loop declared OPEN | **NOT YET DECLARED — conditioned on a real close** | Unchanged — this is a campaign-close action, and the campaign is not closing this pass. |

## Summary

**What changed since PR #703's GATED pass:** the B-1 full re-run — which that pass found did not
exist beyond an uncommitted `dr17_grading.ts` scaffold — has since been **completed, assembled, and
pushed to `origin`** (`wave/D-4b/B1-full-rerun` @ `0aa69c06`, six new commits): 14 contenders scored
across the full 54-of-56-event corpus, manifest-hash-consistent (independently re-verified this
pass), DR-12 discharged `NO_WINNER` per the pre-committed no-winner branch. `pratyantar_lord` (n=54,
the only adequately-sampled contender) scored CRPS skill −0.1557 vs its shuffled-birth control — no
contender with a meaningful sample beats its control. **It has never been opened as a pull request.**

**What did NOT change:** `mimamsa_multipliers` is still at 0 observations for every one of its 9
rows (live-requeried this pass, byte-identical to both prior passes). `ka_gochara_sweep`
materialization is still 165/300 (55%), byte-identical. B-2/B-3 remain correctly un-dispatched. B-4/
B-5 are untouched and still MET.

**Net effect on the wave's blocker:** the blocker has narrowed a third time. PR #695 pass: "two
known defects block a trustworthy B-1 result." PR #703 pass: "both fixes are on `main`, unexercised
— no B-1 re-run exists." This pass: **the re-run exists, is complete and honest, but has never been
merged** — `b1.merged = false`, independently reproduced. Per this session's own dispatch terms,
this is exactly the condition that forces GATED rather than FULL close: a genuine merge failure, not
a red/no-winner result on a merged branch. B-2 and B-3 remain correctly `skipped` — hard-gated on a
merged receipt that does not yet exist. **No commitment in this ledger is marked MET without a
citable PR, commit, or live query result named in this document.**
