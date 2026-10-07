"""test_formgap_static_read.py: FORM-GAP form 4 (SS N-191): the STATIC / VIEW asset form of `prose_none`.

`prose_checks` requires ONE observed WRITE before it accepts `prose_fields []` + `prose_none` (a scan that saw no write is not evidence of "no narration write"). An asset with no writer (bg_sarvatobhadra_grid:
zero rows by design, has_writer false) or whose writer runs no DDL / DML on a view (bo_samvada: vw_chart_digest) can never produce that write, so it could never leave NO_DETECTOR. `static_read` accepts
ONE observed READ in its place, CHECKED against the live schema and data:
  * mode `zero_rows`  : the table holds NO row (a bounded `SELECT EXISTS`); a row is a FAIL (the declaration says empty by design); every text column of an empty table is then exempt;
  * mode `closed_read`: the asset's closed columns are read live (the existing closure reads) in place of the write; a view's columns / closed values are verified by that read.
It applies only to a declared kind `static` / `view` and only while the facts hold: the writer scope contains no write to the asset's tables, or no writer exists and the declaration and the registry row agree on
has_writer false. A writer that DOES write the asset's tables contradicts the declaration (FAIL).
Real DDL (migrations 529, 325, 204) on a disposable PostgreSQL; the view is the writer's own `_CREATE_VIEW_CLEAN` statement, read by AST.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import CHART_A, CHART_B, NA, FAIL, NO_DET, CELLS  # noqa: E402

SG_EV = "platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql:65"
VIEW_EV = "platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py:62"


def _sr(mode="zero_rows", **kw):
    d = dict(mode=mode, why="the asset has no writer and its table is empty by design, so one live read stands in for the observed write", evidence=SG_EV)
    d.update(kw)
    return d


def _decl(sr=None, kind="static", has_writer=False, closed=(), **extra):
    d = {"kind": kind, "prose_fields": [], "evidence": {"prose_fields": fs.EV}, "prose_none": dict(why=fs.WHY, closed_columns=list(closed), static_read=sr or _sr())}
    if has_writer is not None:
        d["has_writer"] = has_writer
    d.update(extra)
    return d


# ───────────────────────────── the validator ─────────────────────────────

def test_the_declaration_is_sound_and_the_fields_are_closed():
    assert ac.prose_none_problem(_decl()) is None and ac.prose_none_problem(_decl(_sr("closed_read"))) is None
    assert ac.STATIC_READ_FIELDS == ("mode", "why", "evidence") and ac.STATIC_READ_MODES == ("zero_rows", "closed_read") and "static_read" in ac.PROSE_NONE_DECL_FIELDS


@pytest.mark.parametrize("bad,needle", [
    (dict(mode="open_read"), "mode must be one of"),
    (dict(mode=None), "mode must be one of"),
    (dict(why="tbd"), "static_read.why"),
    (dict(evidence="unverified: it just has no writer"), "static_read.evidence"),
    (dict(evidence="platform/nowhere/none.sql:1"), "static_read.evidence"),
    (dict(extra=1), "exactly the fields"),
])
def test_a_malformed_static_read_is_refused(bad, needle):
    sr = _sr()
    for k, v in bad.items():
        sr[k] = v
    got = ac.prose_none_problem(_decl(sr))
    assert got is not None and needle in got, got
    for missing in ("mode", "why", "evidence"):
        assert "exactly the fields" in ac.prose_none_problem(_decl({k: v for k, v in _sr().items() if k != missing}))
    assert "must be an object" in ac.prose_none_problem(_decl("zero_rows"))


def test_static_read_is_incompatible_with_a_written_column_scope():
    d = _decl()
    d["prose_none"]["column_scope"] = "written"
    assert "cannot beside column_scope" in ac.prose_none_problem(d)


# ───────────────────────────── the facts that make an asset static ─────────────────────────────

F = ac.formgap_static_facts


COMPLETE = dict(complete=True, why=None, hit=[])
VIEW = lambda: _decl(_sr("closed_read"), kind="view", has_writer=None)      # noqa: E731


def test_a_writer_scope_that_writes_none_of_the_assets_tables_applies_when_the_scan_is_complete():
    got = F("bo_samvada", VIEW(), dict(has_writer=True), ["bo_samvada.py"], {}, COMPLETE)
    assert got["applies"] is True and "no write" in got["via"]


def test_FORGERY_an_unproven_empty_write_scan_never_applies():
    """Review fix HIGH 4: written == {} is the answer of a scan that may have been cut short or unable to read a write; it must not release the asset."""
    for scan, needle in ((None, "was not made"), (dict(complete=False, why="the delegation chain of the writer is cut (x)", hit=[]), "not shown complete"), ({}, "not shown complete")):
        got = F("bo_samvada", VIEW(), dict(has_writer=True), ["bo_samvada.py"], {}, scan)
        assert got["applies"] is False and needle in got["why"], (scan, got)
    got = F("bo_samvada", VIEW(), dict(has_writer=True), ["bo_samvada.py"], {}, dict(complete=True, why=None, hit=["vw_chart_digest"]))
    assert got["applies"] is False and got["contradicted"] is True and "deletes from or truncates" in got["why"]


def test_FORGERY_zero_rows_is_refused_for_an_asset_a_registered_writer_exists_for():
    got = F("bg_sarvatobhadra_grid", _decl(has_writer=None), dict(has_writer=True), ["x.py"], {}, COMPLETE)
    assert got["applies"] is False and "zero_rows is for an asset with no writer" in got["why"]


def test_a_writer_that_writes_the_assets_tables_contradicts_the_declaration():
    got = F("bo_samvada", VIEW(), dict(has_writer=True), ["bo_samvada.py"], {"vw_chart_digest": {"x"}}, COMPLETE)
    assert got == dict(applies=False, contradicted=True, why="the writer scope writes ['vw_chart_digest']: an asset a writer fills is not a static / view asset")


def test_unreadable_writes_never_apply():
    got = F("bo_samvada", VIEW(), dict(has_writer=True), ["bo_samvada.py"], None, COMPLETE)
    assert got["applies"] is False and "could not be read" in got["why"]


def test_the_asset_kind_must_be_static_or_view():
    for kind in ("data", "service", None):
        got = F("a", _decl(kind=kind), dict(has_writer=False), [], None)
        assert got["applies"] is False and "kind `static` or `view`" in got["why"], kind


def test_no_writer_file_needs_the_declaration_and_the_registry_to_agree_and_no_register_call(monkeypatch):
    monkeypatch.setattr(ac, "register_call_mentions", lambda aid: [])
    ok = F("bg_sarvatobhadra_grid", _decl(), dict(has_writer=False), [], None)
    assert ok["applies"] is True and "no @register writer exists" in ok["via"]
    assert F("a", _decl(has_writer=None), dict(has_writer=False), [], None)["applies"] is False             # the declaration does not say has_writer false
    assert F("a", _decl(has_writer=True), dict(has_writer=False), [], None)["applies"] is False
    assert F("a", _decl(), dict(has_writer=True), [], None)["applies"] is False                             # the registry row says it has a writer
    monkeypatch.setattr(ac, "register_call_mentions", lambda aid: ["platform/python-sidecar/x.py"])
    assert F("a", _decl(), dict(has_writer=False), [], None)["applies"] is False                            # a register( call names the asset
    assert F("a", {"kind": "static", "prose_fields": [], "prose_none": dict(why=fs.WHY, closed_columns=[])}, dict(has_writer=False), [], None) is None      # no static_read declared


# ───────────────────────────── mode zero_rows on the real table of bg_sarvatobhadra_grid ─────────────────────────────

SG = "bg_sarvatobhadra_grid"


@pytest.fixture()
def sg(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, SG)
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "529_bg_sarvatobhadra_grid.sql", SG))
    yield pg
    fs.drop_tables(pg, SG)


def _measure_sg(pg, monkeypatch, decl=None, registry=None, files=()):
    monkeypatch.setattr(ac, "register_call_mentions", lambda aid: [])
    return fs.measure(SG, pg, monkeypatch, list(files), SG, [SG], decl or _decl(), registry=dict({"has_writer": False}, **(registry or {})))


def test_REAL_SQL_an_empty_static_table_with_no_writer_reads_na_on_all_six_through_the_observed_read(sg, monkeypatch):
    got = _measure_sg(sg, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["forms"]["static_read"] == dict(mode="zero_rows", verified=True, rows={SG: 0}, via="no @register writer exists; the declaration and the registry row agree on has_writer false, and no register( call names the asset")
    assert b["open"] == [] and b["closed"] == [] and "FORM-GAP forms CHECKED: static_read" in got["Narr.agree"]["measured"]


def test_REAL_SQL_the_same_asset_without_the_form_is_the_old_no_detector(sg, monkeypatch):
    d = _decl()
    del d["prose_none"]["static_read"]
    got = _measure_sg(sg, monkeypatch, d)
    assert all(got[c]["v"] == NO_DET and "its writes could not be read" in got[c]["measured"] for c in CELLS)


def test_MUTATION_a_row_in_the_table_declared_empty_by_design_is_a_FAIL(sg, monkeypatch):
    fs.psql(sg, f"INSERT INTO {SG} (school_tag, cell_index, cell_kind, cell_value, table_version) VALUES ('x', 1, 'vedha_pair', 'a free sentence', 'v1')")
    got = _measure_sg(sg, monkeypatch)
    assert got["Narr.agree"]["v"] == FAIL and "holds at least 1 row but is declared empty by design" in got["Narr.agree"]["measured"]
    assert all(got[c]["v"] == NO_DET for c in CELLS[1:])


def test_MUTATION_the_registry_or_the_declaration_saying_there_is_a_writer_withdraws_the_release(sg, monkeypatch):
    got = _measure_sg(sg, monkeypatch, registry=dict(has_writer=True))
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "do not both say has_writer false" in got["Narr.agree"]["measured"] and "static_read does not apply" in got["Narr.agree"]["measured"]
    got = _measure_sg(sg, monkeypatch, _decl(has_writer=None))
    assert all(got[c]["v"] == NO_DET for c in CELLS)
    got = _measure_sg(sg, monkeypatch, _decl(kind="data"))
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "kind `static` or `view`" in got["Narr.agree"]["measured"]
    monkeypatch.setattr(ac, "register_call_mentions", lambda aid: ["platform/python-sidecar/x.py"])
    got = fs.measure(SG, sg, monkeypatch, [], SG, [SG], _decl(), registry=dict(has_writer=False))
    assert all(got[c]["v"] == NO_DET for c in CELLS)


def test_REAL_SQL_a_writer_that_writes_the_table_makes_the_declaration_a_FAIL(sg, monkeypatch):
    monkeypatch.setattr(ac, "written_columns", lambda units, tables: {SG: {"cell_value"}})
    point_psql_at(sg, monkeypatch)
    cat = ac.catalog([SG])
    vocab = ac.prose_vocabulary({SG: _decl()}, {SG: {SG}})
    got = ac._measure_prose(SG, _decl(), dict(target_table=SG, has_writer=True), ["ga_transit_anchors.py"], cat, [], {}, (), vocab)
    assert got["Narr.agree"]["v"] == FAIL and "an asset a writer fills is not a static / view asset" in got["Narr.agree"]["measured"]


def test_REAL_SQL_a_view_or_table_the_census_role_may_not_read_is_no_detector(sg, monkeypatch):
    def boom(q):
        raise ac.Unknown("ERROR:  permission denied for table bg_sarvatobhadra_grid")
    forms = None
    monkeypatch.setattr(ac, "scalar", boom)
    tables = {SG: (["id", "cell_value"], {"id": "bigint", "cell_value": "text"}, None)}
    d = _decl()
    forms = ac.formgap_reads(SG, d, tables, SG, udts={})
    forms["static_facts"] = dict(applies=True, via="x")
    got = ac.grade_prose_none(SG, d, tables, SG, {}, forms=forms)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "was not read" in got["Narr.agree"]["measured"]


def test_the_read_is_one_bounded_exists_that_stops_at_the_first_row():
    sql = ac.static_rows_sql(SG, None)
    assert sql == f'SELECT EXISTS (SELECT 1 FROM "{SG}")::text'
    assert "count(" not in sql and "ORDER BY" not in sql
    assert ac.static_rows_sql("t", dict(column="k", equals="v")).startswith('SELECT EXISTS (SELECT 1 FROM "t" WHERE "k"::text = \'v\')')


def test_a_zero_rows_read_is_global_the_measured_chart_scope_never_hides_a_row(sg, monkeypatch):
    """Zero rows by design is a claim about the WHOLE table: a chart scope that happens to exclude the one row must not make it read empty."""
    fs.psql(sg, f"INSERT INTO {SG} (school_tag, cell_index, cell_kind, cell_value, table_version) VALUES ('x', 1, 'vedha_pair', 'v', 'v1')")
    ac.set_read_scope({SG: dict(where="false", label="excludes everything")})
    try:
        assert ac.scalar(ac.static_rows_sql(SG, None)).strip() == "true"
    finally:
        ac.set_read_scope(None)


# ───────────────────────────── mode closed_read on the real view of bo_samvada ─────────────────────────────

VIEW_SRC_TABLES = [("bodha_msr_signals", fs.MIG / "325_l2_bodha_enriched_schema.sql"), ("bodha_contradictions", fs.MIG / "325_l2_bodha_enriched_schema.sql"),
                   ("bodha_convergence", fs.MIG / "325_l2_bodha_enriched_schema.sql"), ("bodha_rm_resonances", fs.MIG / "325_l2_bodha_enriched_schema.sql"),
                   ("synthesis_quality_scorecard", fs.MIG / "325_l2_bodha_enriched_schema.sql"), ("chart_facts", fs.SMIG / "204_chart_facts.sql")]


def _view_sql():
    """The view statement exactly as the writer holds it (a module-level string literal, read by AST: nothing is imported or run)."""
    tree = ast.parse((fs.REPO / "platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py").read_text(encoding="utf-8"))
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_CREATE_VIEW_CLEAN" for t in n.targets):
            return ast.literal_eval(n.value)
    raise AssertionError("_CREATE_VIEW_CLEAN not found")


@pytest.fixture()
def view(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, "vw_chart_digest")
    fs.psql(pg, "DROP VIEW IF EXISTS vw_chart_digest")
    fs.drop_tables(pg, *[t for t, _ in VIEW_SRC_TABLES])
    for t, path in VIEW_SRC_TABLES:
        fs.psql(pg, fs.create_table_ddl(path, t))
        # the view reads a handful of columns; the other NOT NULL columns of the real tables are relaxed so a fixture row needs only those (names and types stay the real ones)
        fs.psql(pg, f"DO $$ DECLARE r record; BEGIN FOR r IN SELECT column_name c FROM information_schema.columns WHERE table_name = '{t}' AND is_nullable = 'NO' AND column_name NOT IN "
                    f"(SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) WHERE i.indrelid = '{t}'::regclass AND i.indisprimary) LOOP "
                    f"EXECUTE format('ALTER TABLE {t} ALTER COLUMN %I DROP NOT NULL', r.c); END LOOP; "
                    f"FOR r IN SELECT a.attname c FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) WHERE i.indrelid = '{t}'::regclass AND i.indisprimary AND a.atttypid = 'uuid'::regtype LOOP "
                    f"EXECUTE format('ALTER TABLE {t} ALTER COLUMN %I SET DEFAULT gen_random_uuid()', r.c); END LOOP; END $$")
    fs.psql(pg, _view_sql())
    yield pg
    fs.psql(pg, "DROP VIEW IF EXISTS vw_chart_digest")
    fs.drop_tables(pg, *[t for t, _ in VIEW_SRC_TABLES])


AYAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
DOMAINS = ["career", "character", "education", "family", "general", "health", "progeny", "relationship", "residence", "spirituality", "transition", "travel", "wealth"]
GRAHA_SUBJECT = {"SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury", "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn"}


def _seed_view(pg, chart=CHART_A, ayas=AYAS):
    for a in ayas:
        for i in range(3):
            fs.psql(pg, f"INSERT INTO bodha_msr_signals (signal_id, chart_id, ayanamsha_id, signal_type_class, computed_salience) VALUES (gen_random_uuid(), '{chart}', '{a}', "
                        f"'{['yoga', 'dosha', 'position'][i]}', {0.2 * (i + 1)})")
        for k, (subj, g) in enumerate(GRAHA_SUBJECT.items()):
            fs.psql(pg, f"INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) VALUES "
                        f"('{chart}|{a}|{subj}', '{chart}', '{a}', 'graha_shadbala_total', '{subj}', 'rupa', {5 + k})")
        fs.psql(pg, f"INSERT INTO bodha_rm_resonances (chart_id, ayanamsha_id, graha, weakest_rank_in_chart, remedy_priority_class) VALUES ('{chart}', '{a}', 'Sun', 1, 'critical')")
        for j, dom in enumerate(DOMAINS[:5]):
            fs.psql(pg, f"INSERT INTO bodha_convergence (chart_id, ayanamsha_id, snapshot_type, domain, convergence_score, convergence_count) VALUES ('{chart}', '{a}', 'static_natal', '{dom}', {1 - j * 0.1}, {5 - j})")


def _bo_decl(static=True, **kw):
    d = {k: v for k, v in ac.load_asset_declarations()["bo_samvada"].items()}
    d = json.loads(json.dumps(d))
    d["kind"] = "view"
    d["prose_none"].pop("static_read", None)                         # the committed declaration (1.41.0) carries it: each test states its own
    if static:
        d["prose_none"]["static_read"] = dict(mode="closed_read", why="the asset is a view its writer never writes, so the live read of its closed columns stands in for the write", evidence=VIEW_EV)
    d.update(kw)
    return d


def _measure_view(pg, monkeypatch, decl, scope=None):
    scope = {"vw_chart_digest": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")} if scope is None else scope
    return fs.measure("bo_samvada", pg, monkeypatch, ac.registered_ids("")["bo_samvada"], "vw_chart_digest", ["vw_chart_digest"], decl, scope=scope, registry=dict(has_writer=True))


def test_REAL_SQL_the_writers_own_view_statement_runs_on_the_real_source_ddl(view):
    _seed_view(view)
    assert fs.psql(view, f"SELECT count(*) FROM vw_chart_digest WHERE chart_id = '{CHART_A}'").strip() == "5"
    assert fs.psql(view, f"SELECT DISTINCT weakest_graha FROM vw_chart_digest WHERE chart_id = '{CHART_A}'").strip() == "Sun"


def test_REAL_SQL_without_the_form_the_view_asset_is_no_detector_and_with_it_the_closed_read_decides(view, monkeypatch):
    _seed_view(view)
    old = _measure_view(view, monkeypatch, _bo_decl(static=False))
    assert all(old[c]["v"] == NO_DET and "its writes could not be read" in old[c]["measured"] for c in CELLS)            # the bug this form fixes
    got = _measure_view(view, monkeypatch, _bo_decl())
    fs.all_na(got)
    assert got["Narr.agree"]["prose_none"]["forms"]["static_read"]["mode"] == "closed_read" and "static_read" in got["Narr.agree"]["measured"]
    assert sorted(x["column"] for x in got["Narr.agree"]["prose_none"]["closed"]) == ["ayanamsha_id", "top_convergence_domains", "top_priority_class", "weakest_graha"]


def test_REAL_SQL_MUTATION_a_closed_value_outside_its_vocabulary_in_the_view_is_a_FAIL(view, monkeypatch):
    _seed_view(view)
    fs.psql(view, f"UPDATE bodha_rm_resonances SET remedy_priority_class = 'urgent' WHERE chart_id = '{CHART_A}' AND ayanamsha_id = 'raman'")
    got = _measure_view(view, monkeypatch, _bo_decl())
    assert got["Narr.agree"]["v"] == FAIL and "vw_chart_digest.top_priority_class" in got["Narr.agree"]["measured"]
    fs.psql(view, f"UPDATE bodha_rm_resonances SET remedy_priority_class = 'critical'")
    fs.psql(view, f"UPDATE bodha_convergence SET domain = 'made_up_domain' WHERE domain = 'career'")
    got = _measure_view(view, monkeypatch, _bo_decl())
    assert got["Narr.agree"]["v"] == FAIL and "top_convergence_domains" in got["Narr.agree"]["measured"]


def test_REAL_SQL_MUTATION_a_view_that_gains_an_open_text_column_is_no_longer_declared_closed(view, monkeypatch):
    _seed_view(view)
    fs.psql(view, "DROP VIEW vw_chart_digest")
    fs.psql(view, _view_sql().replace("NOW()                                                            AS digest_at", "NOW() AS digest_at, 'a note about the sun' AS free_note"))
    got = _measure_view(view, monkeypatch, _bo_decl())
    assert got["Narr.agree"]["v"] == FAIL and "free_note" in got["Narr.agree"]["measured"] and "open text column" in got["Narr.agree"]["measured"]


def test_REAL_SQL_a_chart_with_no_row_in_the_view_is_vacuous_not_a_pass(view, monkeypatch):
    _seed_view(view, chart=CHART_B)
    scope = {"vw_chart_digest": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart", block="no rows in the read scope: nothing to judge")}
    got = _measure_view(view, monkeypatch, _bo_decl(), scope=scope)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "nothing to judge" in got["Narr.agree"]["measured"]


def test_REAL_SQL_two_charts_the_closed_read_judges_the_measured_chart_only(view, monkeypatch):
    _seed_view(view, chart=CHART_A)
    _seed_view(view, chart=CHART_B)
    fs.psql(view, f"UPDATE bodha_rm_resonances SET remedy_priority_class = 'urgent' WHERE chart_id = '{CHART_B}'")
    assert _measure_view(view, monkeypatch, _bo_decl())["Narr.agree"]["v"] == NA                                           # chart B's drifted label is not the measured chart's
    other = {"vw_chart_digest": dict(where=f"chart_id = '{CHART_B}'", label="the other chart")}
    assert _measure_view(view, monkeypatch, _bo_decl(), scope=other)["Narr.agree"]["v"] == FAIL


def test_the_rollup_guard_refuses_a_static_read_block_it_cannot_trust(view, monkeypatch):
    _seed_view(view)
    rec = _measure_view(view, monkeypatch, _bo_decl())["Narr.agree"]
    assert ac.prose_none_na_problem("Narr.agree", rec) is None
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["static_read"]["verified"] = False
    assert "not a verified read" in ac.prose_none_na_problem("Narr.agree", forged)
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["static_read"]["via"] = ""
    assert "not a verified read" in ac.prose_none_na_problem("Narr.agree", forged)
    zero = dict(mode="zero_rows", verified=True, rows={}, via="x")
    assert ac.formgap_block_problem(dict(static_read=zero)) is not None                                                   # a zero_rows entry names every table at 0 rows
    assert ac.formgap_block_problem(dict(static_read=dict(zero, rows={"t": 3}))) is not None
    assert ac.formgap_block_problem(dict(static_read=dict(zero, rows={"t": 0}))) is None


# ───────────────────────────── the completeness of the writer scan (review fix HIGH 4) ─────────────────────────────

def _units(monkeypatch, src, beyond=()):
    import ast
    import textwrap
    tree = ast.parse(textwrap.dedent(src))
    unit = dict(rel="platform/python-sidecar/pipeline/orchestrator/writers/fake.py", path=pathlib.Path("fake.py"), tree=tree, nodes=list(tree.body), hop=0, via="fake.py")
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None: ([unit], list(beyond)))


def test_FORGERY_the_complete_scan_names_what_it_could_not_resolve(monkeypatch):
    scan = ac.static_write_scan
    _units(monkeypatch, "def run(ctx):\n    ctx.db_conn.cursor().execute('SELECT 1')\n")
    assert scan("a", ["fake.py"], ["vw_chart_digest"]) == dict(complete=True, why=None, hit=[])
    _units(monkeypatch, "def run(ctx):\n    t = ctx.config['t']\n    ctx.db_conn.cursor().execute(f'INSERT INTO {t} (a) VALUES (1)')\n")
    got = scan("a", ["fake.py"], ["vw_chart_digest"])
    assert got["complete"] is False and "table the scan cannot resolve" in got["why"]
    _units(monkeypatch, "def run(ctx):\n    sql = build()\n    ctx.db_conn.cursor().execute(sql)\n")
    got = scan("a", ["fake.py"], ["vw_chart_digest"])
    assert got["complete"] is False and "not a literal" in got["why"]
    _units(monkeypatch, "def run(ctx):\n    pass\n", beyond=["helpers.py"])
    got = scan("a", ["fake.py"], ["vw_chart_digest"])
    assert got["complete"] is False and "delegation chain" in got["why"]
    _units(monkeypatch, "def run(ctx):\n    ctx.db_conn.cursor().execute('DELETE FROM vw_chart_digest WHERE chart_id = %s', (1,))\n")
    assert scan("a", ["fake.py"], ["vw_chart_digest"]) == dict(complete=True, why=None, hit=["vw_chart_digest"])
    _units(monkeypatch, "def run(ctx):\n    ctx.db_conn.cursor().execute('TRUNCATE TABLE public.vw_chart_digest')\n")
    assert scan("a", ["fake.py"], ["vw_chart_digest"])["hit"] == ["vw_chart_digest"]


def test_FORGERY_a_view_asset_whose_writer_writes_through_an_unresolved_table_reads_no_detector_end_to_end(view, monkeypatch):
    from test_formgap_decl_static import _m_bo, _own
    _seed_view(view)
    _units(monkeypatch, "def run(ctx):\n    t = ctx.config['t']\n    ctx.db_conn.cursor().execute(f'INSERT INTO {t} (a) VALUES (1)')\n")
    monkeypatch.setattr(ac, "written_columns", lambda units, tables: {})                    # the column scan alone sees no write (it skips a table it cannot name)
    got = _m_bo(view, monkeypatch, _own("bo_samvada"))
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "not shown complete" in got["Narr.agree"]["measured"]
