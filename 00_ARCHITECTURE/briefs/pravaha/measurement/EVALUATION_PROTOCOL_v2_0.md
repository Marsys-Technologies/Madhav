---
artifact: EVALUATION_PROTOCOL
canonical_id: EVALUATION_PROTOCOL
version: "2.0"
status: PRE_DECLARED
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "EVALUATION_PROTOCOL_v1_0.md, v1_1.md, v1_2-DRAFT.md — all retained as disclosed history; v2.0 is the single consolidated protocol"
registry: "measurement/EVENT_REGISTRY_v2_0.md (the only event source for any v2.0 scoring)"
declared_before: "the v2.0 re-run of '3.0' and any '4.1'/'5.0' scoring"
amendment_disclosure: >
  Written after the '3.0' v1.0-protocol pass and after both design-spec reviews (Kimi K3,
  Astra/Codex) were dispositioned in design/RECONCILIATION_DESIGN_SPECS_v1_0.md. Consolidates
  v1.0 + v1.1 + the v1.2 draft and implements the native's B3.6 priority-6 items (Codex
  M-01…M-06, Kimi Q-M2/Q-M3). No '4.1'/'5.0' scoring occurs until the native reports the
  protocol review closed; the v2.0 re-run of '3.0' is a re-measurement of an already-served
  generation, not a candidate score.
deviation_history: >
  Retained in full: B4.3 scored '3.0' before the B4.2 protocol review closed (disclosed in
  BASELINE_3_0_v1_0.md and v1.1's header). The '3.0' measurement stands as a measurement taken
  under an unreviewed protocol; v2.0 re-runs it under this protocol from a pinned extract.
---

# Gochara evaluation protocol v2.0 — consolidated

## 1. Event source

The only event source is **EVENT_REGISTRY_v2_0.md** (built row-by-row from
LIFE_EVENT_LOG_v1_2.md, read-only). No event enters scoring except through the registry; any
registry change after a scoring pass is a versioned amendment naming what was seen. Registry
facts this protocol relies on: held-out 46 (27 timing-usable + 19 year-grain); dev 3
(calibration only); observation mask ends **2026-04-17**; scored horizon H = 1998-01-01 →
2026-04-17 = **10,334 days**.

Onset vs status (Codex M-01): only `point`/`interval` rows are scored. `status` rows
(EVT.CURRENT.01) are annotations, never dated events.

## 2. Class universe

Fixed 27-class universe (from the design specs' class list); a generation's rows map into it or
are reported `unmapped`. Class mappings with reasons live in the registry, not here. The frozen
adverse classes: bereavement, career_setback, chronic_onset, financial_deception, illness_acute,
parental_event, separation, surgery, major_loss.

## 3. Timezone and calendar conventions

- All event dates are **IST calendar dates** as logged in the LEL.
- Window timestamps stored in UTC follow the platform's 18:30-UTC (= 00:00 IST) day-anchor
  convention; a stored timestamp `T` represents the IST civil date `T + 5:30`. All scoring
  converts to IST dates before any comparison. (Codex M-04: stated, not assumed.)
- A generation whose coverage ends before 2026-04-17 is scored on the intersection and the
  shortfall is reported as coverage, never as absence of events.

## 4. Window identity, deduplication, ties

1. **Candidate identity:** a candidate window is the tuple (class, window_start, window_end,
   peak_date, generation) after conversion to IST dates.
2. **Dedup before counting:** overlapping or abutting windows of the same class within a
   generation are merged into one candidate **before** N (candidate count) is computed and
   before any ranking (Codex M-05). A plateau of 40 contiguous daily rows is one candidate.
3. **Ranking:** candidates of class c in event e's year are ranked by signed intensity
   (descending for gain classes; for adverse classes, most-adverse first). **Ties take the
   average rank** of the tied group (disclosed convention).
4. **Eligible misses stay in the ranking:** if no admitted window of class c contains e's date,
   e is retained in the T-rank median at the **worst-rank convention — percentile 100**
   (Codex M-03). Misses are also counted separately for T-cover; the two reports never silently
   drop the same event.

## 5. Timing error — single rule

One rule, no parallel formulations (steward item 4; v1.1's "misses ≤ 5 of 7" and "≥ 4 of 7
within 45 d" formulations are withdrawn):

- **grain exact:** error = |peak IST date of the highest-ranked containing window − event date|
  in days; 0 if peak = event date.
- **grain month:** event date = 15th of the month; error in days on the same scale.
- **grain interval [a,b]:** hit iff the containing window overlaps [a,b]; error = distance from
  peak to the nearest point of [a,b] (0 if peak ∈ [a,b]). (The grandfather row is the only
  interval event.)
- **Miss:** no containing window → error = **182 days** (capped miss value).
- **All errors are capped at 182 days**, so a 3-year miss and a 7-month miss are not averaged
  into a meaningless figure (Codex M-06). Alongside the capped median, the scorer reports
  separately: (a) the miss count, (b) the uncapped errors of the hits. The capped median is the
  endpoint; the separate reports are mandatory disclosure.

## 6. Endpoints (all co-primary, each necessary, none sufficient)

1. **T-cover:** of the 46 held-out events, the fraction with at least one admitted window of the
   event's class containing the event's date (month-grain: month; year-grain: year; interval:
   overlap) must be **≥ 31/46** — the v2.0 re-run figure of '3.0' on this identical registry
   (BASELINE_3_0_v2_0.md; the bar equals the served floor), and every
   miss must be named. Same tier policy for hits and for the burden below: an event either has
   a containing window or it does not, under one definition used identically everywhere
   (Kimi Q-M3).
2. **T-time (single rule):** capped-median timing error over the 5 exact-date held-out events
   (registry §2, exact cohort) **≤ 45 days**. Misses enter at 182 d per §5.
3. **T-rank:** over timing-usable held-out events with **N ≥ 3 candidate windows** of the
   event's class in the event's year (post-dedup), median rank percentile ≤ **25**. **Validity
   floor:** at least **floor(27/2)+1 = 14** of the 27 timing-usable events must reach N ≥ 3,
   else the generation is **rank-unproven**, which **blocks the flip** regardless of other
   endpoints. Worst-rank misses stay in the median per §4.4. Degenerate classes (§8) contribute
   no N to the floor.
4. **T-FP (per-class budgets — the chosen form, Codex M-02 arithmetic printed):** for each
   frozen adverse class c, the admitted day-fraction over that class's **negative days**
   (all horizon days not inside a containing-window hit of a true class-c event) must be
   ≤ **min(1, 3·n_c·90/H)** where n_c = held-out in-horizon events of class c, H = 10,334.
   Arithmetic (registry §5): n_c = 1 → 270/10,334 = **2.61 %**; n_c = 2 → **5.23 %**;
   n_c = 0 (major_loss) → single-event allowance **2.61 %** (a class the registry cannot
   falsify may not be blanket-claimed). Derivation: a true event justifies at most a ±45-day
   footprint (the T-time tolerance); the budget is 3× that density per event. The bar comes
   from event density, not from '3.0''s degenerate 99.87 % figure. Gain classes keep the
   two-horns rule: 0.5 % ≤ base rate ≤ 40 % of scored-horizon days.
5. **T-honesty:** every metric carries its coverage; a class with coverage < 50 % of the scored
   horizon is reported `unqualified`, not scored.

Failure on any co-primary endpoint is failure of the generation. D-FLIP additionally requires
the A5.7 engineering gates.

## 7. Controls

- **Negative days/years:** per class, every horizon day/year with no registry event of that
  class (LEL completeness disclosed as a limit).
- **Random controls:** **20 intervals per held-out event**, drawn uniformly from the scored
  horizon at the event's resolution, **seed = 482012**, **materialised**: the draw script and
  its output are committed beside the score file so the controls are reproducible byte-for-byte.
- **Placebo classes:** classes with zero registry events (e.g. major_loss) — scored against the
  single-event allowance, §6.4.
- **Annotation guard (Codex S-06):** only annotations verified in
  `measurement/LEL_CHART_STATE_RECONCILED_v1_0.md` may enter scoring; any unverified event-log
  annotation is **rejected** by the scorer, not downweighted.

## 8. Degeneracy tests (run on every generation before any endpoint; from v1.1 §B, unchanged)

1. **Era-boundary fingerprint:** ≥ 50 % of class pairs sharing identical window boundaries →
   generation flagged **class-indiscriminate**; T-rank void, flag printed atop the score file.
2. **Two-horns check:** class base rate > 95 % or < 0.5 % → class degenerate-high/-low; such
   classes count in T-cover and T-FP but never toward T-rank's N.

## 9. Procedure

1. Pin the scored rows to a file (read-only dump, sha256 recorded) before any counting.
2. Compute registry-derived counts first; any mismatch with the registry's §6 table is a scorer
   bug, not a registry amendment.
3. Score each generation once per protocol version, read-only, every figure with its predicate
   and the pinned extract's hash.
4. Dev-tier events are reported separately (calibration view), never in a median.
5. Aggregation: per class, then macro-averaged with equal class weights; missing values are
   reported as missing (never silently zero-filled); a class with no scored rows is `absent`.
6. A protocol change after a scoring pass is a versioned amendment naming what was seen.

## 10. Honest limits (retained)

Single chart; 27 timing-usable held-out events (5 exact-date): medians, not distributions; no
significance claim beyond the pre-declared thresholds. The LEL is the native's curated
recollection; negative years assume log completeness for the major classes. '3.0''s windows are
known-collapsed; its re-run baseline is the honest floor, not a straw man.

*End of protocol v2.0. The '3.0' v2.0 re-run follows immediately in BASELINE_3_0_v2_0.md; no
'4.1'/'5.0' scoring until the native reports the protocol review closed.*
