"""test_c1_3_census_d3_wiring.py: C1-3: the census side of the D3 engine: the declaration validator accepts a well-formed D3 declaration and refuses a malformed one, `carriage_declared_checks`
measures a declared D3 asset through the engine (the stated reads monkeypatched with the REAL writer-row fixtures: no database), the other two Carr checks read N/A
`not-the-declared-carriage`, and a D3 verdict is honoured only with its evidence.

The Carr.D3 registry entry is a real detector since N-156 (this branch lifts it from NONE). No declaration of any real asset is filled by this file.
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

pytest.importorskip("swisseph")
import asset_census as ac  # noqa: E402
import test_c1_3_carriage_d3 as t3  # noqa: E402

AID = "ga_positions"
EV = "platform/python-sidecar/ga_writers/ga_positions_writer.py:289"
WHY = "ga_positions stores graha longitudes computed by PyJHora, re-derivable by the Swiss Ephemeris called directly"
NO_DET, PASS, PARTIAL, NA = ac.NO_DET, ac.PASS, ac.PARTIAL, ac.NA


def car(**over):
    spec = t3.pos_spec()
    spec["uncovered"] = [{"column": "retrograde_flag", "reason": "the node flag convention is not yet ruled", "evidence": EV}]
    del spec["columns"]["retrograde_flag"]
    c = dict(applies="D3", nature="computation", why=WHY, evidence=EV, spec=spec)
    c.update(over)
    return c


def car_pass():
    """A declaration that can read PASS on the nodes-fixed rows: retrograde_flag compared, nothing uncovered."""
    return dict(applies="D3", nature="computation", why=WHY, evidence=EV, spec=t3.pos_spec())


def doc(c, aid=AID):
    return dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={aid: {"kind": "data", "carriage": c}})


@pytest.fixture()
def reads(monkeypatch):
    calls = []

    def rows(table, read, chart_id=None):
        calls.append(("rows", table, read, chart_id))
        return t3.fix_nodes(t3.pos_rows())

    def inputs(inp, chart_id):
        calls.append(("inputs", inp, chart_id))
        return t3.pos_inputs()
    monkeypatch.setattr(ac, "d3_fetch_rows", rows)
    monkeypatch.setattr(ac, "d3_fetch_inputs", inputs)
    monkeypatch.setattr(ac, "CENSUS_ROLE_UNREADABLE_TABLES", frozenset())          # these tests emulate a role that CAN read `charts` (the census role cannot: see the NO_DETECTOR tests below)
    return calls


KW = dict(column_types=None, prose_columns=[])


# ───────────────────────── the declaration validator ─────────────────────────

def test_validator_accepts_a_d3_declaration_and_a_derivation():
    ac.validate_declarations(doc(car()))
    ac.validate_declarations(doc(car_pass()))
    ac.validate_declarations(doc(dict(car(), nature="derivation")))


def test_validator_refuses_a_malformed_d3_spec():
    for mutate, msg in ((lambda c: c["spec"].__setitem__("method", "nope"), "closed registry"),
                        (lambda c: c["spec"]["columns"]["longitude_sidereal"].__setitem__("tol", 0.5), "reviewed maximum"),
                        (lambda c: c["spec"]["conventions"].pop("node_model"), "conventions"),
                        (lambda c: c["spec"].pop("read"), "missing field"),
                        (lambda c: c.__setitem__("citation_state", "sourced"), "citation_state"),
                        (lambda c: c["spec"]["uncovered"][0].__setitem__("evidence", "platform/python-sidecar/nope.py:1"), "not an existing"),
                        (lambda c: c["spec"]["conventions"]["node_model"].__setitem__("evidence", "platform/python-sidecar/nope.py:1"), "not an existing")):
        c = car()
        mutate(c)
        with pytest.raises(ac.DeclarationsError, match=msg):
            ac.validate_declarations(doc(c))


def test_a_transcription_cannot_borrow_the_d3_engine():
    with pytest.raises(ac.DeclarationsError, match="requires applies|serves it"):
        ac.validate_declarations(doc(dict(car(), nature="transcription", citation_state="sourced")))


# ───────────────────────── the measurement ─────────────────────────

def test_a_declared_d3_is_measured_and_the_other_two_read_na(reads):
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == PASS, got["Carr.D3"]["measured"]
    for c in ("Carr.D1", "Carr.D2"):
        assert got[c]["v"] == NA and got[c]["cause"] == "not-the-declared-carriage"
    kinds = [c[0] for c in reads]
    assert kinds == ["rows", "inputs"]
    assert reads[0][1] == "chart_facts" and reads[0][3] == ac.CHART_ID and reads[1][2] == ac.CHART_ID
    assert reads[0][2]["where"] == [{"column": "fact_category", "in": ["graha_position", "graha_sign_attributes", "bhava_cusps", "house_chalit", "sandhi_flag"]}]


def test_the_stated_read_is_exactly_the_declared_one_and_unscoped_tables_are_not_chart_scoped(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda table, read, chart_id=None: seen.append((table, read["chart_scoped"], chart_id)) or t3.sky_rows())
    monkeypatch.setattr(ac, "d3_fetch_inputs", lambda *a: pytest.fail("a method with no inputs table must not read charts"))
    c = dict(applies="D3", nature="computation", why="the sky calendar ingress events re-found by a root-finder", evidence=EV, spec=t3.sky_spec())
    got = ac.carriage_declared_checks("bg_sky_calendar", c, "bg_sky_calendar", False, asset_rows=len(t3.SKY["window_a"]["rows"]), **KW)
    assert got["Carr.D3"]["v"] == PASS and seen == [("bg_sky_calendar", False, None)]


def test_the_asset_row_count_caps_the_verdict(reads):
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1300, **KW)          # the asset holds more rows than the declared read covers
    assert got["Carr.D3"]["v"] == PARTIAL and "1205 of the asset's 1300" in got["Carr.D3"]["measured"]


def test_a_spec_for_another_table_is_never_measured_and_reads_nothing(monkeypatch):
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda *a, **k: pytest.fail("the table guard runs before any read"))
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_dashas", True, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and "does not guess" in got["Carr.D3"]["measured"]


def test_a_failed_read_degrades_only_the_d3_check(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "CENSUS_ROLE_UNREADABLE_TABLES", frozenset())          # a role that can read the inputs: the failure under test is the asset-row read
    monkeypatch.setattr(ac, "d3_fetch_rows", boom)
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == ac.ERRORED and "connection refused" in got["Carr.D3"]["measured"]
    assert got["Carr.D1"]["v"] == NA and got["Carr.D2"]["v"] == NA


def test_a_d3_declaration_without_a_spec_says_so():
    got = ac.carriage_declared_checks(AID, dict(applies="D3", nature="computation", why=WHY, evidence=EV), "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and "without a `spec`" in got["Carr.D3"]["measured"] and got["Carr.D3"]["declared_carriage"] == dict(applies="D3", nature="computation")


# ───────────────────────── the rollup ─────────────────────────

def test_the_registry_entry_is_a_real_detector_so_a_measured_verdict_counts(reads):
    assert ac.CRITERION_REGISTRY["Carr.D3"]["detector"] == "asset_census.py:measure()"
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    assert ac.rollup_asset("L1", got)["Carr"]["v"] == PASS


def test_with_the_detector_declared_a_real_d3_pass_makes_the_carr_cell_pass(reads, monkeypatch):
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    cell = ac.rollup_asset("L1", got)["Carr"]
    assert cell["v"] == PASS, cell
    assert [c["v"] for c in cell["checks"] if c["criterion"] == "Carr.D3"] == [PASS]


def test_a_partial_d3_does_not_close_the_cell(reads, monkeypatch):
    got = ac.carriage_declared_checks(AID, car(), "chart_facts", True, asset_rows=1205, **KW)          # retrograde_flag declared uncovered
    assert got["Carr.D3"]["v"] == PARTIAL
    assert ac.rollup_asset("L1", got)["Carr"]["v"] == PARTIAL


def test_a_bare_or_forged_d3_pass_is_not_honoured(monkeypatch):
    m = {"Carr.D3": dict(v=PASS, measured="hypothetical PASS (proof only)"),
         "Carr.D1": dict(v=NA, cause="not-the-declared-carriage", measured="n/a"), "Carr.D2": dict(v=NA, cause="not-the-declared-carriage", measured="n/a")}
    cell = ac.rollup_asset("L1", m)["Carr"]
    d3c = next(c for c in cell["checks"] if c["criterion"] == "Carr.D3")
    assert d3c["v"] == NO_DET and "without re-derivation evidence" in d3c["reason"]


# ───────────────────────── the stated reads (SQL) ─────────────────────────

def test_the_where_sql_is_closed(monkeypatch):
    assert ac._d3_where_sql([{"column": "fact_category", "in": ["a", "b"]}, {"column": "event_type", "equals": "ingress"}]) == "\"fact_category\" IN ('a','b') AND \"event_type\" IN ('ingress')"
    for bad in ([{"column": "x; drop", "equals": "a"}], [{"column": "x", "equals": "a'b"}], [{"column": "x", "in": []}], [{"column": "x", "equals": "a\nb"}]):
        with pytest.raises((ac.Unknown, KeyError, TypeError)):
            ac._d3_where_sql(bad)


def test_the_fetch_sql_is_scoped_ordered_and_capped(monkeypatch):
    sqls = []

    def scalar(sql):
        sqls.append(sql)
        return "3" if sql.startswith("SELECT count") else "[]"
    timeouts = []

    def psql(sql, timeout=None, **k):
        sqls.append(sql)
        timeouts.append(timeout)
        return [["[]"]]
    monkeypatch.setattr(ac, "scalar", scalar)
    monkeypatch.setattr(ac, "psql", psql)
    read = dict(columns=["fact_subject", "fact_value_num"], where=[{"column": "fact_category", "in": ["graha_position"]}], chart_scoped=True)
    assert ac.d3_fetch_rows("chart_facts", read, ac.CHART_ID) == []
    assert timeouts == [ac.D3_READ_TIMEOUT_SECONDS]            # the big read runs under its own stated timeout, in one pass
    assert sqls[0] == f"SELECT count(*) FROM \"chart_facts\" WHERE \"chart_id\" = '{ac.CHART_ID}' AND \"fact_category\" IN ('graha_position')"
    assert "ORDER BY t.\"fact_subject\",t.\"fact_value_num\"" in sqls[1] and "FROM \"chart_facts\" WHERE" in sqls[1] and sqls[1].count("SELECT") == 2
    with pytest.raises(ac.Unknown):
        ac.d3_fetch_rows("chart_facts", read, "not-a-uuid")
    with pytest.raises(ac.Unknown):
        ac.d3_fetch_rows("chart_facts; drop", read, ac.CHART_ID)
    monkeypatch.setattr(ac, "scalar", lambda sql: str(ac.D3_READ_ROW_CAP + 1) if sql.startswith("SELECT count") else "[]")
    with pytest.raises(ac.Unknown, match="cap"):
        ac.d3_fetch_rows("chart_facts", read, ac.CHART_ID)
    sqls.clear()
    monkeypatch.setattr(ac, "scalar", scalar)
    monkeypatch.setattr(ac, "CENSUS_ROLE_UNREADABLE_TABLES", frozenset())          # the inputs SQL shape, for a role that may read the table
    ac.d3_fetch_inputs(dict(table="charts", columns=["birth_date", "birth_time"], id_column="id"), ac.CHART_ID)
    assert sqls == [f"SELECT coalesce(jsonb_agg(to_jsonb(t))::text,'[]') FROM (SELECT \"birth_date\",\"birth_time\" FROM \"charts\" WHERE \"id\"::text = '{ac.CHART_ID}' LIMIT 2) t"]


def test_the_read_timeout_is_stated_in_the_record_and_a_timeout_is_an_error_never_a_partial_verdict(reads, monkeypatch):
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["d3"]["read_timeout_s"] == ac.D3_READ_TIMEOUT_SECONDS and f"{ac.D3_READ_TIMEOUT_SECONDS} second client timeout" in got["Carr.D3"]["measured"]

    def slow(*a, **k):
        raise ac.CheckTimeout("client-side timeout after 900s (psql killed)")
    monkeypatch.setattr(ac, "d3_fetch_rows", slow)
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == ac.ERRORED and "ONE read-only pass" in got["Carr.D3"]["measured"] and "nothing is truncated" in got["Carr.D3"]["measured"]


# ───────────────────── the census role cannot read `charts`: NO_DETECTOR, no statement against it (SS ruling 2026-10-06) ─────────────────────

def _capture_sql(monkeypatch):
    """Every statement the census would send: scalar() and psql() both record and return an empty answer (no database)."""
    sqls = []
    monkeypatch.setattr(ac, "scalar", lambda sql: sqls.append(sql) or "0")
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: sqls.append(sql) or [["[]"]])
    return sqls


def test_the_census_role_default_cannot_read_charts():
    assert "charts" in ac.CENSUS_ROLE_UNREADABLE_TABLES


def test_d3_on_charts_inputs_issues_no_sql_at_all_and_reads_no_detector_with_the_cause(monkeypatch):
    sqls = _capture_sql(monkeypatch)
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    d3 = got["Carr.D3"]
    assert sqls == []                                                               # not the asset rows, not `charts`, not a privilege probe: no D3 statement exists
    assert not any("charts" in q.lower() for q in sqls)
    assert d3["v"] == NO_DET and d3["v"] != ac.ERRORED and d3["v"] != PASS
    assert "needs a table the census role cannot read" in d3["measured"] and "`charts`" in d3["measured"] and "birth_date" in d3["measured"]
    assert d3["d3"]["cause"] == "needs-a-table-the-census-role-cannot-read"
    needs = d3["d3"]["needs"]
    assert needs["table"] == "charts" and needs["id_column"] == "id" and needs["census_role_privilege"] == "SELECT"
    assert {"birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id"} <= set(needs["columns"])
    assert d3["declared_carriage"] == dict(applies="D3", nature="computation")
    for c in ("Carr.D1", "Carr.D2"):
        assert got[c]["v"] == NA and got[c]["cause"] == "not-the-declared-carriage"


def test_d3_on_charts_inputs_never_reads_the_asset_rows_either(monkeypatch):
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda *a, **k: pytest.fail("the 900 s asset-row read must not run when the verdict cannot be reached"))
    monkeypatch.setattr(ac, "d3_fetch_inputs", lambda *a, **k: pytest.fail("charts must not be read"))
    assert ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)["Carr.D3"]["v"] == NO_DET


def test_the_unreadable_d3_cell_rolls_up_as_no_detector_never_pass_or_errored(monkeypatch):
    _capture_sql(monkeypatch)
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    cell = ac.rollup_asset("L1", got)["Carr"]
    assert cell["v"] == NO_DET
    assert [c["v"] for c in cell["checks"] if c["criterion"] == "Carr.D3"] == [NO_DET]


def test_d3_fetch_inputs_refuses_before_any_sql_for_an_unreadable_table(monkeypatch):
    sqls = _capture_sql(monkeypatch)
    with pytest.raises(ac.CensusRoleCannotRead):
        ac.d3_fetch_inputs(dict(table="charts", columns=["birth_date"], id_column="id"), ac.CHART_ID)
    assert sqls == []


def test_a_readable_inputs_table_still_reaches_the_verdict_path(reads):
    """The same declaration under a role that can read the inputs (the `reads` fixture empties the unreadable set): both reads run and the verdict is the engine's PASS."""
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == PASS and [c[0] for c in reads] == ["rows", "inputs"]


def test_a_server_permission_denied_on_any_d3_read_is_no_detector_not_errored(monkeypatch):
    monkeypatch.setattr(ac, "CENSUS_ROLE_UNREADABLE_TABLES", frozenset())

    def denied(*a, **k):
        raise ac.Unknown("ERROR:  permission denied for table chart_facts")
    monkeypatch.setattr(ac, "d3_fetch_rows", denied)
    got = ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, **KW)["Carr.D3"]
    assert got["v"] == NO_DET and "needs a table the census role cannot read" in got["measured"] and got["d3"]["denied_object"] == "table chart_facts"
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda *a, **k: (_ for _ in ()).throw(ac.Unknown("connection refused")))
    assert ac.carriage_declared_checks(AID, car_pass(), "chart_facts", True, **KW)["Carr.D3"]["v"] == ac.ERRORED      # any other failure is still ERRORED, unchanged


def test_the_methods_stated_reads_still_name_charts_as_inputs_only():
    """Guard on the premise: `charts` is the one inputs table of the one method that has one; no other D3 table read names it."""
    d3m = ac._carriage_d3()
    meths = d3m.load_methods()
    assert {mid: m.get("inputs_table", {}) and m["inputs_table"]["table"] for mid, m in meths.items() if m.get("inputs_table")} == {"swisseph_sidereal_positions_v1": "charts"}


def test_the_reference_route_of_the_real_ga_positions_declaration_reads_no_detector_under_the_census_role(monkeypatch):
    """The reference route (re-derive from birth data) stays NO_DETECTOR under the census role. N-169: the REAL declaration now carries the build-recorded form instead (see
    test_n169_build_recorded_d3.py), so this pins the route with the form removed."""
    sqls = _capture_sql(monkeypatch)
    real = json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"]["ga_positions"]["carriage"]
    real["spec"].pop("form")
    real["spec"].pop("recorded")
    got = ac.carriage_declared_checks("ga_positions", real, "chart_facts", True, asset_rows=None, **KW)["Carr.D3"]
    assert sqls == [] and got["v"] == NO_DET and got["d3"]["needs"]["table"] == "charts"


def test_the_real_ga_positions_declaration_reads_the_build_record_and_never_charts(monkeypatch):
    sqls = _capture_sql(monkeypatch)
    real = json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"]["ga_positions"]["carriage"]
    got = ac.carriage_declared_checks("ga_positions", real, "chart_facts", True, asset_rows=None, **KW)["Carr.D3"]
    assert got["v"] == NO_DET and got["d3"]["form"] == "build_recorded_second_calculation"           # an empty fake database: no attempt on record
    assert sqls and not any(re.search(r"\bcharts\b", q) for q in sqls) and any("build_run_assets" in q for q in sqls)
