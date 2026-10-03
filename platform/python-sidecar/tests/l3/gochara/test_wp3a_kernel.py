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

Tier 0-G regression index (Pravāha A2.1; GOCHARA_DESIGN_SPECS_v1_4 §6.2,
GOCHARA_TEST_ORACLES_v1_4) — the mutation guards live in THIS file unless
noted:
  aspect_direction        (T0-1/#13): test_oad_aspect_direction[*],
                          test_oad_levels_computed_as_target_minus_angle
  zero_degree_seam        (T0-2/#14): test_oss2_case1_*, test_oss2_case2_*,
                          test_oss1_boundary_counts_one_revolution,
                          test_oss_grids_include_zero_exactly_once
  no_fabricated_ingress   (N2/N3):    test_n2_retrograde_upper_boundary_entry_found,
                          test_n3_clipped_span_never_fabricates_ingress
  truncated_contacts_kept (T0-3/O-SS-3): test_contact_id_no_exact_t_in_fallback
                          (identity) + test_step06_enumeration.py::
                          test_truncated_contacts_kept_and_counted (producer)
  residence_spans_persisted (T0-3 #6/#7): test_step06_enumeration.py::
                          test_interval_target_residence_and_agent_restriction
  global_boundary_table   (O-SS-1):   test_step06_enumeration.py::
                          test_boundary_events_solved_and_stored_once_per_body

A2.2 rework index (Codex R2–R6 / Kimi #1–#3 + steward scope ruling; the
reviewers' own counterexamples):
  R6 seam endpoint ownership: test_r6_direct_path_beginning_at_seam_keeps_endpoint_root,
                          test_r6_retrograde_path_ending_at_seam_keeps_endpoint_root,
                          test_r6_interior_seam_crossing_emitted_exactly_once
  R3 every revolution:    test_r3_every_intersected_revolution_enumerated
  R2 coherent refined boundary events: test_r2_residence_entry_exit_are_coherent_refined_events,
                          test_r2_sun_2025_twelve_spans_eleven_exact_ingresses (swieph)
  Kimi #1 upper-boundary longitude: test_kimi1_retrograde_upper_edge_entry_names_the_upper_boundary
  R4 in-orb w/o exact root: test_step06_enumeration.py::test_r4_in_orb_support_without_exact_root_is_kept_truncated
  Kimi #2 'both' both rows: test_step06_enumeration.py::test_truncated_both_preserved_and_jd_round_trip
  Kimi #3 count once:     test_step06_enumeration.py::test_kimi3_physical_truncation_counted_once
  R5 sky-once + reuse:    test_step06_enumeration.py::test_boundary_events_solved_and_stored_once_per_body,
                          test_r5_residence_ingress_reuses_the_sky_event
  identity golden (i):    test_exact_contact_ids_byte_identical_to_origin_main
                          (fixture golden_contact_ids_origin_main.json, computed
                          by executing origin/main ids.py — never self-comparison)
  candidate gate (iii):   test_step06_enumeration.py::test_candidate_gate_null_exact_and_residence_rows_only_for_41_plus,
                          test_s1_find_episodes.py::TestFindEpisodesLedger::
                          test_null_exact_and_residence_rows_never_served
  migration 1152 (7):     test_wp6_ledger.py::test_1152_valid_and_invalid_null_combinations
                          (DB); header states single-run + irreversible-in-practice;
                          preflight query scripts/kala_gochara_cutover/
                          preflight_1152_existing_rows_satisfy_check.sql
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

from .conftest import EPHE_PATH, assert_real_ephemeris, requires_swieph

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
        assert ep.completeness_state == "applied"


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


# ── O-AD-1…4 — aspect direction, computed never mirrored (spec §6.2 inv 6) ──
#
# GOCHARA_TEST_ORACLES_v1_4.json O-AD-1..O-AD-4 (literal fixtures, tolerance
# ±1 arcmin), plus the two brief cases (Saturn at Libra 24°15′ → Sagittarius
# 24°15′ by the 3rd aspect; Mars at Aries 10° → Cancer 10° by the 4th).
# Forward count: the aspect from body b falls at (λ_b + angle) mod 360, so the
# contact occurs with the body at (target − angle) mod 360. The mirrored
# implementation (target + angle) is the mutation that must fail.

OAD_SWEEP_RATE = 0.5  # °/day synthetic sweep
OAD_TIME_TOL_DAYS = (1.0 / 60.0) / OAD_SWEEP_RATE  # ±1 arcmin of longitude

# (oracle, body, target_deg, aspect_deg, body_longitude_at_contact)
OAD_CASES = [
    ("O-AD-1", "Mars", 0.0, 90.0, 270.0),     # Mars 4th  → body at 0−90
    ("O-AD-2", "Mars", 0.0, 210.0, 150.0),    # Mars 8th  → body at 0−210
    ("O-AD-3", "Saturn", 0.0, 60.0, 300.0),   # Saturn 3rd → body at 0−60
    ("O-AD-4", "Saturn", 0.0, 270.0, 90.0),   # Saturn 10th → body at 0−270
    ("brief-1", "Saturn", 264.25, 60.0, 204.25),   # Libra 24°15′ → Sag 24°15′
    ("brief-2", "Mars", 100.0, 90.0, 10.0),        # Aries 10° → Cancer 10°
]


def _oad_index(body: str) -> tuple[arcs.ArcIndex, float]:
    """A 0.5°/day sweep starting at 0° — over three years it crosses every
    level in [0,360) several times, so both the true level (target−angle) and
    the mirrored level (target+angle) are traversed; only the true one may
    produce a root at this aspect."""
    t0 = swe.julday(2026, 1, 1, 12.0)
    jds, lons = daily_knots(
        date(2026, 1, 1), date(2029, 1, 1),
        lambda jd: OAD_SWEEP_RATE * (jd - t0),
    )
    return arcs.build_arc_index(
        body, jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC
    ), t0


@pytest.mark.parametrize(
    "oracle,body,target,aspect,body_lon", OAD_CASES,
    ids=[c[0] for c in OAD_CASES],
)
def test_oad_aspect_direction(oracle, body, target, aspect, body_lon):
    idx, t0 = _oad_index(body)
    roots = contacts.find_roots(
        idx, body, "drishti_contact", target, refine=False
    )
    hits = [r for r in roots if r.aspect_deg == aspect]
    assert hits, f"{oracle}: no {aspect}°-aspect root found for {body}"

    # then-clause: the level is (target − angle) mod 360 and the root occurs
    # with the body there (first crossing at t0 + body_lon / rate).
    assert all(
        r.level_deg == pytest.approx((target - aspect) % 360.0, abs=1e-9)
        for r in hits
    )
    t_true = t0 + (body_lon % 360.0) / OAD_SWEEP_RATE
    assert any(
        abs(r.spline_exact_jd - t_true) < OAD_TIME_TOL_DAYS for r in hits
    ), f"{oracle}: no root with the body at {body_lon}° (target − {aspect}°)"

    # mutation detector: an implementation computing target + angle roots the
    # aspect with the body at (target + angle) mod 360 — that instant must
    # carry NO root at this aspect.
    t_mirror = t0 + ((target + aspect) % 360.0) / OAD_SWEEP_RATE
    assert not any(
        abs(r.spline_exact_jd - t_mirror) < OAD_TIME_TOL_DAYS for r in hits
    ), f"{oracle}: mirrored direction produced a root at target + {aspect}°"


def test_oad_levels_computed_as_target_minus_angle():
    """Direct statement of the rule the mutation flips: for the 0° target the
    solved levels are 300/150/270/90 for Saturn-3rd/Mars-8th/Saturn-10th/
    Mars-4th — never 60/210/90→270."""
    levels = dict(contacts._levels_for_relation("Saturn", "drishti_contact", 0.0))
    assert levels[60.0] == pytest.approx(300.0)
    assert levels[270.0] == pytest.approx(90.0)
    assert levels[180.0] == pytest.approx(180.0)  # 7th: self-mirror invariant
    levels = dict(contacts._levels_for_relation("Mars", "drishti_contact", 0.0))
    assert levels[90.0] == pytest.approx(270.0)
    assert levels[210.0] == pytest.approx(150.0)


# ── O-SS-1/O-SS-2 — the 0°/360° seam is a boundary root (spec §6.2, #14) ────
#
# GOCHARA_TEST_ORACLES_v1_4.json O-SS-2: case 1 direct 359.9°→0.1° over
# [2025-03-01T00:00Z, 2025-03-02T00:00Z] (Aries ingress at the seam); case 2
# retrograde 0.1°→359.9° over [2025-09-01T00:00Z, 2025-09-02T00:00Z] (Pisces
# re-entry through the UPPER boundary). Tolerance δt < 60 s; synthetic linear
# curves are reproduced exactly by the spline (refine=False). O-SS-1 count
# contract per revolution: sign 12 / nakṣatra 27 / kakṣyā 96 (the
# "each event stored once" producer half is step 6's global_boundary_table).

OSS2_HORIZON = ("2025-01-01T00:00:00Z", "2026-01-01T00:00:00Z")


def _oss2_solve(curve, knot_start, knot_end, relation):
    jds, lons = daily_knots(knot_start, knot_end, curve)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = tuple(jd_from_iso(s) for s in OSS2_HORIZON)
    return episodes.solve_boundary_episodes(idx, "Sun", relation, horizon, refine=False)


def test_oss2_case1_direct_crossing_aries_ingress():
    h = jd_from_iso("2025-03-01T00:00:00Z")

    def curve(jd):
        return 359.9 + 0.2 * (jd - h)  # 359.9° at 03-01T00 → 0.1° at 03-02T00

    eps = _oss2_solve(curve, date(2025, 2, 25), date(2025, 3, 5), "sign_ingress")
    assert len(eps) == 1  # the curve crosses ONLY the seam — one root, not two
    ep = eps[0]
    assert ep.level_deg == 0.0 and ep.target_deg == 0.0
    assert ep.exact_crossing is True
    # δt < 60 s: seam at λ=360 exactly midway, 2025-03-01T12:00:00Z
    assert iso_from_jd(ep.t_exact) == "2025-03-01T12:00:00Z"
    # never a fabricated t_exact at the horizon edge
    assert ep.t_in == ep.t_exact == ep.t_out
    assert abs(ep.t_exact - jd_from_iso(OSS2_HORIZON[0])) > 1.0
    assert abs(ep.t_exact - jd_from_iso(OSS2_HORIZON[1])) > 1.0
    # 0° is a nakṣatra boundary too (360/27·27 ≡ 0): same seam, one root
    naks = _oss2_solve(curve, date(2025, 2, 25), date(2025, 3, 5), "nakshatra_ingress")
    assert len(naks) == 1 and naks[0].level_deg == 0.0
    assert iso_from_jd(naks[0].t_exact) == "2025-03-01T12:00:00Z"


def test_oss2_case2_retrograde_pisces_reentry_upper_boundary():
    h = jd_from_iso("2025-09-01T00:00:00Z")

    def curve(jd):
        return 0.1 - 0.2 * (jd - h)  # 0.1° at 09-01T00 → 359.9° at 09-02T00

    eps = _oss2_solve(curve, date(2025, 8, 26), date(2025, 9, 5), "sign_ingress")
    assert len(eps) == 1  # the retrograde seam crossing, through the UPPER edge
    ep = eps[0]
    assert ep.level_deg == 0.0
    assert ep.exact_crossing is True
    assert iso_from_jd(ep.t_exact) == "2025-09-01T12:00:00Z"


def test_oss1_boundary_counts_one_revolution():
    """O-SS-1 count contract (per-body grid half): a Sun-like direct sweep
    (~0.986°/day) across exactly one revolution yields exactly 12 sign, 27
    nakṣatra and 96 kakṣyā roots — including exactly ONE 0°-seam root in each
    grid. Removing 0° from any grid (the pre-fix mutation) drops the count to
    11/26/95 and fails; so does double-emitting the seam."""
    t0 = swe.julday(2026, 1, 1, 12.0)
    rate = 360.0 / 365.25  # Sun-like: one revolution per year

    def curve(jd):
        return 350.0 + rate * (jd - t0)  # knot window spans 352° → ~711° unwrapped

    jds, lons = daily_knots(date(2026, 1, 3), date(2027, 1, 3), curve)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (jds[0], jds[-1])
    expected = {"sign_ingress": 12, "nakshatra_ingress": 27,
                "kakshya_cell_crossing": 96}
    for relation, count in expected.items():
        eps = episodes.solve_boundary_episodes(
            idx, "Sun", relation, horizon, refine=False
        )
        assert len(eps) == count, (
            f"{relation}: {len(eps)} roots over one revolution, expected {count}"
        )
        assert all(e.exact_crossing for e in eps)
        seam = [e for e in eps if e.level_deg == 0.0]
        assert len(seam) == 1, (
            f"{relation}: {len(seam)} seam roots — the 0° crossing must be "
            "present exactly once (attributed to the arc reaching the seam)"
        )
        # δt < 60 s: the seam root is at λ=360, t0 + 10°/rate
        assert abs(seam[0].t_exact - (t0 + 10.0 / rate)) < 60.0 / 86400.0


def test_oss_grids_include_zero_exactly_once():
    """Grid-level pin: 0° is a member of all three boundary grids, listed once."""
    for relation, n in (("sign_ingress", 12), ("nakshatra_ingress", 27),
                        ("kakshya_cell_crossing", 96)):
        grid = contacts.boundary_degrees(relation)
        assert len(grid) == n and len(set(grid)) == n
        assert grid.count(0.0) == 1
        assert all(0.0 <= d < 360.0 for d in grid)


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


@pytest.fixture(autouse=True)
def _real_ephemeris_or_named_failure():
    """§12.5: fail with the cause named if the ephemeris global is stubbed."""
    assert_real_ephemeris()
    yield


def test_guard_fires_when_the_ephemeris_is_stubbed(monkeypatch):
    """Negative fixture: the detector above must be able to go red."""
    import swisseph as swe_mod

    monkeypatch.setattr(swe_mod, "julday", lambda *a, **k: -0.00101)
    with pytest.raises(AssertionError, match="stubbed or replaced"):
        assert_real_ephemeris()


def test_guard_fires_when_the_module_is_not_a_module(monkeypatch):
    from unittest.mock import MagicMock

    monkeypatch.setitem(__import__("sys").modules, "swisseph", MagicMock())
    with pytest.raises(AssertionError, match="not a real module"):
        assert_real_ephemeris()


# ── 4.13g: per-call node-mode assertion (N-4a(b″), mean node only) ──────────


def test_rahu_ketu_calc_asserts_mean_node_per_call(monkeypatch):
    """Patching GRAHA_TO_SWE to TRUE_NODE must raise NodeModelError before any
    calc_ut call — the node model is asserted per call, not assumed from the
    module-level mapping."""
    from services.gochara_kernel import knots

    monkeypatch.setitem(knots.GRAHA_TO_SWE, "Rahu", swe.TRUE_NODE)
    with pytest.raises(knots.NodeModelError, match="MEAN_NODE"):
        knots.calc_sidereal_lon("Rahu", 2460000.5, None)
    monkeypatch.setitem(knots.GRAHA_TO_SWE, "Ketu", swe.TRUE_NODE)
    with pytest.raises(knots.NodeModelError, match="MEAN_NODE"):
        knots.calc_sidereal_lon("Ketu", 2460000.5, None)


def test_rahu_ketu_mean_node_calc_unaffected():
    """Positive control: with the pinned mapping the calc proceeds (retflag
    gate still applies; any backend result other than a raise is success)."""
    from services.gochara_kernel import knots

    try:
        lon, retflag = calc_sidereal_lon("Rahu", 2460000.5, EPHE_PATH)
    except EphemerisBackendError:
        pytest.skip("swieph data unavailable on this host")
    assert 0.0 <= lon < 360.0
    assert knots.GRAHA_TO_SWE["Rahu"] == swe.MEAN_NODE
    assert knots.GRAHA_TO_SWE["Ketu"] == swe.MEAN_NODE


# ── ADK-0019 regression: refine=True over REAL long arcs ────────────────────
# The pre-ADK-0019 kernel refined each boundary/conjunction root by
# Swiss-bisecting the WHOLE arc; the wrapped-separation objective crosses its
# ±180° branch cut when the arc spans >180° of travel past the level, so the
# bracket was "lost" (ValueError) for Sun, Moon and Venus on a 2029 horizon
# (PRAMĀṆIN reproduction). The fix brackets a narrow window around the spline
# root instead. These tests build REAL arc indexes from the pinned ephemeris
# and require refine=True to complete and to stay within tolerance of the
# spline stage — the coverage hole (all-synthetic, refine=False) is closed
# here, per the ruling's mandatory-regression clause.


def _real_arc_index(body: str, start: date, end: date) -> arcs.ArcIndex:
    def real_curve(jd: float) -> float:
        lon, retflag = calc_sidereal_lon(body, jd, EPHE_PATH)
        if not (retflag & 2) or (retflag & 4):
            raise EphemerisBackendError(body, retflag)
        return lon

    jds, lons = daily_knots(start, end, real_curve)
    # Production tolerance (DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC), not the
    # synthetic-fixture one: the spline only approximates the real curve.
    return arcs.build_arc_index(body, jds, lons)


@requires_swieph
def test_adk0019_refine_real_long_arcs_2029():
    """Sun, Moon AND Venus over calendar 2029 (the PRAMĀṆIN failure year):
    every sign-ingress root must refine under refine=True, and the refined
    instant must (i) stay within 0.1 day of the spline root and (ii) land the
    body on the level to under an arcsecond."""
    assert_real_ephemeris()
    start, end = date(2029, 1, 1), date(2030, 1, 1)
    expected_min_roots = {"Sun": 11, "Moon": 140, "Venus": 11}
    for body, min_roots in expected_min_roots.items():
        idx = _real_arc_index(body, start, end)
        roots = contacts.find_boundary_roots(
            idx, body, "sign_ingress", ephe_path=EPHE_PATH, refine=True
        )
        assert len(roots) >= min_roots, (
            f"{body}: {len(roots)} sign-ingress roots in 2029, expected >= {min_roots}"
        )
        for r in roots:
            assert abs(r.exact_jd - r.spline_exact_jd) < 0.1, (
                f"{body} level {r.level_deg}: refined {r.exact_jd} drifted "
                f"{r.exact_jd - r.spline_exact_jd:+.4f}d from spline"
            )
            lon, retflag = calc_sidereal_lon(body, r.exact_jd, EPHE_PATH)
            assert retflag & 2
            sep = abs(((lon - r.level_deg + 180.0) % 360.0) - 180.0)
            assert sep < 1.0 / 3600.0, (
                f"{body} level {r.level_deg}: refined root off by {sep * 3600:.2f}\""
            )


@requires_swieph
def test_adk0019_refine_find_roots_conjunction_2029():
    """find_roots shares the defect (conjunction/drishti levels): a real Sun
    conjunction target in 2029 must refine green."""
    assert_real_ephemeris()
    idx = _real_arc_index("Sun", date(2029, 1, 1), date(2030, 1, 1))
    target, _ = calc_sidereal_lon("Sun", swe.julday(2029, 6, 15, 12.0), EPHE_PATH)
    roots = contacts.find_roots(
        idx, "Sun", "conjunction", target, ephe_path=EPHE_PATH, refine=True
    )
    assert len(roots) == 1
    r = roots[0]
    assert abs(r.exact_jd - r.spline_exact_jd) < 0.1
    lon, retflag = calc_sidereal_lon("Sun", r.exact_jd, EPHE_PATH)
    assert retflag & 2
    sep = abs(((lon - r.level_deg + 180.0) % 360.0) - 180.0)
    assert sep < 1.0 / 3600.0


# ── Pisces whole-sign span wrap fix (beyond ADK-0019's two call sites) ───────

def test_pisces_whole_sign_span_not_refused():
    """The driver's _sign_span legitimately emits (330.0, 360.0) for sign 12;
    before the episodes.py fix, residence_spans wrapped 360.0 → 0.0 and
    raised ValueError for the one whole-sign span that ends on the circle's
    end. Now it must produce a normal residence span."""
    h0 = jd_from_iso("2026-01-01T00:00:00Z")

    def curve(jd):
        return 300.0 + 0.5 * (jd - h0)  # sweeps 300°→330°(60d)→360°(120d)

    jds, lons = daily_knots(date(2025, 12, 15), date(2026, 6, 1), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (jds[0], jds[-1])
    spans = episodes.residence_spans(
        idx, "Saturn", (330.0, 360.0), horizon, "bhava", refine=False
    )
    assert len(spans) == 1
    span = spans[0]
    assert (span.span_lo_deg, span.span_hi_deg) == (330.0, 360.0)
    assert span.t_enter == pytest.approx(h0 + 30.0 / 0.5, abs=1e-4)  # λ=330 at t=60 d
    assert span.t_exit == pytest.approx(h0 + 60.0 / 0.5, abs=1e-4)  # egress at λ=360, t=120 d
    assert span.truncated_at_horizon is None
    assert span.ingress_episode.relation == "sign_ingress"


# ── N2/N3 — no fabricated ingress at a clipped horizon start ────────────────

def test_n2_retrograde_upper_boundary_entry_found():
    """N2: the ingress search covers BOTH span boundaries. A retrograde body
    enters a span through its UPPER edge (here the 0°/360° seam of the Pisces
    whole-sign span); pre-fix only lo_w was searched, so the root was missed
    and t_exact was fabricated at the clip instant."""
    h = jd_from_iso("2026-01-01T00:00:00Z")

    def curve(jd):
        return 361.0 - 0.2 * (jd - h)  # 1° Aries → crosses 360 (Pisces top) at t=5 d

    jds, lons = daily_knots(date(2025, 12, 28), date(2026, 1, 20), curve)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (jds[0], jds[-1])
    spans = episodes.residence_spans(
        idx, "Sun", (330.0, 360.0), horizon, "bhava", refine=False
    )
    assert len(spans) == 1
    span = spans[0]
    assert span.t_enter == pytest.approx(h + 5.0, abs=1e-4)  # λ=360 crossing
    ep = span.ingress_episode
    assert ep.exact_crossing is True
    assert ep.t_exact == pytest.approx(h + 5.0, abs=1e-4)
    # the root came from the UPPER boundary (0° seam): root-derived fields are
    # populated — pre-fix (lo_w-only search) found no root and left
    # spline_exact_jd None while stamping exact_crossing=True (the lie N2 kills)
    assert ep.spline_exact_jd == pytest.approx(h + 5.0, abs=1e-4)
    assert ep.t_exact != pytest.approx(horizon[0], abs=1.0)


def test_n3_clipped_span_never_fabricates_ingress():
    """N3/O-SS-3: the true ingress lies BEFORE the horizon start (span clipped
    at the start edge). The span is KEPT as truncated; the ingress episode
    carries t_exact=None / exact_crossing=False — never a fabricated instant
    at the horizon edge stamped as an observed crossing."""
    h0 = jd_from_iso("2026-01-01T00:00:00Z")

    def curve(jd):
        return 300.0 + 0.5 * (jd - h0)  # λ=330 at t=60 d, λ=360 at t=120 d

    jds, lons = daily_knots(date(2025, 12, 15), date(2026, 6, 1), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (h0 + 70.0, jds[-1])  # starts 10 d AFTER the true ingress (λ=335)
    spans = episodes.residence_spans(
        idx, "Saturn", (330.0, 360.0), horizon, "bhava", refine=False
    )
    assert len(spans) == 1
    span = spans[0]
    assert span.truncated_at_horizon == "start"
    assert span.t_enter == pytest.approx(horizon[0], abs=1e-9)  # the clip instant
    ep = span.ingress_episode
    assert ep.exact_crossing is False
    assert ep.t_exact is None
    assert ep.truncated_at_horizon == "start"
    # mutation guard: no fabricated exact instant at (or near) the clip edge
    assert ep.t_in == pytest.approx(horizon[0], abs=1e-9)
    assert not (ep.exact_crossing and ep.t_exact == ep.t_in)


def test_contact_id_no_exact_t_in_fallback():
    """N3 truncated contacts (t_exact=None) get a stable identity from the
    floored t_in, marked as a substitution in the payload — so a truncated
    contact can never collide with an exact one at the same minute, and the
    exact-contact id shape is byte-identical to before the fallback existed."""
    jd_exact = swe.julday(2026, 3, 6, 0.0) + 37 / 86400.0
    kw = dict(
        chart_id="wp2-synth-00000000-0000-4000-8000-00000000000b",
        convention_id="sha256:abc", body="Saturn", target_type="karaka",
        relation="conjunction", aspect_deg=0.0, target_ref="Sun",
        method_version="1.0.0",
    )
    exact = contact_id(t_exact_jd=jd_exact, **kw)
    # exact shape unchanged: no t_fallback needed, same value as pre-change
    assert exact == contact_id(t_exact_jd=jd_exact, t_fallback_jd=None, **kw)
    # no-exact: requires the fallback instant
    with pytest.raises(ValueError):
        contact_id(t_exact_jd=None, **kw)
    trunc = contact_id(t_exact_jd=None, t_fallback_jd=jd_exact, **kw)
    # same minute, same everything — but NOT the same id (substitution marked)
    assert trunc != exact
    # stable under sub-minute jitter of t_in
    assert trunc == contact_id(
        t_exact_jd=None, t_fallback_jd=jd_exact + 20 / 86400.0, **kw)


# ── Pravāha A2.2 rework regressions — the reviewers' own counterexamples ─────
# (Codex gpt-6-astra R2/R3/R6, Kimi K3 #1; ASTRA_REVIEW/KIMI_K3_REVIEW
# A2_KERNEL_GEOMETRY_v1_0). Each test names the mutation it catches.

def test_r6_direct_path_beginning_at_seam_keeps_endpoint_root():
    """Codex R6 (baseline comparison): a direct path BEGINNING exactly at 0°
    owns a root at the domain start. The pre-rework 0→360 mapping discarded
    it (the arc's lon_hi < 360)."""
    t0 = swe.julday(2026, 1, 1, 12.0)  # daily_knots samples at noon UT

    def curve(jd):
        return 0.5 * (jd - t0)  # exactly 0.0° at the FIRST knot

    jds, lons = daily_knots(date(2026, 1, 1), date(2026, 1, 25), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    assert lons[0] == 0.0  # the window opens exactly on the seam
    roots = contacts.find_roots(idx, "Saturn", "conjunction", 0.0, refine=False)
    # the body departs 0 at the window start — exactly one root at the first
    # knot, never none (pre-fix) and never two
    assert len(roots) == 1
    assert roots[0].spline_exact_jd == pytest.approx(jds[0], abs=1e-9)


def test_r6_retrograde_path_ending_at_seam_keeps_endpoint_root():
    """Codex R6 (baseline): a retrograde path ENDING exactly at 0° owns a
    root at the domain end."""
    t0 = swe.julday(2026, 1, 1, 12.0)  # daily_knots samples at noon UT

    def curve(jd):
        return 5.0 - 0.5 * (jd - t0)  # reaches exactly 0° at day 10

    jds, lons = daily_knots(date(2026, 1, 1), date(2026, 1, 25), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    assert lons[10] == pytest.approx(0.0, abs=1e-9)  # day 10 of the window
    roots = contacts.find_roots(idx, "Saturn", "conjunction", 0.0, refine=False)
    assert len(roots) == 1
    assert roots[0].spline_exact_jd == pytest.approx(jds[10], abs=1e-9)
    boundary = contacts.find_boundary_roots(idx, "Saturn", "sign_ingress", refine=False)
    seam = [r for r in boundary if r.level_deg == 0.0]
    assert len(seam) == 1
    assert seam[0].spline_exact_jd == pytest.approx(jds[10], abs=1e-9)


def test_r6_interior_seam_crossing_emitted_exactly_once():
    """R6 ownership: an interior wrap crossing is covered by BOTH the arc
    reaching 360 and the next band's arc starting at 0 — the stored root is
    ONE physical event (the duplicate candidate at the shared cut is dropped),
    while the arc that reaches the boundary keeps the attribution."""
    t0 = swe.julday(2026, 3, 1, 0.0)

    def curve(jd):
        return 350.0 + 0.5 * (jd - t0)  # crosses 360→0 at t0+20, mid-window

    jds, lons = daily_knots(date(2026, 2, 20), date(2026, 3, 25), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    boundary = contacts.find_boundary_roots(idx, "Saturn", "sign_ingress", refine=False)
    seam = [r for r in boundary if r.level_deg == 0.0]
    assert len(seam) == 1, f"seam crossing duplicated: {len(seam)} roots"
    assert seam[0].spline_exact_jd == pytest.approx(t0 + 20.0, abs=1e-6)
    conj = contacts.find_roots(idx, "Saturn", "conjunction", 0.0, refine=False)
    assert len(conj) == 1
    assert conj[0].spline_exact_jd == pytest.approx(t0 + 20.0, abs=1e-6)


def test_r3_every_intersected_revolution_enumerated():
    """Codex R3 (verbatim counterexample): λ(t)=t° over [0,1000] days,
    residence [30°,60°] must yield [30,60], [390,420], [750,780] — the
    pre-rework midpoint-band choice returned only [390,420]."""
    t0 = swe.julday(2026, 1, 1, 0.0)

    def curve(jd):
        return jd - t0  # 1°/day, many revolutions inside one knot window

    jds, lons = daily_knots(date(2025, 12, 20), date(2028, 12, 20), curve)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (t0, t0 + 1000.0)
    spans = episodes.residence_spans(
        idx, "Sun", (30.0, 60.0), horizon, "bhava", refine=False)
    entries = [s.t_enter - t0 for s in spans]
    exits = [s.t_exit - t0 for s in spans]
    assert entries == pytest.approx([30.0, 390.0, 750.0], abs=1e-6)
    assert exits == pytest.approx([60.0, 420.0, 780.0], abs=1e-6)
    # every ingress is an observed exact crossing at the LOWER edge (direct)
    for s in spans:
        assert s.ingress_episode.exact_crossing is True
        assert s.ingress_episode.t_exact == pytest.approx(s.t_enter, abs=1e-9)
        assert s.ingress_episode.level_deg == 30.0
        assert s.truncated_at_horizon is None


def test_r2_residence_entry_exit_are_coherent_refined_events():
    """Codex R2 (verbatim counterexample geometry): λ = 200 + 0.137°·day,
    span [210°, 240°]. Entry and exit instants are THE refined boundary
    events of the actual edges — the ingress episode's t_exact IS the span's
    t_enter (no 1e-6-day join between differently refined roots, which turned
    every real ingress into a false null)."""
    t0 = swe.julday(2026, 1, 1, 0.0)

    def curve(jd):
        return 200.0 + 0.137 * (jd - t0)

    jds, lons = daily_knots(date(2025, 12, 20), date(2027, 1, 20), curve)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    horizon = (jds[0], jds[-1])
    spans = episodes.residence_spans(
        idx, "Sun", (210.0, 240.0), horizon, "bhava", refine=False)
    assert len(spans) == 1
    span = spans[0]
    entry_analytic = 10.0 / 0.137
    exit_analytic = 40.0 / 0.137
    assert span.t_enter - t0 == pytest.approx(entry_analytic, abs=1e-6)
    assert span.t_exit - t0 == pytest.approx(exit_analytic, abs=1e-6)
    ing = span.ingress_episode
    assert ing.t_exact is not None and ing.exact_crossing is True
    assert ing.t_exact == span.t_enter  # ONE coherent event, not a join
    assert ing.level_deg == 210.0 and ing.target_deg == 210.0
    assert ing.completeness_state == "applied"
    assert span.truncated_at_horizon is None


def test_kimi1_retrograde_upper_edge_entry_names_the_upper_boundary():
    """Kimi #1: a retrograde body entering [30°,60°] through its UPPER edge
    is stamped 60° — never the lower boundary 30° (the pre-rework code
    stamped lo_w unconditionally; Kṣetra reads level/target degrees, so the
    mislabel was consumer-visible wrong data)."""
    t0 = swe.julday(2026, 1, 1, 0.0)

    def curve(jd):
        return 70.0 - 0.2 * (jd - t0)  # enters [30,60] through 60 at t=50

    jds, lons = daily_knots(date(2025, 12, 20), date(2026, 8, 1), curve)
    idx = arcs.build_arc_index("Saturn", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    spans = episodes.residence_spans(
        idx, "Saturn", (30.0, 60.0), (jds[0], jds[-1]), "bhava", refine=False)
    assert len(spans) == 1
    ing = spans[0].ingress_episode
    assert ing.level_deg == 60.0 and ing.target_deg == 60.0
    assert ing.t_exact - t0 == pytest.approx(50.0, abs=1e-6)
    assert spans[0].t_exit - t0 == pytest.approx(200.0, abs=1e-6)  # 30° at t=200
    # Pisces-span variant through the seam: entering [330,360] through 360
    # stamps the seam degree (360 ≡ 0), never the lower edge 330.
    def curve2(jd):
        return 5.0 - 0.2 * (jd - t0)  # enters [330,360] through 360 at t=25

    jds2, lons2 = daily_knots(date(2025, 12, 20), date(2026, 6, 1), curve2)
    idx2 = arcs.build_arc_index("Saturn", jds2, lons2, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    spans2 = episodes.residence_spans(
        idx2, "Saturn", (330.0, 360.0), (jds2[0], jds2[-1]), "bhava", refine=False)
    assert len(spans2) == 1
    ing2 = spans2[0].ingress_episode
    assert ing2.level_deg == 0.0 and ing2.target_deg == 0.0  # the 360 seam
    assert ing2.t_exact - t0 == pytest.approx(25.0, abs=1e-6)


@requires_swieph
def test_r2_sun_2025_twelve_spans_eleven_exact_ingresses():
    """Codex R2's real-ephemeris reproduction, inverted: pre-rework ALL 12
    Sun 2025 residence spans carried null ingress. Now every ingress inside
    the horizon is exact (each within 2 s of an independent Swiss bisection);
    only the tail of the Dec 2024 Sagittarius ingress is truncated-start with
    t_exact=None. (Sagittarius appears twice inside 2025 — the January tail
    and the December re-entry — so 13 spans, 12 exact ingresses.)"""
    start = date(2024, 12, 15)
    end = date(2026, 1, 15)
    jds, lons = [], []
    d = start
    while d <= end:
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        lon, retflag = calc_sidereal_lon("Sun", jd, EPHE_PATH)
        if not (retflag & 2) or (retflag & 4):
            pytest.skip(f"NOT_RUN: Sun retflag {retflag} (F-14)")
        jds.append(jd)
        lons.append(lon)
        d += timedelta(days=1)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=1.0)
    horizon = (jd_from_iso("2025-01-01T00:00:00Z"), jd_from_iso("2026-01-01T00:00:00Z"))
    total, exact, truncated = 0, 0, 0
    for k in range(12):
        lo = 30.0 * k
        spans = episodes.residence_spans(
            idx, "Sun", (lo, lo + 30.0), horizon, "bhava", ephe_path=EPHE_PATH)
        # The knot window covers Dec 2024 – Jan 2026, so Sagittarius (the
        # sign the Sun is in on Jan 1) appears TWICE inside 2025: the
        # truncated-start tail of the Dec 2024 ingress and the next ingress
        # in Dec 2025. Every other sign appears once.
        assert len(spans) == (2 if lo == 240.0 else 1), (
            f"sign {k}: {len(spans)} spans in 2025")
        for span in spans:
            total += 1
            if lo == 240.0 and span.ingress_episode.t_exact is None:
                # Sun is at ~265° on 2025-01-01: this span's ingress was in
                # Dec 2024 — truncated start, never a fabricated instant (N3).
                assert span.truncated_at_horizon == "start"
                truncated += 1
                continue
            ing = span.ingress_episode
            assert ing.t_exact is not None and ing.exact_crossing is True
            assert ing.t_exact == pytest.approx(span.t_enter, abs=1e-9)
            # independent re-derivation: direct Swiss bisection around the
            # found instant (NOT the residence path's own refinement)
            jd_ind, _ = contacts.swiss_bisect(
                "Sun", ing.t_exact - 1.0, ing.t_exact + 1.0, lo, EPHE_PATH)
            assert abs(jd_ind - ing.t_exact) < 2.0 / 86400.0
            exact += 1
    assert (total, exact, truncated) == (13, 12, 1)


def test_exact_contact_ids_byte_identical_to_origin_main():
    """Steward scope ruling (A2 rework, item i): exact-contact ids for
    unchanged inputs are byte-identical to origin/main. The goldens were
    computed by EXECUTING origin/main's ids.py (extracted via git show) on
    the 27 fixed cases — not by comparing the function against itself (the
    defect in the earlier identity assertion). Any drift in the exact-contact
    payload (fields, rounding, canonicalization) fails here."""
    golden = json.loads(
        (Path(__file__).parent / "fixtures"
         / "golden_contact_ids_origin_main.json").read_text())
    assert len(golden["cases"]) == 27
    for case in golden["cases"]:
        got = contact_id(**case["inputs"])
        assert got == case["contact_id"], (
            f"exact-contact id drifted from origin/main for "
            f"{case['inputs']['body']}/{case['inputs']['relation']}: "
            f"{got} != {case['contact_id']}")


# ── Pravāha A2.2 closure-check (v1.1) round-2 regressions ────────────────────
# Each test is the Codex v1.1 reviewer's own counterexample.

def test_r2q1_domain_start_on_entry_boundary_is_observed_ingress():
    """Codex v1.1 amendment 2: λ=30+t over [0,40], residence [30,60] — the
    body sits exactly ON the entry boundary at the domain start. Baseline
    (95e765c3c) found t_exact = day 0; the strict-comparison rework made it
    null. Endpoint-on-edge is an observed crossing."""
    t0 = swe.julday(2026, 1, 1, 12.0)

    def curve(jd):
        return 30.0 + (jd - t0)

    jds, lons = daily_knots(date(2026, 1, 1), date(2026, 2, 20), curve)
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    spans = episodes.residence_spans(
        idx, "Sun", (30.0, 60.0), (t0, t0 + 40.0), "bhava", refine=False)
    assert len(spans) == 1
    ing = spans[0].ingress_episode
    assert ing.t_exact == pytest.approx(t0, abs=1e-9)  # day 0, observed
    assert ing.exact_crossing is True
    assert spans[0].truncated_at_horizon is None


def test_r2q1_station_spanning_exit_refined_on_its_own_segment():
    """Codex v1.1 amendment 1 (analytic probe): λ=20−(t−10)², span [0,30] —
    a station at t=10 INSIDE the span, entry on the rising leg, exit on the
    falling leg. The exit must be refined against the FALLING segment (its
    own), and with the shared roots supplied the construction must not raise
    (pre-fix it refined the exit against the entry segment → ValueError /
    wrong instant). λ=20−(t−10)² enters [0,30] at 20−(t−10)²=0 → t=10−√20
    and exits at t=10+√20."""
    t0 = swe.julday(2026, 1, 1, 12.0)

    def curve(jd):
        return 20.0 - (jd - t0 - 10.0) ** 2

    jds, lons = daily_knots(date(2025, 12, 25), date(2026, 1, 20), curve)
    idx = arcs.build_arc_index("Mars", jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    roots = contacts.find_boundary_roots(idx, "Mars", "sign_ingress", refine=False)
    horizon = (jds[0], jds[-1])
    spans = episodes.residence_spans(
        idx, "Mars", (0.0, 30.0), horizon, "bhava", refine=False,
        boundary_roots=roots)  # must NOT raise
    assert len(spans) == 1
    span = spans[0]
    assert span.t_enter - t0 == pytest.approx(10.0 - math.sqrt(20.0), abs=1e-6)
    assert span.t_exit - t0 == pytest.approx(10.0 + math.sqrt(20.0), abs=1e-6)


@requires_swieph
def test_r2q1_swiss_mars_jupiter_station_spanning_exits():
    """Codex v1.1 amendment 1, real ephemeris: Mars 2025 residence [60°,90°]
    (retrograde station inside the span) exits 2025-04-02 at 90° — never
    2025-03-14 at 84.72° (the wrong-segment refinement); Jupiter [30°,60°]
    exits 2025-05-14 at 60°. Each exit within 2 min of an independent Swiss
    bisection."""
    for body, span_deg, want_exit_date in (
            ("Mars", (60.0, 90.0), "2025-04-02"),
            ("Jupiter", (30.0, 60.0), "2025-05-14")):
        jds, lons = [], []
        d = date(2024, 12, 15)
        while d <= date(2026, 1, 15):
            jd = swe.julday(d.year, d.month, d.day, 12.0)
            lon, retflag = calc_sidereal_lon(body, jd, EPHE_PATH)
            if not (retflag & 2) or (retflag & 4):
                pytest.skip(f"NOT_RUN: {body} retflag {retflag} (F-14)")
            jds.append(jd)
            lons.append(lon)
            d += timedelta(days=1)
        idx = arcs.build_arc_index(body, jds, lons, tolerance_arcsec=1.0)
        horizon = (jd_from_iso("2025-01-01T00:00:00Z"),
                   jd_from_iso("2026-01-01T00:00:00Z"))
        spans = episodes.residence_spans(
            idx, body, span_deg, horizon, "bhava", ephe_path=EPHE_PATH)
        assert len(spans) == 1
        span = spans[0]
        assert iso_from_jd(span.t_exit)[:10] == want_exit_date
        # independent re-derivation of the exit instant (exit edge = span hi)
        jd_ind, _ = contacts.swiss_bisect(
            body, span.t_exit - 1.0, span.t_exit + 1.0, span_deg[1], EPHE_PATH)
        assert abs(jd_ind - span.t_exit) < 120.0 / 86400.0


def test_r2q3_multi_revolution_seam_ownership():
    """Codex v1.1 amendment 3 (verbatim): an arc whose BOTH endpoints are
    seams owns a distinct crossing at each end. λ=10+t over [0,1500] → seam
    crossings at 350, 710, 1070, 1430 (the start-anchored dedupe dropped 710
    and duplicated 1430); λ=t over [0,1000] → 0, 360, 720 (the domain start
    at 0 is a real crossing)."""
    for c0, days, want in ((10.0, 1500, [350, 710, 1070, 1430]),
                           (0.0, 1000, [0, 360, 720])):
        t0 = swe.julday(2026, 1, 1, 12.0)

        def curve(jd, c0=c0):
            return c0 + (jd - t0)

        jds, lons = daily_knots(date(2025, 12, 25),
                                date(2025, 12, 25) + timedelta(days=days + 20),
                                curve)
        idx = arcs.build_arc_index("Sun", jds, lons,
                                   tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
        eps = episodes.solve_boundary_episodes(
            idx, "Sun", "sign_ingress", (t0, t0 + days), refine=False)
        got = sorted(round(e.t_exact - t0) for e in eps if e.level_deg == 0.0)
        assert got == want, f"c0={c0}: {got} != {want}"


@requires_swieph
def test_r2q3_swiss_sun_seam_crossings_once_per_year_2025_2035():
    """Codex v1.1 amendment 3, real ephemeris: Sun seam (0° Aries) crossings
    2025–2035 — exactly one per year (2026 present, 2034 once). The
    start-anchored dedupe made 2026 disappear and 2034 appear twice."""
    jds, lons = [], []
    d = date(2024, 12, 20)
    while d <= date(2035, 12, 31):
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        lon, retflag = calc_sidereal_lon("Sun", jd, EPHE_PATH)
        if not (retflag & 2) or (retflag & 4):
            pytest.skip(f"NOT_RUN: Sun retflag {retflag} (F-14)")
        jds.append(jd)
        lons.append(lon)
        d += timedelta(days=7)  # weekly knots suffice for the year count
    idx = arcs.build_arc_index("Sun", jds, lons, tolerance_arcsec=1.0)
    horizon = (jd_from_iso("2025-01-01T00:00:00Z"),
               jd_from_iso("2035-12-31T00:00:00Z"))
    eps = episodes.solve_boundary_episodes(
        idx, "Sun", "sign_ingress", horizon, ephe_path=EPHE_PATH)
    seam_years = sorted(int(iso_from_jd(e.t_exact)[:4])
                        for e in eps if e.level_deg == 0.0)
    # horizon covers the March equinoxes of 2025 through 2035 inclusive
    assert seam_years == list(range(2025, 2036)), seam_years


# ── Multi-revolution in-orb enumeration (steward ruling M20261001T172824-ebbd) ──
#
# The pre-fix in_orb_intervals resolved ONE unwrapped band representative per
# segment (nearest the segment midpoint). A stationless body's segment spans
# the whole domain, so every revolution's in-orb span but one was silently
# ABSENT (N3-class). The fix enumerates every revolution band intersecting
# the segment — the R3-class rule residence_spans already obeyed. These tests
# run through the REAL solve_episodes.


def _sweep_index(body: str, start_lon: float, rate: float, days: int,
                 start: date = date(2025, 12, 20)):
    """Monotone sweep λ = start_lon + rate·(jd − t0), daily noon knots; a
    stationless body yields ONE segment over the whole window."""
    t0 = swe.julday(start.year, start.month, start.day, 12.0)
    jds, lons = daily_knots(start, start + timedelta(days=days),
                            lambda jd: start_lon + rate * (jd - t0))
    idx = arcs.build_arc_index(body, jds, lons,
                               tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    return idx, t0, (jds[0], jds[-1])


def test_sun_multi_revolution_both_episodes_emitted():
    """The ruling's reproducer: Sun 1°/day from 100°, target 200° — exact
    roots at +100d and +460d; solve_episodes must emit BOTH episodes (the
    pre-fix code emitted only the one nearest the segment midpoint)."""
    idx, t0, horizon = _sweep_index("Sun", 100.0, 1.0, 600)
    eps = episodes.solve_episodes(
        idx, "Sun", "conjunction", 200.0, horizon, "orb_conj_slow",
        refine=False)
    exacts = sorted(e.t_exact - t0 for e in eps if e.exact_crossing)
    assert exacts == pytest.approx([100.0, 460.0], abs=1e-6)
    # orb_conj_slow is 1°: at 1°/day each episode spans exact ± 1 day.
    for e, te in zip(sorted(eps, key=lambda e: e.t_exact), (100.0, 460.0)):
        assert e.t_in - t0 == pytest.approx(te - 1.0, abs=1e-6)
        assert e.t_out - t0 == pytest.approx(te + 1.0, abs=1e-6)
        assert e.truncated_at_horizon is None


@pytest.mark.parametrize(
    "body,rate,start_lon,target,days",
    [
        ("Sun", 1.0, 100.0, 200.0, 600),      # roots at +100, +460
        ("Moon", 13.0, 0.0, 40.0, 200),       # ~7 revolutions
        ("Mercury", 4.0, 10.0, 30.0, 300),    # fast body, ~3⅓ revolutions
    ],
    ids=["Sun", "Moon", "Mercury"],
)
def test_multi_revolution_every_occurrence_present(body, rate, start_lon,
                                                   target, days):
    """Every revolution's occurrence of the contact yields an episode with an
    exact crossing at the analytic instant — none silently absent."""
    idx, t0, horizon = _sweep_index(body, start_lon, rate, days)
    eps = episodes.solve_episodes(
        idx, body, "conjunction", target, horizon,
        "orb_conj_slow" if body != "Moon" else "orb_conj_moon",
        refine=False)
    # analytic crossings: λ = target + 360k, k = 0.. while inside the horizon
    want = []
    k = 0
    while True:
        lam = target + 360.0 * k
        d = (lam - start_lon) / rate
        if d < -1e-9:
            k += 1
            continue
        if t0 + d > horizon[1]:
            break
        want.append(d)
        k += 1
    exacts = sorted(e.t_exact - t0 for e in eps if e.exact_crossing)
    assert exacts == pytest.approx(want, abs=1e-6)
    # count identity: one exact episode per find_roots root (grouped by
    # occurrence) — the solver's candidate set and the episodes agree 1:1.
    roots = contacts.find_roots(idx, body, "conjunction", target, refine=False)
    assert len(exacts) == len(roots) == len(want)


def test_multi_revolution_retrograde_control_unchanged():
    """Retrograde control: the fix must not alter the pinned station-complex
    behaviour. Piecewise λ: rise 1°/day to 210° at d=210, fall to 190° at
    d=230, rise again — target 200°, orb 1°. Three distinct in-orb intervals
    ([199,201], [219,221], [239,241]) each with one exact root; the middle
    crossing is on the internal retrograde leg (branch 'retrograde'), the
    outer two 'direct' — exactly the pre-fix WP2 semantics."""
    t0 = swe.julday(2026, 1, 1, 12.0)

    def curve(jd):
        d = jd - t0
        if d <= 210.0:
            return d
        if d <= 230.0:
            return 210.0 - (d - 210.0)
        return 190.0 + (d - 230.0)

    jds, lons = daily_knots(date(2025, 12, 20), date(2026, 9, 1), curve)
    idx = arcs.build_arc_index("Mars", jds, lons,
                               tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)
    eps = episodes.solve_episodes(
        idx, "Mars", "conjunction", 200.0, (jds[0], jds[-1]),
        "orb_conj_slow", refine=False)
    assert len(eps) == 3
    eps.sort(key=lambda e: e.t_exact)
    want = [
        (200.0, "direct", 199.0, 201.0),
        (220.0, "retrograde", 219.0, 221.0),
        (240.0, "direct", 239.0, 241.0),
    ]
    for e, (te, branch, tin, tout) in zip(eps, want):
        assert e.t_exact - t0 == pytest.approx(te, abs=1e-6)
        assert e.branch == branch
        assert e.t_in - t0 == pytest.approx(tin, abs=1e-6)
        assert e.t_out - t0 == pytest.approx(tout, abs=1e-6)
    assert all(e.truncated_at_horizon is None for e in eps)


def test_multi_revolution_retrograde_falling_sweep_all_revolutions():
    """A falling (retrograde-direction) sweep crossing the same level once
    per revolution: every revolution's band is enumerated on the direction-
    aware path too (a falling segment enters at the band's UPPER edge)."""
    idx, t0, horizon = _sweep_index("Mars", 700.0, -1.0, 700)
    eps = episodes.solve_episodes(
        idx, "Mars", "conjunction", 200.0, horizon, "orb_conj_slow",
        refine=False)
    exacts = sorted(e.t_exact - t0 for e in eps if e.exact_crossing)
    # λ = 700 − d = 200 + 360k → d = 500 − 360k: k=1 → 140, k=0 → 500
    # (k=−1 → 860 lies beyond the 700-day window).
    assert exacts == pytest.approx([140.0, 500.0], abs=1e-6)
    eps.sort(key=lambda e: e.t_exact)
    for e, te in zip(eps, (140.0, 500.0)):
        # falling: enters at the band's UPPER edge (201°), exits the lower
        assert e.t_in - t0 == pytest.approx(te - 1.0, abs=1e-6)
        assert e.t_out - t0 == pytest.approx(te + 1.0, abs=1e-6)
        assert e.branch == "direct"  # bare falling stretch, station outside
        assert e.truncated_at_horizon is None
