---
artifact: DR_13_EVENT_SCORING_SEMANTICS_DRAFT
type: DOCTRINE RULING — RATIFIED
status: RATIFIED (native, 2026-07-18, D-3 closeout directive). See DISAGREEMENT_REGISTER_v1_0.md
  DIS.026 for the canonical ratified text; this file is retained as the full authoring record.
dr_id: DR-13
dis_id: DIS.026
campaign_ref: D-4 C-1 (event-shape-aware matcher spec)
authored_by: D-3 conductor session, pre-D-4 wrap-up pass, 2026-07-18, per native directive
depends_on: DR-11 (DIS.024, T-0 retrodiction thresholds) — this DR AMENDS DR-11's scoring
  discipline for events whose shape is not a bare point; DR-11's ±45d/top-decile/top-tercile
  numbers stand unchanged for point-shaped events.
---

# DR-13 (draft) — Event-Scoring Semantics: shape, tolerance, and control-mirroring

## Why this exists

D-3's §G retrodiction gate scored every LEL event as a bare point (`event_date`) matched to a
served activation curve's peak within a fixed ±45-day window. The gate came back RED. Reviewing
the per-event detail surfaced a recording-discipline problem underneath the scoring problem: a
meaningful share of the LEL corpus is not actually point-shaped in reality — it is a **process
over an interval** (a payment flow, an onset-to-resolution arc) or a **chain of independently
dateable milestones** (an application → exam → result → enrollment sequence) that got recorded
as one fuzzy point at intake. Scoring a process as if it were a point measures the wrong thing
regardless of kernel quality. This DR proposes to fix the *measurement*, not the *kernel*, and
is explicitly quarantined from re-scoring D-3's already-red result (§ below).

## The ruling (draft — five parts)

**(a) LEL events carry a `shape`: `point | interval | chain`.**
Every event gets an explicit shape tag at intake or retrofit. Default for legacy rows without a
shape tag is `point` (no silent reclassification — see LEL schema v2, §B2, for the migration
discipline).

**(b) Intervals score by overlap, not distance-to-point.**
An `interval`-shaped event (start_date, end_date) is scored HIT if the served curve's top-decile
window (per DR-11's existing threshold) overlaps the event's `[start_date, end_date]` span at
all — not by measuring lag from a single representative date to a peak. A process that plays out
over months is retrodicted correctly if the kernel's high-activation window falls anywhere inside
that process's real span; measuring lag-to-a-fuzzy-midpoint of a process penalizes both the event
recording AND the kernel for a mismatch neither actually made.

**(c) Chains record named milestone anchors, each independently scoreable.**
A `chain`-shaped event decomposes into named sub-events (e.g. `exam_written`, `result_declared`,
`enrollment_confirmed`), each with its own date and its own `point` or `interval` shape, scored
independently under (a)/(b). Collapsing a chain to one fuzzy date at intake is a **recording
error**, not an acceptable simplification — a chain's milestones are usually genuinely
independently timed astrological triggers (different lords, different windows), and averaging
them into one mushy date destroys exactly the signal the gate exists to test for.

**(d) Tolerance scales with `date_confidence`.**
- `exact` (day-known): ±45 days (DR-11's existing figure, unchanged).
- `month-known`: ±75 days.
- `year-only`: **not scored in the primary battery.** Interval-scored (per (b), treating the
  whole year as the interval) in a **clearly-labeled SECONDARY battery**, reported separately,
  never silently folded into the primary hit-rate. Year-only events are not discarded (B.10 — no
  fabricated computation, but also no silent dropping of real data); they are scored honestly at
  the resolution the data actually supports.

**(e) Control-mirroring rule — non-negotiable.**
Every scoring loosening in (a)–(d) applies IDENTICALLY to the shuffled-birth negative control.
If an interval scores by overlap, the control's shuffled activation curve is checked for overlap
against the SAME interval, not a point. If a chain's milestones score independently, the
control scores each shuffled milestone independently too. **A looser real-chart criterion without
an identically-loosened control is gate-gaming by definition** — this is the single hardest
constraint in this DR and the one a future implementer is most likely to get wrong under time
pressure. Any C-1 matcher implementation that cannot demonstrate identical treatment of real and
control events under every one of (a)–(d) fails its own verifier by construction.

## Explicit non-scope (what this DR does NOT do)

- Does **not** retroactively re-score D-3's §G RED result. D-3's gate ran under DR-11's existing
  point-only discipline, correctly, and its RED stands as recorded in `REPORT_D-3.md` — this DR
  is prospective, feeding D-4's C-1 matcher, not a re-litigation of D-3.
- Does **not** loosen DR-11's ±45-day figure for `exact`-confidence point events — that number is
  untouched.
- Does **not** authorize any kernel-weight, threshold, orb, or valence change — this is purely
  about how an event's ground-truth date is represented and matched, symmetric on both sides of
  the comparison (real vs. control).
- One correction carried forward from D-3's own data (native-flagged, not new): the 2010-07-01
  "windfall" anchor event is itself a process/interval event (payments over a period from a land
  sale, "July 2010" approximate) — under (a)/(b) it should be RE-CLASSIFIED interval-shaped for
  any re-scoring. Its proximity check already PASSED under the old point-only scoring (peak
  within +43 days); only intensity failed (67% of top-decile threshold) — reclassification
  changes what "hit" means for this event but does not retroactively alter D-3's recorded RED.

## What ratifying this DR unlocks

D-4's C-1 (event-shape-aware matcher spec) is speced against this ruling's five parts. Native
ratification at D-4 bind is the gate for C-1 to proceed; until ratified, this stays a draft, no
implementation work is authorized against it, and D-3's RED stands unmodified as campaign
evidence per DR-12's bakeoff.

## Falsifier

If a future review finds that (e)'s control-mirroring cannot be implemented cleanly for one of
(b)/(c) — i.e., there is no principled way to apply the SAME loosening to a shuffled control —
that specific sub-rule should be dropped rather than implemented asymmetrically, and the DR
re-drafted narrower.
