---
artifact: BRIEF_D4
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-4 — Calibration ignition (L5 finally fed)
version: 1.0
status: FROZEN — §B slots bind at wave open
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §7 +
  DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §7
prerequisite: D-3 gate GREEN (mechanism curves exist and retrodict).
gate: discrimination + negative-control gates (§G) with anti-gaming verifier pass.
---

# D-4 — Calibration Ignition

## FROZEN §F1 — Lane map (6 lanes)

### Lane C-1 — Shared LEL↔candidate matcher fix (CR-47 root)
The matcher scored 0/36 LEL events across all 185 rectification candidates — silently. Root-cause
the shared matcher; a zero-signal run must self-report as non-discriminating. Healing this heals
rectification too (same component). Verifier: matcher matches known specimens (2025-05 fraud →
8L-Mars→2H mechanism; 2010-07 windfall → wealth mechanism) with nonzero fit.

### Lane C-2 — LEL firewall re-scope + retrodiction backfill
Firewall re-scoped: quarantine LEL → prediction-INPUTS only; LEL → outcome-SCORING flows freely.
One-time backfill job: score all 57 LEL events (per chart) against their D-3 mechanism curves;
batch-write `mimamsa_outcome_record` rows under PH-4-3's train/test discipline. Flips
n_observations 0 → ~40/chart; promotion gates evaluate for the first time.

### Lane C-3 — Event-class evidence + verdict function (CR-79)
Evidence sets become event-class-specific (gain ≠ loss — opposite outcomes may never share
identical evidence + identical grade); QA checks that always return 0.5 self-report as
non-discriminating; kill-switch release criteria defined as data.

### Lane C-4 — Negative controls
Shuffled-birth + antiphase controls implemented (the `not_implemented` stubs become real); every
calibration claim carries its control delta. No control, no claim.

### Lane C-5 — Remedy-leverage join (CR-20/67)
bo_upaya populated from: leverage_index (weakest load-bearing graha) × existing sādhanā history
(LEL spiritual arc) × dasha runway (intervention window = years BEFORE the weak lord's MD opens).
The Venus/Venkaṭeśvara specimen becomes computable: system holds both halves today and never joins
them. Wealth resonances ≠ 0; at least one schedulable program.

### Lane C-6 — mechanism_retrodiction surface (CR-68)
LEL events joined to the mechanism that predicts them, served as CONFIRMATION ("this chart's 2H
mechanism has fired N times: …") — never as prediction input. Feeds L5 honestly; gives readings
their retrodictive-evidence section.

**Merge order:** C-1 → C-3/C-4 (parallel) → C-2 (backfill runs AFTER matcher+evidence fixed) →
C-5/C-6. The backfill is one-shot: never run it on an unverified matcher.

**Then the standing live loop opens (not a lane — a property):** every reading logs
falsifier-bearing predictions per its vidhi; every LEL append triggers outcome matching;
multipliers update; the next compiled contract retrieves with calibrated priors.

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK) · the leakage firewall on prediction-INPUTS (re-scoped, never
removed) · raw LEL event data (append-only corpus) · all prior gate surfaces (regression batteries).

## §B — BIND-AT-OPEN slots (Fable Binder)
- Matcher root-cause hypothesis ← C-1 diagnosis spike at open (read the actual matcher code + one
  traced run) before lane briefs finalize.
- Evidence-set taxonomy per event class ← LEL HEAD's actual event classes (enumerate, don't assume).
- Curve-shape parameters ← D-3's shipped kernel (intensity distribution percentiles for scoring
  thresholds).
- Promotion-gate + kill-switch release thresholds ← Adjudicator-doctrine (DR-n; these are
  epistemics, not engineering).
- Rollback pin + all prior batteries green.

## §G — Gate
1. `mimamsa_calibration_get`: n_observations ≈ 40/chart; multipliers evaluating (no longer all
   prior_only); verdict_distribution + reliability_curve non-empty.
2. Discrimination: `mimamsa_insight_get(wealth)` — "Major Financial Gain" and "Major Financial
   Loss" carry DIFFERENT evidence sets and DIFFERENT grades on 482012f1.
3. Negative controls: implemented, and calibration beats shuffled-birth with the gap reported.
4. At least one served verdict demonstrably moved by a calibrated multiplier (before/after receipt).
5. Remedy: bo_upaya wealth resonances ≠ 0; the leverage-ranked intervention (Venus, pre-2034
   window) served with its sādhanā join.
6. Anti-gaming pass on 1–4 + all prior wave batteries green (full regression).

**Campaign close (after this gate):** parked-items review + all DR-n rulings presented to the
native for ratification; register final sweep; CURRENT_STATE + SESSION_LOG campaign seal; the
master test becomes the standing per-release regression suite.
