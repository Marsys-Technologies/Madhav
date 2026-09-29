---
artifact: EVALUATION_PROTOCOL
canonical_id: EVALUATION_PROTOCOL
version: "1.1"
status: PRE_DECLARED
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "EVALUATION_PROTOCOL_v1_0.md (retained; v1.0's partition, controls, metrics and procedure stand)"
amendment_disclosure: >
  Written AFTER the '3.0' scoring pass (B4.3, measurement/BASELINE_3_0_v1_0.md) and BEFORE any
  '4.1' or '5.0' scoring. What was seen before this amendment: the full '3.0' baseline — era
  classes admit 99.88 % of the horizon (FP 99.87 %), five classes serve only zero-width instants
  and miss their events, the rank median is degenerate (N=1 candidate windows in-year), timing
  median over 7 exact events is ∞. No '4.1' or '5.0' row had been scored or inspected.
reason: >
  v1.0's primary endpoint (median rank percentile) is uninformative against a two-horns-degenerate
  baseline: a generation that admits everything and one that admits nothing can both produce
  meaningless rank medians. The endpoint set is sharpened now — before the candidates that will be
  judged by it exist as scored artifacts — so the standard cannot be accused of fitting the
  candidate. This is the v1.0 §5.5 amendment path, used exactly as declared.
deviation_disclosure: >
  DISCLOSED PROCESS DEVIATION (steward review, 2026-09-29): B4.3 scored '3.0' before the B4.2
  protocol review closed, contrary to v1.0's own gate language. The '3.0' measurement stands but
  was taken under an unreviewed protocol; no further generation is scored until the native reports
  the protocol review is done. This v1.1 (and the v1.2 draft) form part of the review surface for
  that review.
---

# Evaluation protocol v1.1 — amendment to v1.0 (only the deltas)

## A. Endpoints (replaces v1.0 §4's reliance on T-rank alone)

**Co-primary endpoints**, each necessary, none sufficient:

1. **T-cover (new, co-primary):** of the timing-usable held-out events, the fraction with at
   least one admitted window of the event's class containing the event's date (month) must be
   **≥ 22 of 36 (61 %)** — '3.0''s own figure on the identical set — and every miss must be
   named. A candidate that covers fewer true events than the served floor is not an elevation.
2. **T-time (co-primary, tightened):** median timing error over exact-date held-out events with
   a containing window ≤ **45 days**, and the count of misses (no containing window) no greater
   than '3.0''s 5-of-7. '3.0''s median is ∞ with hits at 686 d and 998 d — any '5.0' median
   within 45 days on ≥ 4 of 7 passes outright.
3. **T-FP (co-primary):** false-positive burden (negative-year admitted day-fraction) on every
   adverse class < '3.0''s 99.87 % by at least 50 points (i.e. ≤ 49.87 %); on gain classes,
   base rate ≤ 40 % of scored-horizon days — AND, new lower horn: every scored class's base rate
   ≥ 0.5 % (a class that admits nothing is `unqualified`, not "specific"). Classes violating the
   lower horn are reported `unqualified` per T-honesty and count against T-cover's denominator.
4. **T-rank (demoted to secondary):** reported as in v1.0, but reads as evidence only where the
   in-year candidate count N ≥ 3; where N < 3 the event's rank row is annotated `degenerate-N`
   and excluded from the median. No threshold.

## B. Degeneracy tests (new §3.6, runs on every generation before any endpoint)

1. **Era-boundary fingerprint:** if a generation's classes share identical window boundaries
   across ≥ 50 % of class pairs ('3.0': all 22 era-bearing classes identical, overlap 1.000), the
   generation is flagged **class-indiscriminate**; T-rank is void for it and the flag is reported
   at the top of the score file.
2. **Two-horns check:** base rate > 95 % or < 0.5 % on a scored class marks that class
   degenerate-high / degenerate-low; degenerate classes contribute to T-cover and T-FP as above
   but never to T-rank.
3. **Peak-diversity check:** if ≥ 50 % of a class's in-year windows share one score value
   (a plateau, cf. E5's 27-of-41), T-rank for that class is void (ties make rank arbitrary).

## C. What does not change

The development/held-out partition, the event-class mapping, the control intervals and seed
(482012), the metric definitions, the ablation requirement, the one-pass rule (this amendment is
that rule's own mechanism), and T-honesty (coverage < 50 % of horizon ⇒ `unqualified`).

## D. Consequence for B4.4 / B5.4

'4.1' (geometric baseline) is scored under v1.1 exactly as '3.0' was under v1.0, with the
degeneracy tests first. '5.0' passes measurement iff **all three co-primaries** pass; the D-FLIP
recommendation reads this file plus the engineering gates (A5.7). If '5.0' fails T-cover or
T-time, the report says so plainly — honest null over a flipped verdict (ADK-0026).
