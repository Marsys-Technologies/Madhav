"""STATION-FIX (reworked per Codex STATION-CODEX-1) — the STORED station row tells the truth; the COMPUTATION is untouched.

THE DEFECT: the sky-event substrate stored every station at the root of the SPLINE derivative (daily noon knots) under solver_method 'swiss_refined' / delta_t 1e-9 d /
'swiss_bisect_tol_1e-9d', though no Swiss refinement ran for stations. Measured on the pinned files over the whole 1998-2085 domain (1,066 stations): the spline instant
is up to 16.7 s (Mercury) from the ephemeris station. The database REQUIRES the label for station rows (migration 1153: event_kind <> 'station' OR solver_method =
'swiss_refined'), so the row is made true by refining, not relabelled.

THE FIRST DESIGN WAS WRONG (and is withdrawn): feeding the refined stations into the arc index moved arc boundaries away from the spline's own extrema, so a ray level inside
the sliver was covered by neither arc: real crossings were lost (Mercury conjunction at 295.8493268245402: two crossings on 2074-01-24 vanished, 111 roots became 109, later
ordinals and contact ids changed), identity-bearing station targets changed for all 1,066 stations, and ordinary orb spans moved by up to 70 s.

THE DESIGN: (A) the arc index, segments, episodes, record store and writer are UNTOUCHED — unchanged from main to within platform float noise, 1e-7 day (pinned below by a golden produced on the unmodified main
tree, over the whole domain); (B) the stored row keeps its IDENTITY exactly (same target longitude = the spline's value at the spline station, so no event id changes), stores
the ephemeris-refined instant as t_exact, a per-body DEFENSIBLE BOUND as delta_t and an honest precision_regime; (C) the gap between the in-memory spline boundary and the
true station is documented and pinned (measured over the whole domain); (D) the writer refuses a convention that already holds station rows of the old false regime.

Real pinned files (skip NOT_RUN without them, a hard failure under GOCHARA_SE1_REQUIRE=1); no database.
"""
from __future__ import annotations

import ast
import inspect
import json
import pathlib
from datetime import date, timezone

import numpy as np
import pytest

from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel import knots as gk_knots
from services.gochara_kernel import substrate as gk_substrate
from services.gochara_kernel.knots import StationRefinementError, refine_station, sample_knots, station_delta_t_bound_days
from services.gochara_kernel.substrate import STATION_OLD_FALSE_REGIME, STATION_PRECISION_REGIME, SkyEventStore, StationRegimeConflict, boundary_target, jd_to_utc

from . import station_golden_matrix as matrix
from .conftest import EPHE_PATH, requires_swieph
from .test_a53_substrate_store import CID, CONVENTION_ROW, FakeConn

pytestmark = requires_swieph

ROOT = pathlib.Path(__file__).resolve().parents[3]
GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "station_matrix_golden_main.json"
BODIES = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_series: dict = {}


def _knots(body, start=date(1998, 1, 1), end=date(2085, 1, 1)):
    if (body, start, end) not in _series:
        _series[(body, start, end)] = sample_knots(body, start, end, EPHE_PATH)
    return _series[(body, start, end)]


# ── A. the computation is untouched ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_computation_is_unchanged_from_main_through_the_production_wiring_and_solve_point_edges():
    """Codex STATION-CODEX-2: the regression exercises the PRODUCTION index wiring (`substrate.production_arc_index`, the one function the substrate and the v5 writer's record
    phase build their index with) and `record_store.solve_point_edges`, and compares for every occurrence (ordinal, contact_id, truncated, solver_method, and t_exact, t_in,
    t_out) over the whole 1998-2085 domain and over the scored horizon, with the index (stations, arcs, segments) and the boundary roots, against the golden produced on the
    UNMODIFIED main tree. Both Mercury cases of the reviews are in: 295.8493268245402 (111 roots on main; the withdrawn design produced 109) and 5.39 (103; the withdrawn
    design moved its exit by up to 70 s).

    EXACT for everything discrete (key set, occurrence and row counts, ordinals, contact ids, truncated flags, solver_method, arc/segment structure): a missing or an extra
    occurrence always fails. TOLERANT, 1e-7 day (about 8.6 ms; 1e-7 degree on longitudes), on the continuous instants and station/arc values only. Why: platform libm / fused
    multiply-add last-bit differences, MEASURED between Mac arm64 and Linux x86_64 on identical code, pinned ephemeris files and requirements: they flipped 37 of the 47
    Jupiter digests of the earlier sha256-of-repr golden (every count identical), and CI failed on a golden that passed locally. The platform difference is ~1e-12; the
    defects this test exists for (a station moved by 8.6 s, an exit moved by 70 s, a lost crossing) are orders of magnitude outside the tolerance. A design that reaches the
    index through the production wiring fails here (shown by the harness mutations 'round-1 design' and 'just outside the tolerance')."""
    golden = json.loads(GOLDEN.read_text())
    assert golden["schema"] == matrix.SCHEMA and golden["tolerance_days"] == matrix.TOLERANCE_DAYS and golden["tolerance_deg"] == matrix.TOLERANCE_DEG
    cases = golden["cases"]
    got = matrix.compute(EPHE_PATH, gk_substrate.production_arc_index)
    assert set(got) == set(cases) and len(cases) >= 200
    assert cases["Mercury|domain|conjunction|295.8493268245402"]["n"] == 111 and cases["Mercury|domain|conjunction|5.39"]["n"] == 103
    problems = matrix.compare(cases, got)
    assert not problems, f"computation changed ({len(problems)} differences): {problems[:10]}"


def test_the_substrate_and_the_writer_build_their_arc_index_only_through_the_one_production_function():
    """The wiring the regression above exercises is the wiring production uses: neither the substrate nor the writer builds an arc index any other way."""
    for rel in ("services/gochara_kernel/substrate.py", "pipeline/orchestrator/writers/ka_gochara_v5.py"):
        tree = ast.parse((ROOT / rel).read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "build_arc_index"]
        in_fn = []
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "production_arc_index"]:
            in_fn = [c for c in ast.walk(fn) if isinstance(c, ast.Call) and getattr(c.func, "attr", getattr(c.func, "id", "")) == "build_arc_index"]
        assert len(calls) == len(in_fn), f"{rel}: build_arc_index called outside production_arc_index"
    assert "production_arc_index" in (ROOT / "pipeline/orchestrator/writers/ka_gochara_v5.py").read_text()


def test_no_production_code_feeds_a_refined_station_into_the_arc_index_the_episodes_the_record_store_or_the_writer():
    """The arc index API is main's: no refiner parameter, no refined-station fields; and `refine_station` is referenced only by the substrate (the stored row)."""
    assert "station_refiner" not in inspect.signature(gk_arcs.build_arc_index).parameters
    assert not {"stations_spline", "station_lons_deg", "station_refined", "station_delta_t_days"} & {f.name for f in gk_arcs.ArcIndex.__dataclass_fields__.values()}
    users = []
    for path in list((ROOT / "services").rglob("*.py")) + list((ROOT / "pipeline").rglob("*.py")):
        text = path.read_text()
        if "refine_station" in text:
            users.append(str(path.relative_to(ROOT)))
    assert sorted(users) == ["services/gochara_kernel/knots.py", "services/gochara_kernel/substrate.py"], users


# ── B. the stored row tells the truth, with its identity unchanged ────────────────────────────────────────────────────────────────────────

def _stored_rows(body):
    ks = _knots(body, date(1998, 1, 1), date(2012, 1, 1))
    idx = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)           # main's API: no refiner
    conn = FakeConn({"convention": [CONVENTION_ROW]})
    counts = SkyEventStore(conn).build_boundary_substrate(body, index=idx, refine=False, convention_id=CID, ephe_path=EPHE_PATH)
    stations = [p for sql, p in conn.statements if "INSERT INTO public.ka_gochara_sky_event" in sql and p[4] == "station"]
    objects = [p for sql, p in conn.statements if "INSERT INTO public.ka_gochara_physical_object" in sql and p[2] == "station"]
    return idx, counts, stations, objects


@pytest.mark.parametrize("body", BODIES)
def test_the_stored_station_row_keeps_its_identity_exactly_and_stores_the_refined_instant_with_an_honest_bound(body):
    idx, counts, stations, objects = _stored_rows(body)
    assert counts["stations"] == len(idx.stations) == len(stations) == len(objects) > 0
    for jd_spline, ev, obj in zip(idx.stations, stations, objects):
        lon = float(idx.evaluate(jd_spline)) % 360.0
        assert obj[3] == boundary_target(lon), "the identity-bearing target is the spline's value at the spline station — exactly as on main"
        assert ev[7] == lon, "the stored longitude is unchanged too"
        fix = refine_station(body, jd_spline, EPHE_PATH)
        assert ev[6] == jd_to_utc(fix.jd), "t_exact is the ephemeris-refined instant"
        assert abs((ev[6] - jd_to_utc(jd_spline)).total_seconds()) <= gk_knots.SPLINE_STATION_ERROR_BOUND_SECONDS[body]
        assert ev[8] == "swiss_refined" and ev[10] == station_delta_t_bound_days(body) and ev[11] == STATION_PRECISION_REGIME
        assert ev[10] != 1e-9 and ev[11] != STATION_OLD_FALSE_REGIME


def test_event_and_object_ids_do_not_change_only_the_stored_instant_and_the_bound_do():
    """The ids are derived from the identity-bearing target and the ordinal, never from t_exact: the same rows built from main's code carry the same ids."""
    from services.gochara_kernel.substrate import assign_occurrence_ordinals, physical_object_id
    idx, _counts, stations, objects = _stored_rows("Mercury")
    for jd_spline, ev, obj in zip(idx.stations, stations, objects):
        lon = float(idx.evaluate(jd_spline)) % 360.0
        poid = physical_object_id(body="mercury", relation_kind="station", canonical_target=boundary_target(lon), convention_id=CID)
        (contact,) = assign_occurrence_ordinals(physical_object_id=poid, t_exact_list=[jd_to_utc(jd_spline)])
        assert str(obj[0]) == str(poid.uuid) and str(ev[1]) == str(poid.uuid)
        assert str(ev[0]) == str(contact.contact_id), "the event id is the one main would mint for the spline instant"


def test_a_convention_holding_station_rows_of_the_old_false_regime_is_refused_by_name():
    ks = _knots("Mars", date(1998, 1, 1), date(2012, 1, 1))
    idx = gk_arcs.build_arc_index("Mars", ks.knot_jds, ks.longitudes_deg)
    conn = FakeConn({"convention": [CONVENTION_ROW], "count": [(3,)]})
    with pytest.raises(StationRegimeConflict, match="swiss_bisect_tol_1e-9d"):
        SkyEventStore(conn).build_boundary_substrate("Mars", index=idx, refine=False, convention_id=CID, ephe_path=EPHE_PATH)
    assert not [1 for sql, _p in conn.statements if "INSERT INTO" in sql], "nothing is written beside old-regime rows"


# ── the refinement itself ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_refine_station_is_deterministic_refuses_a_non_station_and_a_body_without_a_bound():
    ks = _knots("Saturn", date(1998, 1, 1), date(2012, 1, 1))
    idx = gk_arcs.build_arc_index("Saturn", ks.knot_jds, ks.longitudes_deg)
    s0 = idx.stations[0]
    assert refine_station("Saturn", s0, EPHE_PATH) == refine_station("Saturn", s0, EPHE_PATH)
    with pytest.raises(StationRefinementError, match="not an ephemeris station"):
        refine_station("Saturn", s0 + 200.0, EPHE_PATH)
    with pytest.raises(StationRefinementError, match="no station uncertainty bound"):
        station_delta_t_bound_days("Sun")


# ── C. the gap is documented and pinned over the WHOLE domain ──────────────────────────────────────────────────────────────────────────

def _lon(body, jd):
    return gk_knots.calc_sidereal_lon_speed(body, jd, EPHE_PATH)


def _ensemble_offsets(body, centre):
    """Every independent estimator's station instant as an OFFSET (days) from `centre`: cubic / quartic fits of the longitude over several windows, quadratic fits of the
    speed over several windows."""
    out = []
    for width, n, deg in ((0.05, 101, 3), (0.1, 201, 3), (0.15, 301, 4), (0.3, 301, 4), (0.6, 301, 4)):
        xs = np.linspace(-width, width, n)
        lon = np.degrees(np.unwrap(np.radians(np.array([_lon(body, centre + float(x))[0] for x in xs]))))
        roots = [t.real for t in np.roots(np.polyder(np.poly1d(np.polyfit(xs, lon, deg)))) if abs(t.imag) < 1e-12 and abs(t.real) <= width]
        if roots:
            out.append(min(roots, key=abs))
    for width, n in ((0.02, 41), (0.05, 101), (0.1, 201), (0.3, 301)):
        xs = np.linspace(-width, width, n)
        speed = np.array([_lon(body, centre + float(x))[1] for x in xs])
        roots = [t.real for t in np.roots(np.polyfit(xs, speed, 2)) if abs(t.imag) < 1e-12 and abs(t.real) <= width]
        if roots:
            out.append(min(roots, key=abs))
    return out


@pytest.mark.parametrize("body", BODIES)
def test_the_spline_to_ephemeris_gap_and_the_stored_bound_hold_over_every_station_of_the_whole_domain(body):
    """C + the bound of ruling B, for EVERY station of 1998-2085: (i) the spline boundary is within SPLINE_STATION_ERROR_BOUND of the refined station; (ii) no independent
    estimator differs from the stored instant by more than HALF the stored delta_t bound (margin 2), so the bound covers the worst case with room."""
    idx = gk_arcs.build_arc_index(body, _knots(body).knot_jds, _knots(body).longitudes_deg)
    gap_bound = gk_knots.SPLINE_STATION_ERROR_BOUND_SECONDS[body]
    dt_bound = gk_knots.STATION_DELTA_T_BOUND_SECONDS[body]
    worst_gap = worst_dev = 0.0
    assert len(idx.stations) > 10
    for s0 in idx.stations:
        fix = refine_station(body, s0, EPHE_PATH)
        worst_gap = max(worst_gap, abs(fix.jd - s0) * 86400.0)
        offsets = _ensemble_offsets(body, fix.jd)
        assert offsets
        worst_dev = max(worst_dev, max(abs(o) for o in offsets) * 86400.0)
    assert worst_gap <= gap_bound, f"{body}: spline-to-ephemeris gap {worst_gap:.2f} s exceeds the documented {gap_bound} s"
    assert worst_dev <= dt_bound / 2.0, f"{body}: an independent estimator is {worst_dev:.2f} s from the stored instant; the stored bound {dt_bound} s has no margin 2"
