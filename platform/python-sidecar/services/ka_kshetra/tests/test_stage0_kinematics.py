"""Tests for services.ka_kshetra.stage0_kinematics.

Two tiers, matching the project's test-writer convention (see
pipeline/orchestrator/writers/tests/test_bg_cohort.py):

1. Offline (always runs, no DB / no live swisseph): the pure math — unwrap,
   Hermite spline value/velocity/acceleration, Brent root-finding for every
   event kind, dwell time/weight, the trapezoidal kernel, eclipse candidacy —
   on small, hand-verifiable synthetic ephemeris fixtures.
2. Live (skipped unless DATABASE_URL is set): the DB/ephemeris I/O layer
   against a real ephemeris_daily + chart_facts.
"""
from __future__ import annotations

import math
import os

import pytest

from services.ka_kshetra.stage0_kinematics import (
    BRENT_XTOL_DAYS,
    HermiteSpline,
    KinematicsVelocityOutOfRange,
    assert_moon_velocity_in_range,
    build_spline,
    contact_episode_rows,
    contact_kernel,
    dwell_days,
    dwell_nominal_days,
    dwell_weight,
    eclipse_candidate,
    find_contact_episodes,
    find_modulus_boundary_roots,
    find_roots_on_grid,
    find_station_roots,
    find_syzygy_roots,
    ingress_rows,
    make_episode_id,
    station_rows,
    syzygy_rows,
    t_days_to_datetime,
    unwrap_series,
    wrap180,
)


# ── wrap180 / unwrap_series ───────────────────────────────────────────────────

class TestWrap180:
    def test_identity_inside_range(self):
        assert wrap180(10.0) == pytest.approx(10.0)
        assert wrap180(-10.0) == pytest.approx(-10.0)

    def test_wraps_above_180(self):
        assert wrap180(190.0) == pytest.approx(-170.0)
        assert wrap180(360.0) == pytest.approx(0.0)
        assert wrap180(540.0) == pytest.approx(180.0) or wrap180(540.0) == pytest.approx(-180.0)

    def test_wraps_below_minus_180(self):
        assert wrap180(-190.0) == pytest.approx(170.0)


class TestUnwrapSeries:
    def test_empty(self):
        assert unwrap_series([]) == []

    def test_no_wrap_needed(self):
        assert unwrap_series([1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0]

    def test_forward_wrap_at_360(self):
        # A direct (forward) body crossing 0deg/360deg boundary.
        vals = [359.0, 1.0, 3.0]
        assert unwrap_series(vals) == pytest.approx([359.0, 361.0, 363.0])

    def test_retrograde_wrap_uses_180_test_not_is_retrograde(self):
        # A retrograde body decreasing THROUGH 0 (never told is_retrograde).
        vals = [1.0, 359.0, 357.0]
        assert unwrap_series(vals) == pytest.approx([1.0, -1.0, -3.0])

    def test_never_wraps_a_normal_daily_step(self):
        # Even a fast body (Moon, ~13-15 deg/day) never triggers a spurious
        # wrap on an ordinary daily step.
        vals = [10.0, 24.0, 38.0]
        assert unwrap_series(vals) == pytest.approx([10.0, 24.0, 38.0])


# ── HermiteSpline ──────────────────────────────────────────────────────────────

class TestHermiteSpline:
    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            HermiteSpline((0.0, 1.0), (0.0,), (1.0, 1.0))

    def test_rejects_fewer_than_two_knots(self):
        with pytest.raises(ValueError):
            HermiteSpline((0.0,), (0.0,), (1.0,))

    def test_rejects_non_ascending_t(self):
        with pytest.raises(ValueError):
            HermiteSpline((0.0, 0.0), (0.0, 1.0), (1.0, 1.0))

    def test_linear_motion_exact(self):
        # A body moving at exactly 1 deg/day: the Hermite spline must
        # reproduce the line exactly (it interpolates value AND derivative
        # at every knot, and a line has zero curvature).
        t = list(range(10))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        for tq in (0.0, 2.3, 5.0, 8.99):
            assert sp.value(tq) == pytest.approx(tq, abs=1e-9)
            assert sp.velocity(tq) == pytest.approx(1.0, abs=1e-9)
            assert sp.acceleration(tq) == pytest.approx(0.0, abs=1e-9)

    def test_quadratic_motion_matches_analytic_derivative(self):
        # lam(t) = t^2 => lam'(t) = 2t. Hermite with exact tangents at each
        # knot reproduces a quadratic exactly (cubic Hermite is exact up to
        # cubics given exact derivatives at both ends).
        t = [float(x) for x in range(0, 11)]
        lam = [x * x for x in t]
        speed = [2 * x for x in t]
        sp = build_spline(t, lam, speed)
        for tq in (0.5, 3.25, 7.9):
            assert sp.value(tq) == pytest.approx(tq * tq, abs=1e-6)
            assert sp.velocity(tq) == pytest.approx(2 * tq, abs=1e-6)

    def test_clamps_queries_outside_domain(self):
        t = [0.0, 1.0, 2.0]
        lam = [0.0, 1.0, 2.0]
        speed = [1.0, 1.0, 1.0]
        sp = build_spline(t, lam, speed)
        # Should not raise; uses the boundary segment.
        assert sp.value(-5.0) == pytest.approx(-5.0)
        assert sp.value(50.0) == pytest.approx(50.0)


class TestMoonVelocityAssert:
    def test_passes_in_range(self):
        t = list(range(5))
        lam = [13.0 * x for x in t]
        speed = [13.0] * len(t)
        sp = build_spline(t, lam, speed)
        assert_moon_velocity_in_range(sp, sample_stride_days=1.0)  # no raise

    def test_halts_out_of_range(self):
        t = list(range(5))
        lam = [20.0 * x for x in t]
        speed = [20.0] * len(t)  # outside [11.60, 15.50]
        sp = build_spline(t, lam, speed)
        with pytest.raises(KinematicsVelocityOutOfRange):
            assert_moon_velocity_in_range(sp, sample_stride_days=1.0)


# ── Root finding ───────────────────────────────────────────────────────────────

class TestFindRootsOnGrid:
    def test_finds_a_simple_root(self):
        g = lambda t: t - 3.5
        roots = find_roots_on_grid(g, list(range(0, 10)))
        assert len(roots) == 1
        assert roots[0] == pytest.approx(3.5, abs=BRENT_XTOL_DAYS * 10)

    def test_no_root_returns_empty(self):
        g = lambda t: t + 100.0
        assert find_roots_on_grid(g, list(range(0, 10))) == []


class TestModulusBoundaryRoots:
    def test_sign_ingress_linear_motion(self):
        t = list(range(0, 40))
        lam = [float(x) + 0.37 for x in t]  # offset off any integer grid node
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        roots = find_modulus_boundary_roots(sp, t, 30.0)
        assert roots == pytest.approx([29.63], abs=1e-4)

    def test_multiple_boundaries_in_one_fast_day(self):
        # A body moving 40 deg/day crosses TWO 13.3333-wide (nakshatra)
        # boundaries within a single day-pair; both must be found. Offset the
        # start away from an exact multiple of the width so the two INTERIOR
        # crossings aren't confounded with the (also mathematically valid,
        # but not what this test targets) endpoint-exactly-on-a-boundary case.
        t = [0.0, 1.0]
        lam = [0.37, 27.37]  # 27deg span => exactly 2 of the 13.3333-wide boundaries
        speed = [27.0, 27.0]
        sp = build_spline(t, lam, speed)
        roots = find_modulus_boundary_roots(sp, t, 360.0 / 27.0)
        assert len(roots) == 2

    def test_exact_grid_node_boundary_not_missed(self):
        # Regression: a boundary landing exactly on a grid node's value must
        # still be found (this was a real bug caught during development).
        t = list(range(0, 40))
        lam = [float(x) for x in t]  # boundary at t=30 lands exactly on a knot
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        roots = find_modulus_boundary_roots(sp, t, 30.0)
        assert any(abs(r - 30.0) < 1e-6 for r in roots)


class TestStationRoots:
    def test_finds_station_with_correct_direction(self):
        t = [float(x) for x in range(0, 40)]
        lam = [10.0 * math.sin(x / 10.0) for x in t]
        speed = []
        for i in range(len(t)):
            if i == 0:
                speed.append(lam[1] - lam[0])
            elif i == len(t) - 1:
                speed.append(lam[-1] - lam[-2])
            else:
                speed.append((lam[i + 1] - lam[i - 1]) / 2.0)
        sp = build_spline(t, lam, speed)
        stations = find_station_roots(sp, t)
        assert len(stations) >= 1
        t_root, direction = stations[0]
        assert t_root == pytest.approx(5 * math.pi, abs=0.5)
        assert direction == "retro_onset"  # velocity goes + -> - at a sine's peak

    def test_no_station_for_constant_velocity(self):
        t = list(range(0, 10))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        assert find_station_roots(sp, t) == []


class TestSyzygyRoots:
    def test_finds_new_and_full_moon(self):
        # Moon at 13 deg/day, Sun at 1 deg/day, both starting at 0 => they
        # separate; Moon laps the Sun periodically (new moon at separation=0,
        # full moon at separation=180).
        t = [float(x) for x in range(0, 40)]
        moon = build_spline(t, [13.0 * x for x in t], [13.0] * len(t))
        sun = build_spline(t, [1.0 * x for x in t], [1.0] * len(t))
        roots = find_syzygy_roots(moon, sun, t)
        kinds = {k for _, k in roots}
        assert "new" in kinds
        assert "full" in kinds
        # separation(t) = 12t; full moon (separation=180) at t=15.
        full_roots = [r for r, k in roots if k == "full"]
        assert any(abs(r - 15.0) < 1e-3 for r in full_roots)


class TestEclipseCandidate:
    def test_new_moon_threshold(self):
        assert eclipse_candidate("new", 1.0) is True
        assert eclipse_candidate("new", 1.5) is True
        assert eclipse_candidate("new", 1.51) is False

    def test_full_moon_threshold_tighter(self):
        assert eclipse_candidate("full", 1.0) is True
        assert eclipse_candidate("full", 1.01) is False


# ── Contact episodes ───────────────────────────────────────────────────────────

class TestFindContactEpisodes:
    def test_single_pass_through_orb(self):
        t = list(range(0, 40))
        lam = [float(x) for x in t]  # 1 deg/day
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        eps = find_contact_episodes(sp, natal_lon=15.0, body="X", target_ref="Mo",
                                     t_grid=t, orb_deg=3.0, orb_source="default_3deg")
        assert len(eps) == 1
        ep = eps[0]
        assert ep.t_in == pytest.approx(12.0, abs=1e-4)
        assert ep.t_out == pytest.approx(18.0, abs=1e-4)
        assert ep.t_peak == pytest.approx(15.0, abs=1e-4)
        assert ep.ok_core_in == pytest.approx(14.25, abs=1e-4)
        assert ep.ok_core_out == pytest.approx(15.75, abs=1e-4)

    def test_no_contact_when_never_close_enough(self):
        t = list(range(0, 40))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        eps = find_contact_episodes(sp, natal_lon=200.0, body="X", target_ref="Mo",
                                     t_grid=t, orb_deg=3.0, orb_source="default_3deg")
        assert eps == []

    def test_grazing_pass_never_saturates_core(self):
        # A NON-monotonic (retrograde-loop-shaped) path oscillating 15 +/- 2
        # deg. Its closest approach to natal_lon=18.5 is exactly 1.5 deg (at
        # the sine's peak, lam=17) — inside the orb (3deg) but outside
        # omega_core (0.25*3=0.75deg) — a genuine grazing pass that never
        # reaches exact conjunction, only possible with a non-monotonic path
        # (a straight-line/monotonic path sweeping through the natal point's
        # range always reaches exact conjunction; see the saturated-pass test
        # above for that case).
        t = [float(x) for x in range(0, 60)]
        lam = [15.0 + 2.0 * math.sin(x / 10.0) for x in t]
        speed = [0.2 * math.cos(x / 10.0) for x in t]
        sp = build_spline(t, lam, speed)
        eps = find_contact_episodes(sp, natal_lon=18.5, body="X", target_ref="Mo",
                                     t_grid=t, orb_deg=3.0, orb_source="default_3deg")
        assert len(eps) >= 1
        ep = eps[0]
        assert ep.ok_core_in is None
        assert ep.ok_core_out is None
        # sanity: the episode's peak really is the sine's peak (min separation
        # 1.5deg, inside the 3deg orb, outside the 0.75deg core).
        assert abs(sp.value(ep.t_peak) - 17.0) < 0.05


# ── Dwell time / weight ───────────────────────────────────────────────────────

class TestDwellWeight:
    def test_mean_speed_gives_half(self):
        # D_nom for a body at exactly its mean speed with this orb equals the
        # observed dwell exactly, by construction of dwell_nominal_days.
        orb = 3.0
        v_bar = 1.0
        d_nom = dwell_nominal_days(orb, v_bar)
        assert d_nom == pytest.approx(6.0)
        d = dwell_days(12.0, 18.0)  # 6 days, same as d_nom at mean speed
        w = dwell_weight(d, d_nom)
        assert w == pytest.approx(0.5)

    def test_slower_than_mean_pushes_weight_above_half(self):
        d_nom = dwell_nominal_days(3.0, 1.0)  # 6.0
        w = dwell_weight(20.0, d_nom)  # much longer dwell than nominal
        assert w > 0.5

    def test_weight_bounded_open_interval(self):
        d_nom = dwell_nominal_days(3.0, 1.0)
        assert 0.0 < dwell_weight(0.001, d_nom) < 1.0
        assert 0.0 < dwell_weight(1e6, d_nom) < 1.0

    def test_rejects_zero_mean_motion(self):
        with pytest.raises(ValueError):
            dwell_nominal_days(3.0, 0.0)


class TestContactKernel:
    def test_peak_saturates_at_w_dwell(self):
        t = list(range(0, 40))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        w = 0.6
        v = contact_kernel(15.0, 15.0, sp, natal_lon=15.0, orb_deg=3.0, w_dwell=w)
        assert v == pytest.approx(w, abs=1e-9)

    def test_zero_outside_orb(self):
        t = list(range(0, 40))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        v = contact_kernel(0.0, 15.0, sp, natal_lon=15.0, orb_deg=3.0, w_dwell=0.6)
        assert v == pytest.approx(0.0)


# ── Row emission ───────────────────────────────────────────────────────────────

class TestRowEmission:
    def test_t_days_to_datetime_roundtrip_offset(self):
        dt = t_days_to_datetime(0.0)
        assert dt.year == 2000 and dt.month == 1 and dt.day == 1

    def test_make_episode_id_is_deterministic(self):
        a = make_episode_id("c1", "Mars", "Mo", 12.345)
        b = make_episode_id("c1", "Mars", "Mo", 12.345)
        c = make_episode_id("c1", "Mars", "Mo", 12.346)
        assert a == b
        assert a != c

    def test_ingress_rows_shape(self):
        t = list(range(0, 40))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        rows = ingress_rows("c1", "Mars", sp, "sign_ingress", [29.63])
        assert len(rows) == 1
        assert rows[0].event_kind == "sign_ingress"
        assert rows[0].chart_id == "c1"

    def test_station_rows_shape(self):
        t = list(range(0, 10))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        rows = station_rows("c1", "Saturn", sp, [(5.0, "retro_onset")])
        assert len(rows) == 1
        assert rows[0].event_kind == "station"

    def test_syzygy_rows_carries_eclipse_candidate(self):
        t = list(range(0, 10))
        lam_moon = [13.0 * x for x in t]
        lam_sun = [1.0 * x for x in t]
        speed_moon = [13.0] * len(t)
        speed_sun = [1.0] * len(t)
        moon = build_spline(t, lam_moon, speed_moon)
        sun = build_spline(t, lam_sun, speed_sun)
        lat = build_spline(t, [0.5] * len(t), [0.0] * len(t))
        rows = syzygy_rows("c1", moon, sun, lat, [(2.0, "new")])
        assert len(rows) == 1
        assert rows[0].eclipse_candidate is True
        assert rows[0].gamma_proxy == pytest.approx(0.5, abs=1e-2)

    def test_contact_episode_rows_emits_five_knots_when_saturated(self):
        t = list(range(0, 40))
        lam = [float(x) for x in t]
        speed = [1.0] * len(t)
        sp = build_spline(t, lam, speed)
        eps = find_contact_episodes(sp, natal_lon=15.0, body="Mars", target_ref="Mo",
                                     t_grid=t, orb_deg=3.0, orb_source="default_3deg")
        rows = contact_episode_rows("c1", sp, eps[0], "natal_graha", 15.0)
        kinds = [r.event_kind for r in rows]
        assert kinds == ["contact_in", "contact_core_in", "contact_peak",
                          "contact_core_out", "contact_out"]
        episode_ids = {r.episode_id for r in rows}
        assert len(episode_ids) == 1  # all 5 knots share one episode_id

    def test_contact_episode_rows_degrades_to_three_knots_when_grazing(self):
        t = [float(x) for x in range(0, 60)]
        lam = [15.0 + 2.0 * math.sin(x / 10.0) for x in t]
        speed = [0.2 * math.cos(x / 10.0) for x in t]
        sp = build_spline(t, lam, speed)
        eps = find_contact_episodes(sp, natal_lon=18.5, body="Mars", target_ref="Mo",
                                     t_grid=t, orb_deg=3.0, orb_source="default_3deg")
        rows = contact_episode_rows("c1", sp, eps[0], "natal_graha", 18.5)
        kinds = [r.event_kind for r in rows]
        assert kinds == ["contact_in", "contact_peak", "contact_out"]


# ── Live tier: needs a real DB connection ─────────────────────────────────────

_HAS_DB = bool(os.environ.get("DATABASE_URL"))


@pytest.mark.skipif(not _HAS_DB, reason="DATABASE_URL not set; skipping live DB test")
class TestLiveDbIntegration:
    def test_fetch_natal_longitude_and_write_roundtrip(self):
        import psycopg
        from services.ka_kshetra.stage0_kinematics import (
            KinematicsRow, fetch_natal_longitude, write_kinematics_rows,
        )

        conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
        try:
            chart_id = "482012f1-710e-4a25-994a-93821f5871aa"
            lon = fetch_natal_longitude(conn, chart_id, "natal_lagna", "Lagna")
            assert 0.0 <= lon < 360.0

            row = KinematicsRow(
                chart_id=chart_id, event_kind="station", body="__TEST__", t_days=1.0,
                longitude_deg=10.0, velocity_dps=0.0,
            )
            n = write_kinematics_rows(conn, [row])
            assert n == 1
            conn.execute("DELETE FROM kala_field_kinematics WHERE body = '__TEST__'")
            conn.commit()
        finally:
            conn.close()
