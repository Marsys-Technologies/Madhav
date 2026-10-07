"""test_formgap_run_stamp.py: FORM-GAP form 1 (SS N-191): the RUN-STAMP TEXT column of `prose_none`.

`ga_transit_anchors.build_id` is TEXT (migration 267) and holds `ctx.build_id`, the orchestrator run id (str of build_runs.id, a UUID: pipeline/orchestrator/asset_runner.py:1120 builds the context with
`build_id=run_id`; ga_transit_anchors.py:214 binds it). It is not prose, but it is text and it is not a member of the unique key, so no older form could exempt it. `run_stamp_columns` exempts it ONLY through a
CHECK against the data: every distinct value must be a uuid AND a run id of THIS asset (build_run_assets / asset_provenance_receipts). Not a uuid => FAIL; a uuid no run of the asset holds => NO_DETECTOR (a
pruned run record cannot be told from a forged stamp); a read that did not happen => NO_DETECTOR, never PASS.

Real DDL (migrations 171, 596, 267) on a disposable PostgreSQL; the engine's own `_measure_prose` reads the asset; every claim has a mutation that must turn the reading red.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)
from _formgap_support import CHART_A, CHART_B, RUN_1, RUN_2, NA, FAIL, NO_DET, CELLS  # noqa: E402

AID = "ga_transit_anchors"
WRITER_EV = "platform/python-sidecar/pipeline/orchestrator/writers/ga_transit_anchors.py:214"
AYAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]


def _rs(**kw):
    return dict(column="build_id", why="the column holds the orchestrator run id the writer binds from ctx.build_id, never narration", evidence=WRITER_EV, **kw)


def _decl(**extra):
    pn = dict(identifier_columns=[dict(column="ayanamsha_id", why="a member of the unique key (chart_id, ayanamsha_id, graha) of the anchor table", evidence=WRITER_EV),
                                  dict(column="graha", why="a member of the unique key (chart_id, ayanamsha_id, graha) of the anchor table", evidence=WRITER_EV)],
              closed_columns=[dict(column="natal_sign", why="the writer validates the sign against its twelve lower-case names before the insert", values=SIGNS)],
              run_stamp_columns=[_rs()])
    pn.update(extra)
    d = {"prose_fields": [], "evidence": {"prose_fields": WRITER_EV}, "prose_none": dict(why=fs.WHY, **pn)}
    return d


# ───────────────────────────── the validator ─────────────────────────────

def test_the_declaration_is_sound_and_the_fields_are_closed():
    assert ac.prose_none_problem(_decl()) is None
    assert ac.RUN_STAMP_FIELDS == ("column", "table", "why", "evidence") and "run_stamp_columns" in ac.PROSE_NONE_DECL_FIELDS


@pytest.mark.parametrize("bad,needle", [
    (dict(run_stamp_columns=[]), "1 to 8"),
    (dict(run_stamp_columns="build_id"), "1 to 8"),
    (dict(run_stamp_columns=[_rs(extra=1)]), "unknown field"),
    (dict(run_stamp_columns=[dict(_rs(), column="build id")]), "identifier"),
    (dict(run_stamp_columns=[dict(_rs(), table="t;drop")]), "table name"),
    (dict(run_stamp_columns=[dict(_rs(), why="tbd")]), "why"),
    (dict(run_stamp_columns=[dict(_rs(), evidence="unverified: the writer sets it somewhere")]), "evidence"),
    (dict(run_stamp_columns=[dict(_rs(), evidence="platform/scripts/governance/golden_test_scan.py:1")]), "does not mention 'build_id'"),     # the cited file must be about the column
    (dict(run_stamp_columns=[_rs(), _rs()]), "listed twice"),
    (dict(run_stamp_columns=[dict(_rs(), column="natal_sign")]), "declared by both"),                                                 # one column, one form
    (dict(run_stamp_columns=[dict(_rs(), column="graha")]), "declared by both"),
])
def test_a_malformed_run_stamp_declaration_is_refused(bad, needle):
    got = ac.prose_none_problem(_decl(**bad))
    assert got is not None and needle in got, got


# ───────────────────────────── the SQL (bounded, the cast behind the shape test) ─────────────────────────────

def test_the_read_is_one_bounded_statement_and_never_casts_a_non_uuid():
    sql = ac.run_stamp_read_sql(AID, "ga_transit_anchors", "build_id", None)
    assert f"LIMIT {ac.RUN_STAMP_MAX_DISTINCT + 1}) d" in sql and "SELECT DISTINCT" in sql and "count(" not in sql.lower().replace("jsonb_agg", "")
    assert "CASE WHEN d.v ~ " in sql and sql.index("CASE WHEN d.v ~ ") < sql.index("d.v::uuid")                       # the cast sits behind the shape test
    assert "b.asset_id = 'ga_transit_anchors'" in sql and "r.asset_id = 'ga_transit_anchors'" in sql and "build_run_assets" in sql and "asset_provenance_receipts" in sql
    assert sql.count("FROM \"ga_transit_anchors\"") == 1                                                                 # ONE scan of the target


def test_a_filter_and_the_measured_chart_scope_slice_the_read():
    ac.set_read_scope({"t": {"where": "chart_id = 'c1'", "label": "x"}})
    try:
        sql = ac.run_stamp_read_sql(AID, "t", "build_id", dict(column="fact_category", equals="k"), CHART_A)
        with pytest.raises(ac.Unknown):
            ac.run_stamp_read_sql(AID, "t", "build_id", None)                                                          # a scoped read with no chart to bind the run to is refused
    finally:
        ac.set_read_scope(None)
    assert "\"fact_category\"::text = 'k'" in sql and "(chart_id = 'c1')" in sql and f"br.chart_id = '{CHART_A}'::uuid" in sql
    assert "br.chart_id" not in ac.run_stamp_read_sql(AID, "t", "build_id", None)                                       # unscoped (a global reference table): any chart's run of the asset


# ───────────────────────────── real SQL on a disposable database ─────────────────────────────

@pytest.fixture()
def db(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.install_run_tables(pg)
    fs.drop_tables(pg, "ga_transit_anchors")
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "267_ga_transit_anchors.sql", "ga_transit_anchors"))
    fs.add_run(pg, RUN_1, AID)
    yield pg
    fs.drop_tables(pg, "ga_transit_anchors", "asset_provenance_receipts", "build_run_assets", "build_runs", "charts", "asset_registry")


def _fill(pg, chart=CHART_A, stamp=RUN_1, ayas=AYAS):
    for a in ayas:
        for i, g in enumerate(GRAHAS):
            fs.psql(pg, f"INSERT INTO ga_transit_anchors (chart_id, build_id, ayanamsha_id, graha, natal_sign, natal_house_from_moon, natal_degree_absolute) "
                        f"VALUES ('{chart}', '{stamp}', '{a}', '{g}', '{SIGNS[i]}', {i + 1}, {i * 30 + 5.5})")


def _measure(pg, monkeypatch, decl=None, scope=None):
    return fs.measure(AID, pg, monkeypatch, ac.registered_ids("")[AID], "ga_transit_anchors", ["ga_transit_anchors"], decl or _decl(), scope=scope)


def test_REAL_SQL_every_stamp_a_run_of_the_asset_reads_na_on_all_six_with_the_verified_block(db, monkeypatch):
    _fill(db)
    got = _measure(db, monkeypatch)
    fs.all_na(got)
    blk = got["Narr.agree"]["prose_none"]["forms"]["run_stamp"]
    assert blk == [dict(table="ga_transit_anchors", column="build_id", verified=True, distinct=1, resolved=1, pattern="uuid")]
    assert "FORM-GAP forms CHECKED: run_stamp" in got["Narr.agree"]["measured"]
    assert "build_id" not in got["Narr.agree"]["prose_none"]["source_columns"]                                           # not mislabelled as a source column


def test_REAL_SQL_a_receipt_alone_resolves_a_stamp_the_run_record_of_which_was_pruned(db, monkeypatch):
    fs.psql(db, "DELETE FROM build_run_assets")                                                                      # the 90-day prune removed the run record
    fs.psql(db, f"INSERT INTO asset_registry VALUES ('{AID}')")
    fs.psql(db, f"INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id) VALUES ('{AID}', NULL, 'p', 'v1', 'proven', '{RUN_1}')")
    _fill(db)
    fs.all_na(_measure(db, monkeypatch))


def test_REAL_SQL_the_cast_is_case_insensitive_so_an_upper_case_run_id_is_still_that_run(db, monkeypatch):
    _fill(db, stamp=RUN_1.upper())
    fs.all_na(_measure(db, monkeypatch))


# ── mutations: a forged declaration or a drifted value turns the reading red ──

def test_MUTATION_a_value_that_is_not_a_uuid_is_a_FAIL_never_na(db, monkeypatch):
    _fill(db)
    fs.psql(db, "UPDATE ga_transit_anchors SET build_id = 'rebuilt by hand on friday' WHERE graha = 'sun' AND ayanamsha_id = 'raman'")
    got = _measure(db, monkeypatch)
    assert got["Narr.agree"]["v"] == FAIL and "not run ids (not a uuid)" in got["Narr.agree"]["measured"] and "rebuilt by hand" in got["Narr.agree"]["measured"]
    assert all(got[c]["v"] == NO_DET for c in CELLS[1:])


def test_MUTATION_a_forged_declaration_naming_a_sentence_column_as_the_run_stamp_FAILS(db, monkeypatch):
    """The declaration cannot make a prose column a stamp: the column the data holds sentences in reads FAIL (here the sign column, declared closed AND, wrongly, a stamp in a copy)."""
    _fill(db)
    forged = _decl(closed_columns=[], run_stamp_columns=[_rs(), dict(_rs(), column="natal_sign")])
    got = _measure(db, monkeypatch, forged)
    assert got["Narr.agree"]["v"] == FAIL and "natal_sign (run stamp)" in got["Narr.agree"]["measured"]
    fs.psql(db, "ALTER TABLE ga_transit_anchors ADD COLUMN note text")
    fs.psql(db, "UPDATE ga_transit_anchors SET note = 'a composed sentence about the Sun in Aries'")
    got = _measure(db, monkeypatch, _decl(run_stamp_columns=[_rs(), dict(_rs(), column="note")]))
    assert got["Narr.agree"]["v"] == FAIL and "note (run stamp)" in got["Narr.agree"]["measured"]


def test_MUTATION_a_uuid_no_run_of_this_asset_holds_is_NO_DETECTOR_never_a_pass(db, monkeypatch):
    _fill(db, stamp="33333333-3333-4333-8333-333333333333")                                                          # well-formed, held by no run
    got = _measure(db, monkeypatch)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "no run id of this asset" in got["Narr.agree"]["measured"]
    assert got["Narr.agree"]["prose_none"]["unread"] and "pruned run record cannot be told from a forged stamp" in got["Narr.agree"]["measured"]
    fs.add_run(db, RUN_2, "ga_chart_facts_other")                                                                    # a run of ANOTHER asset does not vouch for this one
    fs.psql(db, f"UPDATE ga_transit_anchors SET build_id = '{RUN_2}'")
    assert _measure(db, monkeypatch)["Narr.agree"]["v"] == NO_DET


def _scope(chart):
    return {"ga_transit_anchors": dict(where=f"chart_id = '{chart}'", label="the measured chart")}


def test_FORGERY_a_stamp_vouched_by_another_charts_run_of_the_same_asset_is_no_detector_in_the_measured_chart_scope(db, monkeypatch):
    """Review fix HIGH 3: chart A's rows are stamped with a real run of THIS asset, but a run on chart B; the chart-scoped read must not accept it."""
    fs.add_run(db, RUN_2, AID, chart_id=CHART_B)
    _fill(db, chart=CHART_A, stamp=RUN_2)
    got = _measure(db, monkeypatch, scope=_scope(CHART_A))
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "no run id of this asset" in got["Narr.agree"]["measured"], {c: got[c]["v"] for c in CELLS}
    fs.psql(db, f"UPDATE ga_transit_anchors SET build_id = '{RUN_1}'")                                                  # chart A's own run resolves
    fs.all_na(_measure(db, monkeypatch, scope=_scope(CHART_A)))


def test_FORGERY_a_receipt_of_another_chart_does_not_vouch_in_the_measured_chart_scope(db, monkeypatch):
    fs.add_run(db, RUN_2, AID, chart_id=CHART_B, receipt=True)
    fs.psql(db, "DELETE FROM build_run_assets WHERE run_id = '" + RUN_2 + "'")                                          # only the receipt remains
    _fill(db, chart=CHART_A, stamp=RUN_2)
    got = _measure(db, monkeypatch, scope=_scope(CHART_A))
    assert all(got[c]["v"] == NO_DET for c in CELLS)


def test_FORGERY_an_aborted_run_does_not_resolve_a_stamp(db, monkeypatch):
    fs.add_run(db, RUN_2, AID, state="aborted")
    _fill(db, stamp=RUN_2)
    got = _measure(db, monkeypatch)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "no run id of this asset" in got["Narr.agree"]["measured"]
    for st in ("queued", "skipped"):
        fs.psql(db, f"UPDATE build_run_assets SET state = '{st}' WHERE run_id = '{RUN_2}'")
        assert all(_measure(db, monkeypatch)[c]["v"] == NO_DET for c in CELLS), st


def test_MUTATION_one_rebuild_that_restamps_part_of_the_rows_with_a_forged_id_is_caught(db, monkeypatch):
    _fill(db)
    assert _measure(db, monkeypatch)["Narr.agree"]["v"] == NA
    fs.psql(db, "UPDATE ga_transit_anchors SET build_id = '44444444-4444-4444-8444-444444444444' WHERE ayanamsha_id = 'raman'")
    got = _measure(db, monkeypatch)
    assert got["Narr.agree"]["v"] == NO_DET and "1 distinct uuid-shaped value(s)" in got["Narr.agree"]["measured"]


def test_REAL_SQL_more_than_the_bound_of_distinct_stamps_is_not_a_run_stamp_column(db, monkeypatch):
    for k in range(ac.RUN_STAMP_MAX_DISTINCT + 2):
        rid = f"{k:08x}-0000-4000-8000-000000000000"
        fs.add_run(db, rid, AID)
        fs.psql(db, f"INSERT INTO ga_transit_anchors (chart_id, build_id, ayanamsha_id, graha, natal_sign, natal_house_from_moon, natal_degree_absolute) "
                    f"VALUES ('{CHART_A}', '{rid}', 'lahiri_chitrapaksha', 'g{k}', 'aries', 1, 1)")
    got = _measure(db, monkeypatch)
    assert got["Narr.agree"]["v"] == NO_DET and f"more than {ac.RUN_STAMP_MAX_DISTINCT} distinct values" in got["Narr.agree"]["measured"]


# ── the measured chart's rows only (the engine's read scope) ──

def test_REAL_SQL_two_charts_the_stamp_check_judges_the_measured_charts_rows_only(db, monkeypatch):
    _fill(db, chart=CHART_A)
    _fill(db, chart=CHART_B, stamp="not a run id at all", ayas=AYAS[:1])
    scope_a = {"ga_transit_anchors": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")}
    scope_b = {"ga_transit_anchors": dict(where=f"chart_id = '{CHART_B}'", label="the other chart")}
    assert _measure(db, monkeypatch, scope=scope_a)["Narr.agree"]["v"] == NA                                         # chart B's garbage is not judged
    got = _measure(db, monkeypatch, scope=scope_b)
    assert got["Narr.agree"]["v"] == FAIL and "not a uuid" in got["Narr.agree"]["measured"]                          # and is, when it is the measured chart's
    whole = _measure(db, monkeypatch)
    assert whole["Narr.agree"]["v"] == FAIL                                                                          # unscoped (a unit test): every row is judged


def test_REAL_SQL_a_scope_with_no_row_blocks_the_read_it_is_vacuous_not_a_pass(db, monkeypatch):
    _fill(db, chart=CHART_B)
    scope = {"ga_transit_anchors": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart", block="no rows in the read scope: nothing to judge")}
    got = _measure(db, monkeypatch, scope=scope)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "nothing to judge" in got["Narr.agree"]["measured"]


# ───────────────────────────── timeouts and permissions: NO_DETECTOR, never PASS ─────────────────────────────

TIMEOUT = "ERROR:  canceling statement due to statement timeout"


def _grade(read, forms_key="run_stamp"):
    tables = {"t": (["build_id", "id"], {"build_id": "text", "id": "integer"}, None)}
    decl = {"prose_fields": [], "evidence": {"prose_fields": fs.EV}, "prose_none": dict(why=fs.WHY, closed_columns=[], run_stamp_columns=[_rs()])}
    return ac.grade_prose_none("x_asset", decl, tables, "t", {}, forms={"run_stamp": {("t", "build_id"): read}})


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)"), ac.Unknown("ERROR:  permission denied for table build_run_assets")])
def test_a_read_that_timed_out_or_was_refused_is_no_detector_with_the_cause(monkeypatch, err):
    def boom(q):
        raise err
    monkeypatch.setattr(ac, "scalar", boom)
    out = ac._formgap_guard(lambda: dict(stamps=ac._formgap_list(ac._formgap_json(ac.run_stamp_read_sql(AID, "t", "build_id"), "t.build_id"), "t.build_id")))
    assert "unread" in out
    got = _grade(out)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and got["Narr.agree"]["prose_none"]["unread"]


def test_any_other_failure_still_raises_so_the_cells_read_errored(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda q: (_ for _ in ()).throw(ac.Unknown('ERROR:  relation "build_run_assets" does not exist')))
    with pytest.raises(ac.Unknown, match="does not exist"):
        ac._formgap_guard(lambda: dict(stamps=ac._formgap_list(ac._formgap_json(ac.run_stamp_read_sql(AID, "t", "build_id"), "t.build_id"), "t.build_id")))
    monkeypatch.setattr(ac, "scalar", lambda q: "not json")
    with pytest.raises(ac.Unknown, match="unparseable"):
        ac._formgap_guard(lambda: dict(stamps=ac._formgap_list(ac._formgap_json(ac.run_stamp_read_sql(AID, "t", "build_id"), "t.build_id"), "t.build_id")))


def test_no_read_at_all_is_no_detector_never_na():
    assert all(_grade(None)[c]["v"] == NO_DET for c in CELLS)
    assert all(_grade(dict(stamps="not a list"))[c]["v"] == NO_DET for c in CELLS)


def test_the_grader_states_of_one_read():
    g = ac.grade_run_stamp
    ok = dict(stamps=[dict(v="a", shape=True, resolved=True)])
    assert g(ok)["state"] == "ok" and g(dict(stamps=[]))["state"] == "unread"                                          # review fix LOW: an empty / all-NULL column verifies nothing
    assert g(dict(stamps=[dict(v="x", shape=False, resolved=False)]))["state"] == "wrong"
    assert g(dict(stamps=[dict(v="a", shape=True, resolved=False)]))["state"] == "unread"
    assert g(dict(stamps=[dict(v="a", shape=True, resolved=True)] * (ac.RUN_STAMP_MAX_DISTINCT + 1)))["state"] == "unread"
    assert g(dict(unread="x"))["state"] == "unread" and g(None)["state"] == "unread"


# ───────────────────────────── the rollup does not trust a record's own claim ─────────────────────────────

def test_the_rollup_guard_refuses_a_block_that_lists_a_stamp_it_did_not_verify(db, monkeypatch):
    _fill(db)
    rec = _measure(db, monkeypatch)["Narr.agree"]
    assert ac.prose_none_na_problem("Narr.agree", rec) is None
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["run_stamp"][0]["verified"] = False
    assert "not all verified" in ac.prose_none_na_problem("Narr.agree", forged)
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["run_stamp"][0]["resolved"] = 0                                                   # a stamp that resolved to no run is not a release
    assert "do not show every distinct value resolved" in ac.prose_none_na_problem("Narr.agree", forged) or "not all verified" in ac.prose_none_na_problem("Narr.agree", forged)
    c = ac._check_contribution("Narr.agree", "L1", forged, {"columns": ["build_id"], "asset_kind": "data"})
    assert c["v"] != NA                                                                                              # the cell the rollup computes from the forged record is not N/A


def test_no_declared_form_means_the_block_is_what_it_was(db, monkeypatch):
    """A prose_none with no FORM-GAP form: the block carries no `forms` key (byte for byte the old shape)."""
    _fill(db)
    d = _decl()
    del d["prose_none"]["run_stamp_columns"]
    d["prose_none"]["closed_columns"].append(dict(column="build_id", why="the stamp as a closed list of the one run id", values=[RUN_1]))
    got = _measure(db, monkeypatch, d)
    fs.all_na(got)
    assert "forms" not in got["Narr.agree"]["prose_none"] and "FORM-GAP" not in got["Narr.agree"]["measured"]


def test_FORGERY_a_run_stamp_column_that_holds_no_value_is_no_detector_never_na(db, monkeypatch):
    """Review fix LOW: a column with no value in the measured scope has no stamp to verify; declaring it a run stamp must not read N/A (the table is empty here)."""
    got = _measure(db, monkeypatch)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "holds no value in the measured scope" in got["Narr.agree"]["measured"]
    _fill(db)
    ok = _measure(db, monkeypatch)["Narr.agree"]
    assert ok["v"] == NA
    forged = fs.clone(ok)
    forged["prose_none"]["forms"]["run_stamp"][0].update(distinct=0, resolved=0)
    assert ac.prose_none_na_problem("Narr.agree", forged) is not None
