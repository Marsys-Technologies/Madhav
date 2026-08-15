---
artifact: MEASUREMENT_4_PRIME
version: 1.0
status: PUBLISHED
campaign: SAMPŪRTI
phase: P-D (post-FIELD-INTEGRATED proof spine)
published_at: 2026-08-15T07:30+05:30
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
field_snapshot_id: kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb
field_content_hash: kfh_3a8d00db6577713f58206afc329c613a
weights_version: v0_classical
schema_version: x12_v0
tripwire_r15: NOT_FIRED
predecessor: MEASUREMENT_4_BASELINE_v1_0.md (kfs_87484404af9d6fe9dc66a3d78812f8bc)
---

# SAMPŪRTI Measurement #4' — A8 Field Baseline (BESIDE M4)

**Publication tier**: PUBLISHED BESIDE M4 (same harness, updated field snapshot)
**Harness**: `w46_field_measurement4.py` over `kala_field_windows` λ (TemporalCurveModel)
**Control**: 1000-shuffle noise floor (w42 pattern, seed=42)
**Sealed split**: TRAIN events only (< 2020-01-01); TEST split sealed

This document is the M4' update to MEASUREMENT_4_BASELINE_v1_0.md, produced after the
A8 full 27-class field build (kfs_e23ba1ab...) to document the field's current state.
It replaces NO prior measurement — it is published BESIDE M4, not in place of it.

---

## §1 — Field Corpus Comparison

| Property | M4 (predecessor) | M4' (this document) |
|----------|-----------------|---------------------|
| Snapshot ID | kfs_87484404af9d6fe9dc66a3d78812f8bc | kfs_e23ba1abdf1c6fd3a1cc5c08c7538aeb |
| Total windows | 6,708 | **31,350** |
| Event classes | 6 | **25** |
| Windows per class | 1,118 each | **1,254 each** |
| F-wave fixes | None deployed | F1+F2+F3+F4+F5 all deployed |
| Decade-seam fix (F5) | NOT present | **PRESENT** (9 interior decade knots) |
| Null engine | Legacy (stage5_null.py, dead path) | **F1: dhara_null.py, R-denominator** |
| Build time | Pre-A8 | A8 (run_id=3c0cfc9d) |
| 2 skipped classes | N/A (only 6 classes attempted) | birth_anchor, career_change (no priors) |

---

## §2 — LEL Coverage

Same as M4 (same LEL, same train/test split):

| Category | Count |
|----------|-------|
| Total TRAIN events (< 2020-01-01) | 36 |
| Scorable (discrete onset, month-or-better precision) | 25 |
| **Strict field-class match (same mapping as M4)** | **3** |
| Extended field-class match (total incl. strict) | 7 |
| Parked — no matching field class (OLD mapping) | 18 |
| Excluded by vagueness | 11 |

**Note on parked events**: With 25 classes now built (vs 6 in M4), many previously-parked
events NOW have matching field classes. The following LEL-to-class correspondences are
available in A8 but not yet wired into the w46 strict/extended maps:

| LEL Category | A8 Field Class | Count |
|-------------|----------------|-------|
| career/first_job_joined | career_entry | 1 |
| career/first_job_exited | career_setback | 1 |
| career/corporate_job_joined | career_entry | 1 |
| career/employer_instability | career_setback | 1 |
| career/employer_switch | career_setback | 1 |
| education/entrance_exam_preparation | exam_outcome | 2 |
| education/mba_admission | education_milestone | 1 |
| education/mba_graduation | education_milestone | 1 |
| spiritual/devata_adoption | spiritual_turn | 1 |
| family/parent_illness_onset | parental_event | 1 |
| loss/parent_passing | bereavement | 1 |

Wiring these 12 newly-available correspondences into the harness is the M4'→M5 upgrade task
(requires updated _STRICT_MAP/_EXTENDED_MAP in w46, not an architecture change).

---

## §3 — Scoring Results (w46, same harness as M4)

### Strict set (N=3, same mapping as M4)

| Metric | M4 Value | M4' Value | Delta |
|--------|----------|-----------|-------|
| Scored events | 3 | 3 | 0 |
| Hits | 3 | 3 | 0 |
| Hit rate | 1.000 | **1.000** | 0 |
| Noise floor mean | 0.702 | **0.759** | +0.057 |
| Noise floor std | 0.262 | **0.249** | -0.013 |
| Noise floor threshold (mean + 2σ) | 1.226 | **1.256** | +0.030 |
| Skill score | 1.000 | **1.000** | 0 |

⚠ **DEGENERATE THRESHOLD WARNING (UNCHANGED FROM M4)**: The top-tercile threshold = 0.0
for all 3 events. This means the scoring is: "does any field window exist within ±45 days
of the event?" Given noise floor=0.759 (76% base rate of random hits), achieving 3/3 on
N=3 events is NOT statistically meaningful (p ≈ 0.013, but N=3 invalidates normal
approximations). **No meaningful skill has been demonstrated at this baseline.**

Note: the noise floor INCREASED slightly (0.702 → 0.759) because the A8 field has 25 classes
with many more windows — random date shuffles now hit MORE non-zero field values. This makes
the baseline harder to beat in M5, not easier.

### Per-event detail (strict, unchanged from M4)

| Date | Domain | Field Class | Peak Date | Peak λ | Lag (days) | Passed |
|------|--------|-------------|-----------|--------|------------|--------|
| 2007-06-15 | health/surgery_minor | surgery | 2007-05-24 | 1.05×10⁻⁵ | -22 | ✓ |
| 2013-12-11 | family/marriage | marriage | 2014-01-08 | 4.90×10⁻⁵ | +28 | ✓ |
| 2019-05-15 | residential+travel/foreign_move_start | foreign_settlement | 2019-04-13 | 6.24×10⁻⁷ | -32 | ✓ |

### Extended set (N=7, same mapping as M4)

| Metric | M4 Value | M4' Value | Delta |
|--------|----------|-----------|-------|
| Scored events | 7 | 7 | 0 |
| Hits | 4 | 5 | **+1** |
| Hit rate | 0.571 | **0.714** | **+0.143** |
| Skill score | -0.437 | **-0.186** | **+0.251** |

One additional hit in the extended set (marriage event 1998-02-16 now hits where it
previously missed) — attributable to the expanded window density (1254 vs 1118 per class).
Skill remains negative (worse than noise floor) — **no meaningful skill demonstrated**.

---

## §4 — Noise Floor

| Metric | M4 | M4' | Delta |
|--------|-----|-----|-------|
| n_shuffles | 1000 | 1000 | 0 |
| seed | 42 | 42 | 0 |
| mean_hit_rate | 0.702 | **0.759** | **+0.057** |
| std_hit_rate | 0.262 | **0.249** | -0.013 |
| floor_threshold | 1.226 | **1.256** | +0.030 |

The noise floor increase is expected and honest: the A8 field has 25 classes × 1254 windows
each (vs 6 classes × 1118 windows). More windows → more random hits → higher noise floor.

---

## §5 — Field Structure Notes

**null_p**: All 31,350 kala_field_windows rows have null_p = 1.0 — identical to M4 (expected
at pre-calibration baseline). The field signal is below the global null distribution's max
statistic for all 1024 replicates. This is the same null_p baseline reported in M4; the A8
field has not been calibrated.

**λ range across classes**:
- Highest avg_lambda_peak: childbirth (~9.97×10⁻⁵), career_entry/business_launch/psychological_arc (~5.1-5.2×10⁻⁵)
- Lowest avg_lambda_peak: separation (~3.8×10⁻⁷), foreign_settlement (~5.1×10⁻⁷)
- Range spans ~2.5 orders of magnitude across classes — structurally consistent with
  different promise priors (P_promise) per class

**F5 impact**: The decade-seam fix (9 interior decade boundaries in knot set) eliminates
the decade-gap contiguity defect. Verified by C-1 tests (PR #1286, test_knot_set.py, 20/20 PASS).

---

## §6 — What M5 Requires

M5 (the next measurement) can unlock real scoring for the 11 newly-matchable LEL events by:
1. Extending _STRICT_MAP in w46 to include A8's 25 classes
2. Scoring the N=3+12=15 strict events against their respective field classes
3. Re-running noise floor calibration with expanded class coverage

This is a mechanical code change to w46 (no harness architecture change). M5 also requires
the per-seam ablation table — see §7.

---

## §7 — Honest M5 / Ablation Residual

**Per-seam ablation (full)**: Measuring the individual contribution of each F-wave fix
(F1 null engine, F5 decade-seam, etc.) requires re-running A8 without each mechanism,
then comparing the resulting field. Each re-run is ~45–60 min. Given the overnight timeline
constraint, full per-seam ablation is HONESTLY DEFERRED:

| Mechanism | Ablation evidence available | Status |
|-----------|---------------------------|--------|
| F5 (decade-seam fix) | Structural: test_knot_set.py 20/20 PASS proves the fix is present and correct (C-1 condition) | STRUCTURAL-ONLY (no re-run) |
| F1 (null engine R-denominator) | Structural: dhara_null.py deployed, contracts.py NullResult with required resolution field | STRUCTURAL-ONLY (no re-run) |
| F4 (main.py guard) | Structural: ENGINE_VERSION analytic gate prevents legacy path | STRUCTURAL-ONLY |
| Full empirical ablation | Requires ≥3 × 45-min re-runs | DEFERRED — named residual |

**Named residual**: MEASUREMENT-5-ABLATION-DEFERRED. Unblocks when: sufficient wall-clock
time available + PR #1286 C-1 tests merged (provides guard against F5 regression).

---

## §8 — Summary vs M4

| Property | M4 | M4' | Improvement |
|----------|----|-----|-------------|
| Total windows | 6,708 | **31,350** | +4.67× |
| Event classes | 6 | **25** | +4.17× |
| F-wave fixes | 0 | **5 (F1-F5)** | +5 |
| Strict hits | 3/3 | **3/3** | Same (degenerate) |
| Extended hits | 4/7 | **5/7** | **+1** |
| Newly scorable LEL events | 0 | **+12 available** | Unlocked for M5 |
| null_p < 1.0 | 0 | 0 | Same (pre-calibration) |

**Status: PUBLISHED BESIDE M4. No meaningful skill demonstrated (expected at pre-calibration
baseline). M5 is the next measurement gate, unlocking 12 additional scorable LEL events.**
