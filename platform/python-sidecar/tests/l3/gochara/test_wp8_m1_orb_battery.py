"""WP8 M-1 orb battery (L3 §4.6) — evidence, not a ruling.

Six arms on the two pre-declared synthetic workloads (marriage-2013;
ordinary quarter 2027-03→05): legacy box ±5 d · no-box×5.0° · ×2.0° ·
×1.0° · ×0.5° — plus a no-box×10.0° wide-end control as the sixth arm
(the sheet says "six arms" while listing five; the interpretation is
recorded in WP8_M1_ORB_BATTERY_v1_0.md §2).

Every number printed here is transcribed into WP8_M1_ORB_BATTERY_v1_0.md.
Assertions are detectors only (determinism, bounds, independent analytic
re-derivation, engine cross-check); the comparative metrics are printed
for the report, not fitted to expectations.

Synthetic data only (invented geometry; no real chart, no person).
"""
from __future__ import annotations

import math

import pytest

from services.gochara_v3 import engine

from .wp8synth import (
    activity_at, active_day_count, daily_grid, dynamic_range, evaluate_full,
    lam_series, recall_metrics, windows,
)
from .wp8workloads import (
    ENVELOPE_ONLY_CLASSES, build_envelope_class, build_marriage_2013,
    build_quarter_class,
)

MAIN_ARMS = [
    ("legacy_box", {}),
    ("no_box_10.0", dict(activity_shape="linear_no_box", orb_max_deg=10.0)),
    ("no_box_5.0", dict(activity_shape="linear_no_box", orb_max_deg=5.0)),
    ("no_box_2.0", dict(activity_shape="linear_no_box", orb_max_deg=2.0)),
    ("no_box_1.0", dict(activity_shape="linear_no_box", orb_max_deg=1.0)),
    ("no_box_0.5", dict(activity_shape="linear_no_box", orb_max_deg=0.5)),
]
# Plateau set: 0.5×/2× of every no-box candidate (union, deduplicated).
PLATEAU_ORBS = (10.0, 5.0, 4.0, 2.5, 2.0, 1.0, 0.5, 0.25)


def _report_line(*parts):
    print("WP8BATT|" + "|".join(str(p) for p in parts))


# ── Detector 0: harness surface == full engine activity term ─────────────────

def test_harness_matches_full_engine_activity():
    wl = build_marriage_2013()
    samples = [wl.jd0 + off for off in (0.0, 40.0, 75.0, 130.0, 196.0, 222.0,
                                        250.0, 300.0, 312.0, 340.0, 364.0)]
    jds = samples
    full_legacy = evaluate_full(wl, jds)
    full_nobox = evaluate_full(wl, jds, activity_shape="linear_no_box",
                               orb_max_deg=1.0)
    for jd, r_leg, r_nb in zip(jds, full_legacy, full_nobox):
        a_leg, _ = activity_at(wl, jd)
        a_nb, _ = activity_at(wl, jd, activity_shape="linear_no_box",
                              orb_max_deg=1.0)
        assert abs(r_leg.x_t - a_leg) < 1e-9, f"legacy mismatch at {jd}"
        assert abs(r_nb.x_t - a_nb) < 1e-9, f"no-box mismatch at {jd}"
    _report_line("crosscheck", "engine==harness", len(jds), "jds", "OK")


# ── Detector 1: legacy active-day count == independent analytic box union ────

def test_legacy_active_days_equals_analytic_box_union():
    wl = build_marriage_2013()
    jds = daily_grid(wl.jd0, wl.jd1)
    series = lam_series(wl, jds)
    got = active_day_count(series)
    # Independent derivation: day is active iff within ±5 d of a sentence's
    # event_jd (the box), given every synthetic sentence scores p_i > 0.
    crossing_jds = [s.event_jd for s in wl.sentences]
    expect = sum(1 for jd in jds
                 if any(abs(jd - t) <= 5.0 for t in crossing_jds))
    _report_line("marriage-2013", "legacy_box", "active_days_engine", got,
                 "active_days_analytic", expect)
    assert got == expect


# ── Detector 2: active-day monotonicity in orb ───────────────────────────────

def test_active_days_monotone_in_orb():
    wl = build_marriage_2013()
    jds = daily_grid(wl.jd0, wl.jd1)
    counts = [active_day_count(lam_series(
        wl, jds, activity_shape="linear_no_box", orb_max_deg=v))
        for v in sorted(PLATEAU_ORBS)]
    _report_line("marriage-2013", "monotonicity",
                 ",".join(map(str, sorted(PLATEAU_ORBS))),
                 ",".join(map(str, counts)))
    assert all(a <= b for a, b in zip(counts, counts[1:]))


# ── Battery: marriage-2013 main arms ─────────────────────────────────────────

def test_battery_marriage_main_arms():
    wl = build_marriage_2013()
    jds = daily_grid(wl.jd0, wl.jd1)
    for arm, kw in MAIN_ARMS:
        series = lam_series(wl, jds, **kw)
        rec = recall_metrics(series, jds, wl.anchors)
        rng = dynamic_range(series, jds)
        wins = windows(series, jds)
        anchor_peak = max((a["lam_margin"] + rec["median_background_lam"]
                           for a in rec["anchors"]), default=0.0)
        ratio = (anchor_peak / rng["median_active"]
                 if rng["median_active"] > 0 else 0.0)
        for a in rec["anchors"]:
            _report_line("marriage-2013", arm, "anchor", a["label"],
                         "recalled", a["recalled"], "rank", a["rank"],
                         "lam_margin", round(a["lam_margin"], 6))
        _report_line("marriage-2013", arm, "recall", rec["recalled"], "of",
                     rec["of"], "active_days", active_day_count(series),
                     "windows", len(wins),
                     "variance_active", round(rng["variance_active"], 8),
                     "median_active", round(rng["median_active"], 6),
                     "anchor_peak_over_median", round(ratio, 4))


def test_battery_marriage_plateau():
    """Plateau stability: every no-box candidate at 0.5×/2× of itself."""
    wl = build_marriage_2013()
    jds = daily_grid(wl.jd0, wl.jd1)
    for v in PLATEAU_ORBS:
        series = lam_series(wl, jds, activity_shape="linear_no_box",
                            orb_max_deg=v)
        rec = recall_metrics(series, jds, wl.anchors)
        rng = dynamic_range(series, jds)
        _report_line("marriage-2013", f"plateau_{v}", "recall", rec["recalled"],
                     "of", rec["of"], "active_days", active_day_count(series),
                     "windows", len(windows(series, jds)),
                     "variance_active", round(rng["variance_active"], 8),
                     "margins",
                     ",".join(str(round(a["lam_margin"], 4))
                              for a in rec["anchors"]))


# ── Battery: 13 envelope-only classes, distinct windows (metric iii) ─────────

def test_battery_envelope_classes_windows():
    for i, cls in enumerate(ENVELOPE_ONLY_CLASSES):
        wl = build_envelope_class(i)
        jds = daily_grid(wl.jd0, wl.jd1)
        counts = {}
        for arm, kw in MAIN_ARMS:
            series = lam_series(wl, jds, **kw)
            counts[arm] = (len(windows(series, jds)), active_day_count(series))
        for arm, (nw, nd) in counts.items():
            _report_line(f"class:{cls}", arm, "cluster_delta",
                         wl.cluster_delta_days, "windows", nw,
                         "active_days", nd)


# ── Battery: ordinary quarter 2027-03→05 (control) ──────────────────────────

def test_battery_quarter_control():
    totals = {arm: 0 for arm, _ in MAIN_ARMS}
    for i, cls in enumerate(ENVELOPE_ONLY_CLASSES):
        wl = build_quarter_class(i)
        jds = daily_grid(wl.jd0, wl.jd1)
        for arm, kw in MAIN_ARMS:
            series = lam_series(wl, jds, **kw)
            nw, nd = len(windows(series, jds)), active_day_count(series)
            totals[arm] += nd
            _report_line(f"quarter:{cls}", arm, "windows", nw,
                         "active_days", nd)
    for arm, total in totals.items():
        _report_line("quarter:TOTAL", arm, "active_days", total)


# ── Detector 3: ordinary-quarter active-day totals are bounded and honest ────

def test_quarter_zero_contact_classes_report_zero_windows():
    zero = []
    for i, cls in enumerate(ENVELOPE_ONLY_CLASSES):
        wl = build_quarter_class(i)
        if not wl.sentences:
            jds = daily_grid(wl.jd0, wl.jd1)
            series = lam_series(wl, jds)
            assert active_day_count(series) == 0
            zero.append(cls)
    _report_line("quarter", "zero_contact_classes", ",".join(zero))
    assert zero  # at least one class honestly has no contacts
