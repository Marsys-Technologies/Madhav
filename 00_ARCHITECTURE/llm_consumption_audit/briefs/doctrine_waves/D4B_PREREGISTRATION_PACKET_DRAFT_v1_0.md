---
artifact: D4B_PREREGISTRATION_PACKET_DRAFT
type: PRE-REGISTRATION PACKET (STAGED / DRAFTED — NOT COMMITTED, NOT RUN)
version: 0.1-draft
status: DRAFT ONLY. Per native's explicit constraint on this readiness pass ("no bakeoff scoring"),
  this packet is NOT committed to the ledger and NO scoring run has been dispatched against it.
  D-4b's own Binder reviews, amends as needed, and commits this (or a revised version) to the
  ledger BEFORE B-1's first scoring call — per DR-17 §2's harness-refusal guard, the harness
  itself will refuse to run if its live tie-band/threshold parameters differ from whatever IS
  committed at that time, so this draft cannot silently become binding by omission.
prerequisite_check: this packet assumes B-1 runs against a FULLY MATERIALIZED ka_gochara_sweep
  (BRIEF_D4B §0) — event coverage below is bounded by the chart's LEL corpus, not the sweep's
  completeness, but win-criterion evaluation is meaningless on partial data (see BRIEF_D4B §0).
---

# D-4b Pre-Registration Packet (draft, staged for Binder review)

## §1 — Event set

Source: `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (canonical LEL, chart 482012f1). Live count at this
draft's authoring: **58 `EVT.*` entries** across 8 chronological eras (1984–2026), spanning
categories {career: 11, education: 10, spiritual: 8, relationship: 6, health: 5, loss: 3, family:
3, residential+travel: 2, psychological: 2, finance: 2, creative: 2, travel: 1, other: 2 — some
events carry multiple categories}. This is close to but not identical to BRIEF_D4 v2.0's "57 LEL
events" figure — the Binder reconciles the exact count fresh at open (LEL is append-only and may
have grown since v2.0 was authored).

**Date-tightening status:** `NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md` is a PARTIAL submission (16
of a larger questionnaire answered, 2026-07-19) — 2 items carry native CORRECTIONS to previously
recorded dates (item 3: father's spiritual dialogues, 1997→2001; item 10: Mahadev adoption,
~2015→2021-04/05), one item (13) reorders chronology (relationship end date corrected earlier than
the affair-start date it previously followed). **The Binder ingests these corrections via C-1's LEL
schema v2 additive migration (per BRIEF_D4 v2.0 Lane C-1) BEFORE this event set is finalized** — a
scoring run against un-tightened dates would silently score against known-stale ground truth.
Un-answered items remain at their recorded (year/month) confidence tier, used as-is.

**Named specimens (highest-scrutiny, carried across every prior wave):**
- `EVT.2010.XX.XX.01` — major_gain windfall, RECLASSIFIED interval per approved tightening:
  [2010-07 → 2011-03], month-confidence bounds (native-tightened, item 9).
- `EVT.2013.12.11.01` — marriage, double-transit specimen, day-confidence.
- Sarvatobhadra (~2025-05) — NO scoreable LEL anchor exists for this as a distinct event; carried
  as a structural/primitive-level demonstration only (G-2's own honest finding), NOT part of the
  scored event set for B-1.

## §2 — DR-13 shapes (per event, drawn from LEL + tightening responses, Binder confirms final map)

| Shape | Example events (this chart) |
|---|---|
| `point` | EVT.2013.12.11.01 (marriage), EVT.2009.06.XX.01→tightened point w/ bounds (grandfather's passing), EVT.2022.XX.XX (Tepper affair start, week-confidence point) |
| `interval` | EVT.2010.XX.XX.01 (windfall, tightened), EVT.1995.XX.XX.01 (headaches chronic_onset — chain/interval hybrid per native's answer), item-5 vertigo peak sub-interval |
| `chain` | father's spiritual dialogues arc (2001→present, multiple milestones per tightening item 3), sleep-disorder chain (onset↔arthroscopy hard-link, item 7), quarry chain (#11→#16) |

## §3 — Thresholds (DRAFT — Binder ratifies or amends)

- **Point-shape tolerance** (DR-13, unchanged from D-3 baseline): exact ±45 days for day/week-
  confidence events; ±75 days (month-confidence secondary battery) for month-confidence events;
  year-only tolerance events score in a labeled SECONDARY battery, never discarded, never mixed into
  the primary hit-rate figure.
- **Interval-shape scoring** (DR-15/DR-17 corrected, per D-5's own gate_run_2 native disposition):
  OVERLAP assertion — a model's served window/plateau overlapping the LEL interval's own
  [start,end] bounds by ANY nonzero duration counts, evaluated under DR-17's graded scale (§1, the
  companion doctrine artifact `DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md`), not a binary
  hit/miss.
- **Win criterion** (DR-15(b), CRPS primary): `skill = 1 − CRPS_model / CRPS_control` > 0 AND
  statistically distinguishable from 0 (not just numerically positive) — the model's own
  coverage-matched shuffled-birth control is the comparator. Hit-rate (±45d top-decile, D-3
  continuity) retained as legacy secondary, reported alongside CRPS, never substituted for it.
- **Tie-band widths** (DR-17 §2): fixed at the model's own declared `date_confidence` tier — day
  (±3d), week (±7d), month (±45d), year (±180d) — committed at pre-registration, harness-refusal-
  guarded against post-hoc widening.
- **Top-K local-maxima constant** (D-5 gate_run_2 finding 2 fix, `shape_output._local_maxima`):
  K is NOT specimen-tuned. Per that fix's own implementation, K = every genuine local maximum above
  the event_class's own structural-prior baseline threshold (no fixed numeric cap) — response-row-
  count limiting is a SEPARATE, later concern owned by §N.6's response-budget discipline, never
  conflated with how many peaks the model is ALLOWED to find.
- **Anti-hit constant** (DR-17 §1, proposed): −1.0 for a valence-crossing `contra` grade
  (confidently-wrong DIRECTION on an adverse-class specimen), −0.5 for a same-valence `contra`.
  PROPOSED, not yet ratified (DR-17 §4).

## §4 — Control construction (DR-15(c), unchanged discipline)

Coverage-matched shuffled-birth control per model: the SAME model, SAME harness, run against N
synthetic birth dates drawn to match this chart's real coverage span (not a single alternate date —
D-3's own finding that a single-shuffle control understates variance). Antiphase control (C-4,
BRIEF_D4 v2.0) retained as a secondary robustness check, not the primary comparator.

## §5 — What this draft explicitly does NOT do

- Does not commit to the ledger (Binder's job, at D-4b open).
- Does not dispatch any scoring run (native's explicit constraint on this readiness pass).
- Does not resolve the LEL date-tightening ingestion (C-1's job).
- Does not finalize DR-17's anti-hit constant or tie-band mechanism ratification (Fable, doctrine-
  class, per protocol §4.1) — this packet stages the proposal, the Binder/Adjudicator ratifies.
