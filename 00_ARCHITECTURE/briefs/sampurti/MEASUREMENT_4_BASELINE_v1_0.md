---
artifact: MEASUREMENT_4_BASELINE
version: 1.0
status: PUBLISHED
campaign: SAMPŪRTI
phase: P2
published_at: 2026-08-13T04:15+05:30
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
field_snapshot_id: kfs_87484404af9d6fe9dc66a3d78812f8bc
weights_version: v0_classical
schema_version: x12_v0
tripwire_r15: NOT_FIRED
---

# SAMPŪRTI Measurement #4 — Field Baseline

**Publication tier**: BASELINE (earned; honest-null result acceptable per G-P2)
**Harness**: `w46_field_measurement4.py` over `kala_field_windows` λ (TemporalCurveModel)
**Control**: 1000-shuffle noise floor (w42 pattern, seed=42)
**Sealed split**: TRAIN events only (< 2020-01-01); TEST split sealed

---

## §1 — Field Corpus

| Property | Value |
|----------|-------|
| Table | `kala_field_windows` |
| Chart | `482012f1` (Abhisek Mohanty, native) |
| Total windows | 6,708 |
| Event classes | 6: childbirth, foreign_settlement, marriage, relocation, separation, surgery |
| Windows per class | 1,118 each |
| Average window duration | 1.4 days |
| Snapshot ID | `kfs_87484404af9d6fe9dc66a3d78812f8bc` |
| Weights version | `v0_classical` |
| Schema version | `x12_v0` |

**Field status note**: All 6,708 windows have `null_p = 1.0` — the observed λ_peak values
(range: 3.5×10⁻⁷ to 1.5×10⁻⁴) are below the global null distribution's max statistic
for all 256 replicates. This is expected at baseline: the field has not been calibrated
(integration layers P3+ required). The null_p signal is a within-window permutation test;
the scoring harness below measures a different quantity (local max proximity).

---

## §2 — LEL Coverage

| Category | Count |
|----------|-------|
| Total TRAIN events (< 2020-01-01) | 36 |
| Scorable (discrete onset, month-or-better precision) | 25 |
| **Strict field-class match** | **3** |
| Extended field-class match (total incl. strict) | 7 |
| Parked — no matching field class | 18 |
| Excluded by vagueness | 11 |

**Strict mapping** (exact semantic match to field event_class):
- `family/marriage` → `marriage`
- `health/surgery_minor` → `surgery`
- `residential+travel/foreign_move_start` → `foreign_settlement`

**Extended mapping** (loose semantic match, scored separately):
- `relationship/*` → `marriage` (3 additional romantic relationship events)
- `travel/*` → `foreign_settlement` (1 additional travel event)

**PARKED** (18 events): education (9), career (5), spiritual (1), creative (2), loss (1) —
no matching field class built yet. Field currently covers 6 of an eventual ≥13 event class set.

---

## §3 — Scoring Results

### Strict set (N=3)

| Metric | Value |
|--------|-------|
| Scored events | 3 |
| Hits | 3 |
| Hit rate | **1.000** |
| Noise floor mean | 0.702 |
| Noise floor std | 0.262 |
| Noise floor threshold (mean + 2σ) | 1.226 |
| Skill score | **1.000** ⚠ SEE NOTE |

⚠ **DEGENERATE THRESHOLD WARNING**: The top-tercile threshold = **0.0** for all 3 events.
This means the scoring is: "does any field window exist within ±45 days of the event?"
rather than "is the field significantly elevated?" The 1.4-day average window duration
means only ~5–7% of dates in a 5-year window have non-zero intensity; the top-tercile
of a mostly-zero curve is 0. Accordingly, ANY non-zero λ counts as "at or above threshold."

The apparent skill=1.0 should be read as: "all 3 strict events had at least one field
window within 45 days." Given noise floor=0.702 (70% base rate of random hits), achieving
3/3 on N=3 events is NOT statistically meaningful (one-sided p ≈ 0.026, but N=3 invalidates
normal approximations). **No meaningful skill has been demonstrated at this baseline.**

### Per-event detail (strict)

| Date | Domain | Field Class | Peak Date | Peak λ | Lag (days) | Passed |
|------|--------|-------------|-----------|--------|------------|--------|
| 2007-06-15 | health/surgery_minor | surgery | 2007-05-24 | 1.05×10⁻⁵ | -22 | ✓ |
| 2013-12-11 | family/marriage | marriage | 2014-01-08 | 4.90×10⁻⁵ | +28 | ✓ |
| 2019-05-15 | residential+travel/foreign_move_start | foreign_settlement | 2019-04-13 | 6.24×10⁻⁷ | -32 | ✓ |

### Extended set (N=7)

| Metric | Value |
|--------|-------|
| Scored events | 7 |
| Hits | 4 |
| Hit rate | **0.571** |
| Skill score | **-0.437** (worse than noise floor) |

---

## §4 — Noise Floor

Method: w42 pattern — 1000 shuffles of strict-event dates within TRAIN period (seed=42).

| Metric | Value |
|--------|-------|
| N shuffles | 1,000 |
| Seed | 42 |
| Mean hit rate | 0.702 |
| Std | 0.262 |
| Floor (mean + 2σ) | 1.226 |

Noise floor of 0.702 reflects that ~70% of random train dates have at least one field window
within ±45 days, given 1,118 windows × 1.4 days average duration across 35 TRAIN years.

---

## §5 — Degenerate-Interval Tripwire (R15)

**TRIPWIRE: NOT_FIRED**

Condition: < 3 strict-match events. Found: 3 (exactly at minimum threshold).
Note: the threshold=0 degenerate condition is separately flagged above (§3 warning).
This measurement is publishable at the BASELINE tier with the documented limitations.

---

## §6 — Interpretation and Next Steps

### What this measurement establishes:
1. The field exists, is built, and produces valid windows for 6 event classes.
2. For the 3 strict-match TRAIN events, the field has at least one window within ±45 days.
3. The scoring is degenerate (threshold=0) due to sparse 1.4-day windows.
4. No statistical skill claim is defensible at N=3.

### What this measurement does NOT establish:
- Predictive skill over the field's intended test of event concentration.
- Coverage for 18/25 scorable LEL categories (education, career, spiritual, etc.) — these
  require additional field event classes to be built in P3+.
- Calibrated λ values — all windows have null_p=1.0 at current baseline weights.

### What Measurement #5 (P3 / G-P3b gate) will show:
- After A4 x13 integration (schema bump x13_v0 → ?, weights refit, circular-shift test),
  windows MOVED vs. this baseline → skill delta shows whether integration improved the field.
- Per-seam ablation table beside #5.
- BRILLIANCE GATE #1 fires at G-P3b.

---

## §7 — VERIFIER Re-Derivation Target

To satisfy G-P2 "VERIFIER re-derives one number from raw output":

**Target number**: hit_count=3 for strict set.
**Re-derivation path**:
1. Load kala_field_windows for chart 482012f1, event_class='marriage'.
2. For event 2013-12-11 (family/marriage), build curve over 2011-06-13 to 2016-06-10
   at 5-day step intervals.
3. At each date d: intensity = Σ(λ_peak for marriage windows where start ≤ d ≤ end).
4. Top-tercile threshold = percentile_threshold(curve, 2/3).
5. Find local max within ±45 days of 2013-12-11.
6. Confirm: local max intensity (≈4.90×10⁻⁵) > 0.0 = threshold → passed=True.
7. Verify peak_date=2014-01-08, lag=+28 days, within_proximity=True.

Raw JSON: `MEASUREMENT_4_BASELINE_raw.json` (same directory).
