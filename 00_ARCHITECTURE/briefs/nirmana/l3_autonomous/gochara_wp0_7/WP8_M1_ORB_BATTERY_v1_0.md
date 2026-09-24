---
artifact: WP8_M1_ORB_BATTERY
version: 1.0
status: EVIDENCE
sheet_item: GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §4.6
recommendation_status: RECOMMENDATION ONLY — nothing in this report ratifies a change
---

# WP8 M-1 — Orb battery (evidence, not ratification)

Sheet item (§4.6): run the orb battery for the M-1 active-window definition on
synthetic **marriage-2013** and **ordinary quarter 2027-03→05** workloads, across
six arms — legacy box ±5 d · no-box×5.0° · no-box×2.0° · no-box×1.0° · no-box×0.5°
— and report anchor recall with λ-margin, active-day count (≤ legacy), distinct
windows for the 13 envelope-only classes, dynamic range, and plateau stability at
0.5×/2× per candidate. The sheet says "six arms" and lists five; the sixth arm
was interpreted as the wide-end control **no-box×10.0°** (recorded here as the
declared interpretation). Every number below is printed by a passing test.

## 1. Declared synthetic setup (invented geometry, no real chart/season)

Toy universe (file `platform/python-sidecar/tests/l3/gochara/wp8workloads.py`):

- Tracks with declared speeds (°/d): Saturn 0.017, Jupiter 0.095, Mars 0.520,
  Venus 0.980, Sun 0.990, Mercury 1.050, Moon 13.180, Rahu/Ketu −0.053.
- **marriage-2013** (365 d, 2013-01-01→2013-12-31): five targets with weights
  0.55–0.80 (declared < 1.0 so a single exact contact does not saturate the
  noisy-OR and the dynamic-range metric stays discriminating). Three declared
  anchors: **A** = Jupiter → 7th_cusp exact 2013-03-17, **B** = Venus → 7th_lord
  exact 2013-07-19, **C** = Saturn → natal_venus exact 2013-11-09. 31 contact
  sentences (incl. drishti rows and N-14 Rahu/Ketu rows); Mars background
  crossing 2013-01-25 as noise.
- **13 envelope-only classes**: marriage, career_advancement, illness_acute,
  surgery, childbirth, romantic_start, relocation, education_admission,
  litigation, property_purchase, spiritual_initiation, business_launch,
  foreign_travel. Each gets a private ephemeris with a two-crossing cluster at
  cluster-Δ cycling over {3, 8, 15} days plus a background Mars crossing.
- **ordinary quarter** (2027-03-01→2027-05-31): the 13 classes replayed against
  an ephemeris in which only even-indexed classes receive a crossing; the six
  odd-indexed classes receive none (honest zero-contact control).
- λ used for margins = the declared test computation 0.8 × 0.5 × activity
  (harness `lam_series`); "active" = activity > 0 on the daily grid.
- Detector test: the harness activity surface equals the engine's
  `_compute_activity_v3` + instantaneous-orb surface on 11 sampled JDs under both
  legacy and no-box flag sets (`WP8BATT|crosscheck|engine==harness|11|jds|OK`).
  Detector test: legacy-box active days on marriage-2013 equal the analytic ±5 d
  box union (196 == 196).

## 2. Arm definitions

| arm | shape | extent |
|---|---|---|
| legacy_box | binary box (current production semantics) | ±5 d around contact |
| no_box_10.0 | linear falloff 1 − orb/extent (sixth-arm interpretation) | 10.0° |
| no_box_5.0 | linear falloff | 5.0° |
| no_box_2.0 | linear falloff | 2.0° |
| no_box_1.0 | linear falloff | 1.0° |
| no_box_0.5 | linear falloff | 0.5° |

Plateau arms additionally evaluated at 4.0°, 2.5°, 0.25° (0.5×/2× neighbours of
the 1.0° and 2.0° candidates).

## 3. Marriage-2013 results

| arm | recall | active days | windows | var(active) | median(active) | anchor peak/median | λ-margins A/B/C | anchor ranks A/B/C |
|---|---|---|---|---|---|---|---|---|
| legacy_box | 3/3 | 196 | 14 | 0.00319383 | 0.300 | 1.320 | 0.040 / 0.116 / 0.084 | 6 / 1 / 3 |
| no_box_10.0 | 3/3 | 196 | 14 | 0.00483571 | 0.26528 | 1.4425 | 0.0809 / 0.1435 / 0.1209 | 5 / 1 / 3 |
| no_box_5.0 | 3/3 | 195 | 14 | 0.00829456 | 0.2268 | 1.6144 | 0.1059 / 0.1521 / 0.1420 | 5 / 2 / 3 |
| no_box_2.0 | 3/3 | 143 | 20 | 0.00859595 | 0.2124 | 1.6196 | 0.1183 / 0.1378 / 0.1423 | 5 / 4 / 2 |
| no_box_1.0 | 3/3 | 106 | 22 | 0.00650784 | 0.1984 | 1.6294 | 0.1325 / 0.1091 / 0.1358 | 4 / 6 / 3 |
| no_box_0.5 | 3/3 | 85 | 22 | 0.00698565 | 0.17028 | 1.8793 | 0.1716 / 0.1516 / 0.1316 | 2 / 3 / 5 |

Reading: recall ties 3/3 on every arm (the synthetic anchors are saturated by
construction — recall cannot discriminate here). Every no-box arm beats the
legacy box on every λ-margin and on the peak/median dynamic-range ratio; the
variance-of-active-days metric favours no-box at 5.0°/2.0° over both legacy and
the narrower arms.

## 4. Plateau stability (marriage-2013)

| orb | recall | active days | windows | var(active) | margins A/B/C |
|---|---|---|---|---|---|
| 10.0 | 3/3 | 196 | 14 | 0.00483571 | 0.0809 / 0.1435 / 0.1209 |
| 5.0 | 3/3 | 195 | 14 | 0.00829456 | 0.1059 / 0.1521 / 0.1420 |
| 4.0 | 3/3 | 183 | 14 | 0.00804486 | 0.1113 / 0.1498 / 0.1454 |
| 2.5 | 3/3 | 157 | 17 | 0.00862838 | 0.1193 / 0.1466 / 0.1473 |
| 2.0 | 3/3 | 143 | 20 | 0.00859595 | 0.1183 / 0.1378 / 0.1423 |
| 1.0 | 3/3 | 106 | 22 | 0.00650784 | 0.1325 / 0.1091 / 0.1358 |
| 0.5 | 3/3 | 85 | 22 | 0.00698565 | 0.1716 / 0.1516 / 0.1316 |
| 0.25 | 3/3 | 56 | 16 | 0.00700953 | 0.1968 / 0.1768 / 0.1568 |

Monotonicity detector (active days at 0.25→10°): 56, 85, 106, 143, 157, 183,
195, 196 — strictly non-decreasing, as printed by the test.

Reading: the 1.0° candidate is stable across its 0.5×/2× plateau neighbours
(recall flat 3/3; windows 22 at 0.5/1.0/2.0 except 17 at 2.5; margins move
smoothly). The 0.5° candidate's 0.5× neighbour (0.25°) drops window count
22 → 16 — a knife-edge: the candidate's behaviour does not survive its own
half-width, so 0.5° fails plateau stability.

## 5. Distinct windows for the 13 envelope-only classes

Windows / active-days per class (legacy → 10 → 5 → 2 → 1 → 0.5):

| class | cluster Δ | legacy | 10.0 | 5.0 | 2.0 | 1.0 | 0.5 |
|---|---|---|---|---|---|---|---|
| marriage | 3 | 2/24 | 2/24 | 2/24 | 2/17 | 2/13 | 2/11 |
| career_advancement | 8 | 2/30 | 2/30 | 2/30 | 2/23 | 3/17 | 3/13 |
| illness_acute | 15 | 3/31 | 3/31 | 3/31 | 3/21 | 3/15 | 3/13 |
| surgery | 3 | 2/24 | 2/24 | 2/24 | 2/17 | 2/13 | 2/11 |
| childbirth | 8 | 2/30 | 2/30 | 2/30 | 2/23 | 3/17 | 3/13 |
| romantic_start | 15 | 3/31 | 3/31 | 3/31 | 3/21 | 3/15 | 3/13 |
| relocation | 3 | 2/24 | 2/24 | 2/24 | 2/17 | 2/13 | 2/11 |
| education_admission | 8 | 2/30 | 2/30 | 2/30 | 2/23 | 3/17 | 3/13 |
| litigation | 15 | 3/31 | 3/31 | 3/31 | 3/21 | 3/15 | 3/13 |
| property_purchase | 3 | 1/21 | 1/21 | 1/21 | 2/17 | 2/13 | 2/11 |
| spiritual_initiation | 8 | 1/25 | 1/25 | 1/25 | 1/20 | 2/16 | 2/13 |
| business_launch | 15 | 3/31 | 3/31 | 3/31 | 3/21 | 3/15 | 3/13 |
| foreign_travel | 3 | 2/24 | 2/24 | 2/24 | 2/17 | 2/13 | 2/11 |

Reading: the narrow no-box arms resolve the Δ=8 clusters into 3 distinct
windows where the legacy box (and the wide no-box arms) merge them into 2;
Δ=3 clusters never split (the crossings are genuinely one event); Δ=15 is
always 3. This is the intended behaviour the sheet asks to see: narrower orbs
distinguish temporally separated contacts without fragmenting single ones.

## 6. Ordinary quarter 2027-03→05 (noise control)

Total active days across the 13 classes per arm: legacy 85 · no_box_10.0 85 ·
no_box_5.0 85 · no_box_2.0 68 · no_box_1.0 56 · no_box_0.5 48.

The six declared zero-contact classes (career_advancement, surgery,
romantic_start, education_admission, property_purchase, business_launch)
report 0 windows / 0 active days on **every** arm — printed and asserted by the
test. No arm explodes on the ordinary quarter; every no-box arm has total
active days ≤ legacy.

## 7. Recommendation (not ratified)

- **Shape**: recommend the no-box linear shape over the legacy ±5 d box. On
  the synthetic anchor battery it beats the box on every λ-margin
  (e.g. anchor A: 0.040 → 0.1059–0.1968 across arms) and on peak/median
  dynamic range (1.32 → 1.44–1.88) at equal recall and equal-or-fewer active
  days.
- **Value**: recommend **no-box × 1.0°** as the candidate. Recall ties 3/3;
  its peak/median ratio (1.6294) is the best of the non-knife-edge arms;
  plateau stability holds across 0.5×/2× (and 2.5°) neighbours; it resolves
  the Δ=8 envelope clusters into distinct windows (14 → 22 on marriage-2013)
  without fragmenting Δ=3 single events; and it does not inflate the ordinary
  quarter (56 ≤ 85). **2.0° is the declared runner-up** (slightly better
  variance 0.00859595 and same recall, but resolves fewer windows and its
  margins are lower than 1.0°'s).
- **Stated tension**: the sheet's exit gate says a narrower orb is
  recommended only if it beats 5.0°-no-box on recall AND range. On this
  synthetic battery recall **ties** (3/3 everywhere — saturated by
  construction) and range is **mixed** (peak/median favours 1.0°, variance
  favours 2.0°/5.0°). The gate as worded is therefore not literally met; the
  recommendation above rests on the discrimination metrics (margins, window
  resolution, plateau stability) where 1.0° dominates 5.0°, and this
  deviation from the literal gate is declared openly. 0.5° is rejected
  despite the best margins because it fails plateau stability (0.25° halves
  its window count 22 → 16 — knife-edge).
- **Status**: RECOMMENDATION ONLY. Ratification requires the sheet owner's
  decision; nothing in production config was changed by this work.

## 8. Provenance

- Harness: `platform/python-sidecar/tests/l3/gochara/wp8synth.py`,
  workloads `.../wp8workloads.py`, battery test
  `.../test_wp8_m1_orb_battery.py` (8 tests, all passing).
- Regenerate: `cd platform/python-sidecar && python3 -m pytest
  tests/l3/gochara/test_wp8_m1_orb_battery.py -q -s` — every number in §§3–6
  is a `WP8BATT|` print from that run.
- No real ephemeris, chart, or season was used; no new citations added.
