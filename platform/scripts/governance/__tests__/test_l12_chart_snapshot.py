"""test_l12_chart_snapshot.py -- l12_chart_snapshot.py: read-only per-chart counts + content/ids digests for the 20 ga_* and 23 bo_* assets.

Proof map
  offline     every committed component (l12_snapshot_scopes.json) builds SELECT-only SQL the guard accepts; every asset of the census is covered;
              the committed scopes equal what the generator produces
  real SQL    a disposable Postgres with realistic mini DDL (chart_facts shared by two assets, chart_dashas with dasha_row_id, bodha_msr_signals with
              signal_id): digest stability (two runs equal), a one-cell mutation moves exactly the right group / digest, the volatile-column
              exclusion, ids-only changes move only the ids digest, chunking does not change the digest, the psql driver equals the psycopg driver,
              the read-only guard refuses non-SELECT and the session is read only
  compare     IDENTICAL / CHANGED, EXPECTED / UNEXPECTED, predicted-not-seen, row-level count check
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

import l12_chart_snapshot as snap  # noqa: E402
import l12_snapshot_scope_gen as gen  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

CHART = snap.CANONICAL_CHART
OTHER = "362f9f17-0000-4000-8000-000000000000"
SCOPES = snap.load_scopes()


# ───────────────────────────── offline ─────────────────────────────

def test_committed_scopes_equal_the_generator_output():
    assert gen.OUT.read_text(encoding="utf-8") == json.dumps(gen.build(), indent=1, sort_keys=True) + "\n"


def test_scopes_cover_exactly_the_20_ga_and_23_bo_assets():
    ga = [a for a in SCOPES["assets"] if a.startswith("ga_")]
    bo = [a for a in SCOPES["assets"] if a.startswith("bo_")]
    assert len(ga) == 20 and len(bo) == 23 and "ga_fact_identity" in ga
    census = pathlib.Path("/Users/Dev/suvarna-evidence/census_interim/42e96d491")
    if census.exists():
        for f, mine in (("census_L1.json", ga), ("census_L2.json", bo)):
            ids = sorted(a["asset_id"] for a in json.loads((census / f).read_text())[f[7:9]]["assets"])
            assert ids == sorted(mine)


class FakeInfo(snap.RelationInfo):
    def __init__(self, comp):
        names = list(dict.fromkeys((comp.get("content_columns") or ["a_col"]) + (comp.get("id_columns") or []) + (comp.get("id_ref_columns") or [])
                                   + (comp.get("key") or []) + (comp.get("dims") or []) + ["chart_id", "ayanamsha_id", "computed_at"]))
        super().__init__([(n, "text", "text") for n in names])


def test_every_component_builds_select_only_sql_the_guard_accepts():
    n = 0
    for a, spec in list(SCOPES["assets"].items()) + [("residual", SCOPES["residual"])]:
        for comp in spec["components"]:
            plan = snap.Plan(comp, FakeInfo(comp), SCOPES["volatile"], False)
            for sql in (snap.group_query(CHART, comp, plan, "lahiri"), snap.rowdetail_query(CHART, comp, plan, "lahiri") if plan.row_key else "SELECT 1",
                        snap.aya_values_query(CHART, comp, plan)):
                snap.slw.assert_select_only(sql)
                n += 1
    assert n >= 100


def test_guard_refuses_non_select_before_anything_is_sent():
    class Boom(snap.Runner):
        def _run(self, sql):
            raise AssertionError("must not reach the database")
    for bad in ("DELETE FROM chart_facts", "SELECT 1; DROP TABLE x", "WITH x AS (DELETE FROM t RETURNING 1) SELECT * FROM x", "UPDATE t SET a = 1",
                "SELECT * INTO t2 FROM t", "COPY t TO '/tmp/x'", "SELECT pg_sleep(1)"):
        with pytest.raises(ValueError):
            Boom().run(bad)


def test_literals_and_identifiers_are_quoted():
    assert snap.lit("a'b") == "'a''b'"
    with pytest.raises(snap.SnapshotError):
        snap.q('x"; drop table y; --')
    assert "AT TIME ZONE 'UTC'" in snap.column_expr("t", "timestamp with time zone", "timestamptz", False)
    assert snap.column_expr("v", "USER-DEFINED", "vector", False) is None and "md5" in snap.column_expr("v", "USER-DEFINED", "vector", True)


# ───────────────────────────── real SQL ─────────────────────────────

DDL = """
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, fact_category text NOT NULL, fact_subject text,
  fact_key text NOT NULL, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, citation_human text, build_id uuid,
  computed_at timestamptz DEFAULT now(), updated_at timestamptz);
CREATE TABLE chart_dashas (dasha_row_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, system_id text NOT NULL, level_n int NOT NULL,
  start_iso text NOT NULL, lord_graha text, duration_days numeric, build_id uuid, created_at timestamptz DEFAULT now());
CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, signal_type_class text NOT NULL, signal_type_id text,
  computed_salience numeric, constituent_signals_array uuid[], configuration_jsonb jsonb, computed_at timestamptz DEFAULT now(), build_id uuid);
CREATE TABLE ga_medical (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, graha text NOT NULL, strength numeric, computed_at timestamptz);
"""

MINI = {
    "schema": "suvarna.l12_snapshot_scopes/1",
    "volatile": SCOPES["volatile"],
    "prose": SCOPES["prose"],
    "assets": {
        "ga_positions": {"layer": "L1", "components": [
            {"name": "chart_facts", "relation": "chart_facts", "where_sql": "fact_category IN ('graha_position', 'sandhi_flag')", "key": ["ayanamsha_id", "fact_category", "fact_subject", "fact_key"],
             "row_key": ["ayanamsha_id", "fact_category", "fact_subject", "fact_key"], "dims": ["ayanamsha_id", "fact_category", "fact_key"], "id_columns": [], "id_ref_columns": [],
             "content_columns": ["fact_id", "chart_id", "ayanamsha_id", "fact_category", "fact_subject", "fact_key", "fact_value_text", "fact_value_num", "fact_value_jsonb", "citation_human"]}]},
        "ga_ayurdaya": {"layer": "L1", "components": [
            {"name": "chart_facts", "relation": "chart_facts", "where_sql": "fact_category = 'ayurdaya'", "key": ["fact_id"], "row_key": [], "dims": ["ayanamsha_id", "fact_category", "fact_key"],
             "id_columns": [], "id_ref_columns": [], "content_columns": None}]},
        "ga_dashas": {"layer": "L1", "components": [
            {"name": "chart_dashas", "relation": "chart_dashas", "where_sql": None, "key": ["chart_id", "ayanamsha_id", "system_id", "level_n", "start_iso"],
             "row_key": ["ayanamsha_id", "system_id", "level_n", "start_iso"], "dims": ["ayanamsha_id", "system_id", "level_n"], "id_columns": ["dasha_row_id"], "id_ref_columns": [],
             "content_columns": None}]},
        "ga_medical": {"layer": "L1", "components": [
            {"name": "ga_medical", "relation": "ga_medical", "where_sql": None, "key": [], "row_key": [], "dims": [], "id_columns": ["id"], "id_ref_columns": [], "content_columns": None}]},
        "bo_laksana": {"layer": "L2", "components": [
            {"name": "bodha_msr_signals", "relation": "bodha_msr_signals", "where_sql": None, "key": ["signal_id"], "row_key": [], "dims": ["ayanamsha_id", "signal_type_class"],
             "id_columns": ["signal_id"], "id_ref_columns": ["constituent_signals_array"], "content_columns": None}]},
        "bo_arudha": {"layer": "L2", "components": [
            {"name": "bodha_msr_signals", "relation": "bodha_msr_signals", "where_sql": "signal_type_class = 'arudha'", "key": ["signal_id"], "row_key": [], "dims": ["ayanamsha_id", "signal_type_class"],
             "id_columns": ["signal_id"], "id_ref_columns": ["constituent_signals_array"], "content_columns": None}]},
    },
    "residual": {"layer": "L1", "components": [
        {"name": "chart_facts_unclaimed", "relation": "chart_facts",
         "where_sql": "NOT coalesce((fact_category IN ('graha_position', 'sandhi_flag')) OR (fact_category = 'ayurdaya'), false)",
         "key": ["ayanamsha_id", "fact_category", "fact_subject", "fact_key"], "row_key": ["ayanamsha_id", "fact_category", "fact_subject", "fact_key"],
         "dims": ["ayanamsha_id", "fact_category", "fact_key"], "id_columns": [], "id_ref_columns": [], "content_columns": ["fact_id", "fact_category", "fact_subject", "fact_key", "fact_value_text"]}]},
}


def _uuid(i):
    return "00000000-0000-4000-8000-%012d" % i


@pytest.fixture()
def db(disposable_pg, monkeypatch):
    cl = disposable_pg
    point_psql_at(cl, monkeypatch)
    cl.psql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    for stmt in [s for s in DDL.split(";\n") if s.strip()]:
        cl.psql(stmt)
    rows = []
    n = 0
    for aya in ("lahiri", "raman"):
        for cat, key, subj in (("graha_position", "longitude", "Sun"), ("graha_position", "longitude", "Moon"), ("graha_position", "retrograde_flag", "Rahu"),
                               ("graha_position", "retrograde_flag", "Ketu"), ("sandhi_flag", "sandhi_flag", "Sun"), ("ayurdaya", "pindayu", "Sun"),
                               ("yoga_misc", "k1", "Sun"), ("yoga_misc", "k2", "Moon")):
            n += 1
            rows.append("('F%d','%s','%s','%s','%s','%s','v%d',%d.5,'{\"k\": %d}','cite %d')" % (n, CHART, aya, cat, subj, key, n, n, n, n))
    cl.psql("INSERT INTO chart_facts (fact_id,chart_id,ayanamsha_id,fact_category,fact_subject,fact_key,fact_value_text,fact_value_num,fact_value_jsonb,citation_human) VALUES "
            + ",".join(rows))
    cl.psql("INSERT INTO chart_facts (fact_id,chart_id,ayanamsha_id,fact_category,fact_subject,fact_key) VALUES ('X1','%s','lahiri','graha_position','Sun','longitude')" % OTHER)
    d = []
    for aya in ("lahiri", "raman"):
        for lvl in (1, 2):
            for i in range(3):
                d.append("('%s','%s','vimshottari',%d,'2000-0%d-01','Sun',%d.25)" % (CHART, aya, lvl, i + 1, 30 + i))
    cl.psql("INSERT INTO chart_dashas (chart_id,ayanamsha_id,system_id,level_n,start_iso,lord_graha,duration_days) VALUES " + ",".join(d))
    s = []
    for i in range(1, 7):
        s.append("('%s','%s','%s','%s','sig%d',%d.5,ARRAY['%s']::uuid[],'{\"a\": %d}')" % (_uuid(i), CHART, "lahiri", "arudha" if i <= 2 else "dhana_axis", i, i, _uuid(i + 100), i))
    cl.psql("INSERT INTO bodha_msr_signals (signal_id,chart_id,ayanamsha_id,signal_type_class,signal_type_id,computed_salience,constituent_signals_array,configuration_jsonb) VALUES "
            + ",".join(s))
    cl.psql("INSERT INTO ga_medical (chart_id,ayanamsha_id,graha,strength) VALUES ('%s','lahiri','Sun',1.5),('%s','lahiri','Moon',2.5)" % (CHART, CHART))
    return cl


def _snap(runner, **kw):
    return snap.build_snapshot(runner, MINI, chart_id=CHART, **kw)


def _runners(db):
    return snap.PsycopgRunner(None), snap.PsqlRunner(str(db.bin_dir / "psql"))


def test_digest_is_stable_and_the_two_drivers_agree(db):
    pg, ps = _runners(db)
    try:
        a, b = _snap(pg), _snap(pg)
        c = _snap(ps)
    finally:
        pg.close()
    for asset in a["assets"]:
        assert a["assets"][asset]["status"] == "ok", a["assets"][asset]["error"]
        for k in ("rows", "content_digest", "ids_digest"):
            assert a["assets"][asset][k] == b["assets"][asset][k] == c["assets"][asset][k], (asset, k)
    ca = a["assets"]["ga_positions"]["components"]["chart_facts"]
    assert ca["rows"] == 10 and ca["distinct_keys"] == 10                        # the other chart's row is not counted; 5 rows x 2 ayanamshas
    assert a["assets"]["ga_dashas"]["rows"] == 12 and a["assets"]["bo_laksana"]["rows"] == 6 and a["assets"]["bo_arudha"]["rows"] == 2
    assert a["assets"]["_residual_chart_facts"]["rows"] == 4                      # yoga_misc x 2 x 2 ayanamshas: claimed by no slice
    assert snap.compare(a, b)["summary"]["unexpected_changes"] == 0
    assert all(r["verdict"] == "IDENTICAL" for r in snap.compare(a, b)["assets"].values())


def test_one_cell_mutation_moves_exactly_its_group_and_asset(db):
    pg, _ = _runners(db)
    try:
        before = _snap(pg)
        db.psql("UPDATE chart_facts SET fact_value_text = 'changed' WHERE chart_id = '%s' AND ayanamsha_id = 'raman' AND fact_subject = 'Sun' AND fact_key = 'longitude'" % CHART)
        after = _snap(pg)
    finally:
        pg.close()
    res = snap.compare(before, after)
    assert res["assets"]["ga_positions"]["verdict"] == "CHANGED"
    ch = res["assets"]["ga_positions"]["changes"]
    assert len(ch) == 1 and ch[0]["kind"] == "value" and ch[0]["row_level"] and ch[0]["where"]["fact_subject"] == "Sun" and ch[0]["where"]["ayanamsha_id"] == "raman"
    gb = before["assets"]["ga_positions"]["components"]["chart_facts"]["groups"]
    ga = after["assets"]["ga_positions"]["components"]["chart_facts"]["groups"]
    moved = sorted(k for k in gb if gb[k] != ga[k])
    assert moved == ["raman|graha_position|longitude"]                           # exactly one group of ten moved
    for other in ("ga_ayurdaya", "ga_dashas", "ga_medical", "bo_laksana", "bo_arudha", "_residual_chart_facts"):
        assert res["assets"][other]["verdict"] == "IDENTICAL", other


def test_volatile_columns_are_excluded_and_other_chart_rows_do_not_count(db):
    pg, _ = _runners(db)
    try:
        before = _snap(pg)
        db.psql("UPDATE chart_dashas SET build_id = gen_random_uuid(), created_at = now() + interval '1 day'")
        db.psql("UPDATE chart_facts SET computed_at = now() + interval '2 day', updated_at = now(), build_id = gen_random_uuid()")
        db.psql("UPDATE bodha_msr_signals SET computed_at = now() + interval '3 day', build_id = gen_random_uuid()")
        db.psql("UPDATE ga_medical SET computed_at = now()")
        db.psql("UPDATE chart_facts SET fact_value_text = 'zzz' WHERE chart_id = '%s'" % OTHER)             # a different chart: invisible
        after = _snap(pg)
    finally:
        pg.close()
    res = snap.compare(before, after)
    assert all(r["verdict"] == "IDENTICAL" for r in res["assets"].values()), json.dumps(res["assets"], indent=1)[:2000]
    comp = before["assets"]["ga_dashas"]["components"]["chart_dashas"]
    assert "build_id" in comp["excluded_columns"] and "created_at" in comp["excluded_columns"] and "dasha_row_id" not in comp["value_columns"]
    assert "dasha_row_id" in comp["id_columns"]


def test_ids_only_change_moves_only_the_ids_digest(db):
    pg, _ = _runners(db)
    try:
        before = _snap(pg)
        db.psql("UPDATE chart_dashas SET dasha_row_id = dasha_row_id + 1000")
        db.psql("UPDATE bodha_msr_signals SET signal_id = ('00000000-0000-4000-9000-' || right(signal_id::text, 12))::uuid, "
                "constituent_signals_array = ARRAY['00000000-0000-4000-9000-000000000009']::uuid[]")                  # the re-mint
        after = _snap(pg)
    finally:
        pg.close()
    for asset in ("ga_dashas", "bo_laksana", "bo_arudha"):
        b, a = before["assets"][asset], after["assets"][asset]
        assert b["content_digest"] == a["content_digest"], asset              # content untouched
        assert b["ids_digest"] != a["ids_digest"], asset                       # ids moved
    res = snap.compare(before, after)
    for asset in ("ga_dashas", "bo_laksana"):
        assert res["assets"][asset]["verdict"] == "CHANGED"
        assert {c["kind"] for c in res["assets"][asset]["changes"]} == {"ids_only"}
        assert all(c["verdict"] == "UNEXPECTED" for c in res["assets"][asset]["changes"])          # not predicted -> UNEXPECTED
    predicted = {"assets": {"bo_laksana": [{"id": "T1", "description": "signal re-mint", "change": "ids_only", "scope": {"relation": "bodha_msr_signals"}}],
                            "bo_arudha": [{"id": "T1", "description": "signal re-mint", "change": "ids_only", "scope": {"relation": "bodha_msr_signals"}}],
                            "ga_dashas": [{"id": "T2", "description": "dasha_row_id determinism", "change": "ids_only", "scope": {"relation": "chart_dashas"}}]}}
    res2 = snap.compare(before, after, predicted)
    assert res2["summary"]["unexpected_changes"] == 0 and res2["summary"]["changed"] == 3


def test_chunking_does_not_change_the_digest(db):
    pg, _ = _runners(db)
    try:
        chunked = _snap(pg, chunk=True)
        whole = _snap(pg, chunk=False)
    finally:
        pg.close()
    for asset in chunked["assets"]:
        assert chunked["assets"][asset]["content_digest"] == whole["assets"][asset]["content_digest"], asset
        assert chunked["assets"][asset]["ids_digest"] == whole["assets"][asset]["ids_digest"], asset
    assert len(chunked["assets"]["ga_dashas"]["components"]["chart_dashas"]["chunks"]) == 2          # one query per ayanamsha value
    assert len(whole["assets"]["ga_dashas"]["components"]["chart_dashas"]["chunks"]) == 1


def test_shared_table_slices_are_independent_and_the_residual_catches_the_unclaimed(db):
    pg, _ = _runners(db)
    try:
        before = _snap(pg)
        db.psql("UPDATE chart_facts SET fact_value_text = 'changed' WHERE chart_id = '%s' AND fact_category = 'yoga_misc' AND fact_subject = 'Moon'" % CHART)
        db.psql("UPDATE bodha_msr_signals SET computed_salience = 99 WHERE signal_type_class = 'dhana_axis'")
        after = _snap(pg)
    finally:
        pg.close()
    res = snap.compare(before, after)
    assert res["assets"]["_residual_chart_facts"]["verdict"] == "CHANGED"
    assert res["assets"]["ga_positions"]["verdict"] == "IDENTICAL" and res["assets"]["ga_ayurdaya"]["verdict"] == "IDENTICAL"
    assert res["assets"]["bo_laksana"]["verdict"] == "CHANGED" and res["assets"]["bo_arudha"]["verdict"] == "IDENTICAL"          # the whole-table asset sees the slice change
    assert res["summary"]["unexpected_changes"] >= 2


def test_a_prose_only_change_is_told_apart_from_a_value_change(db):
    pg, _ = _runners(db)
    try:
        before = _snap(pg)
        db.psql("UPDATE chart_facts SET citation_human = 'a rewritten sentence' WHERE chart_id = '%s' AND fact_category = 'sandhi_flag'" % CHART)      # 2 rows
        after = _snap(pg)
    finally:
        pg.close()
    b = before["assets"]["ga_positions"]["components"]["chart_facts"]
    assert "citation_human" in b["prose_columns"] and "fact_value_text" in b["value_columns"]
    assert b["value_digest"] == after["assets"]["ga_positions"]["components"]["chart_facts"]["value_digest"]          # values untouched
    assert b["content_digest"] != after["assets"]["ga_positions"]["components"]["chart_facts"]["content_digest"]
    res = snap.compare(before, after, {"assets": {"ga_positions": [{"id": "C1", "description": "citation rewrite", "change": "prose", "expected_rows": 2,
                                                                      "scope": {"relation": "chart_facts", "where": {"fact_category": "sandhi_flag"}}}]}})
    ch = res["assets"]["ga_positions"]["changes"]
    assert len(ch) == 2 and all(c["kind"] == "prose" and c["verdict"] == "EXPECTED" for c in ch)
    # the same rows changed as a VALUE do not satisfy a prose prediction
    db.psql("UPDATE chart_facts SET fact_value_text = 'v' WHERE chart_id = '%s' AND fact_category = 'sandhi_flag'" % CHART)
    pg = snap.PsycopgRunner(None)
    try:
        later = _snap(pg)
    finally:
        pg.close()
    res2 = snap.compare(after, later, {"assets": {"ga_positions": [{"id": "C1", "change": "prose", "scope": {"relation": "chart_facts"}}]}})
    assert all(c["verdict"] == "UNEXPECTED" and c["kind"] == "value" for c in res2["assets"]["ga_positions"]["changes"])
    # max_rows is a bound: 2 rows moved, a bound of 1 is exceeded
    res3 = snap.compare(before, after, {"assets": {"ga_positions": [{"id": "C2", "change": "prose", "max_rows": 1, "scope": {"relation": "chart_facts"}}]}})
    assert all(c["verdict"] == "UNEXPECTED" for c in res3["assets"]["ga_positions"]["changes"])


def test_compare_expected_unexpected_count_and_not_seen(db):
    pg, _ = _runners(db)
    try:
        before = _snap(pg)
        db.psql("UPDATE chart_facts SET fact_value_text = 'cited' WHERE chart_id = '%s' AND fact_category = 'graha_position' AND fact_key = 'retrograde_flag'" % CHART)   # 4 rows
        db.psql("UPDATE chart_facts SET fact_value_text = 'oops' WHERE chart_id = '%s' AND fact_category = 'sandhi_flag' AND ayanamsha_id = 'lahiri'" % CHART)        # 1 row
        after = _snap(pg)
    finally:
        pg.close()
    predicted = {"assets": {"ga_positions": [
        {"id": "P1", "description": "node retrograde rows", "change": "value", "expected_rows": 4,
         "scope": {"relation": "chart_facts", "where": {"fact_category": "graha_position", "fact_key": "retrograde_flag", "fact_subject": ["Rahu", "Ketu"]}}},
        {"id": "P2", "description": "never happens", "change": "content", "scope": {"relation": "chart_facts", "where": {"fact_category": "house_chalit"}}}]}}
    res = snap.compare(before, after, predicted)
    ch = {(c["where"]["fact_category"], c["where"]["ayanamsha_id"], c["where"]["fact_subject"]): c for c in res["assets"]["ga_positions"]["changes"]}
    assert len(ch) == 5
    assert sum(1 for c in ch.values() if c["verdict"] == "EXPECTED") == 4 and ch[("sandhi_flag", "lahiri", "Sun")]["verdict"] == "UNEXPECTED"
    assert [p["id"] for p in res["assets"]["ga_positions"]["predicted_not_seen"]] == ["P2"]
    predicted["assets"]["ga_positions"][0]["expected_rows"] = 10                     # a wrong count turns the EXPECTED rows into UNEXPECTED
    res2 = snap.compare(before, after, predicted)
    assert all(c["verdict"] == "UNEXPECTED" for c in res2["assets"]["ga_positions"]["changes"] if c.get("predicted") == "P1")
    text = snap.render_compare(res, before, after)
    assert "UNEXPECTED" in text and "EXPECTED [P1]" in text and "PREDICTED-NOT-SEEN" in text


def test_session_is_read_only_and_resume_skips_finished_assets(db):
    pg = snap.PsycopgRunner(None)
    try:
        with pytest.raises(Exception) as ei:
            pg._run("DELETE FROM chart_facts")                                      # bypasses the lexer guard on purpose: the SESSION must still refuse
        assert "read-only" in str(ei.value).lower()
        first = snap.build_snapshot(pg, MINI, chart_id=CHART, assets=["ga_positions"])
        calls = []

        class Counting(snap.PsycopgRunner):
            def __init__(self, inner):
                self._conn = inner._conn

            def _run(self, sql):
                calls.append(sql)
                return super()._run(sql)
        full = snap.build_snapshot(Counting(pg), MINI, chart_id=CHART, assets=["ga_positions", "ga_medical"], previous=first)
    finally:
        pg.close()
    assert sorted(full["assets"]) == ["ga_medical", "ga_positions"]
    assert not any("chart_facts" in c for c in calls)                              # ga_positions was resumed, not re-read
    assert db.psql("SELECT count(*) FROM chart_facts") == "17"


def test_missing_relation_is_recorded_not_fatal_and_other_chart_is_refused(db, tmp_path):
    scopes = copy.deepcopy(MINI)
    scopes["assets"]["ga_medical"]["components"][0]["relation"] = "no_such_table"
    pg = snap.PsycopgRunner(None)
    try:
        doc = snap.build_snapshot(pg, scopes, chart_id=CHART, assets=["ga_medical", "ga_positions"])
    finally:
        pg.close()
    assert doc["assets"]["ga_medical"]["status"] == "error" and doc["assets"]["ga_positions"]["status"] == "ok"
    assert snap.main(["--out", str(tmp_path / "x.json"), "--chart-id", OTHER]) == 2


# ───────────────────────────── predicted-changes data + the CLI ─────────────────────────────

def test_predicted_changes_data_is_well_formed_and_points_at_real_components():
    pred = json.loads(snap.DEFAULT_PREDICTED.read_text(encoding="utf-8"))
    assert pred["schema"] == "suvarna.l12_predicted_changes/1"
    ids = []
    for asset, entries in pred["assets"].items():
        assert asset in SCOPES["assets"], asset
        rels = {c["relation"] for c in SCOPES["assets"][asset]["components"]}
        for e in entries:
            ids.append(e["id"])
            assert e["change"] in ("any", "content", "value", "prose", "ids_only", "added", "removed"), e["id"]
            assert e["scope"]["relation"] in rels, (asset, e["id"], e["scope"]["relation"], sorted(rels))
            assert e["description"] and e["source"], e["id"]
            for k in ("expected_rows", "max_rows"):
                assert e.get(k) is None or isinstance(e[k], int)
    assert len(ids) >= 30
    for must in ("GP-1", "GC-1", "GS-1", "GV-1", "BL-1", "AN-1", "GE-1"):
        assert must in ids, must


def test_cli_snapshot_then_compare_exit_codes(db, tmp_path, capsys):
    scopes_file = tmp_path / "scopes.json"
    scopes_file.write_text(json.dumps(MINI), encoding="utf-8")
    pred_file = tmp_path / "pred.json"
    pred_file.write_text(json.dumps({"assets": {}}), encoding="utf-8")
    b, a = str(tmp_path / "before.json"), str(tmp_path / "after.json")
    assert snap.main(["--out", b, "--scopes", str(scopes_file), "--driver", "psql"]) == 0
    assert snap.main(["--out", a, "--scopes", str(scopes_file), "--driver", "psycopg"]) == 0
    assert snap.main(["--compare", b, a, "--predicted", str(pred_file)]) == 0                       # nothing moved
    db.psql("UPDATE ga_medical SET strength = 9 WHERE graha = 'Sun'")
    assert snap.main(["--out", a, "--scopes", str(scopes_file)]) == 0
    capsys.readouterr()
    assert snap.main(["--compare", b, a, "--predicted", str(pred_file)]) == 1                       # an unpredicted change
    out = capsys.readouterr().out
    assert "ga_medical" in out and "UNEXPECTED" in out and "SUMMARY" in out
    pred_file.write_text(json.dumps({"assets": {"ga_medical": [{"id": "M", "description": "x", "source": "y", "change": "value", "scope": {"relation": "ga_medical"}}]}}), encoding="utf-8")
    assert snap.main(["--compare", b, a, "--predicted", str(pred_file)]) == 0
    assert snap.main(["--compare", b, a, "--predicted", str(pred_file), "--json"]) == 0
    # resume: an `ok` asset of an existing file is not read again
    assert snap.main(["--out", a, "--scopes", str(scopes_file), "--resume", "--assets", "ga_medical"]) == 0


def test_every_committed_component_executes_on_a_synthetic_schema(disposable_pg, monkeypatch):
    """The full committed scopes (43 assets + residual) run end to end: tables are built from the scope's own column names (text), so every generated
    statement -- the 82-column jsonb batches, the ownership subselect, ANY(ARRAY[...]), the residual NOT coalesce -- is executed for real."""
    cl = disposable_pg
    point_psql_at(cl, monkeypatch)
    cl.psql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    cols: dict = {}
    for spec in list(SCOPES["assets"].values()) + [SCOPES["residual"]]:
        for c in spec["components"]:
            s = cols.setdefault(c["relation"], {"chart_id": "uuid", "ayanamsha_id": "text"})
            for k in (c.get("content_columns") or []) + (c.get("id_columns") or []) + (c.get("id_ref_columns") or []) + (c.get("key") or []) + (c.get("dims") or []):
                s.setdefault(k, "text")
            s["computed_at"] = "timestamptz"
            s["build_id"] = "uuid"
    s = cols["chart_facts"]
    s.update(fact_category="text", fact_subject="text", fact_key="text")
    cols["fact_category_ownership"] = {"fact_category": "text", "owning_asset_id": "text"}
    cols["bodha_msr_signals"].update(signal_type_class="text", graph_node_strength_contribution_jsonb="text")
    cols["bodha_cgm_nodes"].update(node_type="text")
    cols["chart_vichara"].update(vichara_family="text")
    for rel, cs in cols.items():
        if rel == "fact_category_ownership":
            cs.pop("chart_id", None), cs.pop("ayanamsha_id", None), cs.pop("computed_at", None), cs.pop("build_id", None)
        cl.psql("CREATE TABLE " + rel + " (" + ", ".join('"' + c + '" ' + t for c, t in cs.items()) + ")")
    cl.psql("INSERT INTO fact_category_ownership VALUES ('dosha_label', 'ga_structural'), ('aspect_x', 'ga_structural')")
    cl.psql("INSERT INTO chart_facts (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key) VALUES "
            "('%s','lahiri','graha_position','SUN','longitude'), ('%s','lahiri','dosha_label','daridra','dosha_name'), ('%s','lahiri','aspect_x','SUN','a'), ('%s','lahiri','unclaimed_cat','SUN','z')"
            % (CHART, CHART, CHART, CHART))
    pg = snap.PsycopgRunner(None)
    try:
        doc = snap.build_snapshot(pg, SCOPES, chart_id=CHART)
    finally:
        pg.close()
    bad = {a: r["error"] for a, r in doc["assets"].items() if r["status"] != "ok"}
    assert not bad, bad
    assert len(doc["assets"]) == 44 and doc["assets"]["ga_positions"]["rows"] == 1 and doc["assets"]["_residual_chart_facts"]["rows"] == 1
    assert doc["assets"]["ga_structural"]["components"]["chart_facts"]["rows"] == 2                  # dosha_label + aspect_x via the ownership map
    assert doc["assets"]["ga_vichara"]["components"]["chart_facts_daridra"]["rows"] == 1
    assert doc["assets"]["ga_structural"]["components"]["fact_category_ownership"]["rows"] == 2      # the global map is not chart scoped
    assert snap.compare(doc, doc)["summary"]["identical"] == 44


def test_registry_count_reads_a_multiline_stored_statement_whole_and_runs_with_queries(db):
    """The stored count_sql of bo_laksana / bo_upaya / ga_prashna / bo_cdlm_summary is multi-line (and one starts with WITH): the first run read only the first
    line of it through psql's line-oriented output (a syntax error) and refused the WITH. Both drivers must now return the real count."""
    db.psql("CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text)")
    stmts = {
        "ga_x_array": "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category = ANY(ARRAY[\n  'graha_position',\n  'ayurdaya'\n])",
        "ga_x_sum": "\nSELECT (\n  (SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category = 'ayurdaya') +\n  (SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category = 'sandhi_flag')\n) AS count\n",
        "bo_x_with": "WITH p AS (SELECT $1::uuid AS cid)\nSELECT (SELECT count(*) FROM chart_facts f, p WHERE f.chart_id = p.cid) AS count",
        "bo_x_write": "WITH w AS (DELETE FROM chart_facts RETURNING 1)\nSELECT count(*) FROM w",
        "bo_x_comment": "SELECT count(*) -- how many\n FROM chart_facts WHERE chart_id = $1",
    }
    for k, v in stmts.items():
        db.psql("INSERT INTO asset_registry VALUES ('%s', $q$%s$q$)" % (k, v))
    want = {"ga_x_array": 10, "ga_x_sum": 4, "bo_x_with": 16, "bo_x_comment": 16}
    for runner in _runners(db):
        try:
            for a, n in want.items():
                got = snap.registry_count(runner, CHART, a)
                assert got == {"result": "ok", "count": n}, (type(runner).__name__, a, got)
            assert snap.registry_count(runner, CHART, "bo_x_write")["result"] == "refused"      # a data-modifying CTE is still refused
            assert snap.registry_count(runner, CHART, "nope")["result"] == "no_count_sql"
        finally:
            runner.close()
    assert db.psql("SELECT count(*) FROM chart_facts") == "17"
