"""WP8 factor-level delta report (L3 §4.11).

Test-driven generator for `WP8_FACTOR_DELTA_REPORT_v1_0.md`: runs the full
engine (`_evaluate_single_from_context`, all DB-touching primitives patched to
synthetic sentences) on the synthetic marriage-2013 workload and the quarter
marriage class, once per flag individually and once with all flags together,
and prints per-factor deltas (promise / permission incl. denominator shift /
activity / tārā / w30 / quality_gates), peak counts, and (primitive × body)
slice contributions. Every reported number is a `WP8DELTA|` print here.

Configs (recorded flags of `services/gochara_v3/engine.py`):
- baseline: all legacy defaults
- m1: activity_shape="linear_no_box", orb_max_deg=1.0 (the §4.6 candidate)
- m3: moon_channel="separate"
- n14: nodal_drishti="removed"
- n15: sade_sati_mode="testimony"
- all: all four together

Structural detectors (not just prints): promise / tārā / quality_gates must
be identical across configs (no flag touches them); N-15 shifts the
permission denominator 1.0 → 0.9; N-14 sends w30 → 1.0.
"""
from __future__ import annotations

from .wp8synth import (
    daily_grid, evaluate_full, factor_row, peak_count, slice_contributions,
)
from .wp8workloads import build_marriage_2013, build_quarter_class

CONFIGS = {
    "baseline": {},
    "m1": {"activity_shape": "linear_no_box", "orb_max_deg": 1.0},
    "m3": {"moon_channel": "separate"},
    "n14": {"nodal_drishti": "removed"},
    "n15": {"sade_sati_mode": "testimony"},
    "all": {"activity_shape": "linear_no_box", "orb_max_deg": 1.0,
            "moon_channel": "separate", "nodal_drishti": "removed",
            "sade_sati_mode": "testimony"},
}

FACTORS = ("lambda", "promise", "permission", "activity", "tara", "w30",
           "quality_gates", "permission_denominator")


def _run(workload):
    jds = daily_grid(workload.jd0, workload.jd1)
    rows, lambdas = {}, {}
    for name, flags in CONFIGS.items():
        results = evaluate_full(workload, jds, **flags)
        rows[name] = factor_row(results)
        lambdas[name] = [r.raw_lambda for r in results]
    # slice_contributions runs on the activity surface; only activity-surface
    # flags apply (nodal_drishti/sade_sati_mode act on w30/permission, not on
    # the per-sentence p_i slices).
    act_flags = ("activity_shape", "orb_max_deg", "moon_channel")
    slices = {name: slice_contributions(
        workload, jds, **{k: v for k, v in flags.items() if k in act_flags})
        for name, flags in CONFIGS.items()}
    return jds, rows, lambdas, slices


def _print_rows(tag, rows, lambdas):
    base = rows["baseline"]
    for name in CONFIGS:
        r = rows[name]
        deltas = {f: round(r[f] - base[f], 6) for f in FACTORS}
        print(f"WP8DELTA|{tag}|config|{name}|"
              + "|".join(f"{f}|{round(r[f], 6)}" for f in FACTORS)
              + f"|peaks|{peak_count(lambdas[name])}")
        print(f"WP8DELTA|{tag}|config|{name}|delta_vs_baseline|"
              + ",".join(f"{f}:{deltas[f]:+}" for f in FACTORS))


def _check_invariants(rows):
    base = rows["baseline"]
    for name, r in rows.items():
        for f in ("promise", "tara", "quality_gates"):
            assert abs(r[f] - base[f]) < 1e-9, f"{name}: {f} moved ({base[f]} -> {r[f]})"
    assert abs(base["permission_denominator"] - 1.0) < 1e-9
    for name in ("n15", "all"):
        assert abs(rows[name]["permission_denominator"] - 0.9) < 1e-9, name
    for name in ("n14", "all"):
        assert abs(rows[name]["w30"] - 1.0) < 1e-9, name


def test_marriage_2013_factor_deltas():
    wl = build_marriage_2013()
    _jds, rows, lambdas, slices = _run(wl)
    _check_invariants(rows)
    _print_rows("marriage-2013", rows, lambdas)
    keys = sorted({k for s in slices.values() for k in s})
    for k in keys:
        print(f"WP8DELTA|marriage-2013|slice|{k[0]}|{k[1]}|"
              + "|".join(f"{name}|{round(slices[name].get(k, 0.0), 4)}"
                         for name in CONFIGS))


def test_quarter_marriage_factor_deltas():
    wl = build_quarter_class(0)
    _jds, rows, lambdas, slices = _run(wl)
    _check_invariants(rows)
    _print_rows("quarter-marriage", rows, lambdas)
    keys = sorted({k for s in slices.values() for k in s})
    for k in keys:
        print(f"WP8DELTA|quarter-marriage|slice|{k[0]}|{k[1]}|"
              + "|".join(f"{name}|{round(slices[name].get(k, 0.0), 4)}"
                         for name in CONFIGS))
