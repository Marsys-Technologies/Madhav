"""test_c1_3_carriage_d3.py: C1-3 (SS N-101; design /Users/Dev/suvarna-evidence/L0_WAVE/C1_CARR_DESIGN.md section 3; spike /Users/Dev/suvarna-evidence/E5.7/CARR_SPIKE_REPORT.md):
the generic D3 engine (`carriage_d3.py`) and its two reviewed methods (`carriage_d3_methods.py`).

Ordinary tests on REAL fixtures, no database:
  * `fixtures/c1_3_ga_positions_writer_rows_moshier.json`: the REAL `ga_positions_writer._build_position_rows` output (530 chart_facts rows: five ayanamshas x the nine grahas and
    the Lagna) at origin/main f8fb06402, from the adapter's own position / ascendant code on a Moshier backend (no .se1 on the generating host);
  * `fixtures/c1_3_bg_sky_calendar_ingress_writer_rows.json`: the REAL `bg_sky_calendar.scan_ingresses` + `_to_insert_dict` output (419 ingress rows, 2010-2012).
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
SKY = json.loads((FIX / "c1_3_bg_sky_calendar_ingress_writer_rows.json").read_text(encoding="utf-8"))
EV = "platform/python-sidecar/ga_writers/ga_positions_writer.py:289"
METHODS = d3.load_methods()
BACKENDS = ["swieph", "moseph"]


def pos_spec(**over):
    s = dict(
        method="swisseph_sidereal_positions_v1", table="chart_facts", expected_rows=50, key=["subject", "ayanamsha"],
        read=dict(columns=["fact_category", "fact_subject", "fact_key", "ayanamsha_id", "fact_value_num", "fact_value_text"],
                  where=[{"column": "fact_category", "in": ["graha_position", "graha_sign_attributes"]}], chart_scoped=True,
                  inputs=dict(table="charts", columns=["birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id"], id_column="id")),
        columns={"longitude_sidereal": dict(kind="circular_deg", tol=0.001, basis="Moshier versus se1 envelope 0.67 arcsec, 5x margin"),
                 "degree_in_sign": dict(kind="circular_30", tol=0.001, basis="Moshier versus se1 envelope 0.67 arcsec, 5x margin"),
                 "sign_num": dict(kind="exact", tol=0, basis="discrete value derived from the longitude"),
                 "nakshatra_num": dict(kind="exact", tol=0, basis="discrete value derived from the longitude"),
                 "pada": dict(kind="exact", tol=0, basis="discrete value derived from the longitude"),
                 "house_d1": dict(kind="exact", tol=0, basis="whole-sign house from the sign numbers"),
                 "retrograde_flag": dict(kind="exact", tol=0, basis="sign of the longitude speed")},
        conventions={"position_model": dict(value="true_geometric", evidence="unverified:jhora drik.py:124 _rise_flags carries swe.FLG_TRUEPOS (the PyJHora position convention)"),
                     "node_model": dict(value="mean_node", evidence="platform/python-sidecar/pyjhora_adapter/positions.py:20"),
                     "house_rule": dict(value="whole_sign", evidence="platform/python-sidecar/pyjhora_adapter/compute.py:80")},
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


def measure_pos(spec=None, rows=None, **kw):
    return d3.d3_measure(spec or pos_spec(), rows if rows is not None else pos_rows(), "chart_facts", inputs=kw.pop("inputs", pos_inputs()), **kw)


# ───────────────────────── positions ─────────────────────────

def test_spec_validates():
    d3.validate_spec(pos_spec(), "x")


def test_real_writer_rows_pass_with_the_node_flag_ruled_by_the_reference():
    m = measure_pos(rows=fix_nodes(pos_rows()))
    assert m["v"] == "PASS", m["measured"]
    ev = m["d3"]
    assert ev["rows_total"] == 50 and ev["rows_checked"] == 50 and ev["rows_agree"] == 50 and ev["full_population"] is True and ev["n_mismatch"] == 0
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
    m = measure_pos(rows=fix_nodes(pos_rows()), asset_rows=1205)
    assert m["v"] == "PARTIAL" and "530 of the asset's 1205" in m["measured"]
    assert d3.d3_evidence_problem(dict(m, v="PASS")) != ""
    assert measure_pos(rows=fix_nodes(pos_rows()), asset_rows=530)["v"] == "PASS"


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
    r = d3.d3_measure(spec, [{"x": 1}], "chart_facts", method=m, inputs=[])
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


# ───────────────────────── bg_sky_calendar ingress ─────────────────────────

def sky_spec(**over):
    s = dict(method="swisseph_ingress_root_find_v1", table="bg_sky_calendar", expected_rows=len(SKY["rows"]), key=["primary_body", "sign", "event_jd"],
             read=dict(columns=["event_type", "primary_body", "sign", "event_jd", "longitude_deg", "ayanamsha_key"], where=[{"column": "event_type", "equals": "ingress"}], chart_scoped=False),
             columns={"edge_distance_deg": dict(kind="linear", tol={"default": 0.001, "by": {"column": "primary_body", "values": {"Rahu": 0.006, "Ketu": 0.006}}},
                                                 basis="Moshier versus se1 envelope 0.67 arcsec for planets, true node 18 arcsec, margins stated"),
                      "longitude_deg": dict(kind="circular_deg", tol={"default": 0.001, "by": {"column": "primary_body", "values": {"Rahu": 0.006, "Ketu": 0.006}}},
                                            basis="writer stores longitude to 4 decimals; same ephemeris envelope"),
                      "sign": dict(kind="exact", tol=0, basis="the sign entered at the crossing"), "ayanamsha_key": dict(kind="exact", tol=0, basis="stored label equals the declared ayanamsha")},
             conventions={"position_model": dict(value="apparent", evidence="platform/python-sidecar/pipeline/transit_search.py:262"),
                          "node_model": dict(value="true_node", evidence="platform/python-sidecar/pipeline/transit_search.py:60"),
                          "ayanamsha": dict(value="lahiri", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:195")},
             uncovered=[], backend=dict(allowed=BACKENDS, basis="a 1 second declared tolerance covers the Moshier versus se1 shift"), strata="primary_body")
    s.update(copy.deepcopy(over))
    return s


def sky_rows():
    return copy.deepcopy(SKY["rows"])


def test_real_writer_ingress_rows_pass_in_full():
    t0 = time.time()
    m = d3.d3_measure(sky_spec(), sky_rows(), "bg_sky_calendar")
    assert m["v"] == "PASS", m["measured"]
    ev = m["d3"]
    assert ev["rows_total"] == ev["rows_checked"] == len(SKY["rows"]) and ev["full_population"] is True and ev["max_residual"]["edge_distance_deg"] <= 0.006
    assert set(ev["strata"]) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    assert time.time() - t0 < 30 and d3.d3_evidence_problem(m) == ""


def _sky_mut(fn, spec=None):
    rows = sky_rows()
    fn(rows)
    return d3.d3_measure(spec or sky_spec(expected_rows=len(rows)), rows, "bg_sky_calendar")


def _first(rs, body):
    return next(r for r in rs if r["primary_body"] == body)


def test_ingress_time_slips_are_caught_by_position_at_the_stored_instant():
    # a 20 minute slip of a Moon ingress (13 degrees a day): the Moon is 0.18 degree off the edge at the stored instant
    m = _sky_mut(lambda rs: _first(rs, "Moon").__setitem__("event_jd", _first(rs, "Moon")["event_jd"] + 0.014))
    assert m["v"] == "PARTIAL" and m["d3"]["n_mismatch"] == 1 and "edge_distance_deg" in m["d3"]["mismatches"][0]["columns"]
    # a 3 day slip: no crossing of that edge within 0.2 day of the stored instant: a named mismatch
    m = _sky_mut(lambda rs: _first(rs, "Mars").__setitem__("event_jd", _first(rs, "Mars")["event_jd"] + 3.0))
    assert m["v"] == "PARTIAL" and m["d3"]["n_mismatch"] == 1 and m["d3"]["mismatches"][0]["columns"][0].startswith("error:")
    # the honest limit: the tolerance is POSITIONAL (0.001 degree), so a 3 second slip of a Moon event is inside it; a time tolerance would scale with speed (0.001 / 13.2 deg a day = 6.5 s)
    m = _sky_mut(lambda rs: _first(rs, "Moon").__setitem__("event_jd", _first(rs, "Moon")["event_jd"] + 3.0e-5))
    assert m["v"] == "PASS"


def test_ingress_other_mutations_are_caught():
    m = _sky_mut(lambda rs: rs[7].__setitem__("sign", "Aries" if rs[7]["sign"] != "Aries" else "Taurus"))        # (the 3 mutations below keep their first-row indexes)
    assert m["v"] == "PARTIAL" and m["d3"]["n_mismatch"] == 1                      # the row no longer sits on the edge of the sign it names: a named mismatch
    m = _sky_mut(lambda rs: rs[3].__setitem__("longitude_deg", rs[3]["longitude_deg"] + 0.01))
    assert m["v"] == "PARTIAL" and "longitude_deg" in m["d3"]["mismatches"][0]["columns"]
    m = _sky_mut(lambda rs: rs[11].__setitem__("ayanamsha_key", "raman"))
    assert m["v"] == "PARTIAL" and "ayanamsha_key" in m["d3"]["mismatches"][0]["columns"]
    m = _sky_mut(lambda rs: rs[2].__setitem__("primary_body", "Pluto"))
    assert m["v"] == "PARTIAL"


def test_a_dropped_event_breaks_the_declared_count_and_a_duplicate_is_named():
    rows = sky_rows()
    assert d3.d3_measure(sky_spec(), rows[:-1], "bg_sky_calendar")["v"] == "PARTIAL"                       # expected_rows is the full count
    rows.append(copy.deepcopy(rows[0]))
    m = d3.d3_measure(sky_spec(expected_rows=len(rows)), rows, "bg_sky_calendar")
    assert m["v"] == "PARTIAL" and any("duplicate" in x["columns"] for x in m["d3"]["mismatches"])


def test_a_sampled_ingress_run_cannot_pass():
    m = d3.d3_measure(sky_spec(sample=dict(per_stratum=4, seed="s")), sky_rows(), "bg_sky_calendar")
    n = sum(min(4, c) for c in m["d3"]["strata"].values())
    assert m["v"] == "PARTIAL" and m["d3"]["rows_checked"] == n and n < len(SKY["rows"]) and "sample" in m["measured"]


def test_the_two_methods_are_the_closed_registry():
    assert sorted(METHODS) == ["swisseph_ingress_root_find_v1", "swisseph_sidereal_positions_v1"]
    for k, m in METHODS.items():
        assert m["independence"] == "independent_formula" and set(d3.METHOD_HOOKS) <= set(m)
    with pytest.raises(d3.SpecError):
        d3.register_method("swisseph_sidereal_positions_v1", **METHODS["swisseph_sidereal_positions_v1"])
    with pytest.raises(d3.SpecError):
        d3.register_method("incomplete", independence="independent_formula")
