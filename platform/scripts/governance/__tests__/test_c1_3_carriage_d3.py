"""test_c1_3_carriage_d3.py: C1-3 (SS N-101; design /Users/Dev/suvarna-evidence/L0_WAVE/C1_CARR_DESIGN.md section 3; spike /Users/Dev/suvarna-evidence/E5.7/CARR_SPIKE_REPORT.md):
the generic D3 engine (`carriage_d3.py`) and its two reviewed methods (`carriage_d3_methods.py`).

Ordinary tests on REAL fixtures, no database:
  * `fixtures/c1_3_ga_positions_writer_rows_moshier.json`: the REAL `ga_positions_writer._build_position_rows` output (1,205 chart_facts rows, the asset's own count_sql: graha_position, graha_sign_attributes, bhava_cusps, house_chalit, sandhi_flag; five ayanamshas) at origin/main f8fb06402, from the adapter's own position / ascendant code on a Moshier backend (no .se1 on the generating host);
  * `fixtures/c1_3_bg_sky_calendar_writer_rows.json`: the REAL bg_sky_calendar scan functions + `_to_insert_dict` output (window A 2010-2012: ingresses, stations, solar and lunar eclipses; window B: the 2020 Jupiter-Saturn double transit).
The reference leg is pyswisseph called directly; the tests skip when it is not installed. The generators are in the spike evidence directory (`E5.7/carr_spike/gen_*.py`).
No declaration of any asset is filled by this file: the specs below live in the test.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

pytest.importorskip("swisseph")
import carriage_d3 as d3  # noqa: E402

FIX = HERE / "fixtures"
POS = json.loads((FIX / "c1_3_ga_positions_writer_rows_moshier.json").read_text(encoding="utf-8"))
SKY = json.loads((FIX / "c1_3_bg_sky_calendar_writer_rows.json").read_text(encoding="utf-8"))
EV = "platform/python-sidecar/ga_writers/ga_positions_writer.py:289"
METHODS = d3.load_methods()
BACKENDS = ["swieph", "moseph"]


def _pos_columns():
    env = "Moshier versus se1 envelope 0.67 arcsec, 5x margin"
    cols = {}
    import carriage_d3_methods as cm
    for c in cm.POSITION_COLUMNS:
        if c in ("longitude_sidereal", "dist_to_madhya_deg", "dist_to_nearest_boundary_deg") or c.startswith(("sripati_", "placidus_")):
            cols[c] = dict(kind="circular_deg" if c == "longitude_sidereal" or c.startswith(("sripati_", "placidus_")) else "linear", tol=0.001, basis=env)
        elif c == "degree_in_sign":
            cols[c] = dict(kind="circular_30", tol=0.001, basis=env)
        else:
            cols[c] = dict(kind="exact", tol=0, basis="discrete or tabulated value derived from the longitude")
    return cols


def pos_spec(**over):
    s = dict(
        method="swisseph_sidereal_positions_v1", table="chart_facts", expected_rows=110, key=["subject", "ayanamsha"],
        read=dict(columns=["fact_category", "fact_subject", "fact_key", "ayanamsha_id", "fact_value_num", "fact_value_text"],
                  where=[{"column": "fact_category", "in": ["graha_position", "graha_sign_attributes", "bhava_cusps", "house_chalit", "sandhi_flag"]}], chart_scoped=True,
                  inputs=dict(table="charts", columns=["birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id"], id_column="id")),
        columns=_pos_columns(),
        conventions={"position_model": dict(value="true_geometric", evidence="unverified:jhora drik.py:124 _rise_flags carries swe.FLG_TRUEPOS (the PyJHora position convention)"),
                     "node_model": dict(value="mean_node", evidence="platform/python-sidecar/pyjhora_adapter/positions.py:20"),
                     "house_rule": dict(value="whole_sign", evidence="platform/python-sidecar/pyjhora_adapter/compute.py:80"),
                     "bhava_system": dict(value="sripati_quadrant_trisection_and_placidus", evidence="platform/python-sidecar/pyjhora_adapter/houses.py:198"),
                     "bhava_flags": dict(value="sidereal_only", evidence="unverified:jhora drik.py bhaava_madhya_swe uses FLG_SIDEREAL only (the Lagna and planets carry the true-position flag; the cusps do not)"),
                     "combustion_orbs": dict(value="moon12_mars17_mercury14_jupiter11_venus10_saturn15", evidence="platform/python-sidecar/pyjhora_adapter/dignities.py:39"),
                     "sandhi_orb": dict(value="3.0", evidence="platform/python-sidecar/pyjhora_adapter/houses.py:128")},
        uncovered=[], backend=dict(allowed=BACKENDS, basis="the declared tolerance carries the measured Moshier versus se1 envelope"),
        boundary={"sign_num": dict(source="longitude_sidereal", width=30.0, cells=12), "nakshatra_num": dict(source="longitude_sidereal", width=360 / 27, cells=27),
                  "pada": dict(source="longitude_sidereal", width=360 / 108, cells=4)})
    s.update(copy.deepcopy(over))
    return s


def pos_rows():
    return copy.deepcopy(POS["rows"])


def pos_inputs():
    return [copy.deepcopy(POS["chart"])]


def fix_nodes(rows):
    """The nodes' retrograde flag set to the sign of the mean-node motion (the one real disagreement the writer's rows carry): the 'clean' variant."""
    for r in rows:
        if r["fact_key"] == "retrograde_flag" and r["fact_subject"] in ("RAH_MEAN", "KET_MEAN"):
            r["fact_value_text"] = "retrograde"
    return rows


def _setrow(rows, subj, ay, key, **vals):
    for r in rows:
        if r["fact_subject"] == subj and r["ayanamsha_id"] == ay and r["fact_key"] == key:
            r.update(vals)
            return
    raise AssertionError((subj, ay, key))


def measure_pos(spec=None, rows=None, **kw):
    kw.setdefault("asset_rows", 1205)                       # the asset's live count (its count_sql, 1,205 for the canonical chart): N-156 review MED-2, an unread count is never coverage
    return d3.d3_measure(spec or pos_spec(), rows if rows is not None else pos_rows(), "chart_facts", inputs=kw.pop("inputs", pos_inputs()), **kw)


# ───────────────────────── positions ─────────────────────────

def test_spec_validates():
    d3.validate_spec(pos_spec(), "x")


def test_real_writer_rows_pass_with_the_node_flag_ruled_by_the_reference():
    m = measure_pos(rows=fix_nodes(pos_rows()))
    assert m["v"] == "PASS", m["measured"]
    ev = m["d3"]
    assert ev["rows_total"] == 110 and ev["rows_checked"] == 110 and ev["rows_agree"] == 110 and ev["full_population"] is True and ev["n_mismatch"] == 0
    assert ev["backend"]["name"] in BACKENDS and ev["max_residual"]["longitude_sidereal"] <= 0.001
    assert d3.d3_evidence_problem(m) == ""


def test_the_writers_node_retrograde_flag_is_a_real_finding():
    m = measure_pos()                       # the writer's own rows: Rahu / Ketu stored 'direct', the mean-node longitude moves backward
    assert m["v"] == "PARTIAL" and m["d3"]["n_mismatch"] == 10
    assert {x["row"].split("|")[0] for x in m["d3"]["mismatches"]} == {"RAH_MEAN", "KET_MEAN"} and all(x["columns"] == ["retrograde_flag"] for x in m["d3"]["mismatches"])
    assert d3.d3_evidence_problem(m) == ""


def test_declared_uncovered_column_caps_partial():
    s = pos_spec(uncovered=[{"column": "retrograde_flag", "reason": "the node flag convention is not yet ruled", "evidence": EV}])
    del s["columns"]["retrograde_flag"]
    m = measure_pos(s, fix_nodes(pos_rows()))
    assert m["v"] == "PARTIAL" and "uncovered" in m["measured"] and m["d3"]["n_mismatch"] == 0


def _mut(fn, **kw):
    rows = fix_nodes(pos_rows())
    fn(rows)
    return measure_pos(rows=rows, **kw)


def _setv(rows, subj, ay, key, **vals):
    for r in rows:
        if r["fact_subject"] == subj and r["ayanamsha_id"] == ay and r["fact_key"] == key:
            r.update(vals)
            return
    raise AssertionError((subj, ay, key))


def test_a_longitude_two_tolerances_off_is_caught():
    m = _mut(lambda rs: [r.__setitem__("fact_value_num", r["fact_value_num"] + 0.002) for r in rs
                         if r["fact_subject"] == "SAT" and r["ayanamsha_id"] == "raman" and r["fact_key"] == "longitude_sidereal"])
    assert m["v"] == "PARTIAL" and m["d3"]["mismatches"][0]["row"] == "SAT|raman" and "longitude_sidereal" in m["d3"]["mismatches"][0]["columns"]


def test_a_longitude_within_tolerance_is_not_a_false_alarm():
    m = _mut(lambda rs: [r.__setitem__("fact_value_num", r["fact_value_num"] + 0.0005) for r in rs
                         if r["fact_subject"] == "SAT" and r["ayanamsha_id"] == "raman" and r["fact_key"] == "longitude_sidereal"])
    assert m["v"] == "PASS"


def test_every_discrete_column_is_checked():
    for subj, key, val in (("SUN", "sign_num", 5.0), ("MOON", "pada", 1.0), ("MAR", "house_d1", 12.0), ("JUP", "retrograde_flag", None)):
        def f(rs, subj=subj, key=key, val=val):
            if val is None:
                _setv(rs, subj, "true_chitra", key, fact_value_text="retrograde")
            else:
                _setv(rs, subj, "true_chitra", key, fact_value_num=val)
        m = _mut(f)
        assert m["v"] == "PARTIAL" and m["d3"]["mismatches"][0]["row"] == f"{subj}|true_chitra", (subj, key, m["measured"])
    m = _mut(lambda rs: _setv(rs, "VEN", "krishnamurti", "nakshatra", fact_value_text="Revati"))
    assert m["v"] == "PARTIAL" and "nakshatra_num" in m["d3"]["mismatches"][0]["columns"]
    m = _mut(lambda rs: _setv(rs, "VEN", "krishnamurti", "nakshatra", fact_value_text="Nakshatra X"))     # a name outside the 27 is a mismatch, not a skip
    assert m["v"] == "PARTIAL"
    nn = d3.load_methods()["swisseph_sidereal_positions_v1"]
    import carriage_d3_methods as cm
    assert [cm.nakshatra_number(n) for n in ("Purva Bhadrapada", "Purva_Bhadrapada", "Moola", "Mula", "Mrigasira", "Mrigashira", "Revati", "x", None)] == [25, 25, 19, 19, 5, 5, 27, None, None]


def test_an_ayanamsha_mislabel_is_caught_by_the_independent_sidereal_map():
    """The Track A1 defect class: every KP row carrying Lahiri values. The method's own sidereal-mode map (by swisseph constant name) disagrees with a shared-map error."""
    lah = {(r["fact_subject"], r["fact_key"]): r for r in pos_rows() if r["ayanamsha_id"] == "lahiri_chitrapaksha"}

    def f(rs):
        for r in rs:
            if r["ayanamsha_id"] == "krishnamurti":
                r["fact_value_num"] = lah[(r["fact_subject"], r["fact_key"])]["fact_value_num"]
                r["fact_value_text"] = lah[(r["fact_subject"], r["fact_key"])]["fact_value_text"]
    m = _mut(f)
    assert m["v"] == "PARTIAL" and {x["row"].split("|")[1] for x in m["d3"]["mismatches"]} == {"krishnamurti"}


def test_dropped_row_duplicate_row_and_unknown_ayanamsha():
    assert _mut(lambda rs: rs[:] and [rs.remove(r) for r in [x for x in rs if x["fact_subject"] == "LAGNA" and x["ayanamsha_id"] == "raman"]])["v"] == "PARTIAL"
    m = _mut(lambda rs: _setv(rs, "SUN", "raman", "pada", ayanamsha_id="not_an_ayanamsha"))
    assert m["v"] == "PARTIAL"            # a row the method cannot derive is a named mismatch, not a skip


def test_sampling_never_reads_pass():
    s = pos_spec(strata="ayanamsha", sample=dict(per_stratum=3, seed="t"))
    m = measure_pos(s, fix_nodes(pos_rows()))
    assert m["v"] == "PARTIAL" and m["d3"]["rows_checked"] == 15 and m["d3"]["full_population"] is False and "sample" in m["measured"]
    assert d3.d3_evidence_problem(dict(m, v="PASS")) != ""             # a record that claims PASS beside its own sample is not honoured
    again = measure_pos(s, fix_nodes(pos_rows()))
    assert [x for x in again["d3"]["strata"].items()] == [x for x in m["d3"]["strata"].items()] and again["d3"]["population_sha256"] == m["d3"]["population_sha256"]


def test_asset_rows_beyond_the_declared_read_cap_partial():
    assert len(pos_rows()) == 1205                                 # the declared read covers every row the writer emits (its count_sql: 1,205 for the canonical chart)
    assert measure_pos(rows=fix_nodes(pos_rows()), asset_rows=1205)["v"] == "PASS"
    m = measure_pos(rows=fix_nodes(pos_rows()), asset_rows=1300)          # the asset holds rows the declared read does not cover (a category added later): cannot read PASS
    assert m["v"] == "PARTIAL" and "1205 of the asset's 1300" in m["measured"]
    assert d3.d3_evidence_problem(dict(m, v="PASS")) != ""
    short = [r for r in fix_nodes(pos_rows()) if r["fact_category"] != "sandhi_flag"]        # a writer that stopped emitting a category is a named mismatch (the method derives it)
    assert measure_pos(rows=short)["v"] == "PARTIAL"


def test_expected_rows_and_unreadable_inputs():
    assert measure_pos(pos_spec(expected_rows=51), fix_nodes(pos_rows()))["v"] == "PARTIAL"
    m = measure_pos(rows=fix_nodes(pos_rows()), inputs=[])
    assert m["v"] == "NO_DETECTOR" and "re-derivation inputs" in m["measured"]
    bad = pos_inputs()
    bad[0]["timezone_id"] = "Not/AZone"
    assert measure_pos(rows=fix_nodes(pos_rows()), inputs=bad)["v"] == "NO_DETECTOR"
    assert d3.d3_measure(pos_spec(), None, "chart_facts", inputs=pos_inputs())["v"] == "NO_DETECTOR"
    assert d3.d3_measure(pos_spec(), [], "chart_facts", inputs=pos_inputs())["v"] == "NO_DETECTOR"


def test_the_birth_instant_changes_the_answer():
    """The reference reads the chart's own birth parameters: a chart born a day later does not agree with the stored rows."""
    later = pos_inputs()
    later[0]["birth_date"] = "1984-02-06"
    m = measure_pos(rows=fix_nodes(pos_rows()), inputs=later)
    assert m["v"] in ("PARTIAL", "FAIL") and m["d3"]["n_mismatch"] > 30


def test_forensic_anchors_hold_in_the_reference_leg():
    """FORENSIC grounding (CLAUDE.md section B): Sun in Capricorn, Moon in Purva Bhadrapada, Lagna Aries, for all five ayanamshas, in the REFERENCE values themselves."""
    m = d3.load_methods()["swisseph_sidereal_positions_v1"]
    ctx = m["context"](None, pos_inputs(), pos_spec())
    for ay in ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"):
        sun = m["ref"](dict(subject="SUN", ayanamsha=ay), ctx)
        moon = m["ref"](dict(subject="MOON", ayanamsha=ay), ctx)
        lag = m["ref"](dict(subject="LAGNA", ayanamsha=ay), ctx)
        assert sun["sign_num"] == 10 and moon["nakshatra_num"] == 25 and lag["sign_num"] == 1 and lag["house_d1"] == 1, ay


# ───────────────────────── the engine's own refusals ─────────────────────────

@pytest.mark.parametrize("mutate,msg", [
    (lambda s: s.__setitem__("method", "nope"), "closed registry"),
    (lambda s: s.__setitem__("table", "bg_sky_calendar"), "borrow a method"),
    (lambda s: s["columns"]["longitude_sidereal"].__setitem__("tol", 0.5), "reviewed maximum"),
    (lambda s: s["columns"]["longitude_sidereal"].__setitem__("basis", "tuned"), "basis"),
    (lambda s: s["columns"]["sign_num"].__setitem__("tol", 1), "exact"),
    (lambda s: s["columns"].__setitem__("tropical", dict(kind="linear", tol=0.0, basis="not a column of the method")), "does not re-derive"),
    (lambda s: s["conventions"].pop("position_model"), "conventions"),
    (lambda s: s["conventions"]["position_model"].__setitem__("value", "geocentric_dreams"), "not one the method implements"),
    (lambda s: s.pop("backend"), "backend"),
    (lambda s: s["read"].pop("inputs"), "inputs"),
    (lambda s: s["read"]["where"].append({"column": "x", "equals": "a'; drop table t; --"}), "plain strings"),
    (lambda s: s.__setitem__("sample", dict(per_stratum=3, seed="x")), "needs `strata`"),
    (lambda s: s.__setitem__("expected_rows", 0), "expected_rows"),
    (lambda s: s.__setitem__("extra", 1), "unknown field"),
    (lambda s: s["uncovered"].append({"column": "sign_num", "reason": "declared and uncovered at once", "evidence": EV}), "also re-derived"),
])
def test_spec_refusals(mutate, msg):
    s = pos_spec()
    mutate(s)
    with pytest.raises(d3.SpecError, match=msg):
        d3.validate_spec(s, "x")


def test_a_same_code_method_never_passes_and_an_unusable_backend_is_no_detector():
    m = dict(METHODS["swisseph_sidereal_positions_v1"], independence="same_code")
    r = d3.d3_measure(pos_spec(), fix_nodes(pos_rows()), "chart_facts", method=m, inputs=pos_inputs())
    assert r["v"] == "NO_DETECTOR" and "same-code" in r["measured"]
    m = dict(METHODS["swisseph_sidereal_positions_v1"], backend_probe=lambda: {"name": "other"})
    r = d3.d3_measure(pos_spec(), fix_nodes(pos_rows()), "chart_facts", method=m, inputs=pos_inputs())
    assert r["v"] == "NO_DETECTOR" and "fallen back silently" in r["measured"]

    def boom():
        raise ImportError("swisseph")
    m = dict(METHODS["swisseph_sidereal_positions_v1"], backend_probe=boom)
    r = d3.d3_measure(pos_spec(), fix_nodes(pos_rows()), "chart_facts", method=m, inputs=pos_inputs())
    assert r["v"] == "NO_DETECTOR" and "ImportError" in r["measured"]
    assert d3.d3_measure(pos_spec(), fix_nodes(pos_rows()), "chart_dashas", inputs=pos_inputs())["v"] == "NO_DETECTOR"       # the registry target table is not the spec's


def test_a_relation_method_caps_partial_and_a_total_miss_is_fail():
    base = METHODS["swisseph_sidereal_positions_v1"]
    rel = dict(base, independence="relation")
    r = d3.d3_measure(pos_spec(), fix_nodes(pos_rows()), "chart_facts", method=rel, inputs=pos_inputs())
    assert r["v"] == "PARTIAL" and "relation" in r["measured"]
    wrong = dict(base, ref=lambda row, ctx: {c: (-1 if c != "retrograde_flag" else "sideways") for c in pos_spec()["columns"]})
    r = d3.d3_measure(pos_spec(), fix_nodes(pos_rows()), "chart_facts", method=wrong, inputs=pos_inputs())
    assert r["v"] == "FAIL"


def test_boundary_tolerance_is_listed_never_silent():
    base = METHODS["swisseph_sidereal_positions_v1"]
    ref = lambda row, ctx: dict(longitude_sidereal=30.0004, degree_in_sign=0.0004, sign_num=2, nakshatra_num=3, pada=1, house_d1=1, retrograde_flag="direct")
    rows = [dict(subject="X", ayanamsha="a", longitude_sidereal=29.9999, degree_in_sign=29.9999, sign_num=1, nakshatra_num=3, pada=1, house_d1=1, retrograde_flag="direct")]
    m = dict(base, logical_rows=lambda r, i: rows, ref=ref, context=lambda r, i, s: None)
    spec = pos_spec(expected_rows=1, key=["subject", "ayanamsha"])
    r = d3.d3_measure(spec, [{"x": 1}], "chart_facts", method=m, inputs=[], asset_rows=1)
    assert r["v"] == "PASS" and [b["column"] for b in r["d3"]["boundary_tolerated"]] == ["sign_num"]
    rows[0]["sign_num"] = 7                                    # not adjacent: no tolerance
    assert d3.d3_measure(spec, [{"x": 1}], "chart_facts", method=m, inputs=[])["v"] == "FAIL"


def test_evidence_guard_refuses_bare_and_contradictory_records():
    assert d3.d3_evidence_problem({"v": "PASS"}) != ""
    good = measure_pos(rows=fix_nodes(pos_rows()))
    assert d3.d3_evidence_problem(good) == ""
    for mutate in (lambda e: e.__setitem__("population_sha256", "x"), lambda e: e.__setitem__("independence", "same_code"), lambda e: e.__setitem__("n_mismatch", 1),
                   lambda e: e.__setitem__("conventions", {}), lambda e: e.__setitem__("row_count_ok", False), lambda e: e.__setitem__("rows_checked", 0)):
        bad = copy.deepcopy(good)
        mutate(bad["d3"])
        assert d3.d3_evidence_problem(bad) != ""


# ───────────────────────── bg_sky_calendar: every event family ─────────────────────────

NODE_TOL = {"Rahu": 0.006, "Ketu": 0.006}


def _tol(default):
    return {"default": default, "by": {"column": "primary_body", "values": dict(NODE_TOL)}}


def sky_spec(window="window_a", **over):
    s = dict(method="swisseph_sky_events_v1", table="bg_sky_calendar", expected_rows="method", key=["event_type", "primary_body", "secondary_body", "event_jd"],
             read=dict(columns=["event_type", "primary_body", "secondary_body", "event_jd", "event_datetime_utc", "sign", "nakshatra", "longitude_deg", "speed_dps", "ayanamsha_key", "detail"], where=[], chart_scoped=False),
             columns={"sign": dict(kind="exact", tol=0, basis="the sign at the re-derived instant"),
                      "nakshatra_num": dict(kind="exact", tol=0, basis="the nakshatra of the re-derived longitude"),
                      "event_datetime_s": dict(kind="linear", tol=2.0, basis="the writer stores event_jd to 5 decimals (0.86 s) and truncates the datetime to the second"),
                      "target_sign": dict(kind="exact", tol=0, basis="the ingress detail target_sign equals the sign entered"),
                      "longitude_deg": dict(kind="circular_deg", tol=_tol(0.001), basis="writer stores 4 decimals; true node wider; same ephemeris"),
                      "speed_dps": dict(kind="linear", tol=0.005, basis="writer stores 6 decimals; speed changes under 0.5 degree a day squared"),
                      "ayanamsha_key": dict(kind="exact", tol=0, basis="stored label equals the declared ayanamsha"),
                      "edge_distance_deg": dict(kind="linear", tol=_tol(0.001), basis="positional tolerance at the stored instant, writer bisection and 5-decimal event_jd"),
                      "station_type": dict(kind="exact", tol=0, basis="sign of the speed before the station"),
                      "station_zero_speed": dict(kind="linear", tol=0.0005, basis="five minutes of motion of the fastest stationing body"),
                      "conj_orb_deg": dict(kind="linear", tol=0.001, basis="writer stores the orb to 4 decimals"),
                      "conj_offset_deg": dict(kind="linear", tol=0.001, basis="the stored instant is the minimum separation within a bisection step"),
                      "planet_b_lon": dict(kind="circular_deg", tol=0.002, basis="writer stores 4 decimals"),
                      "eclipse_type": dict(kind="exact", tol=0, basis="shadow-geometry classification, boundary cases listed"),
                      "is_central": dict(kind="exact", tol=0, basis="central limit of the shadow axis, boundary cases listed"),
                      "ecl_time_offset_s": dict(kind="linear", tol=180.0, basis="measured max 49 s solar and 46 s lunar against the swecl.c greatest-eclipse instant, 3x margin"),
                      "begin_offset_s": dict(kind="linear", tol=180.0, basis="measured max 123 s against the swecl.c contact instants, 1.5x margin"),
                      "end_offset_s": dict(kind="linear", tol=180.0, basis="measured max 123 s against the swecl.c contact instants, 1.5x margin")},
             conventions={"position_model": dict(value="apparent", evidence="platform/python-sidecar/pipeline/transit_search.py:262"),
                          "node_model": dict(value="true_node", evidence="platform/python-sidecar/pipeline/transit_search.py:60"),
                          "ayanamsha": dict(value="lahiri", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:195"),
                          "eclipse_geometry": dict(value="swecl_radii_fundamental_plane", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:435"),
                          "shadow_enlargement": dict(value="1_over_0.99", evidence="unverified:swecl.c lunar shadow enlargement (measured: 1/0.99 matches 309 of 311 lunar eclipses 1900-2036)"),
                          "history_start": dict(value=SKY[window]["history_start"], evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:100")},
             uncovered=[], backend=dict(allowed=BACKENDS, basis="the declared tolerances cover the writer's own resolution; a Moshier run is allowed only in this fixture test"),
             boundary={"nakshatra_num": dict(source="longitude_deg", width=360 / 27, cells=27)})
    s.update(copy.deepcopy(over))
    return s


def sky_rows(window="window_a"):
    return copy.deepcopy(SKY[window]["rows"])


def sky_measure(window="window_a", spec=None, rows=None, **kw):
    rows = rows if rows is not None else sky_rows(window)
    kw.setdefault("asset_rows", len(SKY[window]["rows"]))
    return d3.d3_measure(spec or sky_spec(window), rows, "bg_sky_calendar", **kw)


def _types(rows):
    return {r["event_type"] for r in rows}


def test_the_real_writer_rows_cover_every_family_and_pass_in_full():
    t0 = time.time()
    m = sky_measure()
    assert m["v"] == "PASS", m["measured"]
    ev = m["d3"]
    assert _types(sky_rows()) == {"ingress", "station", "eclipse_solar", "eclipse_lunar"} and ev["rows_total"] == ev["rows_checked"] == len(SKY["window_a"]["rows"]) and ev["full_population"] is True
    assert ev["completeness_problems"] == [] and ev["row_count_ok"] is True and d3.d3_evidence_problem(m) == ""
    assert ev["max_residual"]["ecl_time_offset_s"] <= 180 and time.time() - t0 < 120
    m2 = sky_measure("window_b")
    assert m2["v"] == "PASS" and m2["d3"]["rows_total"] == 1 and _types(sky_rows("window_b")) == {"double_transit"}, m2["measured"]


def _row(rows, et, **kw):
    return next(i for i, r in enumerate(rows) if r["event_type"] == et and all(r.get(k) == v for k, v in kw.items()))


def _smut(window, i_et, fn, **kw):
    rows = sky_rows(window)
    i = _row(rows, i_et, **kw)
    fn(rows[i])
    return sky_measure(window, rows=rows)


def _detail_set(**kv):
    def f(r):
        d = json.loads(r["detail"])
        d.update(kv)
        r["detail"] = json.dumps(d)
    return f


def test_ingress_and_station_mutations_are_caught():
    m = _smut("window_a", "ingress", lambda r: r.__setitem__("event_jd", r["event_jd"] + 0.014), primary_body="Moon")           # 20 minutes: the Moon is 0.18 degree off the edge
    assert m["v"] == "PARTIAL" and m["d3"]["n_mismatch"] == 1 and "edge_distance_deg" in m["d3"]["mismatches"][0]["columns"]
    m = _smut("window_a", "ingress", lambda r: r.__setitem__("event_jd", r["event_jd"] + 3.0), primary_body="Mars")
    assert m["v"] == "PARTIAL" and m["d3"]["mismatches"][0]["columns"][0].startswith("error:")                              # no crossing within 0.2 day
    m = _smut("window_a", "ingress", lambda r: r.__setitem__("ayanamsha_key", "raman"), primary_body="Sun")
    assert m["v"] == "PARTIAL" and "ayanamsha_key" in m["d3"]["mismatches"][0]["columns"]
    m = _smut("window_a", "station", lambda r: r.__setitem__("event_jd", r["event_jd"] + 0.4), primary_body="Mercury")
    assert m["v"] == "PARTIAL" and "station_zero_speed" in m["d3"]["mismatches"][0]["columns"]
    m = _smut("window_a", "station", _detail_set(station_type="direct" if True else "retrograde"), primary_body="Saturn")
    assert m["v"] in ("PARTIAL", "PASS")                                                  # (a Saturn station that already was direct leaves the row unchanged)
    rows = sky_rows()
    i = _row(rows, "station", primary_body="Jupiter")
    cur = json.loads(rows[i]["detail"])["station_type"]
    _detail_set(station_type="retrograde" if cur == "direct" else "direct")(rows[i])
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL" and "station_type" in m["d3"]["mismatches"][0]["columns"]


def test_eclipse_mutations_are_caught():
    cur = lambda rows, et: json.loads(rows[_row(rows, et)]["detail"])
    rows = sky_rows()
    t0 = cur(rows, "eclipse_solar")["eclipse_type"]
    m = _smut("window_a", "eclipse_solar", _detail_set(eclipse_type="partial" if t0 != "partial" else "total"))
    assert m["v"] == "PARTIAL" and "eclipse_type" in m["d3"]["mismatches"][0]["columns"]
    m = _smut("window_a", "eclipse_lunar", lambda r: r.__setitem__("event_jd", r["event_jd"] + 0.05))                          # 72 minutes off the greatest eclipse
    assert m["v"] == "PARTIAL" and "ecl_time_offset_s" in m["d3"]["mismatches"][0]["columns"]
    m = _smut("window_a", "eclipse_solar", lambda r: _detail_set(begin_jd=round(json.loads(r["detail"])["begin_jd"] + 0.01, 6))(r))      # a contact 14 minutes off
    assert m["v"] == "PARTIAL" and "begin_offset_s" in m["d3"]["mismatches"][0]["columns"]
    m = _smut("window_a", "eclipse_lunar", lambda r: r.__setitem__("sign", "Aries" if r["sign"] != "Aries" else "Taurus"))
    assert m["v"] == "PARTIAL" and "sign" in m["d3"]["mismatches"][0]["columns"]


def test_a_dropped_or_invented_event_is_a_named_completeness_discrepancy():
    rows = sky_rows()
    i = _row(rows, "eclipse_lunar")
    gone = rows.pop(i)
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL" and any("eclipse_lunar" in p for p in m["d3"]["completeness_problems"]) and "completeness" in m["measured"]
    rows = sky_rows()
    j = _row(rows, "ingress", primary_body="Jupiter")
    rows.pop(j)
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL" and any(p.startswith("ingress Jupiter") for p in m["d3"]["completeness_problems"])
    rows = sky_rows()
    rows.append(dict(rows[_row(rows, "station", primary_body="Venus")], event_jd=rows[_row(rows, "station", primary_body="Venus")]["event_jd"] + 0.5))
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL"


def test_double_transit_mutations_are_caught():
    rows = sky_rows("window_b")
    rows[0]["event_jd"] += 1.0
    assert sky_measure("window_b", rows=rows)["v"] in ("PARTIAL", "FAIL")                      # a day away from the minimum separation
    rows = sky_rows("window_b")
    rows[0]["detail"] = json.dumps(dict(json.loads(rows[0]["detail"]), orb_deg=0.9))
    m = sky_measure("window_b", rows=rows)
    assert m["v"] in ("PARTIAL", "FAIL") and "conj_orb_deg" in m["d3"]["mismatches"][0]["columns"]
    assert sky_measure("window_b", rows=[])["v"] == "NO_DETECTOR"


def test_a_sampled_sky_run_cannot_pass_and_method_completeness_needs_a_method_that_has_one():
    s = sky_spec(strata="event_type", sample=dict(per_stratum=4, seed="s"))
    m = d3.d3_measure(s, sky_rows(), "bg_sky_calendar", asset_rows=len(SKY["window_a"]["rows"]))
    assert m["v"] == "PARTIAL" and m["d3"]["rows_checked"] == 16 and "sample" in m["measured"]
    with pytest.raises(d3.SpecError, match="completeness"):
        d3.validate_spec(pos_spec(expected_rows="method"), "x")
    with pytest.raises(d3.SpecError, match="positive integer"):
        d3.validate_spec(sky_spec(expected_rows="fifty"), "x")


def test_the_two_methods_are_the_closed_registry():
    assert sorted(METHODS) == ["swisseph_sidereal_positions_v1", "swisseph_sky_events_v1"]
    for k, m in METHODS.items():
        assert m["independence"] == "independent_formula" and set(d3.METHOD_HOOKS) <= set(m)
    with pytest.raises(d3.SpecError):
        d3.register_method("swisseph_sidereal_positions_v1", **METHODS["swisseph_sidereal_positions_v1"])
    with pytest.raises(d3.SpecError):
        d3.register_method("incomplete", independence="independent_formula")


# ───────────────────────── N-156 review fixes ─────────────────────────

def test_med2_an_unread_live_count_is_never_coverage():
    rows = fix_nodes(pos_rows())
    m = d3.d3_measure(pos_spec(), rows, "chart_facts", inputs=pos_inputs())                  # asset_rows None: the count_sql could not be read
    assert m["v"] == "PARTIAL" and "live row count is unreadable" in m["measured"]
    assert d3.d3_evidence_problem(dict(m, v="PASS")) != "" and "not read" in d3.d3_evidence_problem(dict(m, v="PASS"))
    ok = d3.d3_measure(pos_spec(), rows, "chart_facts", inputs=pos_inputs(), asset_rows=1205)
    assert ok["v"] == "PASS" and d3.d3_evidence_problem(ok) == ""
    assert d3.d3_measure(pos_spec(), rows, "chart_facts", inputs=pos_inputs(), asset_rows=True)["v"] == "PARTIAL"     # a bool is not a count


def test_med3_a_datetime_disagreeing_with_event_jd_and_a_wrong_target_sign_are_caught():
    rows = sky_rows()
    i = _row(rows, "ingress", primary_body="Mars")
    rows[i]["event_datetime_utc"] = "2010-01-01T00:00:00"
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL" and m["d3"]["mismatches"][0]["columns"] == ["event_datetime_s"]
    rows = sky_rows()
    i = _row(rows, "ingress", primary_body="Jupiter")
    rows[i]["detail"] = json.dumps({"target_sign": "Aries" if json.loads(rows[i]["detail"])["target_sign"] != "Aries" else "Taurus"})
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL" and m["d3"]["mismatches"][0]["columns"] == ["target_sign"]
    rows = sky_rows()
    rows[_row(rows, "eclipse_lunar")]["event_datetime_utc"] = None                         # a missing stored datetime is a mismatch, not a skip
    assert sky_measure(rows=rows)["v"] == "PARTIAL"


def test_low4_no_eclipse_is_never_ambiguous_and_an_ambiguous_value_needs_an_adjacent_stored_one():
    import carriage_d3_methods as cm
    assert cm._solar_type(1.5, 0.01, 0.01, 0.5)[1] == float("inf") and cm._solar_type(1.5, 0.01, 0.01, 0.5)[0] is None
    base = METHODS["swisseph_sky_events_v1"]
    cols = {c: d for c, d in sky_spec()["columns"].items() if c == "eclipse_type"}
    spec = sky_spec(columns=cols, expected_rows=1, key=["event_type", "primary_body", "secondary_body", "event_jd"])
    row = dict(event_type="eclipse_solar", primary_body="Sun", secondary_body="Moon", event_jd=1.0, eclipse_type="total")
    ref = lambda r, ctx: {"eclipse_type": "partial", "_ambiguous": {"eclipse_type": {"note": "near a boundary", "neighbours": ["total", "annular_total"]}}}
    m = dict(base, logical_rows=lambda r, i: [dict(row)], ref=ref, context=lambda r, i, s: None, backend_probe=None, completeness=None)
    spec.pop("backend", None)
    spec["expected_rows"] = 1
    spec["conventions"] = {}
    r = d3.d3_measure(dict(spec, uncovered=[]), [{"x": 1}], "bg_sky_calendar", method=dict(m, required_conventions={}), asset_rows=1)
    assert r["d3"]["boundary_tolerated"] and r["d3"]["boundary_tolerated"][0]["column"] == "eclipse_type" and r["v"] == "PASS"
    far = dict(m, logical_rows=lambda r, i: [dict(row, eclipse_type="annular")])         # not an adjacent classification: ambiguity does not excuse it
    r = d3.d3_measure(dict(spec, uncovered=[]), [{"x": 1}], "bg_sky_calendar", method=dict(far, required_conventions={}), asset_rows=1)
    assert r["v"] == "FAIL" and not r["d3"]["boundary_tolerated"]


def test_low4_the_real_writer_eclipse_rows_use_no_blanket_ambiguity():
    m = sky_measure()
    assert m["v"] == "PASS" and all(b.get("column") != "eclipse_type" or "boundary" in b.get("ambiguity", "") or "limit" in b.get("ambiguity", "") for b in m["d3"]["boundary_tolerated"])


def test_low5_history_start_is_the_production_value_and_early_rows_are_named():
    with pytest.raises(d3.SpecError, match="not one the method implements"):
        d3.validate_spec(sky_spec(), "x")                                                  # the fixture window start 2010-01-01 is not a production value
    s = sky_spec()
    s["conventions"]["history_start"] = dict(value="1900-01-01", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:100")
    d3.validate_spec(s, "x")
    early = sky_rows()
    e = copy.deepcopy(early[_row(early, "ingress", primary_body="Mars")])
    e["event_jd"] -= 3650.0
    early.append(e)
    m = sky_measure(rows=early)
    assert m["v"] != "PASS" and any("before the declared history_start" in p for p in m["d3"]["completeness_problems"])


def test_low5_duplicate_keys_use_a_counter_and_stay_named():
    rows = sky_rows()
    rows.append(copy.deepcopy(rows[_row(rows, "station", primary_body="Venus")]))
    m = sky_measure(rows=rows)
    assert m["v"] == "PARTIAL" and m["d3"]["duplicate_keys"] and any("duplicate" in x["columns"] for x in m["d3"]["mismatches"])
