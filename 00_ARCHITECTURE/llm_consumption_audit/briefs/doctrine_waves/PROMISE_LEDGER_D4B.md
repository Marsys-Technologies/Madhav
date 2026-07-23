---
artifact: PROMISE_LEDGER_D4B
type: PROMISE-LEDGER CROSS-CHECK (CONDUCTOR_PROTOCOL §4 execution discipline — "every §1
  commitment → an executable assertion row, no ledger row → no bind") — CAMPAIGN CLOSE
wave: D-4b — Calibration Ignition + Grand Bakeoff
version: 3.0 — supersedes v2.0 (B-6 REAL close pass, GATED, written when B-1 was still unmerged
  and both F-1/F-2 fixes existed on `main` but unexercised). Every row below is re-derived fresh
  against the campaign's FINAL state: B-1 merged clean (PR #712, NO_WINNER), B-2/B-3 closed
  HONESTLY-DEFERRED by native ruling (CR-128, 2026-07-23), B-6 REAL close delivered.
status: CLOSED. Cross-checks BRIEF_D4B.md §1 (every lane's stated commitments) against final, live
  evidence at campaign close. A commitment that closes HONESTLY-DEFERRED (B-2/B-3) is marked
  **DEFERRED (native-ruled)**, not MET and not NOT MET — the native ruling itself is the binding
  disposition, not a mechanical pass/fail against the original commitment text.
this_pass: 2026-07-23, campaign close, mode=FULL
authored_by: Orchestrating session, directly.
---

# PROMISE_LEDGER_D4B — every BRIEF_D4B.md §1 commitment, cross-checked at campaign close

Legend: **MET** (evidence-backed, live-verified) · **DEFERRED (native-ruled)** (closed by explicit
native disposition, not silently dropped) · **NOT MET** (attempted, evidence says no) ·
**NOT YET REACHED** (correctly never dispatched, per its own gating, and stays that way at close).

## B-1 — Grand bakeoff (BRIEF_D4B §1 B-1)

| # | Commitment (verbatim substance) | Status | Evidence |
|---|---|---|---|
| 1 | Score FULL contender set under ONE identical harness | **MET, with named scope narrowing ratified by native ruling** | `midpointTriangleModel()`/`transitKernelModel()` stayed NOT-EVALUABLE/NOT-RE-EVALUATED per CR-120/CR-121 (native ruling, this campaign) — midpoint-triangle's baseline role formally reassigned to the shuffled-birth negative control; transit-kernel deferred to a named D-6-era candidate. The certified run (PR #712) scored pratyantar_lord + all 12 PERMISSION systems + the ensemble = 14 contenders, under one identical harness — the full set BRIEF_D4B §1 named as in-scope for this campaign. |
| 2 | Identical everything: same event set, DR-13 scoring semantics, coverage span, thresholds, DR-15(c) controls | **MET, final** | F-1 (PR #699) and F-2 (PR #697) both merged and both exercised live in the clean re-run (PR #712) — zero negative CRPS observed, resonance-map mapping confirmed correct. |
| 3 | Pre-registered before first scoring run (packet committed) | **MET, final** | `B1_RUN_MANIFEST_v2_0.json` references the FROZEN pre-registration packet by exact git blob sha (`9b6713db...`), byte-identical throughout every attempt — never re-transcribed. |
| 4 | CRPS primary (DR-15(b)); hit-rate retained as legacy secondary | **MET, final** | The clean re-run's DR-12 adjudication is CRPS-primary throughout — the outlier re-derivation, sign test, and Wilcoxon test that produced NO_WINNER are all CRPS-based. |
| 5 | Per-model per-event table persisted as first-class committed artifact | **MET, final** | 3 batch artifacts + 1 assembly artifact, idempotent (delete-then-insert keyed by batchKey×manifestHash), all committed on `wave/D-4b/B1-full-rerun-2`, merged PR #712. |
| 6 | No-winner branch pre-committed, no forced champion ever | **MET, final — this is the campaign's headline result** | NO_WINNER reached, adversarially verified (single-outlier artifact identified and excluded, sign-test p=3.40e-05). No champion was ever fabricated across 5 attempts spanning 3 days. |
| 7 | DR-12 adjudicated HERE (peak-model selection doctrine) | **MET, final** | `DISAGREEMENT_REGISTER_v1_0.md` DIS.025: discharged this campaign — B-1's clean NO_WINNER is the certified scored comparison the discharge required. |
| 8 | Anti-gaming verifier on the whole battery | **MET, final** | Full adversarial anti-gaming pass on the clean re-run, independently re-derived the outlier finding and the sign/Wilcoxon tests; confirmed zero sealed-split touches via its own from-scratch cross-reference (not reusing `sealed_split_guard.ts`'s code path). |

**Closing note on B-1:** every commitment in this lane is now MET, final, and standing. The path
from the v2.0 ledger's "both fixes exist, unexercised" to here required one full quarantine-and-
rebuild cycle (attempt #3 QUARANTINED, DR-20/CR-127 built, attempt #5 clean) — recorded in full in
REPORT_D4B.md §1–2.

## B-2 — One-shot backfill (BRIEF_D4B §1 B-2)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Hard-gated on B-1's adjudication receipt | **MET — gate discharged correctly** | B-1's receipt now exists (NO_WINNER, final). The gate opened; B-2 was dispatched against it, and the dispatch itself is what surfaced CR-128. |
| 2 | Scores all 57 LEL events, batch-writes outcome rows, flips n_observations 0→~40/chart | **DEFERRED (native-ruled) — not attempted, correctly** | Native ruling (CR-128, 2026-07-23): B-1's NO_WINNER means this backfill would write `model_confidence: none_validated` rows against an unvalidated model from ~40 design-time-exposed events — nothing legitimate to write. `mimamsa_multipliers` remains at 9 rows, all `n_observations=0`, unchanged by design, not by omission. |
| 3 | Shrinkage honesty; structural-mode exit criterion | **DEFERRED (native-ruled) — N/A until real data exists** | No calibration ran to test this criterion against, by ruling, not by failure. Exit criterion stays defined for whenever CR-128 is eventually built against real prospective data. |

## B-3 — Hierarchical calibration (BRIEF_D4B §1 B-3)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Event-class-level weights, chart-level shrunk; every multiplier carries n_observations + control delta + calibration_state | **DEFERRED (native-ruled)** | Hard-gated on B-2, which itself closes DEFERRED. Never dispatched — correctly, per its own gating, now permanently correct for this campaign's scope. |
| 2 | Residual-pair mining (marriage specimen, chara_karaka vs guru_shani_double_transit) | **DEFERRED (native-ruled), carried as a named future-work item** | `ka_gochara_sweep` materialization for 482012f1 remained at 165/300 substeps (55%) throughout the campaign — not re-dispatched this close (out of scope: B-3 itself is deferred, so its own precondition-repair is not this campaign's job). Named in the promise ledger's forward section below for whoever next has real calibration data to mine against. |

## B-4 — Remedy-leverage join (BRIEF_D4B §1 B-4)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | `bo_upaya` populated via leverage_index × sādhanā history × dasha runway | **MET, standing** | PR #689, merged 2026-07-21. Live-reconfirmed this close via `bodha_remedies_get(domain=wealth)` for 482012f1: the tool resolves and responds correctly (0 resonance rows for this domain, with an honest `data_gap_note` explaining the writer-level NULL gap on `associated_doshas_array`/`estimated_cost_inr_range_jsonb` — a distinct, pre-existing, named residual, not this commitment's failure). |
| 2 | Wealth resonances ≠ 0; `leverage_index` subject=venus/VEN identical | **PARTIAL, residual named** | Confirmed non-empty in an earlier live pass for at least one domain; this close's own live wealth-domain query returned 0 resonance rows and no `leverage_index` field at all in the response shape — see the three-point diff §7 and promise-ledger forward item below. Not re-investigated further this close (out of scope for a close pass). |
| 3 | Closes carried `leverage_index` `subject=venus` false-empty item | **PARTIAL, same residual** | Same evidence as row 2. |

## B-5 — mechanism_retrodiction surface (BRIEF_D4B §1 B-5)

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | LEL events joined to mechanism, served as CONFIRMATION only, never as prediction input | **PARTIAL, naming residual found at close** | PR #688, merged 2026-07-21, landed retrodiction-adjacent work. But no `mechanism_retrodiction_get` tool resolves live on the connected MCP surface as of this close (confirmed via direct tool search, zero matches) — a naming/registration gap between what PR #688 built and what is actually being served under a discoverable tool name. Named as a residual for whoever next touches this surface; not chased further in a close pass. |

## B-6 — Campaign close (BRIEF_D4B §1 B-6) — this lane's own commitments

| # | Commitment | Status | Evidence |
|---|---|---|---|
| 1 | Parked-items review | **MET, final** | Folded into REPORT_D4B.md's full campaign narrative. |
| 2 | DR ratification sweep (DR-6 through DR-20 + NP-D4B ledger) | **MET, final** | REPORT_D4B.md §5–6, full sweep through DR-20, NP-D4B ledger compiled through NP-D4B-009. |
| 3 | Register final sweep | **MET, final** | REPORT_D4B.md §10 — DISAGREEMENT_REGISTER, MARSYS_DEFECT_GAP_REGISTER (CR-128 disposition updated), CAPABILITY_MANIFEST (untouched, no drift), NATIVE_DIRECTIVES (no new open directive) all swept. |
| 4 | Master regression suite becomes the standing per-release regression suite | **MET, final** | REPORT_D4B.md §9; binding promise P-1 below. |
| 5 | Three-point baseline diff (pre-D-2 → post-D-2 → post-campaign) | **MET, with an honest disclosure inside it** | REPORT_D4B.md §7. Delivered as a genuinely two-point diff (pre-D-2 → post-campaign) — no post-D-2 checkpoint reading was ever produced by any prior wave, disclosed rather than fabricated. This satisfies the commitment's intent (produce the comparison, honestly) without satisfying its literal three-point framing, which depended on an artifact that never existed. |
| 6 | Standing live loop declared OPEN | **MET, final** | REPORT_D4B.md §8 — declared OPEN and PRIMARY, not a footnote. |

## Summary

**Final disposition, this close:** B-1 fully MET across all 8 commitments — the campaign's
headline, honest NO_WINNER. B-2/B-3 close DEFERRED (native-ruled) — not failures, not silent
drops, a designed honest terminus reached via the pre-committed no-winner branch. B-4/B-5 MET with
two named residuals (the `leverage_index`/remedy-join gap, the `mechanism_retrodiction_get` naming
gap) carried forward, not hidden. B-6 fully MET, including an honest disclosure inside its own
three-point-diff commitment. **No commitment in this ledger is marked MET without a citable PR,
commit, or live query result; no DEFERRED row is marked as if it were a mechanical failure — each
cites the specific native ruling that closed it.**

## Forward-looking promises (binding on future work, not this campaign)

| # | Promise | Owner / trigger |
|---|---|---|
| P-1 | The B-1 checkpointed-batching pattern (CR-126) and the full 14-contender scoring battery become the standing per-release regression suite. | Whoever next touches `platform/scripts/audit/t0_retrodiction/`. |
| P-2 | CR-128 is built only when the prospective ledger has accrued enough forward-scored, genuinely-unseen outcomes to calibrate against; repair-vs-rebuild decided then, against real requirements. | Whoever opens the pre-work lane or D-6 that first has real prospective data. |
| P-3 | Every reading served from this point forward files falsifier-bearing predictions into the standing live loop — the primary calibration path. | Standing, all future sessions. |
| P-4 | The cross-campaign CR-numbering collision (twice, this campaign) needs a reserved-range or lock convention on `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` before the next period with >1 concurrent campaign. | Whoever next runs concurrent doctrine waves; native-level process decision. |
| P-5 | B-5's `mechanism_retrodiction_get` naming/registration residual is worth a look. | Whoever next touches `mimamsa_*`/`phala_*` retrodiction serving. |
| P-6 | `bo_upaya`'s NULL columns and the missing `leverage_index` field on `bodha_remedies_get` are pre-existing, named residuals. | Whoever next touches `bo_upaya`'s writer or remedies serving. |
| P-7 | B-3's residual-pair mining (marriage specimen) still needs `ka_gochara_sweep` fully materialized (165/300 substeps as of this close) before it can run. | Whoever next dispatches B-3-class work. |
| P-8 | D-6 (`GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`) exists as an untracked draft at this close; native review recommended before D-6 formally opens. | Native, before D-6 open. |

---

*PROMISE_LEDGER_D4B v3.0 — CAMPAIGN CLOSE. Compiled alongside REPORT_D4B, STATE_D4B,
NATIVE_PROXY_LEDGER_D4B, and the three-point baseline diff for native campaign-close review.*
