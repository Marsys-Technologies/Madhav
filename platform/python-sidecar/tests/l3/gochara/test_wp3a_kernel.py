"""WP3a kernel acceptance tests — every WP2 geometry fixture must pass.

Fixture source: tests/l3/gochara/fixtures/wp2_geometry.json (independently
derived expected answers — WP2_FIXTURES.md shows every derivation). Synthetic
curves are sampled at daily noon-UT knots and built with a tight spline root
tolerance (1e-7″) because the cubics/lines are reproduced exactly by the
interpolant — the spline root IS the exact root, so the fixture pins (given
to the second) are asserted to 1 s.

E1 retained: the legacy F-07 tropical-arcs defect reproducer stays where it
is — 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_gochara/
E1_w2g_frame_defect.py — and is NOT moved into this suite. The kernel fixes
F-07 by construction (sidereal knots before arc-building, knots.py).
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
import swisseph as swe

from services.gochara_kernel import (
    KAKSHYA_LORD_ORDER,
    SPECIAL_DRISHTI_DEG,
    ArcIndexRegistry,
    build_coverage,
    contact_id,
    independence_group,
)
from services.gochara_kernel import arcs, contacts, episodes, ids, peaks
from services.gochara_kernel.knots import EphemerisBackendError, calc_sidereal_lon

from .conftest import EPHE_PATH, requires_swieph

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "wp2_geometry.json").read_text()
)
CASES = FIXTURES["cases"]

SYNTHETIC_TOL_ARCSEC = 1e-7


def jd_from_iso(iso: str) -> float:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def iso_from_jd(jd: float) -> str:
    y, m, d, h = swe.revjul(jd)
    hh = int(h)
    mm = round((h - hh) * 60)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}T{hh:02d}:{mm:02d}:00Z"


def daily_knots(start: date, end: date, curve) -> tuple[list[float], list[float]]:
    """Sample `curve(jd)` at noon-UT daily knots (F-15 abscissa)."""
    jds, lons = [], []
    d = start
    while d <= end:
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        jds.append(jd)
        lons.append(curve(jd) % 360.0)
        d += timedelta(days=1)
    return jds, lons


def assert_episode_matches(ep, expected: dict, tol_days: float = 1 / 86400.0):
    assert abs(ep.t_in - jd_from_iso(expected["t_in"])) < tol_days, (
        f"t_in {iso_from_jd(ep.t_in)} != {expected['t_in']}"
    )
    if expected.get("t_exact") is None:
        assert ep.t_exact is None and ep.exact_crossing is False
    else:
        assert ep.t_exact is not None, "t_exact missing"
        assert abs(ep.t_exact - jd_from_iso(expected["t_exact"])) < tol_days, (
            f"t_exact {iso_from_jd(ep.t_exact)} != {expected['t_exact']}"
        )
        assert ep.exact_crossing is True
    assert abs(ep.t_out - jd_from_iso(expected["t_out"])) < tol_days, (
        f"t_out {iso_from_jd(ep.t_out)} != {expected['t_out']}"
    )
    assert ep.branch == expected["branch"], f"branch {ep.branch} != {expected['branch']}"
    assert (ep.truncated_at_horizon or None) == expected.get("truncated_at_horizon")


# ── Case 01 — close-station cubic, three roots ───────────────────────────────

def test_case_01_close_station_cubic_three_roots():
    fx = CASES["case_01_close_station_cubic"]
    t0 = swe.julday(2026, 1, 1, 0.0)

    def cubic(jd):
        t = jd - t0
        return 270.0 + 0.001 * (t - 3) * (t - 6) * (t - 9)

    start = date(2025, 12, 20)
    end = date(2026, 1, 25)
    jds, lons = daily_knots(start, end, cubic)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)

    # Independent candidate enumeration (NOT "the kernel found N"): the cubic
    # f(t)/0.001 = t³ − 18t² + 99t − 162, solved here by numpy.roots.
    coeff = [1.0, -18.0, 99.0, -162.0]
    expected_roots = sorted(float(r.real) for r in np.roots(coeff) if abs(r.imag) < 1e-9)
    assert len(expected_roots) == 3

    # The arc index must retain BOTH stations of the close pair (E8-1 fix:
    # no coalescing) — stations at 6 ± √3 days.
    assert len(idx.stations) == 2
    assert abs(idx.stations[0] - (t0 + 6 - math.sqrt(3))) < 1e-5
    assert abs(idx.stations[1] - (t0 + 6 + math.sqrt(3))) < 1e-5

    roots = contacts.find_roots(idx, "Saturn", "conjunction", 270.0, refine=False)
    assert len(roots) == len(expected_roots)  # candidate set == independent set
    for root, expected_t in zip(roots, expected_roots):
        assert abs((root.spline_exact_jd - t0) - expected_t) < 1e-5

    horizon = (jd_from_iso(fx["inputs"]["horizon_utc"][0]),
               jd_from_iso(fx["inputs"]["horizon_utc"][1]))
    eps = episodes.build_episodes(
        idx, "Saturn", "conjunction", 270.0, roots, horizon, "orb_conj_slow"
    )
    expected = fx["expected"]["episodes"]
    assert len(eps) == len(expected) == 3
    for ep, exp in zip(eps, expected):
        assert_episode_matches(ep, exp)
        assert ep.branch == exp["branch"]
        assert ep.station_flag == exp["station_flag"]
        assert ep.exact_crossing == exp["exact_crossing"]
        assert ep.orb_max_deg == exp["orb_max_deg"]
        assert ep.orb_source == exp["orb_source"]
        assert abs(ep.dwell_days - exp["dwell_days"]) < 1e-3
    assert [e.branch for e in eps] == fx["expected"]["branches_in_order"]
    declared = fx["expected"]["declared_tolerances"]
    for ep in eps:
        assert ep.tolerance_arcsec == declared["tolerance_arcsec"]
        assert ep.bracket_seconds == declared["bracket_seconds"]
        assert ep.completeness_state == "qualified"


# ── Case 02 — true-node excursion under the mean-node convention ────────────

@requires_swieph
def test_case_02_mean_node_convention():
    fx = CASES["case_02_true_node_excursion"]
    # Recompute the 6-hour separation sweep independently, asserting the
    # SWIEPH backend on every call (F-14); a Moshier fallback is NOT_RUN.
    try:
        max_sep = 0.0
        max_at = None
        d = date(2026, 1, 1)
        jd0 = swe.julday(d.year, d.month, d.day, 0.0)
        for i in range(1465):
            jd = jd0 + i * 0.25
            lon_t, rf_t = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            if not (rf_t & 2) or (rf_t & 4):
                pytest.skip(f"NOT_RUN: TRUE_NODE retflag {rf_t} (F-14)")
            lon_m, rf_m = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            if not (rf_m & 2) or (rf_m & 4):
                pytest.skip(f"NOT_RUN: MEAN_NODE retflag {rf_m} (F-14)")
            sep = abs(lon_t[0] - lon_m[0]) % 360.0
            sep = min(sep, 360.0 - sep)
            if sep > max_sep:
                max_sep, max_at = sep, jd
    except EphemerisBackendError as e:
        pytest.skip(f"NOT_RUN: {e}")
    assert max_sep * 3600.0 == pytest.approx(
        fx["expected"]["max_abs_true_minus_mean_arcsec_2026"], abs=0.01
    )
    assert iso_from_jd(max_at) == fx["expected"]["max_at_utc"]

    # The kernel's node positions are MEAN positions: at the pinned max
    # instant the kernel's Rahu longitude equals the fixture's mean value,
    # and differs from TRUE by the pinned excursion.
    mean_lon, rf = calc_sidereal_lon("Rahu", max_at, EPHE_PATH)
    assert rf & 2
    assert mean_lon * 3600.0 == pytest.approx(
        fx["derivation_detail"]["positions_at_max"]["mean_node_sidereal_deg"] * 3600.0,
        abs=1e-3,
    )


# ── Case 03 — seam tangency at a partition boundary ──────────────────────────

def test_case_03_seam_tangency_single_episode():
    fx = CASES["case_03_seam_tangency"]
    t0 = swe.julday(2026, 3, 1, 0.0)

    # NOTE: the fixture's curve string "270.0 + 0.1*(t-5)" is a typo — its own
    # derivation and every pinned value (contact at t=5 = 2026-03-06, orb span
    # 2026-02-24 → 2026-03-16 = target ± 1.0° at 0.1°/day) are self-consistent
    # only with the constant 270.5, which is what we build here.
    def line(jd):
        return 270.5 + 0.1 * (jd - t0 - 5.0)

    jds, lons = daily_knots(date(2026, 2, 20), date(2026, 3, 17), line)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (jds[0], jds[-1])  # knot window — the pinned orb exit (03-16) lies inside it
    eps = episodes.solve_episodes(
        idx, "Saturn", "conjunction", 270.5, horizon, "orb_conj_slow", refine=False
    )
    expected = fx["expected"]["episodes"]
    assert len(eps) == fx["expected"]["episode_count"] == 1
    assert_episode_matches(eps[0], expected[0])

    # Partition attribution: the kernel solves ONCE and attributes (re-solving
    # per partition would duplicate or truncate seam episodes). End-closed
    # rule: a contact whose t_exact equals a partition seam belongs to the
    # partition whose END it equals (partition A). Exactly one owner, and it
    # must be A — zero episodes and two episodes are both failures.
    partitions = [
        (jd_from_iso(fx["inputs"]["partition_A_utc"][0]), jd_from_iso(fx["inputs"]["partition_A_utc"][1])),
        (jd_from_iso(fx["inputs"]["partition_B_utc"][0]), jd_from_iso(fx["inputs"]["partition_B_utc"][1])),
    ]
    attributed = episodes.attribute_partition(eps, partitions)
    assert len(attributed[0]) == 1
    assert attributed[0][0].t_exact == pytest.approx(jd_from_iso(expected[0]["t_exact"]))
    assert len(attributed[1]) == 0  # the seam contact is owned by A, not duplicated into B


# ── Case 04 — start-inside / end-inside at the horizon edge ─────────────────

def _case_04_index(curve):
    jds, lons = daily_knots(date(2026, 3, 20), date(2026, 5, 10), curve)
    return jds, arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)


def test_case_04a_start_inside_exact_outside():
    fx = CASES["case_04_horizon_edge_truncation"]["subcases"]["start_inside_exact_outside_before"]
    h0 = jd_from_iso("2026-04-01T00:00:00Z")

    def curve(jd):
        return 268.5 + 0.05 * (jd - h0)

    jds, idx = _case_04_index(curve)
    horizon = (h0, jd_from_iso("2026-05-01T00:00:00Z"))
    eps = episodes.solve_episodes(
        idx, "Saturn", "conjunction", 268.0, horizon, "orb_conj_slow", refine=False
    )
    expected = fx["expected"]["episodes"]
    assert len(eps) == fx["expected"]["episode_count"] == 1
    ep = eps[0]
    assert_episode_matches(ep, expected[0])
    assert ep.truncated_at_horizon == "start"
    assert ep.t_exact is None  # never fabricated inside the horizon
    assert ep.exact_crossing is False
    assert ep.dwell_days == pytest.approx(expected[0]["orb_overlap_days"], abs=1e-3)


def test_case_04b_end_inside_exact_inside():
    fx = CASES["case_04_horizon_edge_truncation"]["subcases"]["end_inside_exact_inside"]
    h0 = jd_from_iso("2026-04-01T00:00:00Z")

    def curve(jd):
        return 269.5 - 0.06 * (jd - h0)

    jds, idx = _case_04_index(curve)
    horizon = (h0, jd_from_iso("2026-05-01T00:00:00Z"))
    eps = episodes.solve_episodes(
        idx, "Saturn", "conjunction", 268.0, horizon, "orb_conj_slow", refine=False
    )
    expected = fx["expected"]["episodes"]
    assert len(eps) == fx["expected"]["episode_count"] == 1
    ep = eps[0]
    assert_episode_matches(ep, expected[0])
    assert ep.truncated_at_horizon == "end"
    assert ep.t_out == pytest.approx(horizon[1])  # t_out pinned to the horizon end, never folded
    assert ep.dwell_days == pytest.approx(expected[0]["orb_overlap_days"], abs=1e-3)
    # WP2 case 04b pins branch 'direct' for a bare negative-slope stretch whose
    # station lies outside the searched horizon — see episodes.py for the
    # pinned branch classification rule.


# ── Case 05 — noon/midnight epoch conversion (F-15) ─────────────────────────

@requires_swieph
def test_case_05_noon_knot_abscissa():
    fx = CASES["case_05_noon_midnight_epoch"]
    # The kernel samples knots ONLY at noon UT; the knot abscissa fraction
    # must be exactly 0.5 (12:00) and reproduce the pinned substrate value.
    from services.gochara_kernel.knots import sample_knots

    try:
        series = sample_knots("Moon", date(2026, 6, 13), date(2026, 6, 17), EPHE_PATH)
    except EphemerisBackendError as e:
        pytest.skip(f"NOT_RUN: {e}")
    assert series.ephemeris_backend["backend"] == "swieph"
    # Julian days start at NOON UT: a noon-UT knot is an integer JD
    # (midnight would be fraction 0.5 — the F-15 trap asserts we never see it).
    for jd in series.knot_jds:
        assert abs(jd - round(jd)) < 1e-6, "knot abscissa is not noon UT (F-15)"
    noon_jd = swe.julday(2026, 6, 15, 12.0)
    i = series.knot_jds.index(noon_jd)
    assert series.longitudes_deg[i] * 3600.0 == pytest.approx(
        fx["derivation_detail"]["moon_sidereal_noon_deg"] * 3600.0, abs=1e-3
    )
    # The wrong-answer detector: midnight abscissa is ~27,544″ away — a kernel
    # consuming noon knots as midnight would dwarf every §9 tolerance.
    mid_lon, rf = calc_sidereal_lon("Moon", swe.julday(2026, 6, 15, 0.0), EPHE_PATH)
    assert rf & 2
    diff = abs(mid_lon - series.longitudes_deg[i]) % 360.0
    diff = min(diff, 360.0 - diff)
    assert diff * 3600.0 == pytest.approx(
        fx["expected"]["difference_arcsec"], abs=0.01
    )


# ── Case 06 — per-graha special dṛṣṭi angles (N-14) ─────────────────────────

def test_case_06_special_drishti_table():
    fx = CASES["case_06_special_drishti_table"]["expected"]["drishti_angles_deg"]
    assert SPECIAL_DRISHTI_DEG == fx
    assert SPECIAL_DRISHTI_DEG["Rahu"] == [] and SPECIAL_DRISHTI_DEG["Ketu"] == []
    assert KAKSHYA_LORD_ORDER[0] == "Saturn" and KAKSHYA_LORD_ORDER[7] == "Lagna"

    # A synthetic arc sweeping 0.5°/day across two full revolutions: Saturn
    # must produce dṛṣṭi roots at exactly its three angles; Rāhu must produce
    # NONE (N-14) while remaining a valid conjunction agent.
    t0 = swe.julday(2026, 1, 1, 12.0)

    def sweep(jd):
        return 0.5 * (jd - t0)

    jds, lons = daily_knots(date(2025, 12, 1), date(2028, 12, 1), sweep)
    horizon = (jds[0], jds[-1])

    idx_sat = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    eps_sat = episodes.solve_episodes(
        idx_sat, "Saturn", "drishti_contact", 100.0, horizon, "orb_drishti_slow", refine=False
    )
    aspects = sorted({e.aspect_deg for e in eps_sat})
    assert aspects == [60.0, 180.0, 270.0]
    assert all(e.target_deg == 100.0 for e in eps_sat)
    assert all(e.orb_source == "orb_drishti_slow" for e in eps_sat)

    idx_rah = arcs.build_arc_index("Rahu", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    eps_rah = episodes.solve_episodes(
        idx_rah, "Rahu", "drishti_contact", 100.0, horizon, "orb_drishti_slow", refine=False
    )
    assert eps_rah == []  # no nodal dṛṣṭi at all — not even the 7th (N-14)
    eps_rah_conj = episodes.solve_episodes(
        idx_rah, "Rahu", "conjunction", 100.0, horizon, "orb_conj_slow", refine=False
    )
    assert len(eps_rah_conj) > 0  # nodes remain full conjunction agents/targets


# ── Case 12 — plateau ties in peak detection ────────────────────────────────

def test_case_12_plateau_ties():
    fx = CASES["case_12_plateau_ties"]
    series = fx["inputs"]["series"]
    start = jd_from_iso(fx["inputs"]["series_start_utc"])
    step = 1.0  # days
    admitted = peaks.admit_peaks(series)
    assert len(admitted) == fx["expected"]["peak_count"] == 4
    assert all(p.rank == 1 for p in admitted)
    assert all(abs(p.value - fx["inputs"]["max_value"]) < 1e-12 for p in admitted)
    dates = [iso_from_jd(start + p.index * step) for p in admitted]
    assert dates == fx["expected"]["peak_dates_utc"]
    # H-5: no fixed cap at admission; a serve-time trim is a separate,
    # explicit operation that never re-ranks.
    trimmed = peaks.admit_peaks(series, max_rows=2)
    assert len(trimmed) == 2 and all(p.rank == 1 for p in trimmed)


# ── Honesty cases 07–09 through the kernel's resolution-facing interfaces ────

def test_case_07_negative_sensitive_check_yields_zero_targets():
    # N-12/WP3c R-1 removes negative sensitive-degree rows at the resonance
    # layer. At the kernel boundary the honest shape is: zero targets in, zero
    # episodes out, and a coverage record that says the search ran.
    from services.gochara_kernel.convention import canonical_convention_id

    cov = build_coverage(
        chart_id="wp2-synth-00000000-0000-4000-8000-000000000007",
        generation="wp3a-test",
        partition_kind="body_target",
        partition_key="saturn:sensitive_degree",
        requested_horizon=(0.0, 1.0),
        completed_horizon=(0.0, 1.0),
        resolution_arcsec=2.0,
        relations_searched=("conjunction",),
        resolution_states={},  # zero targets requested, none carried
        convention_id=canonical_convention_id(),
        ephemeris_backend={"backend": "n/a (synthetic)"},
    )
    assert cov.targets_requested == 0 and cov.targets_resolved == 0
    assert cov.targets_unresolved == 0


def test_case_08_cusp_placeholder_arudha_never_a_point():
    # F-20: arudha longitude_sidereal is a sign-cusp placeholder. The kernel's
    # interval-target interface (M-5) accepts ONLY spans; a point shaped like
    # 270.0000° is unrepresentable, and the span produces a residence interval
    # with ingress — never a degree-level point contact.
    h0 = jd_from_iso("2026-01-01T00:00:00Z")

    def curve(jd):
        return 250.0 + 0.4 * (jd - h0)  # sweeps 250°→~275° through [270,300)

    jds, lons = daily_knots(date(2025, 12, 15), date(2026, 2, 25), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (jds[0], jds[-1] - 3.0)  # horizon ends before the knot window does
    spans = episodes.residence_spans(
        idx, "Saturn", (270.0, 300.0), horizon, "arudha", refine=False
    )
    assert len(spans) == 1
    span = spans[0]
    assert (span.span_lo_deg, span.span_hi_deg) == (270.0, 300.0)
    assert span.t_enter == pytest.approx(h0 + 20.0 / 0.4, abs=1e-4)  # λ=270 at t=50 d
    assert span.t_exit == pytest.approx(horizon[1], abs=1e-6)  # clipped to the horizon
    assert span.truncated_at_horizon == "end"
    assert span.ingress_episode.relation == "sign_ingress"
    # No episode against the span may carry a point target at 270.0000:
    # ingress episodes are boundary-exact with orb 0 and the span is an
    # interval object (ResidenceSpan), never a degree contact.
    assert span.ingress_episode.orb_max_deg == 0.0
    with pytest.raises(ValueError):
        episodes.residence_spans(idx, "Saturn", (300.0, 270.0), horizon, "arudha")


def test_case_09_dangling_yoga_id_unavailable_in_coverage():
    # F-21: a yoga id with no live firing row is counted in the coverage
    # manifest as 'unavailable' — never a silent skip, never an invented degree.
    from services.gochara_kernel.convention import canonical_convention_id

    cov = build_coverage(
        chart_id="wp2-synth-00000000-0000-4000-8000-000000000009",
        generation="wp3a-test",
        partition_kind="body_target",
        partition_key="jupiter:yoga_constituent:ardhachandra",
        requested_horizon=(0.0, 1.0),
        completed_horizon=(0.0, 1.0),
        resolution_arcsec=2.0,
        relations_searched=("conjunction",),
        resolution_states={"unavailable": 2},
        convention_id=canonical_convention_id(),
        ephemeris_backend={"backend": "n/a (synthetic)"},
    )
    assert cov.targets_unresolved == 2
    assert cov.target_resolution_state_counts == {"unavailable": 2}
    # Invariant enforcement: a record whose counts do not add up is refused.
    from services.gochara_kernel.coverage import CoverageRecord

    with pytest.raises(ValueError):
        CoverageRecord(
            chart_id="x", generation="g", partition_kind="body_target",
            partition_key="k", requested_horizon=(0.0, 1.0), completed_horizon=(0.0, 1.0),
            resolution_arcsec=2.0, relations_searched=(),
            targets_requested=3, targets_resolved=1, targets_unresolved=1,
            target_resolution_state_counts={"unavailable": 1},
            unavailable_inputs={}, unsearched_reason=None,
            convention_id="c", ephemeris_backend={},
        )


# ── ids (WP1_CONTRACTS.md §3.2) + H-6 independence ──────────────────────────

def test_contact_id_and_independence_group():
    conv = ids.floor_to_minute_utc_iso((swe.julday(2026, 3, 6, 0.0) - 2440587.5) * 86400.0)
    assert conv == "2026-03-06T00:00:00Z"
    jd = swe.julday(2026, 3, 6, 0.0) + 37 / 86400.0  # 37 s past the minute
    c1 = contact_id(
        chart_id="wp2-synth-00000000-0000-4000-8000-000000000003",
        convention_id="sha256:abc",
        body="Saturn", target_type="karaka", relation="conjunction",
        aspect_deg=0.0, t_exact_jd=jd, target_ref="Sun", method_version="1.0.0",
    )
    c2 = contact_id(
        chart_id="wp2-synth-00000000-0000-4000-8000-000000000003",
        convention_id="sha256:abc",
        body="Saturn", target_type="karaka", relation="conjunction",
        aspect_deg=0.0, t_exact_jd=jd + 20 / 86400.0,  # same minute
        target_ref="Sun", method_version="1.0.0",
    )
    assert c1 == c2  # minute-floored: ±30 s jitter cannot move the id
    g1 = independence_group(
        body="Saturn", relation="conjunction", aspect_deg=0.0,
        target_deg=100.0, t_exact_jd=jd, t_fallback_jd=jd,
    )
    g2 = independence_group(
        body="Saturn", relation="conjunction", aspect_deg=0.0,
        target_deg=100.0, t_exact_jd=jd + 20 / 86400.0, t_fallback_jd=jd,
    )
    assert g1 == g2  # H-6: one physical contact via several rules counts once
    g3 = independence_group(
        body="Saturn", relation="conjunction", aspect_deg=0.0,
        target_deg=101.0, t_exact_jd=jd, t_fallback_jd=jd,
    )
    assert g3 != g1


# ── Arc lifecycle: built once per (body × substrate_version × window) ────────

def test_arc_index_registry_builds_once():
    t0 = swe.julday(2026, 1, 1, 12.0)
    jds, lons = daily_knots(date(2026, 1, 1), date(2026, 3, 1),
                            lambda jd: 100.0 + 0.1 * (jd - t0))
    from services.gochara_kernel.knots import KnotSeries

    series = KnotSeries(
        body="Saturn", start_date=date(2026, 1, 1), end_date=date(2026, 3, 1),
        knot_jds=tuple(jds), longitudes_deg=tuple(lons),
        ephemeris_backend={"backend": "n/a (synthetic)"},
    )
    reg = ArcIndexRegistry()
    a1 = reg.get_from_series("Saturn", "substrate-v1", date(2026, 1, 1), date(2026, 3, 1), series)
    a2 = reg.get_from_series("Saturn", "substrate-v1", date(2026, 1, 1), date(2026, 3, 1), series)
    assert a1 is a2 and reg.build_count == 1
    reg.get_from_series("Saturn", "substrate-v2", date(2026, 1, 1), date(2026, 3, 1), series)
    assert reg.build_count == 2  # a new substrate_version rebuilds
