---
artifact: WP8_FACTOR_DELTA_REPORT
version: 1.0
status: EVIDENCE
sheet_item: GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §4.11
---

# WP8 — Factor-level delta report (evidence, not ratification)

Sheet item (§4.11): a test-driven generator emitting per-factor deltas
(promise / permission incl. denominator shift / activity / tārā / w30 /
quality_gates), peak counts, and slices by relation × body, run for every
flag individually and all together. Every number below is a `WP8DELTA|` print
from `tests/l3/gochara/test_wp8_factor_delta.py` (2 tests, both passing),
which runs the **full engine** (`_evaluate_single_from_context` with all
DB-touching primitives patched to the synthetic sentence sets) on the
synthetic marriage-2013 workload and the quarter marriage class.

Configs: `baseline` (all legacy defaults) · `m1`
(activity_shape=linear_no_box, orb_max_deg=1.0 — the §4.6 candidate) ·
`m3` (moon_channel=separate) · `n14` (nodal_drishti=removed) ·
`n15` (sade_sati_mode=testimony) · `all`.

Structural detectors asserted (not merely printed): promise, tārā and
quality_gates are bit-identical across all configs; the permission
denominator is 1.0 at baseline and 0.9 under n15/all; w30 = 1.0 under n14/all.

## 1. marriage-2013 — factor means over the 365-day grid

| config | λ | promise | permission | activity | tārā | w30 | quality_gates | perm. denom | peaks |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.050574 | 0.8 | 0.16 | 0.400774 | 0.989178 | 1.0 | 1.0 | 1.0 | 85 |
| m1 | 0.017424 | 0.8 | 0.16 | 0.139291 | 0.989178 | 1.0 | 1.0 | 1.0 | 43 |
| m3 | 0.050574 | 0.8 | 0.16 | 0.400774 | 0.989178 | 1.0 | 1.0 | 1.0 | 85 |
| n14 | 0.046616 | 0.8 | 0.16 | 0.369267 | 0.989178 | 1.0 | 1.0 | 1.0 | 76 |
| n15 | 0.056194 | 0.8 | 0.177778 | 0.400774 | 0.989178 | 1.0 | 1.0 | 0.9 | 85 |
| all | 0.015543 | 0.8 | 0.177778 | 0.111959 | 0.989178 | 1.0 | 1.0 | 0.9 | 34 |

Deltas vs baseline: m1 Δλ −0.033150 (Δactivity −0.261483, peaks 85→43) ·
m3 no-op · n14 Δλ −0.003958 (Δactivity −0.031507, peaks 85→76) ·
n15 Δλ +0.005619 (Δpermission +0.017778 = 0.16 × 1/0.9, denominator 1.0→0.9) ·
all Δλ −0.035031 (permission +0.017778, activity −0.288815, peaks 85→34).

## 2. quarter-marriage (2027-03→05) — factor means over the 92-day grid

| config | λ | promise | permission | activity | tārā | w30 | quality_gates | perm. denom | peaks |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.020530 | 0.8 | 0.16 | 0.161005 | 0.990761 | 1.0 | 1.0 | 1.0 | 8 |
| m1 | 0.009462 | 0.8 | 0.16 | 0.074918 | 0.990761 | 1.0 | 1.0 | 1.0 | 5 |
| m3 | 0.020530 | 0.8 | 0.16 | 0.161005 | 0.990761 | 1.0 | 1.0 | 1.0 | 8 |
| n14 | 0.020530 | 0.8 | 0.16 | 0.161005 | 0.990761 | 1.0 | 1.0 | 1.0 | 8 |
| n15 | 0.022812 | 0.8 | 0.177778 | 0.161005 | 0.990761 | 1.0 | 1.0 | 0.9 | 8 |
| all | 0.010514 | 0.8 | 0.177778 | 0.074918 | 0.990761 | 1.0 | 1.0 | 0.9 | 5 |

Deltas vs baseline: m1 Δλ −0.011068 (peaks 8→5) · m3 no-op · n14 no-op on
this workload (no nodal-drishti sentence fires in the quarter window) ·
n15 Δλ +0.002281 (same denominator mechanism) · all Δλ −0.010017 (peaks 8→5).

## 3. Slices (summed activity p_i by primitive × body)

marriage-2013 (baseline / m1 / m3 / n14 / n15 / all):

| primitive | body | baseline | m1 | m3 | n14 | n15 | all |
|---|---|---|---|---|---|---|---|
| degree_contact | Jupiter | 16.30 | 12.2387 | 16.30 | 16.30 | 16.30 | 12.2387 |
| degree_contact | Mars | 21.55 | 4.0540 | 21.55 | 21.55 | 21.55 | 4.0540 |
| degree_contact | Mercury | 40.55 | 3.8275 | 40.55 | 40.55 | 40.55 | 3.8275 |
| degree_contact | Saturn | 7.70 | 7.3430 | 7.70 | 7.70 | 7.70 | 7.3430 |
| degree_contact | Sun | 34.60 | 3.4340 | 34.60 | 34.60 | 34.60 | 3.4340 |
| degree_contact | Venus | 34.75 | 3.4830 | 34.75 | 34.75 | 34.75 | 3.4830 |
| drishti_contact | Jupiter | 8.10 | 6.0607 | 8.10 | 8.10 | 8.10 | 6.0607 |
| drishti_contact | Ketu | 6.00 | 5.2050 | 6.00 | 6.00 | 6.00 | 5.2050 |
| drishti_contact | Mars | 12.50 | 2.4000 | 12.50 | 12.50 | 12.50 | 2.4000 |
| drishti_contact | Rahu | 5.50 | 4.7712 | 5.50 | 5.50 | 5.50 | 4.7712 |

quarter-marriage: degree_contact Jupiter 8.25 → 6.1125 (m1/all) ·
degree_contact Venus 8.25 → 0.7800 (m1/all); all other configs equal baseline.

Reading: the slice surface shows where the m1 1.0° orb bites — fast bodies
(Mercury/Sun/Venus/Mars) lose ~90% of their summed contribution because their
daily motion exceeds the orb quickly, while the slow Saturn slice is nearly
untouched (7.70 → 7.3430). This is the expected signature of a degree-orb
projection and matches §4.6's window-resolution finding.

## 4. Honest notes

- **m3 (moon_channel=separate) is a no-op on both workloads** — by
  declaration the battery workloads generate no Moon contact sentences (the
  Moon channel is M-3's separate concern; Moon exists only as the tārā/w30
  ephemeris input). The zero delta is the correct result here, not evidence
  about M-3.
- **The slice table uses the harness activity surface**, which does not model
  the nodal_drishti flag; n14's activity delta (−0.031507 on marriage-2013)
  is captured by the full-engine factor rows (§1), not the slices. Both are
  printed; the discrepancy is declared, not smoothed over.
- **n15's permission shift is a pure denominator effect**: 0.16 →
  0.16/0.9 = 0.177778 exactly, permission systems' summed weight 1.0 → 0.9,
  activity untouched — matching the N-15 testimony-mode semantics.
- promise (0.8), tārā (0.989178 / 0.990761), and quality_gates (1.0) are
  invariant across every flag on both workloads — asserted.

## 5. Provenance

- Generator: `platform/python-sidecar/tests/l3/gochara/test_wp8_factor_delta.py`
  (2 passing). Regenerate: `cd platform/python-sidecar && python3 -m pytest
  tests/l3/gochara/test_wp8_factor_delta.py -q -s`.
- Workloads/harness: `wp8workloads.py`, `wp8synth.py` (same toy universe as
  the §4.6 battery and §4.7 ablation). Synthetic data only; no new citations.
