"""test_n544_carriage_d3_eclipse_class.py: SS N-538 item 4 / N-544 (worker D3B): the bg_sky_calendar Carr.D3 eclipse leg.

Two changes of the reviewed method `swisseph_sky_events_v1` (carriage_d3_methods.py v3) and the one harness extension they need (carriage_d3.py `tol_for` / `validate_spec`):
  1. `is_central` of a solar eclipse is swecl.c's own central test: the shadow AXIS touches the OBLATE Earth (the 2003-05-31 annular eclipse is central by 5.5 km although its umbra circle is not
     wholly inside the Earth disc, which was the method's earlier, stricter criterion `gamma < 1 - |u|`).
  2. The begin / end contact tolerance is scoped by a CLASS the method derives from its own geometry (`ecl_depth_class`, the method's `tol_classes`): 240 s is the reviewed cap for every
     eclipse the method does not class as a shallow partial; the cap for a shallow partial is its MEASURED bound (solar 615 s, lunar 445 s: 1.5x the max over all 622 stored eclipses 1900-2036,
     measured 409.9 s solar / 296.5 s lunar on the pinned Swiss ephemeris). The wide cap exists ONLY for the class column.

The six eclipses below are REAL stored rows of bg_sky_calendar (the exported 622-row eclipse set the measurement of /Users/Dev/suvarna-evidence/N431/bg_sky_calendar_d3_eclipse_measurement.md read).
The reference leg is pyswisseph called directly (Moshier is allowed in this test only; the geometry margins below are far larger than the Moshier-versus-se1 difference); the test skips without it.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

pytest.importorskip("swisseph")
import carriage_d3 as d3  # noqa: E402
import carriage_d3_methods as cm  # noqa: E402
import test_c1_3_carriage_d3 as t3  # noqa: E402

REAL = {
    "S_SHALLOW": {"event_type": "eclipse_solar", "primary_body": "Sun", "secondary_body": "Moon", "event_jd": 2421222.36524, "event_datetime_utc": "1916-12-24T20:45:57", "sign": "Sagittarius", "nakshatra": None, "longitude_deg": 250.0495, "speed_dps": 1.019321, "ayanamsha_key": "lahiri", "detail": {"end_jd": 2421222.373288, "begin_jd": 2421222.357341, "is_central": False, "eclipse_type": "partial"}},
    "L_SHALLOW": {"event_type": "eclipse_lunar", "primary_body": "Moon", "secondary_body": "Sun", "event_jd": 2436327.00896, "event_datetime_utc": "1958-05-03T12:12:54", "sign": "Libra", "nakshatra": None, "longitude_deg": 199.1769, "speed_dps": 14.903689, "ayanamsha_key": "lahiri", "detail": {"end_jd": 2436327.016528, "begin_jd": 2436327.00138, "eclipse_type": "partial"}},
    "S_ANNULAR": {"event_type": "eclipse_solar", "primary_body": "Sun", "secondary_body": "Moon", "event_jd": 2452790.67241, "event_datetime_utc": "2003-05-31T04:08:16", "sign": "Taurus", "nakshatra": None, "longitude_deg": 45.4222, "speed_dps": 0.959126, "ayanamsha_key": "lahiri", "detail": {"end_jd": 2452790.770632, "begin_jd": 2452790.573903, "is_central": True, "eclipse_type": "annular"}},
    "S_ORDINARY": {"event_type": "eclipse_solar", "primary_body": "Sun", "secondary_body": "Moon", "event_jd": 2417413.05145, "event_datetime_utc": "1906-07-21T13:14:05", "sign": "Cancer", "nakshatra": None, "longitude_deg": 95.2897, "speed_dps": 0.955036, "ayanamsha_key": "lahiri", "detail": {"end_jd": 2417413.110596, "begin_jd": 2417412.992323, "is_central": False, "eclipse_type": "partial"}},
    "S_TOTAL": {"event_type": "eclipse_solar", "primary_body": "Sun", "secondary_body": "Moon", "event_jd": 2415168.1208, "event_datetime_utc": "1900-05-28T14:53:57", "sign": "Taurus", "nakshatra": None, "longitude_deg": 44.3169, "speed_dps": 0.959334, "ayanamsha_key": "lahiri", "detail": {"end_jd": 2415168.233003, "begin_jd": 2415168.008615, "is_central": True, "eclipse_type": "total"}},
    "L_ORDINARY": {"event_type": "eclipse_lunar", "primary_body": "Moon", "secondary_body": "Sun", "event_jd": 2421768.93597, "event_datetime_utc": "1918-06-24T10:27:47", "sign": "Sagittarius", "nakshatra": None, "longitude_deg": 249.2748, "speed_dps": 13.286692, "ayanamsha_key": "lahiri", "detail": {"end_jd": 2421768.964637, "begin_jd": 2421768.907321, "eclipse_type": "partial"}},
}
SKY_ID = "swisseph_sky_events_v1"
CLASS_TOL = {"default": 180.0, "by": {"column": "ecl_depth_class", "values": {"shallow_partial_solar": 615.0, "shallow_partial_lunar": 445.0}}}
METHOD = dict(t3.METHODS[SKY_ID], completeness=lambda logical, ctx, spec: (True, None))       # the six rows are not the whole table: only the completeness leg is stubbed


def _spec(blanket=None):
    s = t3.sky_spec()
    s["conventions"]["history_start"] = dict(value="1900-01-01", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:100")
    for c in ("begin_offset_s", "end_offset_s"):
        s["columns"][c]["tol"] = copy.deepcopy(CLASS_TOL) if blanket is None else blanket
    return s


def _rows(*names):
    out = []
    for n in names:
        r = copy.deepcopy(REAL[n])
        r["detail"] = json.dumps(r["detail"])                  # the table stores detail as a jsonb string
        out.append(r)
    return out


def _measure(rows, spec=None):
    return d3.d3_measure(spec or _spec(), rows, "bg_sky_calendar", method=METHOD, asset_rows=len(rows))


def _with_control(row, control="S_TOTAL"):
    """The mutated row next to one untouched real row: the verdict is then PARTIAL (one row disagrees), not FAIL (none agree)."""
    return _measure([row] + _rows(control))


def _ref(name):
    """(method ref dict, logical row) of one real row, by the method's own functions."""
    rows = _rows(name)
    spec = _spec()
    lr = METHOD["logical_rows"](rows, None)[0]
    return METHOD["ref"](lr, METHOD["context"](rows, None, spec)), lr


def _set_offset(row, col, target_s):
    """Move the stored contact so that the method's re-derived offset of that contact is exactly `target_s` (a mutation of a stored contact, in seconds)."""
    key = "begin_jd" if col == "begin_offset_s" else "end_jd"
    ref, _ = _ref_of(row)
    d = json.loads(row["detail"])
    d[key] = d[key] - (target_s - ref[col]) / 86400.0
    row["detail"] = json.dumps(d)
    return row


def _ref_of(row):
    spec = _spec()
    lr = METHOD["logical_rows"]([row], None)[0]
    return METHOD["ref"](lr, METHOD["context"]([row], None, spec)), lr


def _sgn(x):
    return 1.0 if x >= 0 else -1.0


def test_the_six_real_rows_are_classed_by_the_methods_own_geometry_and_pass_class_scoped():
    want = {"S_SHALLOW": "shallow_partial_solar", "L_SHALLOW": "shallow_partial_lunar", "S_ANNULAR": "other", "S_ORDINARY": "other", "S_TOTAL": "other", "L_ORDINARY": "other"}
    assert {n: _ref(n)[0]["ecl_depth_class"] for n in REAL} == want
    m = _measure(_rows(*REAL))
    assert m["v"] == "PASS", m["measured"]
    assert m["d3"]["n_mismatch"] == 0 and m["d3"]["max_residual"]["begin_offset_s"] > 250.0       # the wide class bound is what carried the 345 s shallow-partial contact
    assert d3.d3_evidence_problem(m) == ""


def test_the_blanket_180_s_fails_the_shallow_partials_which_is_why_the_class_exists():
    m = _measure(_rows(*REAL), _spec(blanket=180.0))
    assert m["v"] == "PARTIAL" and {x["row"].split("|")[-1] for x in m["d3"]["mismatches"]} == {"2421222.36524", "2436327.00896"}
    assert all("begin_offset_s" in x["columns"] or "end_offset_s" in x["columns"] for x in m["d3"]["mismatches"])


@pytest.mark.parametrize("name", ["S_ORDINARY", "S_TOTAL", "L_ORDINARY"])
@pytest.mark.parametrize("col", ["begin_offset_s", "end_offset_s"])
@pytest.mark.parametrize("direction", [1.0, -1.0])
def test_mutation_a_non_shallow_contact_shifted_300_s_fails(name, col, direction):
    row = _rows(name)[0]
    ref, _ = _ref_of(row)
    assert ref["ecl_depth_class"] == "other" and abs(ref[col]) < 180.0                                # the unmutated row is inside the ordinary 180 s
    _set_offset(row, col, ref[col] + direction * 300.0)
    m = _with_control(row, "S_TOTAL" if name != "S_TOTAL" else "L_ORDINARY")
    assert m["v"] == "PARTIAL" and m["d3"]["n_mismatch"] == 1 and col in m["d3"]["mismatches"][0]["columns"]


@pytest.mark.parametrize("name,col,cap", [("S_SHALLOW", "begin_offset_s", 615.0), ("S_SHALLOW", "end_offset_s", 615.0), ("L_SHALLOW", "begin_offset_s", 445.0), ("L_SHALLOW", "end_offset_s", 445.0)])
def test_mutation_a_shallow_partial_contact_beyond_its_class_bound_fails_and_inside_it_passes(name, col, cap):
    row = _rows(name)[0]
    ref, _ = _ref_of(row)
    assert ref["ecl_depth_class"].startswith("shallow_partial")
    s = _sgn(ref[col])
    inside = _measure([_set_offset(copy.deepcopy(row), col, s * (cap - 10.0))])
    assert inside["v"] == "PASS", inside["measured"]
    beyond = _with_control(_set_offset(copy.deepcopy(row), col, s * (cap + 10.0)))
    assert beyond["v"] == "PARTIAL" and beyond["d3"]["n_mismatch"] == 1 and col in beyond["d3"]["mismatches"][0]["columns"]


def test_the_class_is_the_methods_own_never_the_stored_rows():
    row = _rows("S_ORDINARY")[0]
    ref, _ = _ref_of(row)
    _set_offset(row, "begin_offset_s", ref["begin_offset_s"] + _sgn(ref["begin_offset_s"]) * 300.0)
    d = json.loads(row["detail"])
    d["ecl_depth_class"] = "shallow_partial_solar"                                                  # a stored claim of the wide class changes nothing
    row["detail"] = json.dumps(d)
    row["ecl_depth_class"] = "shallow_partial_solar"
    m = _with_control(row)
    assert m["v"] == "PARTIAL" and "begin_offset_s" in m["d3"]["mismatches"][0]["columns"]
    assert d3.tol_for(CLASS_TOL, {"ecl_depth_class": "shallow_partial_solar"}, {"ecl_depth_class": "other"}, ("ecl_depth_class",)) == 180.0
    assert d3.tol_for(CLASS_TOL, {}, {"ecl_depth_class": "shallow_partial_lunar"}, ("ecl_depth_class",)) == 445.0
    assert d3.tol_for(CLASS_TOL, {}, {"ecl_depth_class": None}, ("ecl_depth_class",)) == 180.0           # a row the method did not class (an ingress) keeps the default
    assert d3.tol_for(CLASS_TOL, {"ecl_depth_class": "shallow_partial_solar"}, None) == 615.0      # (without `classes` the column is read from the row: the key-column path, unchanged)


def test_the_class_thresholds_separate_the_measured_set():
    solar_deep = _ref("S_ORDINARY")[0]
    assert solar_deep["ecl_depth_class"] == "other"
    for jd_name, depth_max in (("S_SHALLOW", cm._SHALLOW_SOLAR_DEPTH_RE),):
        j = REAL[jd_name]["event_jd"]
        tg = cm._golden_min(lambda x: cm._solar_geom(x)[0], j - 0.1, j + 0.1)
        g, u, l1, z, tf2 = cm._solar_geom(tg)
        assert 1 + l1 - g < depth_max / 10                                                          # 0.0095 Earth radii of overlap: far inside the class
    assert cm._SHALLOW_SOLAR_DEPTH_RE == 0.15 and abs(cm._SHALLOW_LUNAR_DEPTH_RAD * 206264.806247 - 120.0) < 1e-9


# ───────────────────────── is_central: swecl.c's oblate-Earth axis-touch test ─────────────────────────

def test_the_2003_annular_eclipse_is_central_by_the_swecl_axis_test_though_the_old_criterion_said_no():
    j = REAL["S_ANNULAR"]["event_jd"]
    tg = cm._golden_min(lambda x: cm._solar_geom(x)[0], j - 0.1, j + 0.1)
    g, u, l1, z, tf2 = cm._solar_geom(tg)
    assert g >= 1 - abs(u) + 1e-9                                                                   # the earlier criterion (umbra circle wholly inside the disc) reads not central
    assert 1.0 < cm._solar_axis_margin_km(tg) < 12.0                                                # swecl.c: the axis touches the oblate Earth, by about 5.5 km
    ref, lr = _ref("S_ANNULAR")
    assert ref["is_central"] is True and lr["is_central"] is True and "is_central" not in ref.get("_ambiguous", {})
    assert _measure(_rows("S_ANNULAR"))["v"] == "PASS"


def test_mutation_reverting_is_central_to_the_old_criterion_fails_the_2003_row(monkeypatch):
    monkeypatch.setitem(METHOD["ref"].__globals__, "_solar_axis_margin_km", lambda t: -1000.0)       # the axis-touch test reads false (the registered module is a separate load of the file)
    m = _with_control(_rows("S_ANNULAR")[0], "L_ORDINARY")           # a lunar control: the solar axis test is not used for it
    assert m["v"] == "PARTIAL" and m["d3"]["mismatches"][0]["columns"] == ["is_central"] and m["d3"]["n_mismatch"] == 1


def test_a_non_central_partial_and_a_total_keep_their_stored_is_central():
    for n in ("S_SHALLOW", "S_ORDINARY"):
        assert _ref(n)[0]["is_central"] is False and _ref(n)[1]["is_central"] is False
    assert _ref("S_TOTAL")[0]["is_central"] is True
    assert cm._solar_axis_margin_km(cm._golden_min(lambda x: cm._solar_geom(x)[0], REAL["S_SHALLOW"]["event_jd"] - 0.1, REAL["S_SHALLOW"]["event_jd"] + 0.1)) < -1000.0


# ───────────────────────── the reviewed cap: the wide bound only for the class column ─────────────────────────

def _v(**cols):
    s = _spec()
    for c, tol in cols.items():
        s["columns"][c]["tol"] = tol
    return d3.validate_spec(s, "x", methods=t3.METHODS)


def test_the_declared_class_scoped_form_validates():
    _v()
    _v(begin_offset_s=copy.deepcopy(CLASS_TOL), end_offset_s={"default": 240.0, "by": {"column": "ecl_depth_class", "values": {"shallow_partial_solar": 615.0}}})


@pytest.mark.parametrize("col", ["begin_offset_s", "end_offset_s"])
def test_the_cap_refuses_a_wide_tolerance_anywhere_but_the_shallow_classes(col):
    for bad, why in ((1000.0, "scalar 1000"), (241.0, "scalar 241"), (615.0, "scalar 615"),
                     ({"default": 300.0, "by": CLASS_TOL["by"]}, "default 300"),
                     ({"default": 180.0, "by": {"column": "ecl_depth_class", "values": {"other": 300.0}}}, "class other 300"),
                     ({"default": 180.0, "by": {"column": "ecl_depth_class", "values": {"shallow_partial_solar": 616.0}}}, "solar class 616"),
                     ({"default": 180.0, "by": {"column": "ecl_depth_class", "values": {"shallow_partial_lunar": 446.0}}}, "lunar class 446"),
                     ({"default": 180.0, "by": {"column": "primary_body", "values": {"Sun": 615.0}}}, "wide value keyed by a key column"),
                     ({"default": 180.0, "by": {"column": "ecl_depth_class", "values": {"bogus": 100.0}}}, "unknown class value")):
        with pytest.raises(d3.SpecError):
            _v(**{col: bad})
            pytest.fail(why)


def test_the_class_column_is_reviewed_only_where_the_methods_cap_is_keyed_by_it():
    with pytest.raises(d3.SpecError, match="class column"):
        _v(ecl_time_offset_s=copy.deepcopy(CLASS_TOL))                                              # the greatest-eclipse offset has a scalar cap
    with pytest.raises(d3.SpecError, match="class column|a key column"):
        _v(longitude_deg=copy.deepcopy(CLASS_TOL))
    assert t3.METHODS[SKY_ID]["max_tol"]["ecl_time_offset_s"] == 240.0 and t3.METHODS[SKY_ID]["version"] == "3"


def test_mutation_removing_the_cap_makes_validate_spec_accept_1000():
    with pytest.raises(d3.SpecError, match="reviewed maximum"):
        _v(begin_offset_s=1000.0)
    meths = copy.deepcopy({k: v for k, v in t3.METHODS.items()})
    for c in ("begin_offset_s", "end_offset_s"):
        meths[SKY_ID]["max_tol"][c] = 10 ** 9                                                       # the cap removed
    s = _spec()
    s["columns"]["end_offset_s"]["tol"] = 180.0
    s["columns"]["begin_offset_s"]["tol"] = 1000.0
    d3.validate_spec(s, "x", methods=meths)
    meths[SKY_ID]["max_tol"]["begin_offset_s"] = {"default": 240.0, "by": "ecl_depth_class", "values": {"shallow_partial_solar": 10 ** 9}}      # the class cap removed
    s["columns"]["begin_offset_s"]["tol"] = {"default": 180.0, "by": {"column": "ecl_depth_class", "values": {"shallow_partial_solar": 1000.0}}}
    d3.validate_spec(s, "x", methods=meths)
    with pytest.raises(d3.SpecError, match="reviewed maximum"):
        _v(begin_offset_s=s["columns"]["begin_offset_s"]["tol"], end_offset_s=180.0)


def test_only_the_sky_method_declares_tolerance_classes_and_the_positions_method_is_unchanged():
    assert t3.METHODS[SKY_ID]["tol_classes"] == {"ecl_depth_class": ("shallow_partial_solar", "shallow_partial_lunar", "other")}
    assert "tol_classes" not in t3.METHODS["swisseph_sidereal_positions_v1"]
    assert all(not isinstance(v, dict) or "by" not in v for v in t3.METHODS["swisseph_sidereal_positions_v1"]["max_tol"].values())
