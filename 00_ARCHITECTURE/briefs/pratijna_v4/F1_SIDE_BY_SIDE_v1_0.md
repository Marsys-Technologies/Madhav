---
title: "F1 SIDE-BY-SIDE — v4.0 vs v4.1 (AMENDMENT F1, dispositor-conjunction exception)"
canonical_id: F1_SIDE_BY_SIDE
version: 1.0
status: CURRENT — analysis only, no adoption verdict rendered
date: 2026-08-09
campaign: PRATIJÑĀ v4, F1 AMENDMENT CYCLE, Stage 2
scope: charts 482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a-41cb-4450-b4dc-59d440e5f75a,
  ayanamsha lahiri_chitrapaksha, all 27 bo_pratijna_karyatva classes, both engines run live and
  read-only via platform/scripts/probes/probe_f1_side_by_side.py.
r13_compliance: PURE MEASUREMENT. v4.0 = amendments unset (default, production-identical). v4.1 =
  amendments={'F1'} (offline variant, never written to any table). Nothing in
  AMENDMENT_F1_SPEC_v1_0.md or bo_pratijna_v4_engine.py's F1 branch was adjusted after seeing these
  numbers — the implementation and its PARĪKṢAKA review (Stage 1) both closed before this probe ran.
  Per R13, no future tuning may run against either of these two charts.
---

# F1 SIDE-BY-SIDE — v4.0 vs v4.1

**This artifact is analysis, not a verdict.** It reports what changed, cell by cell, and traces
every change to its exact classical trigger. It does **not** recommend adoption. The adoption
decision belongs to the native + Fable (Stage 3 of this campaign presents this artifact to them,
unmodified).

## 0. Method

`probe_f1_side_by_side.py` (permanent, `platform/scripts/probes/`) instantiates two
`PratijnaV4Engine`s against the same live `ChartReaderV4` connection per chart — one default
(`amendments=frozenset()`, byte-identical to production v4.0) and one `amendments={'F1'}` (v4.1) —
and runs `score_all()` on both, for both canonical charts with real chart data
(`482012f1`/`1c826d5a`; the third canonical chart `cb73cd3d` carries no populated chart data and is
out of scope, same convention as `PROMISE_LAYER_SCOREBOARD_v1_0.md`). No DB row was written by this
probe (R19).

## 1. Chart 482012f1 — full 27-class table

| Class | v4.0 occ | v4.0 label | v4.1 occ | v4.1 label | Δocc | v4.0 cond | v4.1 cond | Δcond | Moved |
|---|---|---|---|---|---|---|---|---|---|
| achievement_recognition | 0.891 | VERY_STRONG | 0.891 | VERY_STRONG | 0.000 | 0.00 | 0.00 | 0.00 | no |
| bereavement | 0.686 | STRONG | 0.719 | STRONG | +0.033 | 10.00 | 10.00 | 0.00 | **YES** |
| birth_anchor | 0.564 | MODERATE | 0.564 | MODERATE | 0.000 | 0.00 | 0.00 | 0.00 | no |
| business_launch | 0.698 | STRONG | 0.731 | STRONG | +0.033 | 8.75 | 8.75 | 0.00 | **YES** |
| career_advancement | 0.771 | STRONG | 0.771 | STRONG | 0.000 | 7.50 | 7.50 | 0.00 | no |
| career_change | 0.774 | STRONG | 0.774 | STRONG | 0.000 | 6.25 | 6.25 | 0.00 | no |
| career_entry | 0.786 | STRONG | 0.786 | STRONG | 0.000 | 3.75 | 3.75 | 0.00 | no |
| career_setback | 0.870 | VERY_STRONG | 0.880 | VERY_STRONG | +0.010 | 7.50 | 7.50 | 0.00 | **YES** |
| childbirth | 0.593 | MODERATE | 0.593 | MODERATE | 0.000 | 7.50 | 7.50 | 0.00 | no |
| chronic_onset | 0.586 | MODERATE | 0.586 | MODERATE | 0.000 | 3.75 | 3.75 | 0.00 | no |
| education_milestone | 0.583 | MODERATE | 0.583 | MODERATE | 0.000 | 6.25 | 6.25 | 0.00 | no |
| exam_outcome | 0.500 | MODERATE | 0.500 | MODERATE | 0.000 | 6.25 | 6.25 | 0.00 | no |
| financial_deception | 0.841 | VERY_STRONG | 0.841 | VERY_STRONG | 0.000 | 0.00 | 0.00 | 0.00 | no |
| foreign_settlement | 0.707 | STRONG | 0.740 | STRONG | +0.033 | 7.50 | 7.50 | 0.00 | **YES** |
| illness_acute | 0.471 | MODERATE | 0.471 | MODERATE | 0.000 | 6.25 | 6.25 | 0.00 | no |
| major_gain | 0.639 | STRONG | 0.689 | STRONG | +0.050 | 10.00 | 10.00 | 0.00 | **YES** |
| major_loss | 0.625 | STRONG | 0.695 | STRONG | +0.070 | 10.00 | 10.00 | 0.00 | **YES** |
| **marriage** | **0.321** | **WEAK** | **0.450** | **MODERATE** | **+0.129** | 5.83 | 5.83 | 0.00 | **YES — BAND-CROSS** |
| parental_event | 0.500 | MODERATE | 0.500 | MODERATE | 0.000 | 6.25 | 6.25 | 0.00 | no |
| property_acquisition | 0.350 | WEAK | 0.379 | WEAK | +0.029 | 6.25 | 6.25 | 0.00 | **YES** |
| psychological_arc | 0.661 | STRONG | 0.661 | STRONG | 0.000 | 0.00 | 0.00 | 0.00 | no |
| relocation | 0.486 | MODERATE | 0.486 | MODERATE | 0.000 | 8.75 | 8.75 | 0.00 | no |
| romantic_start | 0.286 | WEAK | 0.393 | WEAK | +0.107 | 7.50 | 7.50 | 0.00 | **YES** |
| separation | 0.505 | MODERATE | 0.575 | MODERATE | +0.070 | 8.75 | 8.75 | 0.00 | **YES** |
| spiritual_turn | 0.740 | STRONG | 0.740 | STRONG | 0.000 | 7.50 | 7.50 | 0.00 | no |
| surgery | 0.471 | MODERATE | 0.471 | MODERATE | 0.000 | 6.25 | 6.25 | 0.00 | no |
| travel_event | 0.745 | STRONG | 0.745 | STRONG | 0.000 | 0.00 | 0.00 | 0.00 | no |

**10/27 classes moved: bereavement, business_launch, career_setback, foreign_settlement,
major_gain, major_loss, marriage, property_acquisition, romantic_start, separation.**
**17/27 classes unmoved (v4.0 ≡ v4.1 exactly, byte-identical occurrence AND condition):**
achievement_recognition, birth_anchor, career_advancement, career_change, career_entry, childbirth,
chronic_onset, education_milestone, exam_outcome, financial_deception, illness_acute,
parental_event, psychological_arc, relocation, spiritual_turn, surgery, travel_event.

**Condition axis: Δcond = 0.000 for all 27 classes, both charts.** Expected and structural, not a
coincidence — §5.2's condition formula has no dignity-band input at all (its only inputs are
`condition_malefic_grahas` aspect fractions, §2.7), so an amendment scoped entirely to §2.1's
dignity band cannot touch it. Verified independently by the live unit test
`test_f1_amendment_does_not_change_condition_axis` (Stage 1).

**Band-crossing summary: exactly ONE class crosses a label boundary — marriage, WEAK → MODERATE.**
Every other moved class shifts its raw occurrence number but stays inside the same §6.1 band
(bereavement/business_launch/foreign_settlement/major_gain/major_loss stay STRONG;
career_setback stays VERY_STRONG; property_acquisition/romantic_start stay WEAK; separation stays
MODERATE).

## 2. Chart 1c826d5a — full 27-class table

| Class | v4.0 occ | v4.0 label | v4.1 occ | v4.1 label | Δocc | v4.0 cond | v4.1 cond | Δcond | Moved |
|---|---|---|---|---|---|---|---|---|---|
| achievement_recognition | 0.218 | WEAK | 0.218 | WEAK | 0.000 | 0.00 | 0.00 | 0.00 | no |
| bereavement | 0.498 | MODERATE | 0.498 | MODERATE | 0.000 | 8.75 | 8.75 | 0.00 | no |
| birth_anchor | 0.627 | STRONG | 0.627 | STRONG | 0.000 | 0.00 | 0.00 | 0.00 | no |
| business_launch | 0.419 | MODERATE | 0.419 | MODERATE | 0.000 | 7.50 | 7.50 | 0.00 | no |
| career_advancement | 0.243 | WEAK | 0.243 | WEAK | 0.000 | 8.75 | 8.75 | 0.00 | no |
| career_change | 0.348 | WEAK | 0.348 | WEAK | 0.000 | 8.75 | 8.75 | 0.00 | no |
| career_entry | 0.271 | WEAK | 0.271 | WEAK | 0.000 | 7.50 | 7.50 | 0.00 | no |
| career_setback | 0.320 | WEAK | 0.320 | WEAK | 0.000 | 6.25 | 6.25 | 0.00 | no |
| childbirth | 0.321 | WEAK | 0.321 | WEAK | 0.000 | 7.50 | 7.50 | 0.00 | no |
| chronic_onset | 0.382 | WEAK | 0.382 | WEAK | 0.000 | 2.50 | 2.50 | 0.00 | no |
| education_milestone | 0.338 | WEAK | 0.338 | WEAK | 0.000 | 7.50 | 7.50 | 0.00 | no |
| exam_outcome | 0.421 | MODERATE | 0.421 | MODERATE | 0.000 | 7.50 | 7.50 | 0.00 | no |
| financial_deception | 0.405 | MODERATE | 0.405 | MODERATE | 0.000 | 0.00 | 0.00 | 0.00 | no |
| foreign_settlement | 0.381 | WEAK | 0.381 | WEAK | 0.000 | 8.75 | 8.75 | 0.00 | no |
| illness_acute | 0.500 | MODERATE | 0.500 | MODERATE | 0.000 | 3.75 | 3.75 | 0.00 | no |
| major_gain | 0.529 | MODERATE | 0.529 | MODERATE | 0.000 | 5.00 | 5.00 | 0.00 | no |
| major_loss | 0.710 | STRONG | 0.710 | STRONG | 0.000 | 3.75 | 3.75 | 0.00 | no |
| marriage | 0.714 | STRONG | 0.714 | STRONG | 0.000 | 8.33 | 8.33 | 0.00 | no |
| parental_event | 0.354 | WEAK | 0.354 | WEAK | 0.000 | 7.50 | 7.50 | 0.00 | no |
| property_acquisition | 0.593 | MODERATE | 0.593 | MODERATE | 0.000 | 7.50 | 7.50 | 0.00 | no |
| psychological_arc | 0.436 | MODERATE | 0.436 | MODERATE | 0.000 | 0.00 | 0.00 | 0.00 | no |
| relocation | 0.311 | WEAK | 0.311 | WEAK | 0.000 | 6.25 | 6.25 | 0.00 | no |
| romantic_start | 0.732 | STRONG | 0.732 | STRONG | 0.000 | 7.50 | 7.50 | 0.00 | no |
| separation | 0.670 | STRONG | 0.670 | STRONG | 0.000 | 10.00 | 10.00 | 0.00 | no |
| spiritual_turn | 0.000 | DENIED | 0.000 | DENIED | 0.000 | 5.00 | 5.00 | 0.00 | no |
| surgery | 0.525 | MODERATE | 0.525 | MODERATE | 0.000 | 3.75 | 3.75 | 0.00 | no |
| travel_event | 0.309 | WEAK | 0.309 | WEAK | 0.000 | 0.00 | 0.00 | 0.00 | no |

**0/27 classes moved on this chart. 27/27 unmoved, byte-identical.** This chart's own §2.1 dignity
evaluations simply never place a scored graha conjunct its own D1 dispositor (the specific
configuration AMENDMENT_F1_SPEC_v1_0.md's TRIGGER SCOPE names) for any of the 27 classes' populated
house-lord/karaka/divisional slots — the amendment's narrow scope means most charts, including this
one, will show zero effect. This is the expected, honest shape of a surgically-scoped exception, not
a probe defect: `test_f1_surgical_scope_non_conjunct_pairs_identical_both_engines` and
`test_f1_amendment_leaves_unaffected_classes_untouched` (Stage 1) already proved the mechanism is
inert absent the trigger; this chart is a second, independent, whole-chart confirmation of the same
property.

## 3. Every moved cell, traced to its exact classical trigger (chart 482012f1 only — the sole chart
with any movement)

All ten moved classes trace to exactly ONE of two underlying dispositor-conjunction pairs on this
chart. No other conjunction pair fires anywhere in the 27-class × 2-chart sweep.

### 3.1 Trigger A — Venus conjunct Jupiter, D1 house 9 (Sagittarius)

**The pair:** Venus occupies D1 sign 9 (Sagittarius); Sagittarius's dispositor (`SIGN_LORD[9]`) is
Jupiter; Jupiter is independently placed in D1 house 9 too — the two are conjunct.

- Venus @ D1 house 9, sign 9 — `fact_id 0183c097-d05c-442b-b415-1141cecfe6c5` (`chart_divisionals`,
  `varga_position`, D1).
- Jupiter @ D1 house 9, sign 9 — `fact_id dc6e8237-b557-4a27-ab02-99ed3275129f` (`chart_divisionals`,
  `varga_position`, D1).

**v4.0 reading:** naisargika(Venus→Jupiter)=neutral, tatkalika(same house, distance 1)=enemy-set →
pañcadhā compound = **enemy (0.30)**. **v4.1 (F1) reading:** tatkalika set aside, naisargika-only =
**neutral (0.50)**. Δband = **+0.20** wherever this exact Venus-in-D1 pair is scored.

**Classes it moves, and which slot(s):**

| Class | Slot(s) using this pair | Weight(s) | Δocc contribution |
|---|---|---|---|
| marriage | house_lord (7L=Venus, w=0.500000) + karaka (Venus, w=0.142857) | both | 0.500000×0.20 + 0.142857×0.20 = **0.128571** (matches observed +0.129, rounding) |
| separation | house_lord (7L=Venus, w=0.35) | one | 0.35×0.20 = **0.070** (exact match) |
| romantic_start | house_lord (5L/7L incl. Venus's 7L share, w=0.250000) + karaka (Venus, w=0.285714) | both | 0.250000×0.20 + 0.285714×0.20 = **0.107143** (matches observed +0.107) |
| bereavement | house_lord (7L… — bereavement's own `primary_bhava=[8,12,2]` maraka-reframed set does not include house 7; **this class's move is via `house_lord` weight on house **) — see note below | — | +0.033 |
| business_launch | house_lord (7L share, w=0.166667) | one | 0.166667×0.20 = **0.033333** (matches observed +0.033) |
| foreign_settlement | house_lord (7L share, w=0.166667) | one | 0.166667×0.20 = **0.033333** (matches observed +0.033) |
| major_gain | karaka (2L/11L — not Venus)... — see note below | — | +0.050 |
| major_loss | — see note below | — | +0.070 |
| property_acquisition | karaka (Venus, w=0.142857) | one | 0.142857×0.20 = **0.028571** (matches observed +0.029) |

**Correction note (R16 — honest self-check during trace verification):** `bereavement`,
`major_gain`, and `major_loss` do NOT list Venus as a house-lord or karaka slot item in their own
`KaryatvaMap` entries (bereavement's `primary_bhava=[8,12,2]`/`karaka_grahas=[Saturn,Ketu]`;
major_gain's `primary_bhava=[2,11]`/`karaka_grahas=[Jupiter,Mercury]`; major_loss's
`primary_bhava=[2]`/`karaka_grahas=[Saturn]`). Their movement traces to whichever house's LORD
happens to be Venus — house 2 and house 7 are both Venus-ruled (`SIGN_LORD[2]=Venus`,
`SIGN_LORD[7]=Venus`) on this whole-sign chart, so any class citing house 2 OR house 7 as a
`primary_bhava` house-lord slot inherits Venus's dignity shift through that slot, not through a
karaka listing. Re-verified against the live `factor_ledger`: bereavement, major_gain, and
major_loss all show `{"slot": "house_lord", ..., "lord": "Venus", "detail": "AMENDMENT F1..."}` —
bereavement via its house 2 (`SIGN_LORD[2]=Venus`, weight 0.166667: 0.166667×0.20=0.033333, matches
+0.033), major_gain via its house 2 (weight 0.250000: 0.250000×0.20=0.050000, matches +0.050
exactly), major_loss via its house 2 (weight 0.35, the 2-slot-equivalent single house_lord weight
for this 5-slot class: 0.35×0.20=0.070, matches +0.070 exactly).

**Complete trigger-A class set (9 of the 10 moved classes):** marriage, separation, romantic_start,
bereavement, business_launch, foreign_settlement, major_gain, major_loss, property_acquisition —
every one of these moves purely because it cites house 2 and/or house 7 (both Venus-ruled) as a
house-lord slot, or Venus itself as a karaka, and nothing else changed about its other slots.

### 3.2 Trigger B — Saturn conjunct Mars, D1 house 7 (Libra) — the one non-Venus mover

**The pair:** `career_setback`'s divisional slot scores its primary karaka (Saturn) in the D10
varga. Saturn's D10 sign is Scorpio (sign 8) — `fact_id 113d4f67-b3ff-4d67-b2cd-b28eb88a5d43`
(`chart_divisionals`, `varga_position`, D10). Scorpio's dispositor (`SIGN_LORD[8]`) is Mars. Per
CHECKPOINT_RECORD_v1_0.md Decision 1 (tātkālika/varga-dignity computed from D1 positions) and
AMENDMENT_F1_SPEC_v1_0.md's own TRIGGER SCOPE clause (varga conjunction tested the same way), the
conjunction test uses D1 positions: Saturn is D1 house 7 (`fact_id
0b6924b7-947f-423a-b741-b7547e4b14d2`) and Mars is also D1 house 7 (`fact_id
5580c393-5e5b-4026-83b7-cac623b34ff2`) — conjunct.

**v4.0 reading (live factor_ledger, confirmed):** naisargika(Saturn→Mars)=enemy,
tatkalika(same house, distance 1)=enemy-set → pañcadhā compound = **great_enemy (0.20)**. **v4.1
(F1) reading (live factor_ledger, confirmed):** tatkalika set aside, naisargika-only =
**enemy (0.30)** (Saturn↔Mars is a naisargika enemy pair per the `NAISARGIKA` table — `Saturn:
{..., "Mars": "enemy", ...}`). Δband = **+0.10**, at the divisional slot's weight 0.10:
0.10 × 0.10 = **0.010** — matches the observed Δocc exactly.

This is the one moved cell in the whole sweep where F1's naisargika-only reading is numerically
HIGHER (0.30 > 0.20) but classically LESS favorable in the ordinary sense of "great enemy" being
worse than "enemy" is reversed here — i.e., great_enemy(0.20) is the weaker dignity state, enemy
(0.30) the stronger one on the §2.1 ladder, so F1 genuinely raises Saturn's dignity reading here,
consistent with every other trigger on this chart. No directional "good/bad for career_setback"
claim is made — occurrence measures promise strength, not favorability, and career_setback is a
denial-class where the checkpoint's own §6.1 semantics apply without a sign-specific gloss here.

**Complete trigger-B class set (1 of the 10 moved classes):** career_setback only — the divisional
slot is the only place this chart's Saturn-D10/Mars-D1-house-7 conjunction is ever evaluated.

### 3.3 No third trigger exists

The full 54-cell sweep (2 charts × 27 classes) surfaces exactly two underlying dispositor-conjunction
pairs, both on chart 482012f1 (chart 1c826d5a has zero conjunctions of this kind anywhere in its 27
classes' populated slots, §2 above). Every moved occurrence cell traces to Trigger A or Trigger B
with no unexplained residual — the `factor_ledger`'s own `"AMENDMENT F1"`-tagged entries account for
100% of the observed deltas (independently re-derived by hand above for each class, not merely
asserted).

## 4. Unmoved cells — stated explicitly, not left implicit

**Chart 482012f1, unmoved (17/27):** achievement_recognition, birth_anchor, career_advancement,
career_change, career_entry, childbirth, chronic_onset, education_milestone, exam_outcome,
financial_deception, illness_acute, parental_event, psychological_arc, relocation, spiritual_turn,
surgery, travel_event. None of these classes' house-lord/karaka/divisional slots ever evaluate
Venus-in-Sagittarius or Saturn's D10 placement against their respective conjunct dispositors — most
cite houses ruled by lords other than Venus, or karakas other than Venus/Saturn-in-the-triggering-
varga.

**Chart 1c826d5a, unmoved (27/27):** all classes — see §2, no trigger fires anywhere on this chart.

## 5. Measurement context for 482012f1's moved classes — the scoreboard's lifetime-outcome column,
re-stated beside old/new bands (no re-adjudication)

Per `PROMISE_LAYER_SCOREBOARD_v1_0.md` (Lane B7, v4.0 baseline). Re-stated here for the ten classes
this amendment actually touches, side by side with v4.0/v4.1 — **measurement context only, not a
verdict on whether the shift is "correct."**

| Class | v4.0 band | v4.1 band | Lifetime outcome (from scoreboard, unmodified) |
|---|---|---|---|
| marriage | WEAK (0.321) | MODERATE (0.450) | **Occurred** — married 2013-12-11 |
| separation | MODERATE (0.505) | MODERATE (0.575) | **Occurred** — separated 2026-04-17 |
| romantic_start | WEAK (0.286) | WEAK (0.393) | **Occurred** (×3) — 1998, 2004, 2012 relationship starts |
| bereavement | STRONG (0.686) | STRONG (0.719) | **Occurred** (×2) — grandfather 2009, father 2018 |
| business_launch | STRONG (0.698) | STRONG (0.731) | **Occurred** — Marsys Group founded 2023, Kotadwara 2024 |
| foreign_settlement | STRONG (0.707) | STRONG (0.740) | **Occurred** — 4-year US residence 2019–2023 |
| major_gain | STRONG (0.639) | STRONG (0.689) | **Occurred** — Marsys contract 2025, Marsys Tech profits 2026 |
| major_loss | STRONG (0.625) | STRONG (0.695) | **Occurred** — deception/scam event May 2025 |
| property_acquisition | WEAK (0.350) | WEAK (0.379) | **NO-OUTCOME-DATA** (scoreboard: no confident match) |
| career_setback | VERY_STRONG (0.870) | VERY_STRONG (0.880) | **Occurred** — Mahindra Retail crash 2016, quarry stall 2021–2026 |

Nine of the ten moved classes' lifetime outcomes were "Occurred" under v4.0 already (only
`property_acquisition` was no-outcome-data, unaffected by this move either way) — F1's effect on
this chart, where it fires at all, uniformly moves occurrence UP for classes that already skewed
toward "occurred" under v4.0, with marriage the only case where the move also crosses a label
boundary (WEAK→MODERATE). Whether this counts as an improvement in calibration direction, a
coincidence of this one chart's Venus/Jupiter placement, or neither, is exactly the question Stage 3
hands to the native + Fable — not resolved here.

## 6. Band-crossing summary (full restatement)

| Class | v4.0 label | v4.1 label | Crossed? |
|---|---|---|---|
| marriage | WEAK | MODERATE | **YES — the only band-crossing cell in the entire 54-cell sweep** |
| separation, business_launch, foreign_settlement, major_gain, major_loss, bereavement | (unchanged label per row) | (unchanged label per row) | no — value moved, label did not |
| career_setback | VERY_STRONG | VERY_STRONG | no |
| property_acquisition, romantic_start | WEAK | WEAK | no |
| all 17 unmoved classes (482012f1) + all 27 classes (1c826d5a) | — | — | no (no movement at all) |

---
*End of F1_SIDE_BY_SIDE_v1_0.md. Produced by `platform/scripts/probes/probe_f1_side_by_side.py`
(permanent, read-only, R19) after Stage 1's engine implementation and PARĪKṢAKA review both closed.
This artifact makes no adoption recommendation — see AMENDMENT_F1_SPEC_v1_0.md's own campaign
framing and Stage 3 of the F1 AMENDMENT CYCLE for the presentation-to-native+Fable step.*
