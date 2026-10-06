"""test_n169_build_recorded_d3.py: N-169, the engine side: Carr.D3 for ga_positions READS THE BUILD RECORD of the in-build second calculation instead of re-deriving
from birth data (the census role has no access to the birth parameters: standing privacy rule).

What this pins (earned-signal rule: no PASS without a detector, and every mutation turns the cell off PASS):
  * the declaration (REAL asset_declarations.json) validates, and the validator refuses a malformed `form` / `recorded`;
  * PASS only when the latest completed build attempt's record shows matched = the derivable total, not_matched = 0, not_derived within the declared allowance, an allowed backend, and
    counts equal to the chart's rows (total and per ayanamsha); the record passes carriage_d3.d3_evidence_problem and the rollup honours it;
  * NO_DETECTOR (with a named cause) for: no attempt, a failed attempt read, no completed attempt, notes that are not persisted (the production reality today: the orchestrator drops
    WriterResult.notes on a completed attempt), an unparseable record, a disallowed backend, unreadable rows;
  * FAIL for: an attempt refused by the second calculation (the recorded error text), a completed record naming not_matched, a count disagreement (total or per ayanamsha);
  * PARTIAL for: not_derived above the allowance, a logical row count that differs from the declaration;
  * the census issues NO statement against `charts` and never calls the birth-parameter read; the attempt SQL is the one stated read.
Fixtures are synthetic row sets of the real shape (1,205 rows: 5 ayanamshas x 241) and fixture build records; no database, no birth data.
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

d3 = ac._carriage_d3()
AID = "ga_positions"
KW = dict(column_types=None, prose_columns=[])
NO_DET, PASS, PARTIAL, FAIL, NA = ac.NO_DET, ac.PASS, ac.PARTIAL, ac.FAIL, ac.NA

AYS = ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical")
GRAHAS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
GRAHA_KEYS = (("graha_position", ("longitude_sidereal", "sign", "sign_lord", "nakshatra", "nakshatra_lord", "pada", "house_d1", "retrograde_flag", "combustion_state")),
              ("graha_sign_attributes", ("sign_num", "degree_in_sign")),
              ("house_chalit", ("chalit_house_sripati", "whole_sign_house", "dist_to_madhya_deg", "dist_to_nearest_boundary_deg", "nearest_boundary")),
              ("sandhi_flag", ("sandhi_flag", "sandhi_reasons")))
LAGNA_KEYS = (("graha_position", ("longitude_sidereal", "sign", "sign_lord", "pada", "house_d1")), ("graha_sign_attributes", ("sign_num", "degree_in_sign")))
CUSPS = tuple(f"{sy}_{e}" for sy in ("sripati", "placidus") for e in ("start", "madhya", "end"))

RECORD = ("chart_facts=1205; positions_second_calc matched=1205 not_matched=0 not_derived=0 boundary_tolerated=0 rows=1205 ayanamshas="
          + ",".join(f"{a}:241" for a in AYS) + "; ephemeris_backend=swieph")


def _rows():
    rows = []
    for ay in AYS:
        def add(cat, subj, key):
            rows.append(dict(ayanamsha_id=ay, fact_category=cat, fact_subject=subj, fact_key=key, fact_value_num=1.0, fact_value_text=None))
        for g in GRAHAS:
            for cat, keys in GRAHA_KEYS:
                for k in keys:
                    add(cat, g, k)
        for cat, keys in LAGNA_KEYS:
            for k in keys:
                add(cat, "LAGNA", k)
        for h in range(1, 13):
            for k in CUSPS:
                add("bhava_cusps", f"BHAVA_{h:02d}", k)
    return rows


def _spec():
    return copy.deepcopy(json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"][AID]["carriage"]["spec"])


def _car():
    return json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"][AID]["carriage"]


def attempt(state="complete", disposition="build", notes=RECORD, error="", run="aaaaaaaa-1111-4111-8111-111111111111", when="2026-10-07"):
    return dict(run_id=run, state=state, disposition=disposition, when=when, error=error, notes=notes)


REFUSAL = ("PositionsSecondCalcMismatch: positions second calculation: matched=1195 not_matched=10 not_derived=0 first mismatches: lahiri_chitrapaksha:(RAH_MEAN, retrograde_flag, "
           "writer='direct', verifier='retrograde')")


def measure(attempts, rows=None, spec=None, **kw):
    kw.setdefault("asset_rows", 1205)
    return d3.d3_recorded_measure(spec or _spec(), attempts, rows if rows is not None else _rows(), "chart_facts", **kw)


def test_the_fixture_has_the_real_shape():
    rows = _rows()
    assert len(rows) == 1205 and len({(r["fact_subject"], r["ayanamsha_id"]) for r in rows}) == 110


# ───────────────────────── the declaration ─────────────────────────

def test_the_real_declaration_validates_and_names_the_form():
    spec = _spec()
    assert spec["form"] == d3.FORM_BUILD_RECORDED and spec["recorded"]["marker"] == "positions_second_calc" and spec["recorded"]["not_derived_allowance"] == 0
    d3.validate_spec(spec, "x", asset_id=AID)
    doc = json.loads((HERE.parent / "asset_declarations.json").read_text())
    ac.validate_declarations(doc)


@pytest.mark.parametrize("mutate,msg", [
    (lambda s: s.pop("recorded"), "declared together"),
    (lambda s: s.pop("form"), "declared together"),
    (lambda s: s.__setitem__("form", "nope"), "not a reviewed form"),
    (lambda s: s["recorded"].__setitem__("marker", "other_marker"), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("not_derived_allowance", -1), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("not_derived_allowance", True), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("basis", "short"), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("extra", 1), "recorded must be"),
])
def test_the_validator_refuses_a_malformed_form(mutate, msg):
    s = _spec()
    mutate(s)
    with pytest.raises(d3.SpecError, match=msg):
        d3.validate_spec(s, "x", asset_id=AID)


def test_a_form_is_not_reviewed_for_a_method_it_does_not_name():
    s = _spec()
    s["method"] = "swisseph_sky_events_v1"
    with pytest.raises(d3.SpecError):
        d3.validate_spec(s, "x")


# ───────────────────────── PASS, and only on the record ─────────────────────────

def test_pass_on_a_clean_record():
    m = measure([attempt()])
    assert m["v"] == PASS, m["measured"]
    ev = m["d3"]
    assert (ev["rows_total"], ev["rows_checked"], ev["rows_agree"], ev["n_mismatch"], ev["logical_rows"]) == (1205, 1205, 1205, 0, 110)
    assert ev["recorded"]["matched"] == 1205 and ev["backend"]["name"] == "swieph" and ev["form"] == d3.FORM_BUILD_RECORDED and ev["independence"] == "independent_formula"
    assert d3.d3_evidence_problem(m) == ""
    assert "re-derived nothing" in ev["claims"] and "birth parameters" in ev["claims"]


def test_the_latest_completed_build_attempt_is_the_one_read():
    old = attempt(notes=RECORD.replace("matched=1205 not_matched=0", "matched=1204 not_matched=1"), run="bbbbbbbb-1111-4111-8111-111111111111")
    skip = attempt(disposition="skip_no_delta", notes=None, run="cccccccc-1111-4111-8111-111111111111")
    m = measure([skip, attempt(), old])
    assert m["v"] == PASS and m["d3"]["recorded"]["run_id"].startswith("aaaaaaaa")


def test_pass_flows_through_the_census_and_the_rollup_honours_it(monkeypatch):
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda table, read, chart_id=None: _rows())
    monkeypatch.setattr(ac, "d3_recorded_attempts", lambda aid, chart_id, limit=25: [attempt()])
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == PASS, got["Carr.D3"]["measured"]
    assert got["Carr.D1"]["v"] == NA and got["Carr.D2"]["v"] == NA
    assert ac.rollup_asset("L1", got)["Carr"]["v"] == PASS


def test_the_census_never_reads_charts_or_calls_the_birth_read(monkeypatch):
    sqls = []
    monkeypatch.setattr(ac, "scalar", lambda sql: sqls.append(sql) or ("1205" if sql.startswith("SELECT count") else json.dumps(_rows())))
    monkeypatch.setattr(ac, "psql", lambda sql, timeout=None, **k: sqls.append(sql) or (
        [[json.dumps(_rows())]] if "jsonb_agg" in sql else [[a["run_id"], a["state"], a["disposition"], a["when"], a["error"]] for a in [attempt()]]))
    monkeypatch.setattr(ac, "d3_fetch_inputs", lambda *a, **k: pytest.fail("the build-recorded form must not read the birth parameters"))
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["d3"]["cause"] == d3.NOT_PERSISTED_CAUSE         # the real fetch returns notes=None
    assert not any(re.search(r"\bcharts\b", q) for q in sqls), sqls
    assert any("build_run_assets" in q for q in sqls)


# ───────────────────────── NO_DETECTOR, each with its cause ─────────────────────────

@pytest.mark.parametrize("attempts,cause", [
    (None, "attempt-read-failed"),
    ([], "no-build-record"),
    ([attempt(state="error", disposition="", notes=None, error="RuntimeError: boom")], "no-completed-build-attempt"),
    ([attempt(disposition="skip_no_delta")], "no-completed-build-attempt"),
    ([attempt(notes=None)], d3.NOT_PERSISTED_CAUSE),
    ([attempt(notes="chart_facts=1205")], "record-missing-or-unparseable"),
    ([attempt(notes=RECORD.replace("rows=1205", "rows=twelve"))], "record-missing-or-unparseable"),
    ([attempt(notes=RECORD.replace("lahiri_chitrapaksha:241,", "lahiri_chitrapaksha:241,lahiri_chitrapaksha:241,"))], "record-missing-or-unparseable"),
    ([attempt(notes=RECORD.replace("ephemeris_backend=swieph", "ephemeris_backend=moseph"))], "backend-not-allowed"),
    ([attempt(notes=RECORD.replace("; ephemeris_backend=swieph", ""))], "backend-not-allowed"),
    ([attempt(notes=RECORD.replace("matched=1205", "matched=1000"))], "record-inconsistent"),
])
def test_no_detector_names_its_cause(attempts, cause):
    m = measure(attempts)
    assert m["v"] == NO_DET and m["d3"]["cause"] == cause, m["measured"]


def test_unreadable_rows_are_no_detector():
    m = d3.d3_recorded_measure(_spec(), [attempt()], None, "chart_facts", asset_rows=1205)
    assert m["v"] == NO_DET and m["d3"]["cause"] == "rows-unreadable"


def test_without_the_record_there_is_no_pass_whatever_else_holds():
    """The production reality today: notes are not persisted. A completed attempt, a full table and every count in order still read NO_DETECTOR."""
    m = measure([attempt(notes=None)])
    assert m["v"] == NO_DET and "does not persist WriterResult.notes" in m["measured"]


# ───────────────────────── FAIL ─────────────────────────

def test_the_latest_attempt_refused_by_the_second_calculation_is_a_fail():
    m = measure([attempt(state="error", disposition="", notes=None, error=REFUSAL), attempt()])
    assert m["v"] == FAIL and m["d3"]["cause"] == "recorded-mismatch"
    assert m["d3"]["recorded"]["not_matched"] == 10 and "REFUSED" in m["measured"]


def test_an_unrelated_error_on_the_latest_attempt_is_not_a_mismatch():
    m = measure([attempt(state="error", disposition="", notes=None, error="OperationalError: connection lost"), attempt()])
    assert m["v"] == PASS


def test_a_completed_record_naming_a_mismatch_is_a_fail():
    m = measure([attempt(notes=RECORD.replace("matched=1205 not_matched=0", "matched=1204 not_matched=1"))])
    assert m["v"] == FAIL and m["d3"]["cause"] == "recorded-mismatch" and "inconsistent" in m["measured"]


def test_a_dropped_row_after_the_record_is_a_count_disagreement():
    rows = _rows()
    del rows[17]
    m = measure([attempt()], rows)
    assert m["v"] == FAIL and m["d3"]["cause"] == "counts-disagree"


def test_the_same_total_with_a_different_per_ayanamsha_split_is_a_count_disagreement():
    rows = _rows()
    moved = next(i for i, r in enumerate(rows) if r["ayanamsha_id"] == AYS[0])
    rows[moved] = dict(rows[moved], ayanamsha_id=AYS[1])
    m = measure([attempt()], rows)
    assert len(rows) == 1205 and m["v"] == FAIL and m["d3"]["cause"] == "counts-disagree"


def test_a_row_added_after_the_record_is_a_count_disagreement():
    m = measure([attempt()], _rows() + [dict(_rows()[0], fact_key="extra")], asset_rows=1206)
    assert m["v"] == FAIL and m["d3"]["cause"] == "counts-disagree"


# ───────────────────────── PARTIAL ─────────────────────────

def test_not_derived_above_the_allowance_is_partial_not_pass():
    rec = RECORD.replace("matched=1205 not_matched=0 not_derived=0", "matched=1204 not_matched=0 not_derived=1")
    m = measure([attempt(notes=rec)])
    assert m["v"] == PARTIAL and m["d3"]["cause"] == "not-derived-above-allowance" and "unchecked claims" in m["measured"]
    s = _spec()
    s["recorded"]["not_derived_allowance"] = 1                      # a declared allowance, not a fudge: PASS only inside it, and rows_total is the derivable total
    m = measure([attempt(notes=rec)], spec=s)
    assert m["v"] == PASS and m["d3"]["rows_total"] == 1204 and d3.d3_evidence_problem(m) == ""


def test_a_logical_row_count_that_differs_from_the_declaration_is_partial():
    s = _spec()
    s["expected_rows"] = 111
    m = measure([attempt()], spec=s)
    assert m["v"] == PARTIAL and m["d3"]["cause"] == "logical-count"


def test_an_asset_that_holds_more_rows_than_the_read_covers_is_partial():
    m = measure([attempt()], asset_rows=1300)
    assert m["v"] == PARTIAL and m["d3"]["cause"] == "coverage"


# ───────────────────────── mutations: every one leaves PASS ─────────────────────────

def _mutations():
    yield "matched-1", measure([attempt(notes=RECORD.replace("matched=1205 not_matched=0", "matched=1204 not_matched=1"))])
    yield "not_derived+1", measure([attempt(notes=RECORD.replace("matched=1205 not_matched=0 not_derived=0", "matched=1204 not_matched=0 not_derived=1"))])
    yield "rows-record+1", measure([attempt(notes=RECORD.replace("rows=1205", "rows=1206").replace("matched=1205", "matched=1206"))])
    yield "ayanamsha-renamed", measure([attempt(notes=RECORD.replace("raman:241", "ramen:241"))])
    yield "ayanamsha-dropped", measure([attempt(notes=RECORD.replace(",raman:241", ""))])
    yield "backend", measure([attempt(notes=RECORD.replace("swieph", "moseph"))])
    yield "no-record", measure([attempt(notes=None)])
    yield "marker-renamed", measure([attempt(notes=RECORD.replace("positions_second_calc", "positions_first_calc"))])
    yield "refused", measure([attempt(state="error", disposition="", notes=None, error=REFUSAL)])
    yield "no-attempt", measure([])
    rows = _rows()
    rows.pop()
    yield "row-dropped", measure([attempt()], rows)


def test_every_mutation_of_a_passing_record_leaves_pass():
    assert measure([attempt()])["v"] == PASS
    for name, m in _mutations():
        assert m["v"] != PASS, (name, m["measured"])


def test_a_forged_recorded_pass_without_its_evidence_is_not_honoured():
    m = {"Carr.D3": dict(v=PASS, measured="hypothetical PASS (proof only)", d3=dict(form=d3.FORM_BUILD_RECORDED)),
         "Carr.D1": dict(v=NA, cause="not-the-declared-carriage", measured="n/a"), "Carr.D2": dict(v=NA, cause="not-the-declared-carriage", measured="n/a")}
    cell = ac.rollup_asset("L1", m)["Carr"]
    assert next(c for c in cell["checks"] if c["criterion"] == "Carr.D3")["v"] == NO_DET


# ───────────────────────── parsing and the attempt read ─────────────────────────

def test_parse_second_calc_line_reads_the_fixed_format_and_nothing_else():
    rec = d3.parse_second_calc_line(RECORD, "positions_second_calc")
    assert rec == dict(matched=1205, not_matched=0, not_derived=0, boundary_tolerated=0, rows=1205, ayanamshas={a: 241 for a in AYS}, backend="swieph")
    assert d3.parse_second_calc_line("positions_second_calc matched=1", "positions_second_calc") is None
    assert d3.parse_second_calc_line(None, "positions_second_calc") is None
    assert d3.parse_second_calc_line(RECORD, "") is None
    assert d3.parse_second_calc_mismatch(REFUSAL) == dict(matched=1195, not_matched=10, not_derived=0)
    assert d3.parse_second_calc_mismatch("RuntimeError: other") is None


def test_the_attempt_read_is_one_stated_select_and_notes_are_not_available(monkeypatch):
    sqls = []
    monkeypatch.setattr(ac, "psql", lambda sql, **k: sqls.append(sql) or [["r1", "complete", "build", "2026-10-07", ""], ["r0", "error", "", "2026-10-06", "X: y"]])
    got = ac.d3_recorded_attempts(AID, ac.CHART_ID)
    assert [a["run_id"] for a in got] == ["r1", "r0"] and all(a["notes"] is None for a in got) and got[1]["error"] == "X: y"
    assert len(sqls) == 1 and sqls[0].startswith("SELECT") and "ORDER BY r.created_at DESC, a.run_id DESC" in sqls[0] and f"r.chart_id::text = '{ac.CHART_ID}'" in sqls[0]
    assert not re.search(r"\bcharts\b", sqls[0])
    for bad in (("ga_positions; drop", ac.CHART_ID), (AID, "not-a-uuid")):
        with pytest.raises(ac.Unknown):
            ac.d3_recorded_attempts(*bad)
    monkeypatch.setattr(ac, "psql", lambda sql, **k: [["only", "three", "fields"]])
    with pytest.raises(ac.Unknown, match="5 selected fields"):
        ac.d3_recorded_attempts(AID, ac.CHART_ID)


def test_a_failed_attempt_read_degrades_to_no_detector_not_errored(monkeypatch):
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda table, read, chart_id=None: _rows())

    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "d3_recorded_attempts", boom)
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["d3"]["cause"] == "attempt-read-failed"


def test_a_failed_row_read_is_errored_for_this_check_only(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "d3_fetch_rows", boom)
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == ac.ERRORED and got["Carr.D1"]["v"] == NA


def test_a_spec_without_the_form_is_still_the_reference_route_and_reads_no_detector_under_the_census_role(monkeypatch):
    c = _car()
    for k in ("form", "recorded"):
        c["spec"].pop(k)
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda *a, **k: pytest.fail("the unreadable inputs table is decided before any read"))
    got = ac.carriage_declared_checks(AID, c, "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["d3"]["cause"] == ac.D3_NEEDS_READABLE_CAUSE
