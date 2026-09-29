---
artifact: EVALUATION_PROTOCOL
canonical_id: EVALUATION_PROTOCOL
version: "1.0"
status: PRE_DECLARED
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
declared_before: "any rule path exists (B5.1 starts only after J1); sealed v3.0 §5 Tier 3 pulled forward into Tier 0 per campaign strategy rule 3"
scope: "chart 482012f1 only (D-SCOPE); generations scored: '3.0' (B4.3, read-only), '4.1' (B4.4, read-only), '5.0' (B5.4)"
lel_ground_truth: "01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md as reconciled by measurement/LEL_CHART_STATE_RECONCILED_v1_0.md (B4.1). The LEL is never edited; annotations enter only via the reconciled derived file"
review: "gate — independent review requested with this declaration; scoring (B4.3) begins only after review closes"
---

# Gochara evaluation protocol v1.0 — declared 2026-09-29, before any new rule path

This file fixes, in advance, how every Gochara generation is scored against the native's lived
events. Anything measured later that is not in this file is **post-hoc** and labelled as such.

## 1. Event set and partition

Source: 57 point events in the LEL (inventory extracted 2026-09-29; IDs below by reference to the
log). Partition rule, applied mechanically:

**Development cases (excluded from all scoring):**
- EVT.2013.12.11.01 (marriage) · EVT.2018.11.28.01 (father's passing) · EVT.2022.01.03.01 (twin
  daughters) — the three worked events of sealed v3.0 §4, used to develop the doctrine.
- Disclosure: the doctrine author also saw LEL §7's retrodictive summary during the earlier
  campaign. No other event was used to design a rule, a weight, or a threshold; the held-out set
  below is therefore untainted by construction choices, and this disclosure is part of the record.

**Held-out set (scored):** every other point event with `date_confidence ∈ {exact, month-exact}`
for timing metrics, plus `{year-exact, year-approx}` for year-grain rank metrics only. That is,
by class (event IDs abbreviated, all in the log):

| class | events (IDs) | timing-usable |
|---|---|---|
| relationship_begin | 1998.02.16, 2004.01, 2012.10 | all three |
| relationship_end | 2022.10 | yes |
| separation | CURRENT.01 (2026-04-17) | yes (exact) |
| career_join | 2007.06.10, 2013.05 | yes |
| career_exit | 2008.06.09 | yes |
| career_switch | 2017.03 | yes |
| career_setback | 2016 (year-exact) | year-grain only |
| education_admission | 2011.01 | yes |
| education_completion | 2007.06, 2013.03, 2023.06 | yes |
| education_selection | 2004 (year-approx), 2021 (year-approx) | year-grain only |
| business_launch | 2023.07, 2024.02.16, 2026.03.20, 2026.04.08 | yes (two exact) |
| relocation_out | 2019.05 | yes |
| relocation_return | 2023.05 | yes |
| travel_international | 2010.12 | yes |
| health_event | 2007.06 (surgery), 2021.01 | yes |
| health_onset | 1995 (year-approx), 2007 (year-approx) | year-grain only |
| health_resolution | 2025 (year-approx) | year-grain only |
| bereavement | 2009.06 (grandfather) | yes |
| family_illness_onset | 2013 (year-exact) | year-grain only |
| financial_gain_family | 2010 (year-approx) | year-grain only |
| financial_gain | 2025.07 | yes |
| financial_deception | 2025.05 | yes |
| recognition_creative | 2012.09 | yes |
| spiritual_shift | 2025 (year-approx) | year-grain only |
| wellbeing_shift | 2026.01 (month-approx) | year-grain only |

Chronic patterns (§4), inner turning-point periods (§5) and spiritual-diary enrichments
(1993–2025 SPR.A–G, PSY.A/B) are **excluded**: undated or year-approx inner events cannot ground
a timing metric. `EVT.CURRENT.01` is included (exact date, relationship/separation class).
Quarry acquisition EVT.2021.XX.XX.03 (year-approx) enters year-grain only under business_launch.

## 2. Control intervals

Declared now, with the seed: for each held-out event e in class c:

1. **Negative years:** every calendar year in the scored horizon in which class c has **no**
   LEL event (the LEL is the native's own complete log; an absent class-year is a negative,
   with the log's completeness disclosed as a limit).
2. **Random controls:** 20 intervals per event, drawn uniformly from the scored horizon at the
   event's resolution, `seed = 482012` (fixed here; any redraw is a protocol amendment).
3. **Placebo classes:** classes the engine admits but the LEL never records (e.g.
   `business_launch` pre-2023 acts as its own negative history) — the false-positive burden
   surface.

Scored horizon: 1998-01-01 → 2026-12-31 (the LEL's dated coverage); a generation whose coverage
ends earlier is scored on the intersection and the shortfall reported as coverage, never as
absence of events.

## 3. Metrics (all per class, then macro-averaged — no weighting by event count)

1. **Rank within class and year** (primary endpoint): the admitted windows of class c in event
   e's year are ranked by score; the metric is the percentile of the window containing e's date
   (month-exact events: containing e's month). Percentile 0 = top-ranked. Reported as median
   across held-out events, per generation.
2. **Base rate:** fraction of days (months) in the scored horizon admitted for class c. A class
   that admits everything ranks nothing — base rate accompanies every rank figure.
3. **Timing error:** for `exact` events, |peak date of the highest-ranked admitted window
   containing the event − event date| in days (0 if the peak is the event); for `month-exact`,
   in months. Median per generation over timing-usable held-out events.
4. **False-positive burden:** admitted day-fraction in negative years and on random controls,
   per class; reported next to base rate (they must agree or the discrepancy is explained).
5. **Per-mechanism attribution** ('5.0' only, B5.4): ablate one rule path (P1…P6) or factor
   family at a time; report Δ median rank. A path whose ablation never moves the rank is dead
   weight and says so in the report; `[P]`-testimony promotion requires a positive ablation
   (D-PADMIT).

## 4. Acceptance thresholds (declared)

'5.0' is **astrologically better than what is served** iff, on the held-out set:

- **T-rank (primary):** median rank percentile ≤ **25** (the typical true event sits in the top
  quartile of its class-year ranking), AND strictly better than both '3.0' and '4.1' medians on
  the identical event set. If '3.0' already meets 25, the bar is: '5.0' beats it by ≥ 10
  percentile points (else the elevation bought nothing).
- **T-time:** median timing error on exact-date held-out events ≤ **45 days**.
- **T-FP:** false-positive burden on adverse classes ≤ that of '3.0' (a windowing system that
  calls everything adverse is not an elevation); on gain classes, base rate ≤ 40 % of scored
  horizon days.
- **T-honesty:** every metric carries its coverage; any class whose coverage < 50 % of the
  scored horizon is reported as `unqualified`, not scored (ADK-0026).

Failure on T-rank is failure of the generation regardless of the other three. D-FLIP requires
this protocol's verdict plus the engineering gates (A5.7).

## 5. Procedure

1. B4.3 scores '3.0' read-only: served windows per class (E4's `kala_gochara_windows`
   generation='3.0'), mapped to classes; ranks, base rates, timing, FP burden per §3.
2. B4.4 scores '4.1' identically when A2.6 lands.
3. B5.4 scores '5.0' identically, plus §3.5 ablations, and writes the comparison.
4. Every query is read-only; every figure carries its predicate; the three development events are
   reported separately (calibration view) and never enter a median.
5. One scoring pass per generation per protocol version. A protocol change after a scoring pass
   is a versioned amendment (v1.1) naming what was seen before the change.

## 6. Honest limits (declared)

- Single chart, ~28 timing-usable held-out events: medians, not distributions; no significance
  claim beyond the pre-declared thresholds.
- The LEL is the native's recollection curated over sessions; negative years assume the log's
  completeness for the major classes (loss, career, relationship, relocation, health).
- '3.0''s windows are known-collapsed (v3.0 §1); its baseline is the honest floor, not a straw
  man — it is what is served today.
- Cross-class window-set correlation is reported as a diagnostic (a generation that fires the
  same windows for marriage and bereavement has learned nothing), not a threshold.

*End of protocol. Reviewed as a gate (B4.2); scoring begins only after review closes.*
