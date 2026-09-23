---
artifact: WP8_M2_RETROGRADE_ABLATION
version: 1.0
status: EVIDENCE
sheet_item: GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §4.7
weight_status: NO WEIGHT SHIPPED — probe ran in test code only; engine untouched
---

# WP8 M-2 — Retrograde qualifier + ablation (evidence, not ratification)

Sheet item (§4.7): pre-declare one Saturn + one Mars synthetic retro season
(done in `WP8_M2_RETROGRADE_WINDOWS_v1_0.md`, commit `73a7cd1a3`, before any
ablation code existed); verify the §5.2 vedha-row qualifier
`intensity_qualifier='retrograde_malefic'`; run with/without the declared
retrograde weight and report; confirm dwell stays geometry-only; ship no
weight. Every number below is a `WP8RETRO|` print from
`tests/l3/gochara/test_wp8_m2_retrograde_ablation.py` (6 tests, all passing).

## 1. Declared setup (from the pre-declaration, unchanged)

- SAT-RETRO-2013-SYN: Saturn, station-retrograde 2013-02-18 → station-direct
  2013-07-08, speed profile +0.017 → −0.030 → +0.017 °/d, loop centre 207.00°.
- MAR-RETRO-2013-SYN: Mars, 2013-04-16 → 2013-06-30, +0.520 → −0.350 → +0.520,
  loop centre 262.00°.
- Probe weight: p_i × (1 − 0.25) for sentences whose malefic body is
  retrograde at the evaluation instant — applied in test code only, by
  re-forming the noisy-OR after the engine's untouched `_compute_activity_v3`
  output. A drift-guard test asserts the probe path with w=0 reproduces the
  engine output bit-for-bit on sampled JDs.
- λ = declared co-factors (0.8 × 0.5) × activity, identical across arms, so
  every delta below isolates the weight.

## 2. §5.2 vedha-row qualifier — NOT_RUN

`WP8RETRO|s5.2_vedha_intensity_qualifier|present|False|status|NOT_RUN`

A grep of `services/` finds no `intensity_qualifier` anywhere. §5 of the
remainder brief is not executed on this branch, so the vedha-row qualifier
`intensity_qualifier='retrograde_malefic'` is reported **NOT_RUN** — an
honest result, per the pre-declaration §5. The ablation below does not depend
on it (it runs on activity-surface sentences, not vedha rows).

## 3. Crossings per season (declared metric 4 — identical across arms)

| season | crossings in season | crossing JD | speed at crossing |
|---|---|---|---|
| SAT-RETRO-2013-SYN | 1 | 2013-04-26 | retrograde (−0.030) |
| MAR-RETRO-2013-SYN | 1 | 2013-05-29 | retrograde (−0.350) |

Crossings are computed from the analytic tracks, independent of either arm;
both arms share the same gathered sentence set, so counts are identical by
construction — asserted and printed anyway. The out-of-season control
crossings (Saturn direct 2013-11-13; Mars direct 2013-03-18 and 2013-07-21)
bracket the seasons as pre-declared.

## 4. Metrics 1+2 — active days in-season, mean λ in vs out

| season | arm | active days in season | mean λ in-season | mean λ out-of-season |
|---|---|---|---|---|
| SAT | without | 31 | 0.087943 | 0.035714 |
| SAT | with | 31 | 0.073759 | 0.035714 |
| MAR | without | 20 | 0.105263 | 0.042907 |
| MAR | with | 20 | 0.078947 | 0.042907 |

Reading: the probe changes nothing outside the seasons (identical out-of-season
means — the weight fires only when the malefic is retrograde). In-season mean λ
drops 16.1% (Saturn season) and 25.0% (Mars season). Active-day counts do not
move: the attenuation lowers the plateau but does not zero it, so the
active/inactive boundary — the thing M-1's battery measures — is invariant
under this weight.

## 5. Metric 3 — peak-λ shift

| season | peak λ JD without | peak λ JD with | shift |
|---|---|---|---|
| SAT | 2013-03-13 | 2013-03-13 | 0.0 d |
| MAR | 2013-04-22 | 2013-04-22 | 0.0 d |

No shift in either season. (Both in-season peaks sit on the direct-motion
Mars/Saturn box edges inside the overlapping other season — the synthetic
geometry puts the maximum outside the attenuated crossings; recorded as
printed, not tuned.)

## 6. Metric 5 — dwell is geometry-only

Kernel episodes of the synthetic Saturn loop vs 207.00° at the declared
`orb_conj_slow` (1.0°), computed through `arcs.build_arc_index` →
`contacts.find_roots(refine=False)` → `episodes.build_episodes`:

| episode | branch | t_in | t_out | dwell_days |
|---|---|---|---|---|
| 0 | retrograde | 2013-03-24 | 2013-05-30 | 66.6667 |
| 1 | direct | 2013-09-16 | 2014-01-01 (horizon-truncated) | 106.8529 |

For every episode the test asserts `dwell_days == t_out − max(t_in,
prev t_out)` to 1e-9 d — the WP2 case-01 pinning
(`services/gochara_kernel/episodes.py:41-45, 282-319`). The 66.7-day retrograde
dwell emerges from the crossing instants alone; no weight participates
anywhere in the dwell path. **Dwell stays geometry-only: confirmed.**

## 7. Conclusion per the exit gate

- The probe weight moves only in-season intensity (mean λ −16% to −25%),
  leaves active-day counts, peak timing, crossings, and dwell untouched.
- **No weight is shipped.** The probe lives exclusively in
  `tests/l3/gochara/wp8synth.py::activity_at(retro_attenuation=...)`; engine
  code was not modified (drift guard proves the w=0 path is the engine's).
- §5.2 qualifier: **NOT_RUN** (reported, §2 above).

## 8. Provenance

- Pre-declaration: `WP8_M2_RETROGRADE_WINDOWS_v1_0.md` (commit `73a7cd1a3`).
- Tests: `platform/python-sidecar/tests/l3/gochara/test_wp8_m2_retrograde_ablation.py`
  (6 passing). Regenerate: `cd platform/python-sidecar && python3 -m pytest
  tests/l3/gochara/test_wp8_m2_retrograde_ablation.py -q -s`.
- Synthetic data only; no new citations.
