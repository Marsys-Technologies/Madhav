# WP8_M2_RETROGRADE_WINDOWS_v1_0 — pre-declared synthetic ablation windows (M-2, L3 §4.7)

**Status: PRE-DECLARATION, written BEFORE any ablation code exists.** The windows,
the candidate weight, and the metrics below are fixed here in advance; the ablation
(`WP8_M2_RETROGRADE_ABLATION_v1_0.md`, to follow) reports against exactly this
declaration. Changing a window or a metric after seeing numbers is not permitted —
a post-hoc edit would invalidate the declaration's purpose.

**Data class: SYNTHETIC.** Invented chart geometry in the shape of plan §3 F-02
walkthroughs. No real chart, no real person, no real ephemeris season is used or
implied. The calendar dates below parameterise an analytic toy ephemeris, nothing
else.

## 1. Declared ablation windows (synthetic retrograde seasons)

| window | body (malefic) | station-retrograde (UTC) | station-direct (UTC) | speed profile (°/d, piecewise linear) | loop centre |
|---|---|---|---|---|---|
| SAT-RETRO-2013-SYN | Saturn | 2013-02-18 | 2013-07-08 | +0.017 → −0.030 → +0.017 | 207.00° |
| MAR-RETRO-2013-SYN | Mars | 2013-04-16 | 2013-06-30 | +0.520 → −0.350 → +0.520 | 262.00° |

Speeds outside the seasons are the constant direct values. The seasons were chosen
to sit inside the synthetic marriage-2013 workload year (WP8 M-1 battery,
`WP8_M1_ORB_BATTERY_v1_0.md`) so the ablation and the orb battery share one toy
universe; they are invented, not the real 2013 seasons.

## 2. Declared candidate weight (experiment only — never shipped)

The ablation applies, in **test code only** (the engine is not modified), an
attenuation `w = 0.25` to the per-sentence activity contribution `p_i` of every
sentence whose transit body is a malefic (Saturn or Mars) **and retrograde at the
evaluation instant**:

    p_i' = p_i × (1 − 0.25)   when body ∈ {Saturn, Mars} and speed(body, t_jd) < 0
    p_i' = p_i                otherwise

`w = 0.25` is a declared arbitrary probe value, chosen to be large enough to
detect and small enough to be plausible; it carries **no doctrinal claim** (`[U]`
— no transit-dwell/retrograde-weight doctrine exists in the served corpus, per
GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §M-2). **No weight is shipped regardless of
the outcome** (L3 §4.7 exit gate).

## 3. Declared metrics (arms: WITHOUT weight vs WITH weight)

1. Active-day count inside each declared season (daily grid, activity > 0).
2. Mean λ in-season vs mean λ out-of-season (λ = declared co-factors × activity;
   co-factors held identical across arms so the delta isolates the weight).
3. Peak-λ shift: JD of the λ maximum inside each season, per arm, in days.
4. Crossings per season (count of exact contact roots) — must be identical across
   arms (the weight may not change the geometry, only the scoring).
5. Dwell check: `dwell_days` on the kernel episodes of each season — asserted
   equal to its geometric definition `t_out,k − max(t_in,k, t_out,k−1)` (WP2 case
   01 pinning, `services/gochara_kernel/episodes.py`), i.e. **geometry-only, no
   weight**. A retrograde loop's dwell must emerge from the crossing instants
   alone.

## 4. Dependency note (§5.2)

The M-2 task row also names `intensity_qualifier='retrograde_malefic'` on vedha
rows as "done in §5.2". §5 of the remainder brief is **not executed** on this
branch; whether the qualifier exists is verified at ablation time and reported
honestly (`NOT_RUN` if absent) in the ablation report. This declaration does not
depend on it: the ablation below runs on activity-surface sentences, not vedha
rows.

## 5. Reporting rule

Every number in the ablation report is printed by a passing test in
`tests/l3/gochara/test_wp8_m2_retrograde_ablation.py`. A green with no detector
is not a result; `NOT_RUN` is a result.
