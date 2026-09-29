---
artifact: EVALUATION_PROTOCOL
canonical_id: EVALUATION_PROTOCOL
version: "2.1"
status: PRE_DECLARED
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "EVALUATION_PROTOCOL_v2_0.md — retained as disclosed history; v1.0/v1.1/v1_2-DRAFT remain history under v2.0's header"
registry: "measurement/EVENT_REGISTRY_v2_1.md (the only event source for any v2.1 scoring)"
declared_before: "the v2.1 re-run of '3.0' and any '4.1'/'5.0' scoring"
amendment_disclosure: >
  Written after BOTH round-2 design-spec reviews were read in full — Kimi K3 round 2
  (KIMI_K3_REVIEW_DESIGN_SPECS_v1_1.md, FREEZE_WITH_AMENDMENTS / ACCEPT_WITH_AMENDMENTS) and
  Codex Astra round 2 (ASTRA_REVIEW_DESIGN_SPECS_v1_1.md, REWORK / REWORK) — and implements
  their protocol-side findings (Kimi NK-1, NK-4…NK-11; Codex R2-M01…R2-M07). v2.0 was written
  having seen only the round-1 reviews. No '4.1'/'5.0' scoring occurs until the native closes
  D-PROTO; the v2.1 re-run of '3.0' is a re-measurement of an already-served generation.
deviation_history: >
  Retained in full: B4.3 scored '3.0' before the B4.2 protocol review closed (disclosed in
  BASELINE_3_0_v1_0.md and v1.1's header). The '3.0' measurement stands as a measurement taken
  under an unreviewed protocol; v2.1 re-runs it under this protocol from the same pinned
  extract (sha256 70ba6142…) used by v2.0.
---

# Gochara evaluation protocol v2.1 — consolidated

Changes v2.0 → v2.1, in one place (everything below is the full protocol; this list is the
delta map): registry v2.1 (47 held-out, floor 16); T-cover month-grain = calendar-month
overlap; T-rank runs degeneracy exclusions before rank and restores the v1.1 peak-diversity
check; T-FP is a single all-observed-time estimand with budget and burden on one denominator;
controls are drawn at matched resolutions with the randrange off-by-one fixed; the T-FP budget
constants are restated as declared engineering allowances; narrative corrections from round 2
are carried into BASELINE_3_0_v2_1.md.

## 1. Event source

The only event source is **EVENT_REGISTRY_v2_1.md** (built row-by-row from
LIFE_EVENT_LOG_v1_2.md, read-only). No event enters scoring except through the registry; any
registry change after a scoring pass is a versioned amendment naming what was seen. Registry
facts this protocol relies on: held-out **47 (30 timing-usable + 17 year-grain)**; dev 3
(calibration only); excluded 7 (EVT.CURRENT.01 inside the 7, counted once); observation mask
ends **2026-04-17**; scored horizon H = 1998-01-01 → 2026-04-17 = **10,334 days**.

Onset vs status: only `point`/`interval` rows are scored. `status` rows (EVT.CURRENT.01)
are annotations, never dated events. Date-uncertainty rows carry the grain the LEL supports
and no finer (the grandfather's June-or-July is an interval; 2026.01's "January to February"
is an interval; month-approx rows are month-grain).

## 2. Class universe

Fixed 27-class universe (from the design specs' class list); a generation's rows map into it
or are reported `unmapped`. Class mappings with reasons live in the registry, not here. The
frozen adverse classes: bereavement, career_setback, chronic_onset, financial_deception,
illness_acute, parental_event, separation, surgery, major_loss. Class polarity
(gain / adverse / anchor) is fixed by the design specs' class table — the polarity table is
part of the class universe, not of any scorer (Codex R2-M06).

## 3. Timezone and calendar conventions

- All event dates are **IST calendar dates** as logged in the LEL.
- Window timestamps stored in UTC follow the platform's 18:30-UTC (= 00:00 IST) day-anchor
  convention; a stored timestamp `T` represents the IST civil date `T + 5:30`. All scoring
  converts to IST dates before any comparison.
- A generation whose coverage ends before 2026-04-17 is scored on the intersection and the
  shortfall is reported as coverage, never as absence of events.

## 4. Window identity, deduplication, ties

1. **Candidate identity:** a candidate window is the tuple (class, window_start, window_end,
   peak_date, generation) after conversion to IST dates.
2. **Dedup before counting:** overlapping or abutting windows of the same class within a
   generation are merged into one candidate **before** N (candidate count) is computed and
   before any ranking. A plateau of 40 contiguous daily rows is one candidate.
3. **Ranking:** candidates of class c in event e's year are ranked by **signed intensity,
   descending, for gain and adverse classes alike**. Sign convention (disclosed, asserted by
   the scorer against the pinned extract): adverse-class rows carry valence `loss` with
   positive si, so "most adverse first" is si descending. If a future extract violates this
   convention the scorer must say so and stop, not silently re-sign. **Ties take the average
   rank** of the tied group (disclosed convention).
4. **Eligible misses stay in the ranking:** if no admitted window of class c overlaps e's
   scored span, e is retained in the T-rank median at the **worst-rank convention —
   percentile 100** (the asymmetry is stated: real ranks land on 100(r−1)/N ≤ 100(N−1)/N,
   so a miss at 100 is strictly worse than any real rank; Kimi NK-9). Misses are also counted
   separately for T-cover; the two reports never silently drop the same event.

## 5. Timing error — single rule

One rule, no parallel formulations:

- **grain exact:** error = |peak IST date of the highest-ranked overlapping window − event
  date| in days; 0 if peak = event date.
- **grain month:** event date = 15th of the month (error proxy only — coverage is the whole
  month, §6.1); error in days on the same scale.
- **grain interval [a,b]:** hit iff an admitted window overlaps [a,b]; error = distance from
  peak to the nearest point of [a,b] (0 if peak ∈ [a,b]).
- **Miss:** no overlapping window → error = **182 days** (capped miss value).
- **All errors are capped at 182 days.** Alongside the capped median, the scorer reports
  separately: (a) the miss count, (b) the uncapped errors of the hits. The capped median is
  the endpoint; the separate reports are mandatory disclosure.

## 6. Endpoints (all co-primary, each necessary, none sufficient)

1. **T-cover:** of the 47 held-out events, the fraction with at least one admitted window of
   the event's class **overlapping the event's scored span** (exact: the day; month: the
   calendar month — any shared day; interval: the interval; year: the year) must be
   **≥ 32/47** — the v2.1 re-run figure of '3.0' on this identical registry
   (BASELINE_3_0_v2_1.md; the bar equals the served floor), and every miss must be named.
   One overlap definition is used identically for hits and for the burden below.
2. **T-time (single rule):** capped-median timing error over the 5 exact-date held-out events
   (registry §2, exact cohort) **≤ 45 days**. Misses enter at 182 d per §5.
3. **T-rank:** over timing-usable held-out events whose class is **not degenerate for the
   event's year** (§8 exclusions run first), with **N ≥ 3 candidate windows** of the event's
   class in the event's year (post-dedup; interval events: N over the event's start year),
   median rank percentile ≤ **25**. **Validity floor:** at least **floor(30/2)+1 = 16** of
   the 30 timing-usable events must be eligible, else the generation is **rank-unproven**,
   which **blocks the flip** regardless of other endpoints. Worst-rank misses stay in the
   median per §4.4. Aggregation: event-pooled (one median over eligible events), stated.
4. **T-FP (single estimand, Codex R2-M02):** for each frozen adverse class c, the **admitted
   day-fraction** (union of admitted days of class c inside the horizon) ÷ H must be
   ≤ **min(1, 3·n_c·90/H)**, n_c = held-out in-horizon events of class c, H = 10,334 — the
   same denominator on both sides. Arithmetic (registry §5): n_c = 1 → 270/10,334 =
   **2.61 %**; n_c = 2 → **5.23 %**; n_c = 0 (major_loss) → single-event allowance
   **2.61 %**. **Policy statement:** the ±45-day legitimate footprint, the factor-3 slack,
   the 90-day window, and the n_c = 0 allowance are **declared engineering allowances**
   (evaluation policy chosen so a blanket-claim class fails by construction), not quantities
   derived from event density; the v2.0 derivation sentence is withdrawn. Gain classes keep
   the two-horns rule: 0.5 % ≤ base rate ≤ 40 % of scored-horizon days.
5. **T-honesty:** every metric carries its coverage; a class with coverage < 50 % of the
   scored horizon is reported `unqualified`, not scored. **Coverage must be verifiable from
   a computation-coverage manifest naming which (class, year) cells the engine computed;
   without that manifest T-honesty is UNVERIFIABLE** (Codex R2-M06) — the manifest is a
   build requirement for future generations, and '3.0' is reported with it absent.

Failure on any co-primary endpoint is failure of the generation. D-FLIP additionally requires
the A5.7 engineering gates.

## 7. Controls

- **Negative days/years:** per class, every horizon day/year with no registry event of that
  class (LEL completeness disclosed as a limit).
- **Random controls:** **20 intervals per held-out event**, drawn uniformly from the scored
  horizon **at the event's own resolution** (exact: 1 d; month: 30 d; year: 365 d; interval:
  the interval's own length — grandfather 61 d, 2026.01 59 d), offset drawn as
  `randrange(0, H − span + 1)` (inclusive; off-by-one fixed per Codex R2-M05), **seed =
  482012**, **materialised**: the draw script and its output are committed beside the score
  file so the controls are reproducible byte-for-byte (v2.1 materialisation:
  random_controls_v1_1.json).
- **Placebo classes:** classes with zero registry events (e.g. major_loss) — scored against
  the single-event allowance, §6.4.
- **Annotation guard:** only annotations verified in
  `measurement/LEL_CHART_STATE_RECONCILED_v1_0.md` may enter scoring; any unverified
  event-log annotation is **rejected** by the scorer, not downweighted. (Scorer-side
  enforcement for this pinned re-run: the registry is hand-built from LEL anchors and the
  reconciliation file; machine enforcement is a build-contract item — Codex R2-M06,
  disclosed.)

## 8. Degeneracy tests (run on every generation BEFORE any endpoint; exclusions feed T-rank)

1. **Era-boundary fingerprint:** ≥ 50 % of class pairs sharing identical window boundaries →
   generation flagged **class-indiscriminate**; T-rank void, flag printed atop the score file.
2. **Two-horns check:** class base rate > 95 % or < 0.5 % → class degenerate-high/-low; such
   classes count in T-cover and T-FP but never toward T-rank's N or floor. The tally is
   reported over **all 27 classes including birth_anchor**.
3. **Peak-diversity check (restored, v1.1 §B.1 wording):** if ≥ 50 % of a class's in-year
   windows share one score value (a plateau), T-rank for that class-year is void (ties make
   rank arbitrary) and its events do not count toward the floor.

## 9. Procedure

1. Pin the scored rows to a file (read-only dump, sha256 recorded) before any counting.
2. Compute registry-derived counts first; any mismatch with the registry's §6 table is a
   scorer bug, not a registry amendment.
3. Score each generation once per protocol version, read-only, every figure with its
   predicate and the pinned extract's hash.
4. Dev-tier events are reported separately (calibration view), never in a median.
5. Aggregation: **T-cover, T-time and T-rank are event-pooled; T-FP is per class** (stated
   once, here). Missing values are reported as missing (never silently zero-filled); a class
   with no scored rows is `absent`.
6. A protocol change after a scoring pass is a versioned amendment naming what was seen.

## 10. Honest limits (retained, restated for v2.1)

Single chart; 30 timing-usable held-out events (5 exact-date): medians, not distributions; no
significance claim beyond the pre-declared thresholds. The LEL is the native's curated
recollection; negative years assume log completeness for the major classes. '3.0''s windows
are known-collapsed; its re-run baseline is the honest floor, not a straw man. For '3.0'
specifically: every timing-usable event sits in a degenerate class, so T-rank has no eligible
events at all — rank-unproven is a statement about '3.0''s windows, not about the test.

*End of protocol v2.1. The '3.0' v2.1 re-run follows in BASELINE_3_0_v2_1.md; no '4.1'/'5.0'
scoring until the native closes D-PROTO.*
