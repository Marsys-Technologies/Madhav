"""test_ss_rd_service_static.py -- SS 2026-10-05 R-d: writer-less services and migration-seeded static data.

  * A writer-less SERVICE with no count_sql: Build.completion / Build.count_integrity read N/A (causes service-no-writer-no-count-sql) ONLY where it declares `has_writer: false` and kind service
    and the registry row (has_writer false, asset_kind service) and the @register scan agree.
  * Migration-seeded STATIC data with a declared dependency edge (bg_gochara_citation_resolution): Build.dag checks the edge for EXISTENCE and acyclicity only (reads-match not applicable: no build
    code), Build.dep_liveness reads N/A (static-data-existence-only) -- only for declared kind static + has_writer false + registry row + @register scan + a migration that owns the row.
Offline: the measure() harness with the git machinery stubbed, plus the rollup guard on forged records.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

NA, FAIL, ND, PASS = ac.NA, ac.FAIL, ac.NO_DET, ac.PASS
SVC = "bg_svc"
STA = "bg_static"


def _row(aid, kind, deps=(), has_writer=False, count_sql="", target_table=None):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql=count_sql, has_integrity=False, integrity_sql=None, depends_on=list(deps), target_floor=None,
                catalog_status="CURRENT", asset_kind=kind)


def _stub(monkeypatch, tmp_path, regs, decls, *, files=None, mentions=(), dep_state="lit"):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(regs), dict(registry_total=len(regs), active=len(regs), excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(), cols={}, keys={}, views=set()))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    dep = {"bg_dep": {"": dict(state=dep_state, rows_written="1", rps="", last_built="2026-10-01", n_rows=1, ambiguous=False, _key=(1.0, 1.0), built_epoch="1", duration=None)}}
    monkeypatch.setattr(ac, "throughput", lambda prefix, ids=None, *a, **k: dep if ids and set(ids) <= {"bg_dep"} else {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: list(r["depends_on"]) for a, r in regs.items()} | {"bg_dep": []}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decls)
    monkeypatch.setattr(ac, "register_call_mentions", lambda a: list(mentions))
    bw = ac._lint_module("build_window")
    monkeypatch.setattr(bw.WindowReader, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(bw.WindowReader, "file_at_main", lambda self, path: files.get(path, None) if files is not None else MIGS.get(path))
    monkeypatch.setattr(bw.WindowReader, "registry_commit", lambda self, a: (1.0, "a" * 40))


def _cells(c, aid):
    return next(a for a in c["assets"] if a["asset_id"] == aid)["measurements"]


SVC_DECL = {SVC: {"kind": "service", "has_writer": False}}
MIG_DIR = "platform/supabase/migrations/"
STATIC = dict(migrations=["565_x.sql", "630_y.sql"], table="bg_static_tbl", why="the table is created and repaired by checked-in migrations; no writer builds it", evidence="platform/scripts/governance/asset_census.py:1")
MIGS = {MIG_DIR + "565_x.sql": "CREATE TABLE bg_static_tbl (id int);\nINSERT INTO bg_static_tbl VALUES (1);\n", MIG_DIR + "630_y.sql": "INSERT INTO public.bg_static_tbl VALUES (2);\n"}
STA_DECL = {STA: {"kind": "static", "has_writer": False, "static_data": STATIC}}


# ───────────── service ─────────────

def test_a_checked_writerless_service_reads_na_on_completion_and_count_integrity(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {SVC: _row(SVC, "service")}, SVC_DECL)
    m = _cells(ac.measure("L0"), SVC)
    for crit in ("Build.completion", "Build.count_integrity"):
        assert m[crit]["v"] == NA and m[crit]["cause"] == "service-no-writer-no-count-sql", (crit, m[crit])
        assert m[crit]["no_writer"]["service"] is True and m[crit]["no_writer"]["registry_kind"] == "service", m[crit]
    roll = ac.rollup_asset("L0", m)
    assert roll["Build"]["checks"] and {c["criterion"]: c["v"] for c in roll["Build"]["checks"]}["Build.completion"] == NA
    assert {c["criterion"]: c["v"] for c in roll["Build"]["checks"]}["Build.count_integrity"] == NA


@pytest.mark.parametrize("name,regs,decls,kw", [
    ("not declared has_writer false", {SVC: _row(SVC, "service")}, {SVC: {"kind": "service"}}, {}),
    ("declared kind is data", {SVC: _row(SVC, "service")}, {SVC: {"kind": "data", "has_writer": False}}, {}),
    ("registry asset_kind is data", {SVC: _row(SVC, "data")}, SVC_DECL, {}),
    ("an @register call mentions it", {SVC: _row(SVC, "service")}, SVC_DECL, dict(mentions=["w.py"])),
])
def test_without_every_agreeing_fact_the_service_keeps_the_unruled_cause_and_reads_no_detector(monkeypatch, tmp_path, name, regs, decls, kw):
    _stub(monkeypatch, tmp_path, regs, decls, **kw)
    m = _cells(ac.measure("L0"), SVC)
    for crit in ("Build.completion", "Build.count_integrity"):
        assert m[crit].get("cause") != "service-no-writer-no-count-sql", (name, m[crit])
    roll = {c["criterion"]: c["v"] for c in ac.rollup_asset("L0", m)["Build"]["checks"]}
    assert roll["Build.completion"] == ND and roll["Build.count_integrity"] == ND, (name, roll)


def test_a_forged_service_record_without_the_service_facts_is_not_released():
    base = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])
    rec = dict(v=NA, cause="service-no-writer-no-count-sql", measured="m")
    assert ac.no_writer_na_problem("Build.completion", dict(rec, no_writer=base))
    assert ac.no_writer_na_problem("Build.completion", dict(rec, no_writer=dict(base, service=True, registry_kind="data", declared_kind="service")))
    assert ac.no_writer_na_problem("Build.completion", dict(rec, no_writer=dict(base, service=True, registry_kind="service", declared_kind="service"))) is None
    assert ac.no_writer_na_problem("Build.completion", dict(rec, no_writer=dict(base, service=True, registry_kind="service", declared_kind="service", register_files=1)))


# ───────────── static data: the declaration names the owning migrations, checked on main ─────────────

def _static_regs():
    return {STA: _row(STA, "data", deps=["bg_dep"], target_table="bg_static_tbl"), "bg_dep": _row("bg_dep", "data", has_writer=True)}


def _run(monkeypatch, tmp_path, decls=None, **kw):
    _stub(monkeypatch, tmp_path, _static_regs(), {**(STA_DECL if decls is None else decls), "bg_dep": {"kind": "data"}}, **kw)
    return _cells(ac.measure("L0"), STA)


def test_static_data_whose_declared_migrations_exist_and_reference_the_table_reads_dag_pass_and_dep_liveness_na(monkeypatch, tmp_path):
    m = _run(monkeypatch, tmp_path, dep_state="error")                                # the dependency is NOT lit: no liveness requirement
    assert m["Build.dag"]["v"] == PASS and "checked for existence only" in m["Build.dag"]["measured"] and m["Build.dag"]["static_data"]["static_data"] is True, m["Build.dag"]
    assert m["Build.dep_liveness"]["v"] == NA and m["Build.dep_liveness"]["cause"] == "static-data-existence-only", m["Build.dep_liveness"]
    nw = m["Build.dep_liveness"]["no_writer"]
    assert nw["migrations_checked"] is True and nw["migrations"] == ["565_x.sql", "630_y.sql"] and nw["table"] == "bg_static_tbl" and len(nw["migration_files"]) == 2, nw
    roll = {c["criterion"]: c["v"] for c in ac.rollup_asset("L0", m)["Build"]["checks"]}
    assert roll["Build.dep_liveness"] == NA and roll["Build.dag"] == PASS


def test_a_missing_migration_file_releases_nothing(monkeypatch, tmp_path):
    m = _run(monkeypatch, tmp_path, files={MIG_DIR + "565_x.sql": MIGS[MIG_DIR + "565_x.sql"]})           # 630 is absent on main
    assert m["Build.dag"]["v"] == ND and m["Build.dep_liveness"].get("cause") != "static-data-existence-only", (m["Build.dag"], m["Build.dep_liveness"])


def test_a_migration_that_does_not_reference_the_table_releases_nothing(monkeypatch, tmp_path):
    m = _run(monkeypatch, tmp_path, files={**MIGS, MIG_DIR + "630_y.sql": "UPDATE some_other_table SET id = 2;\n"})
    assert m["Build.dag"]["v"] == ND and m["Build.dep_liveness"].get("cause") != "static-data-existence-only"


@pytest.mark.parametrize("name,text", [
    ("a comment-only mention", "-- bg_static_tbl is seeded elsewhere\n/* CREATE TABLE bg_static_tbl (id int); */\nSELECT 1;\n"),
    ("a DROP TABLE", "DROP TABLE bg_static_tbl;\n"),
    ("another schema's table", "CREATE TABLE other.bg_static_tbl (id int);\nINSERT INTO other.bg_static_tbl VALUES (1);\n"),
    ("a longer name", "CREATE TABLE bg_static_tbl_v2 (id int);\nINSERT INTO bg_static_tbl_archive VALUES (1);\n"),
    ("a SELECT", "SELECT * FROM bg_static_tbl;\n"),
])
def test_a_migration_that_does_not_create_or_seed_the_table_releases_nothing(monkeypatch, tmp_path, name, text):
    m = _run(monkeypatch, tmp_path, files={**MIGS, MIG_DIR + "630_y.sql": text})
    assert m["Build.dag"]["v"] == ND and m["Build.dep_liveness"].get("cause") != "static-data-existence-only", (name, m["Build.dep_liveness"])
    chk = ac.static_data_check(STATIC, lambda p: text if p.endswith("630_y.sql") else MIGS[p])
    assert not chk["ok"] and "no CREATE TABLE / INSERT INTO / UPDATE" in chk["problems"][0], (name, chk)


@pytest.mark.parametrize("name,text", [
    ("a keyword in a string literal", "SELECT 'INSERT INTO bg_static_tbl';\n"),
    ("a statement inside another statement's literal", "INSERT INTO bar VALUES ('CREATE TABLE bg_static_tbl');\n"),
    ("a notice text in a DO body", "DO $$ BEGIN RAISE NOTICE 'CREATE TABLE bg_static_tbl'; END $$;\n"),
    ("a dollar-quoted string", "SELECT $$CREATE TABLE bg_static_tbl (id int)$$;\n"),
    ("a tagged dollar-quoted string", "SELECT $q$INSERT INTO bg_static_tbl VALUES (1)$q$;\n"),
    ("a nested block comment", "/* a /* b */ CREATE TABLE bg_static_tbl (id int); */\nSELECT 1;\n"),
    ("a doubly nested block comment", "/* x /* y /* z */ INSERT INTO bg_static_tbl VALUES (1); */ */\nSELECT 1;\n"),
    ("an escaped quote hiding the keyword", "SELECT 'it''s INSERT INTO bg_static_tbl';\n"),
])
def test_text_that_only_mentions_a_statement_is_not_a_statement(name, text):
    chk = ac.static_data_check(dict(STATIC, migrations=["565_x.sql"]), lambda p: text)
    assert not chk["ok"] and "no CREATE TABLE / INSERT INTO / UPDATE" in chk["problems"][0], (name, chk)


@pytest.mark.parametrize("text", ["DO $$ BEGIN INSERT INTO bg_static_tbl VALUES (1); END $$;", "DO $b$ BEGIN INSERT INTO bg_static_tbl VALUES (1); END $b$;",
                                  "CREATE FUNCTION f() RETURNS void AS $f$ BEGIN INSERT INTO public.bg_static_tbl VALUES ('x'); END $f$ LANGUAGE plpgsql;",
                                  "/* note */ CREATE TABLE bg_static_tbl (id int DEFAULT 'a''b');", "CREATE TABLE bg_static_tbl (note text DEFAULT '-- not a comment');",
                                  "/* a /* b */ c */ CREATE TABLE bg_static_tbl (id int);"])
def test_statements_inside_a_do_block_or_function_body_and_after_literals_or_nested_comments_still_count(text):
    """The declared migrations 630 / 631 UPDATE their table inside DO blocks: a code body keeps its statements (only its own string literals are blanked)."""
    assert ac.static_data_check(dict(STATIC, migrations=["565_x.sql"]), lambda p: text)["ok"], text


def test_the_blankers_keep_offsets_and_nested_comments():
    w = ac._lint_module("writer_literal_scan")
    s = "/* a /* b */ c */ SELECT 'x y' -- tail\n, $$ z $$"
    assert len(w.blank_sql_comments(s)) == len(s) and len(w.blank_sql_literals(w.blank_sql_comments(s))) == len(s)
    assert "c" not in w.blank_sql_comments(s).split("SELECT")[0]                  # the nested comment is blanked to its OUTER close
    assert w.blank_sql_literals("a 'x'") == "a ' '"
    assert w.blank_sql_literals("an unterminated 'abc") == "an unterminated '   "
    assert w.blank_sql_literals('"quoted ident" \'t\'') == '"quoted ident" \' \''


@pytest.mark.parametrize("text", ["CREATE TABLE bg_static_tbl (id int);", "create table if not exists public.bg_static_tbl (id int);", 'CREATE TABLE IF NOT EXISTS "bg_static_tbl" (id int);',
                                  "INSERT INTO bg_static_tbl (id) VALUES (1);", "-- note\nINSERT INTO public.bg_static_tbl VALUES (1);", "CREATE UNLOGGED TABLE bg_static_tbl (id int);"])
def test_the_create_and_seed_forms_that_count(text):
    assert ac.static_data_check(dict(STATIC, migrations=["565_x.sql"]), lambda p: text)["ok"], text


def test_update_statements_alone_do_not_own_a_table_but_may_repair_a_seeded_one():
    only_updates = ac.static_data_check(STATIC, lambda p: "UPDATE bg_static_tbl SET id = 1;\n")
    assert not only_updates["ok"] and "UPDATE statements alone do not own a table" in only_updates["problems"][0], only_updates
    assert ac.static_data_check(STATIC, lambda p: MIGS[p])["ok"]                                            # 565 creates, 630 inserts
    seeded_then_repaired = ac.static_data_check(STATIC, lambda p: "CREATE TABLE bg_static_tbl (id int);" if p.endswith("565_x.sql") else "UPDATE public.bg_static_tbl SET id = 2;")
    assert seeded_then_repaired["ok"] and len(seeded_then_repaired["files"]) == 2


def test_the_declared_table_must_be_the_assets_own_table(monkeypatch, tmp_path):
    """Review MED: a declaration could name any table that some migration creates; it must be the asset's registry target_table (or a table its count_sql reads)."""
    regs = {STA: _row(STA, "data", deps=["bg_dep"], target_table="some_other_table"), "bg_dep": _row("bg_dep", "data", has_writer=True)}
    _stub(monkeypatch, tmp_path, regs, {**STA_DECL, "bg_dep": {"kind": "data"}})
    m = _cells(ac.measure("L0"), STA)
    assert m["Build.dag"]["v"] == ND and m["Build.dep_liveness"].get("cause") != "static-data-existence-only", m["Build.dep_liveness"]
    chk = ac.static_data_check(STATIC, lambda p: MIGS.get(p), own_tables={"some_other_table"})
    assert not chk["ok"] and "not the asset's own table" in chk["problems"][0]
    assert ac.static_data_check(STATIC, lambda p: MIGS.get(p), own_tables={"bg_static_tbl"})["ok"]
    regs = {STA: _row(STA, "data", deps=["bg_dep"], count_sql="SELECT count(*) FROM bg_static_tbl"), "bg_dep": _row("bg_dep", "data", has_writer=True)}
    _stub(monkeypatch, tmp_path, regs, {**STA_DECL, "bg_dep": {"kind": "data"}})
    assert _cells(ac.measure("L0"), STA)["Build.dep_liveness"]["cause"] == "static-data-existence-only"          # a count_sql table counts as the asset's own


def test_a_registry_seed_row_alone_is_not_ownership(monkeypatch, tmp_path):
    """SS: a seed row is the catalogue entry, not the owner. With no static_data declaration nothing is released (the old seed/migration-statement basis is gone)."""
    m = _run(monkeypatch, tmp_path, decls={STA: {"kind": "static", "has_writer": False}})
    assert m["Build.dag"]["v"] == ND and m["Build.dep_liveness"].get("cause") != "static-data-existence-only", (m["Build.dag"], m["Build.dep_liveness"])


@pytest.mark.parametrize("name,decls,kw", [
    ("kind is data, not static", {STA: {"kind": "data", "has_writer": False}}, {}),
    ("not declared has_writer false", {STA: {"kind": "static", "static_data": STATIC}}, {}),
    ("an @register call mentions it", None, dict(mentions=["w.py"])),
])
def test_without_every_agreeing_fact_static_data_is_not_released(monkeypatch, tmp_path, name, decls, kw):
    m = _run(monkeypatch, tmp_path, decls=decls, **kw)
    assert m["Build.dag"]["v"] == ND, (name, m["Build.dag"])                       # the old reading: edge(s) cannot be compared with reads
    assert m["Build.dep_liveness"].get("cause") != "static-data-existence-only", (name, m["Build.dep_liveness"])


def test_a_writer_built_asset_claiming_static_data_is_refused_by_the_registry_row(monkeypatch, tmp_path):
    regs = {STA: _row(STA, "data", deps=["bg_dep"], has_writer=True), "bg_dep": _row("bg_dep", "data", has_writer=True)}
    _stub(monkeypatch, tmp_path, regs, {**STA_DECL, "bg_dep": {"kind": "data"}})
    m = _cells(ac.measure("L0"), STA)
    assert m["Build.dep_liveness"].get("cause") != "static-data-existence-only" and "static_data" not in (m["Build.dag"] or {}), m["Build.dep_liveness"]


def test_static_data_whose_edge_does_not_exist_fails_dag(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {STA: _row(STA, "data", deps=["bg_missing"])}, STA_DECL)
    m = _cells(ac.measure("L0"), STA)
    assert m["Build.dag"]["v"] == FAIL and "unknown or inactive" in m["Build.dag"]["measured"], m["Build.dag"]
    assert m["Build.dep_liveness"].get("cause") != "static-data-existence-only", m["Build.dep_liveness"]


def test_static_data_on_a_cycle_fails_dag(monkeypatch, tmp_path):
    regs = {STA: _row(STA, "data", deps=["bg_dep"]), "bg_dep": _row("bg_dep", "data", deps=[STA], has_writer=True)}
    _stub(monkeypatch, tmp_path, regs, {**STA_DECL, "bg_dep": {"kind": "data"}})
    monkeypatch.setattr(ac, "dependency_graph", lambda: {STA: ["bg_dep"], "bg_dep": [STA]}, raising=False)
    m = _cells(ac.measure("L0"), STA)
    assert m["Build.dag"]["v"] == FAIL and "cycle" in m["Build.dag"]["measured"], m["Build.dag"]


# ───────────── the declaration field: schema, validator, the checked half ─────────────

def _doc(sd, **entry):
    e = {"kind": "static", "has_writer": False, "static_data": sd}
    e.update(entry)
    return dict(version="x", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_s": e})


def test_a_well_formed_static_data_declaration_validates_and_the_doc_field_list_is_checked():
    ac.validate_declarations(_doc(dict(STATIC)))
    doc = _doc(dict(STATIC))
    doc["static_data_declaration_fields"] = ["migrations", "table", "why"]
    with pytest.raises(ac.DeclarationsError, match="static_data_declaration_fields"):
        ac.validate_declarations(doc)


@pytest.mark.parametrize("patch,match", [
    (dict(migrations=[]), "names no migration"),
    (dict(migrations=None), "names no migration"),
    (dict(migrations=["not_a_migration.txt"]), "names no migration|malformed"),
    (dict(migrations=["565_x.sql", "565_x.sql"]), "distinct"),
    (dict(migrations=["../565_x.sql"]), "malformed"),
    (dict(migrations=["565_x.sql"] * 1 + [f"{i}_a.sql" for i in range(9)]), "1 to"),
    (dict(table="bg static"), "table"),
    (dict(why="short"), "why"),
    (dict(evidence="unverified:i believe so by the migrations"), "evidence"),
    (dict(evidence="platform/nope.sql:1"), "evidence"),
    (dict(extra="x"), "unknown field"),
])
def test_a_malformed_static_data_declaration_is_refused(patch, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(dict(STATIC, **patch)))


@pytest.mark.parametrize("entry", [dict(kind="data"), dict(kind="service"), dict(has_writer=None), dict(has_writer=True)])
def test_a_writer_built_or_non_static_asset_cannot_claim_static_data(entry):
    doc = _doc(dict(STATIC), **entry)
    if entry.get("has_writer") is None:
        doc["assets"]["bg_s"].pop("has_writer")
    with pytest.raises(ac.DeclarationsError, match="static data only|has_writer"):
        ac.validate_declarations(doc)


def test_the_checked_half_is_pure_over_read_file():
    ok = ac.static_data_check(STATIC, lambda p: MIGS.get(p))
    assert ok["ok"] and len(ok["files"]) == 2
    assert not ac.static_data_check(STATIC, lambda p: None)["ok"]
    bad = ac.static_data_check(STATIC, lambda p: "SELECT 1" if p.endswith("565_x.sql") else MIGS[p])
    assert not bad["ok"] and "no CREATE TABLE / INSERT INTO / UPDATE" in bad["problems"][0]
    def boom(p):
        raise OSError("x")
    assert "could not be read" in ac.static_data_check(STATIC, boom)["problems"][0]
    assert ac.static_data_check(dict(STATIC, migrations=[]), lambda p: "")["problems"] == ["the declaration names no migration or no table"]
    assert ac.static_data_check(None, lambda p: "")["ok"] is False
    assert ac.static_data_check(dict(STATIC, table="BG_STATIC_TBL"), lambda p: MIGS.get(p))["ok"]       # case-insensitive
    assert not ac.static_data_check(dict(STATIC, table="bg_static"), lambda p: MIGS.get(p))["ok"]       # a prefix of the name is not the table


def test_the_real_declaration_for_bg_gochara_citation_resolution_names_565_630_631_and_they_check_out_on_this_branch():
    d = ac.load_asset_declarations()["bg_gochara_citation_resolution"]
    assert [m.split("_")[0] for m in d["static_data"]["migrations"]] == ["565", "630", "631"] and d["static_data"]["table"] == "bg_gochara_citation_resolution"
    bw = ac._lint_module("build_window")
    rd = bw.WindowReader(ac.ROOT, env=ac._git_env(), ref="HEAD")
    chk = ac.static_data_check(d["static_data"], rd.file_at_main, {"bg_gochara_citation_resolution"})
    assert chk["ok"] and len(chk["files"]) == 3, chk
    assert [a for a, e in ac.load_asset_declarations().items() if "static_data" in e] == ["bg_gochara_citation_resolution"]      # bg_sarvatobhadra_grid declares no edge: the rule never applied to it


def test_the_rule_rows_and_causes_are_registered_with_the_R_d_decision_text():
    for crit, cause in (("Build.completion", "service-no-writer-no-count-sql"), ("Build.count_integrity", "service-no-writer-no-count-sql"), ("Build.dep_liveness", "static-data-existence-only")):
        assert cause in ac.NA_CAUSES[crit] and ac.NA_RULE_DECISIONS[f"{crit}#measured:{cause}"].startswith("SS 2026-10-05 R-d"), (crit, cause)


def test_a_forged_static_record_is_not_released():
    base = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])
    rec = dict(v=NA, cause="static-data-existence-only", measured="m")
    full = dict(base, static_data=True, declared_kind="static", migrations=["565_x.sql"], table="t", migrations_checked=True)
    assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer=base))
    for drop in ("static_data", "declared_kind", "migrations", "table", "migrations_checked"):
        assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer={k: v for k, v in full.items() if k != drop})), drop
    assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer=dict(full, migrations_checked=False)))
    assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer=dict(full, migrations=[])))
    assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer=dict(full, declared_kind="data")))
    assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer=dict(full, register_files=1)))
    assert ac.no_writer_na_problem("Build.dep_liveness", dict(rec, no_writer=full)) is None


def test_the_real_service_assets_still_agree_with_what_the_service_rule_needs():
    d = ac.load_asset_declarations()
    assert d["bg_ephemeris_engine"]["kind"] == d["bg_panchanga"]["kind"] == "service"
    assert all(d[a]["has_writer"] is False for a in ("bg_ephemeris_engine", "bg_panchanga", "bg_gochara_citation_resolution"))


def test_the_cell_text_names_what_is_checked_not_a_migration_owned_row(monkeypatch, tmp_path):
    m = _run(monkeypatch, tmp_path)
    for crit in ("Build.dag", "Build.dep_liveness"):
        txt = m[crit]["measured"]
        assert "migration-owned" not in txt and "named migrations exist on main and create/seed the declared table" in txt, (crit, txt)
    assert "migration-owned" not in ac.NA_RULE_DECISIONS["Build.dep_liveness#measured:static-data-existence-only"] and "migration that owns the row" not in ac.NA_RULE_DECISIONS["Build.dep_liveness#measured:static-data-existence-only"]
