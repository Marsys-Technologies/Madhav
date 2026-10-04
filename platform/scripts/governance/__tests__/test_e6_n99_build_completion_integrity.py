"""test_e6_n99_build_completion_integrity.py — SS ruling N-99 (Track A finding Q-L4-18; stricter-only), registry pin 25.

Build.completion (revision 3) must NOT read PASS on count equality alone when the asset DECLARES an `integrity_check_sql`: the
declared SQL must ALSO hold (the engine's own convention, asset_runner._probe_asset: one statement, no bind parameters, first column of
the first row true), else the cell reads PARTIAL naming which failed. Motivating cases: ph_pratikara (536 = 536 over empty programmes) and
ph_phaladesa (13 = 13).

Real Postgres: a DISPOSABLE loopback cluster (_disposable_pg.py; never production, no credentials). The integrity SQL runs through the census's
own `psql_read_only` against it; the rest of measure() is stubbed exactly as test_r99_empty_table_agreeing_build_record.py does.

SECURITY PASS (independent review of PR #3038, S1-S4): the SERVER is the independent guard. The stored SQL runs only wrapped as a subquery
(`SELECT * FROM (<sql>\n) AS _integrity LIMIT 1`), so a `;` / COMMIT / BEGIN / SET / DML / second statement is a syntax error at the server
whatever the client lexer missed; the lexer itself is conservative (`--` ends at \n or \r, `$` after any identifier character incl. non-ASCII,
no \r / NUL / non-ASCII / backslash outside literals, no quoted function names); the session is default-read-only so a transaction boundary that
got through still opens read-only. A seeded FUZZ over the review alphabet runs on a real NON-superuser login that OWNS the guarded objects (so only the
server guards stand between it and a write). Every reviewer repro is a named test; each guard has a source-patched mutant.

Guards and the test that has teeth for each (mutation tests at the end re-run the scenario with the guard removed and assert the defect
returns, so a test that could not fail is itself caught):
  * integrity step        -> count equal + integrity false must be PARTIAL            (mutation: step bypassed -> PASS)
  * pre-flight allow-list -> DML / multi-statement / COPY / write function never reach psql  (mutation: validator off, plain psql -> data WRITTEN)
  * READ ONLY transaction -> with the allow-list bypassed, the server still refuses the write (nothing written)
  * error / timeout       -> PARTIAL with the reason, census continues
  * no declared SQL       -> byte-identical record, psql_read_only never called
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture: a throw-away loopback Postgres)


# ───────────────────────── the offline measure() harness (as test_r99_*) ─────────────────────────

def _reg_row(aid, integrity_sql=None, has_integrity=True, target_floor="5"):
    return dict(asset_id=aid, has_writer=True, target_table="ga_t", count_sql="SELECT count(*) FROM ga_t",
                has_integrity=has_integrity, integrity_sql=integrity_sql, depends_on=[], target_floor=target_floor,
                catalog_status="CURRENT", asset_kind="data")


_REC = dict(state="lit", rows_written="5", rps="", last_built="2026-09-01", n_rows=1, ambiguous=False,
            _key=(0.0, 0.0), built_epoch="0", duration=None)
_TABLE = {"ga_t": (["id", "v"], [])}


def _stub_layer(monkeypatch, ctrl, reg, live=5, rec=None):
    rec = dict(_REC if rec is None else rec)
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg), excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(_TABLE), cols={t: c for t, (c, _k) in _TABLE.items()},
                                                       keys={t: k for t, (_c, k) in _TABLE.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: live for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {"": dict(rec)} for aid in reg})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def _cell(census, aid, crit="Build.completion"):
    return next(a for a in census["assets"] if a["asset_id"] == aid)["measurements"][crit]


@pytest.fixture
def pg(disposable_pg, monkeypatch):
    """The census's own psql subprocesses reach the DISPOSABLE cluster only; identity proved; a guard table, a sequence and an
    empty 'programme' table are the things a bad integrity SQL could touch."""
    point_psql_at(disposable_pg, monkeypatch)
    ident = ac.psql("SELECT inet_server_port()::text, current_database()")
    assert ident == [[str(disposable_pg.port), disposable_pg.dbname]], f"refusing to run: not the disposable cluster ({ident!r})"
    disposable_pg.psql("DROP TABLE IF EXISTS t_guard, t_prog, t_new CASCADE; DROP SEQUENCE IF EXISTS seq_guard; "
                       "CREATE TABLE t_guard(id int); INSERT INTO t_guard SELECT generate_series(1,3); "
                       "CREATE TABLE t_prog(id int); CREATE SEQUENCE seq_guard;")
    return disposable_pg


def _untouched(pg):
    """Nothing the guard table / sequence / a would-be new table could show was changed."""
    assert pg.psql("SELECT count(*) FROM t_guard") == "3"
    assert pg.psql("SELECT last_value::text || is_called::text FROM seq_guard") == "1false"
    assert pg.psql("SELECT to_regclass('public.t_new') IS NULL") == "t"


class _Spy:
    """Records every SQL string a psql subprocess is handed (the closest observable to 'was it run')."""
    def __init__(self, monkeypatch):
        self.sent: list[str] = []
        real_run, real_popen = subprocess.run, subprocess.Popen

        def note(argv):
            if argv and str(argv[0]).endswith("psql"):
                self.sent += [argv[i + 1] for i, x in enumerate(argv) if x == "-c" and i + 1 < len(argv)]

        def run(argv, *a, **k):
            note(argv)
            return real_run(argv, *a, **k)

        def popen(argv, *a, **k):                    # the read-only path reads through a byte cap (Popen), not subprocess.run
            note(argv)
            return real_popen(argv, *a, **k)
        monkeypatch.setattr(ac.subprocess, "run", run)
        monkeypatch.setattr(ac.subprocess, "Popen", popen)

    def ran(self, needle: str) -> bool:
        return any(needle in s for s in self.sent)


def _run(monkeypatch, tmp_path, sql, *, live=5, rec=None, extra=None):
    reg = {"ph_x": _reg_row("ph_x", sql)}
    reg.update(extra or {})
    _stub_layer(monkeypatch, tmp_path, reg, live=live, rec=rec)
    return ac.measure("L4")


# ───────────────────────── the result convention (the engine's, with one stricter reading) ─────────────────────────

@pytest.mark.parametrize("rows,ok", [([["t"]], True), ([["true"]], True), ([["f"]], False), ([["false"]], False), ([[""]], False),
                                     ([["0"]], False), ([["3"]], True), ([["1"]], True), ([["0.0"]], False), ([[]], False), ([], False),
                                     ([["abc"]], False), ([["t", "f"]], True), ([["f", "t"]], False)])
def test_the_result_convention_first_column_of_first_row_truthy(rows, ok):
    assert ac._integrity_holds(rows)[0] is ok


# ───────────────────────── PASS / PARTIAL ─────────────────────────

def test_count_equal_and_integrity_holds_reads_pass(pg, monkeypatch, tmp_path):
    c = _cell(_run(monkeypatch, tmp_path, "SELECT count(*) = 3 FROM t_guard"), "ph_x")
    assert c["v"] == ac.PASS and "declared integrity_check_sql holds" in c["measured"], c


def test_count_equal_but_integrity_false_reads_partial_naming_it(pg, monkeypatch, tmp_path):
    c = _cell(_run(monkeypatch, tmp_path, "SELECT count(*) = 99 FROM t_guard"), "ph_x")
    assert c["v"] == ac.PARTIAL, c
    assert "rows_written=5 = live=5" in c["measured"] and "integrity_check_sql does NOT hold" in c["measured"] and "N-99" in c["measured"], c


def test_the_536_equals_536_over_empty_programmes_case(pg, monkeypatch, tmp_path):
    """ph_pratikara's shape: counts agree (rows_written = live) while the related programme set is EMPTY; the integrity SQL that says
    'a programme exists for every row' is false -> PARTIAL; once a programme exists it holds -> PASS. Equality alone proved nothing."""
    sql = "SELECT EXISTS (SELECT 1 FROM t_prog)"
    c = _cell(_run(monkeypatch, tmp_path, sql, live=536, rec=dict(_REC, rows_written="536")), "ph_x")
    assert c["v"] == ac.PARTIAL and "rows_written=536 = live=536" in c["measured"] and "does NOT hold" in c["measured"], c
    pg.psql("INSERT INTO t_prog VALUES (1)")
    c = _cell(_run(monkeypatch, tmp_path, sql, live=536, rec=dict(_REC, rows_written="536")), "ph_x")
    assert c["v"] == ac.PASS, c


@pytest.mark.parametrize("sql,why", [
    ("SELECT count(*) FROM t_prog", "= 0"),                                  # a count of ZERO is not healthy (engine: bool(0) is False)
    ("SELECT NULL::boolean", "NULL"),
    ("SELECT true WHERE false", "no rows"),
    ("SELECT 'yes'", "neither a boolean nor a number"),                      # the engine's bool('yes') would pass this; the census does not
    ("SELECT false UNION ALL SELECT true", "'f'"),                           # FIRST row decides
])
def test_non_holding_results_read_partial(pg, monkeypatch, tmp_path, sql, why):
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    assert c["v"] == ac.PARTIAL and "does NOT hold" in c["measured"], c


def test_the_first_row_decides_when_it_holds(pg, monkeypatch, tmp_path):
    assert _cell(_run(monkeypatch, tmp_path, "SELECT true UNION ALL SELECT false"), "ph_x")["v"] == ac.PASS


# ───────────────────────── refused statements: never executed, never PASS ─────────────────────────

REFUSED = [
    "DELETE FROM t_guard",
    "INSERT INTO t_guard VALUES (9)",
    "UPDATE t_guard SET id = 0",
    "TRUNCATE t_guard",
    "DROP TABLE t_guard",
    "CREATE TABLE t_new(a int)",
    "SELECT true; DELETE FROM t_guard",                                      # multiple statements
    "SELECT true; SELECT true",
    "COPY t_guard TO '{copy_target}'",
    "WITH d AS (DELETE FROM t_guard RETURNING 1) SELECT true",               # data-modifying CTE
    "WITH i AS (INSERT INTO t_guard VALUES (9) RETURNING 1) SELECT true",
    "SELECT true INTO t_new",                                                # SELECT INTO creates a table
    "SELECT nextval('seq_guard') > 0",                                       # write-capable function
    "SELECT setval('seq_guard', 50) > 0",
    "SELECT set_config('default_transaction_read_only','off',false) = 'off'",
    "SELECT pg_advisory_lock(1) IS NULL",
    "SELECT pg_terminate_backend(pg_backend_pid())",
    "SELECT lo_import('/etc/hosts') > 0",
    "SELECT id FROM t_guard FOR UPDATE",                                     # row lock
    "SELECT query_to_xml('DELETE FROM t_guard', true, true, '') IS NOT NULL",
    "EXPLAIN ANALYZE DELETE FROM t_guard",
    "DO $$ BEGIN DELETE FROM t_guard; END $$",
    "VALUES (true)",                                                         # closed list: SELECT / WITH only
    "TABLE t_guard",
    "SELECT 'unterminated",
    "",
    "   ",
]


@pytest.mark.parametrize("sql", REFUSED)
def test_refused_sql_is_never_executed_and_never_reads_pass(pg, monkeypatch, tmp_path, sql):
    sql = sql.replace("{copy_target}", str(tmp_path / "copied.csv"))
    spy = _Spy(monkeypatch)
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    assert c["v"] == ac.PARTIAL and "REFUSED (never run)" in c["measured"], c
    marker = sql.split(";")[0].strip()[:30]
    if marker:
        assert not spy.ran(marker), f"the refused SQL reached a psql subprocess: {spy.sent}"
    assert not any("BEGIN READ ONLY" in s for s in spy.sent), "a refused SQL must not even open the read-only session"
    _untouched(pg)
    assert not (tmp_path / "copied.csv").exists()


def test_a_refused_sql_does_not_stop_the_census(pg, monkeypatch, tmp_path):
    census = _run(monkeypatch, tmp_path, "DELETE FROM t_guard", extra={"ph_y": _reg_row("ph_y", "SELECT true")})
    assert _cell(census, "ph_x")["v"] == ac.PARTIAL and _cell(census, "ph_y")["v"] == ac.PASS


# ───────────────────────── the read-only transaction is the SECOND, independent guard ─────────────────────────

@pytest.mark.parametrize("sql", [
    "WITH d AS (DELETE FROM t_guard RETURNING 1) SELECT true",
    "SELECT nextval('seq_guard') > 0",
    "SELECT true INTO t_new",
    "SELECT (SELECT count(*) FROM t_guard) > 0 AND set_config('x.y','1',false) IS NOT NULL",
])
def test_with_the_allow_list_bypassed_the_server_still_refuses_to_write(pg, monkeypatch, tmp_path, sql):
    monkeypatch.setattr(ac, "_integrity_statement", lambda s: (None, s))      # the pre-flight is OFF: only the server-side guards stand
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    if "set_config" in sql:
        return                                                                 # set_config('x.y') is a harmless session GUC, not a write
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"], c
    _untouched(pg)


# ───────────────────────── error / timeout: PARTIAL with the reason, the census continues ─────────────────────────

def test_a_sql_error_reads_partial_and_the_census_continues(pg, monkeypatch, tmp_path):
    census = _run(monkeypatch, tmp_path, "SELECT 1/0 = 1", extra={"ph_y": _reg_row("ph_y", "SELECT true")})
    c = _cell(census, "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"] and "division by zero" in c["measured"], c
    assert _cell(census, "ph_y")["v"] == ac.PASS


def test_a_missing_relation_reads_partial(pg, monkeypatch, tmp_path):
    c = _cell(_run(monkeypatch, tmp_path, "SELECT count(*) > 0 FROM no_such_table"), "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"], c


def test_an_unbound_parameter_is_an_error_as_in_the_engine(pg, monkeypatch, tmp_path):
    """The engine binds nothing (migration 1027): a `$1` is an error there, so it is not-holding here — never silently bound."""
    c = _cell(_run(monkeypatch, tmp_path, "SELECT count(*) > 0 FROM t_guard WHERE id = $1"), "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"], c


def test_a_timeout_reads_partial_and_the_census_continues(pg, monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "INTEGRITY_TIMEOUT_SECONDS", 1)
    t0 = time.time()
    census = _run(monkeypatch, tmp_path, "SELECT count(*) > 0 FROM generate_series(1, 2000000000)", extra={"ph_y": _reg_row("ph_y", "SELECT true")})
    assert time.time() - t0 < 7, "the timeout did not bound the run"
    c = _cell(census, "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"] and ("timeout" in c["measured"].lower() or "canceling" in c["measured"]), c
    assert _cell(census, "ph_y")["v"] == ac.PASS


def test_a_runner_surprise_is_an_outcome_not_an_exception(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise RuntimeError("psql vanished")
    monkeypatch.setattr(ac, "psql_read_only", boom)
    c = _cell(_run(monkeypatch, tmp_path, "SELECT true"), "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"] and "psql vanished" in c["measured"], c


# ───────────────────────── no declared integrity SQL: exactly as before ─────────────────────────

def test_no_declared_integrity_sql_is_byte_identical_and_never_runs_it(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(ac, "psql_read_only", lambda *a, **k: called.append(a) or [["f"]])
    old_shape = {"ph_x": {k: v for k, v in _reg_row("ph_x", None).items() if k != "integrity_sql"}}       # a registry row from before N-99
    _stub_layer(monkeypatch, tmp_path, old_shape)
    a = _cell(ac.measure("L4"), "ph_x")
    _stub_layer(monkeypatch, tmp_path, {"ph_x": _reg_row("ph_x", None, has_integrity=False)})
    b = _cell(ac.measure("L4"), "ph_x")
    assert a == b and a["v"] == ac.PASS and "integrity" not in a["measured"], (a, b)
    assert called == []


def test_a_declared_but_blank_sql_is_refused_not_ignored(monkeypatch, tmp_path):
    c = _cell(_run(monkeypatch, tmp_path, ""), "ph_x")
    assert c["v"] == ac.PARTIAL and "blank" in c["measured"], c


@pytest.mark.parametrize("over,want", [
    (dict(live=4), ac.FAIL),                                                  # rows_written 5 != live 4
    (dict(rec=dict(_REC, state="error")), ac.FAIL),                           # not a completed build
    (dict(live=0), ac.FAIL),                                                  # empty, floor not 0
])
def test_every_non_pass_branch_is_untouched_and_never_runs_the_sql(monkeypatch, tmp_path, over, want):
    called = []
    monkeypatch.setattr(ac, "psql_read_only", lambda *a, **k: called.append(a) or [["t"]])
    c = _cell(_run(monkeypatch, tmp_path, "SELECT true", **over), "ph_x")
    assert c["v"] == want and "integrity" not in c["measured"] and called == [], c


def test_the_integrity_sql_runs_only_when_the_cell_would_otherwise_pass(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(ac, "psql_read_only", lambda sql, *a, **k: called.append(sql) or [["t"]])
    _run(monkeypatch, tmp_path, "SELECT true")
    assert called == ["SELECT true"]


# ───────────────────────── the registry read carries the declared SQL text ─────────────────────────

def test_registry_read_carries_integrity_sql_text_null_blank_and_multiline(pg, monkeypatch):
    pg.psql("DROP TABLE IF EXISTS asset_registry; CREATE TABLE asset_registry(asset_id text, layer text, has_writer bool, target_table text, "
            "count_sql text, integrity_check_sql text, depends_on text[], target_floor int, catalog_status text, asset_kind text, "
            "is_active bool, dead_flag bool)")
    multi = "-- a comment\nSELECT\n  NOT EXISTS (SELECT 1 FROM t_prog WHERE 'a''b' = 'x')\n"
    pg.psql("INSERT INTO asset_registry(asset_id, layer, has_writer, target_table, count_sql, integrity_check_sql, depends_on, is_active) VALUES "
            "('ph_a','phala',true,'t_prog','SELECT 1',NULL,'{}',true), ('ph_b','phala',true,'t_prog','SELECT 1','','{}',true), "
            f"('ph_c','phala',true,'t_prog','SELECT 1',$q${multi}$q$,'{{}}',true)")
    reg, _ = ac.registry("L4")
    assert reg["ph_a"]["integrity_sql"] is None and reg["ph_a"]["has_integrity"] is False
    assert reg["ph_b"]["integrity_sql"] == "" and reg["ph_b"]["has_integrity"] is True
    assert reg["ph_c"]["integrity_sql"] == multi and reg["ph_c"]["has_integrity"] is True
    assert ac.integrity_sql_problem(reg["ph_c"]["integrity_sql"]) is None
    pg.psql("DROP TABLE asset_registry")


# ───────────────────────── the pre-flight allow-list on its own ─────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT 1", "select 1;", "SELECT 1 ;  ;", "(SELECT true)", "WITH a AS (SELECT 1 x) SELECT x = 1 FROM a",
    "SELECT ';' = ';'", "SELECT 'delete from x' <> ''", "SELECT $q$; DELETE FROM x$q$ <> ''", "SELECT $$a;b$$ <> ''",
    "-- ; DELETE\nSELECT 1", "/* ; DELETE /* nested */ ; */ SELECT 1",
    "SELECT count(*) FROM t WHERE updated_at IS NULL AND inserted_by = 'x'",           # identifiers that merely START with a verb
    "SELECT \"update\" FROM t", "SELECT pg_get_constraintdef(1) IS NOT NULL", "SELECT pg_typeof(1) IS NOT NULL",
    "SELECT E'it\\'s;' <> ''", "SELECT 'it''s; fine' <> ''", "SELECT substring('abc' from 1 for 2) = 'ab'",
])
def test_the_allow_list_accepts_a_single_read_only_select(sql):
    assert ac.integrity_sql_problem(sql) is None, ac.integrity_sql_problem(sql)


@pytest.mark.parametrize("sql,frag", [
    ("SELECT 1; SELECT 2", "more than one statement"), ("SELECT 1; DELETE FROM t", "more than one statement"),
    ("DELETE FROM t", "not a SELECT/WITH"), ("COPY t TO '/tmp/x'", "not a SELECT/WITH"), ("\\! rm -rf /", "backslash"),
    ("WITH d AS (DELETE FROM t RETURNING 1) SELECT 1", "DELETE"), ("SELECT 1 INTO x", "INTO"), ("SELECT 1 FROM t FOR UPDATE", "UPDATE"),
    ("SELECT 1 FROM t FOR SHARE", "SHARE"), ("SELECT nextval('s')", "nextval"), ("SELECT public.setval('s', 1)", "setval"),
    ("SELECT pg_read_file('/etc/passwd')", "pg_read_file"), ("SELECT dblink_exec('x','y')", "dblink_exec"), ("SELECT lo_unlink(1)", "lo_unlink"),
    ("SELECT pg_advisory_xact_lock(1)", "pg_advisory_xact_lock"), ("SELECT set_config('a','b',true)", "set_config"),
    ("SELECT pg_sleep(1)", "pg_sleep"),
    ("SELECT 'x", "unterminated"), ("SELECT 1 /* x", "unterminated"), ("SELECT $q$ x", "unterminated"), ("SELECT \"x", "unterminated"),
    ("", "blank"), (None, "blank"), (12, "blank"), (";", "no statement"),
    ("SELECT (1", "unbalanced"), ("SELECT 1)", "unbalanced"),
])
def test_the_allow_list_refuses_everything_else(sql, frag):
    why = ac.integrity_sql_problem(sql)
    assert why is not None and frag in why, (sql, why)


def _dollar_blobs(text):
    """Every dollar-quoted body in `text`, recursing into each (a `DO $$ ... dasha_check := $check$ SELECT ... $check$ ... $$` nests)."""
    import re
    for m in re.finditer(r"(\$[A-Za-z_]*\$)(.*?)\1", text, re.S):
        yield m.group(2)
        yield from _dollar_blobs(m.group(2))


_SELECTISH = None


def _migration_literals():
    """([(file, sql)], [files that ASSIGN integrity_check_sql but whose literal cannot be resolved statically]). Resolved: every dollar-quoted body
    (nested too) that starts with SELECT / WITH (after comments / an opening parenthesis) in a migration that mentions integrity_check_sql, and every
    `integrity_check_sql = '...'` single-quoted literal. Not resolvable statically: a value DERIVED from a stored one (replace(), ||, read-modify-write)."""
    import re
    global _SELECTISH
    _SELECTISH = _SELECTISH or re.compile(r"\s*(?:--[^\n]*\n\s*|/\*.*?\*/\s*)*\(?\s*(select|with)\b", re.I | re.S)
    lits, unresolved = [], []
    for f in sorted((HERE.parents[2] / "migrations").glob("*.sql")):
        t = f.read_text(encoding="utf-8", errors="replace")
        if "integrity_check_sql" not in t:
            continue
        got = [b for b in _dollar_blobs(t) if _SELECTISH.match(b)]
        got += [m.group(1).replace("''", "'") for m in re.finditer(r"integrity_check_sql\s*=\s*'((?:[^']|'')*)'", t)]
        lits += [(f.name, b) for b in got]
        if not got and re.search(r"\bintegrity_check_sql\s*=(?!=)", re.sub(r"--[^\n]*", "", t)):
            unresolved.append(f.name)
    return lits, unresolved


# files that assign integrity_check_sql only as a DERIVED value (replace(), ||, read-modify-write of the stored text): not statically resolvable.
# Their results are covered by the live read-only run of the stored text, not by this test.
DERIVED_ONLY_MIGRATIONS = {"1026_nirmana_l3_ka_service_selftest_clock_timestamp_fix.sql", "1027_nirmana_l2_bo_pramana_mapa_integrity_check_literal_chart.sql",
                           "1032_nirmana_l2_bo_grounding_set_based_integrity.sql", "1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql",
                           "1230_ka_gochara_registry_revert_1091_pin.sql",
                           "902_nirmana_l1_ga_condition_integrity_check_scope.sql"}


def test_every_integrity_sql_literal_in_the_migrations_passes_the_allow_list_except_oversize():
    """False refusals would be spurious downward moves. Every statically resolvable literal (all assignment forms: `= $tag$..$tag$`, `= '..'`,
    nested DO-block variables, INSERT ... VALUES bodies) is a single SELECT/WITH and is accepted; the ONLY refusal is the explicit oversize one
    (the ga_structural family: ~200 KB, past the 128 KiB per-argument OS cap, so its verdict cannot depend on the host)."""
    lits, unresolved = _migration_literals()
    assert len(lits) > 150, len(lits)
    refused = [(f, ac.integrity_sql_problem(b)) for f, b in lits if ac.integrity_sql_problem(b)]
    assert all("too large to run via psql -c" in why for _f, why in refused), [r for r in refused if "too large" not in r[1]][:5]
    assert {f.split("_")[0] for f, _ in refused} <= {str(n) for n in range(806, 842)} | {"904"}, sorted({f for f, _ in refused})
    assert set(unresolved) <= DERIVED_ONLY_MIGRATIONS, sorted(set(unresolved) - DERIVED_ONLY_MIGRATIONS)


def test_every_resolvable_literal_parses_when_wrapped_as_the_server_will_see_it(pg_np, monkeypatch):
    """The wrapped form must be valid SYNTAX for every real literal (a 42601 would turn a healthy check into 'could NOT be run'). Run on the
    disposable cluster: a missing relation / column is expected (the tables are not there); a syntax error never is."""
    lits, _ = _migration_literals()
    syntax, seen = [], 0
    for f, b in lits:
        if ac.integrity_sql_problem(b):
            continue
        seen += 1
        try:
            ac.psql_read_only(ac._integrity_statement(b)[1])
        except ac.Unknown as exc:
            if "42601" in str(exc) or "syntax error" in str(exc):
                syntax.append((f, str(exc)[:120]))
    assert seen > 140 and syntax == [], (seen, syntax[:5])


# ───────────────────────── one definition: the registry entry, the pin, count_integrity ─────────────────────────

def test_registry_entry_states_the_semantics_and_bumps_the_revision():
    e = ac.CRITERION_REGISTRY["Build.completion"]
    assert e["revision"] == 3 and "integrity_check_sql" in e["applicability"] and "PARTIAL" in e["applicability"]
    assert "READ ONLY" in e["applicability"] and "first column of its first row" in e["applicability"]
    assert ac.REGISTRY_REVISION >= 25


def test_count_integrity_stays_a_presence_check_and_does_not_double_define():
    e = ac.CRITERION_REGISTRY["Build.count_integrity"]
    assert e["revision"] == 1 and "present" in e["applicability"] or "always" in e["applicability"]
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert src.count("psql_read_only(_stmt)") == 1, "the integrity SQL must be run from ONE helper"


def test_consumers_read_the_census_cell_not_a_second_count_equality():
    """nikasha_certify, the E6.3 reader (asset_elevation_tracker) and the gap ledger consume the census CELL for Build.completion; none
    re-implements 'rows_written equals live' (grep found none), so a PARTIAL cell is what they all see."""
    root = HERE.parents[3]
    for f in (HERE.parent / "nikasha_certify.py", root / "00_ARCHITECTURE" / "control" / "asset_elevation_tracker.py"):
        t = f.read_text(encoding="utf-8")
        assert "rows_written" not in t.replace("rows_written=0 against a populated table is a status", ""), f.name


# ───────────────────────── mutation tests: each guard removed, the defect returns ─────────────────────────

def test_mutation_integrity_step_bypassed_count_equality_alone_reads_pass(pg, monkeypatch, tmp_path):
    sql = "SELECT count(*) = 99 FROM t_guard"
    assert _cell(_run(monkeypatch, tmp_path, sql), "ph_x")["v"] == ac.PARTIAL
    monkeypatch.setattr(ac, "_completion_integrity", lambda rec, r: rec)
    assert _cell(_run(monkeypatch, tmp_path, sql), "ph_x")["v"] == ac.PASS          # the N-99 defect, restored


def test_mutation_holds_reading_any_truthy_text_the_engine_way_passes_a_non_boolean(pg, monkeypatch, tmp_path):
    assert _cell(_run(monkeypatch, tmp_path, "SELECT 'yes'"), "ph_x")["v"] == ac.PARTIAL
    monkeypatch.setattr(ac, "_integrity_holds", lambda rows: (bool(rows and rows[0] and rows[0][0]), "mutant"))
    assert _cell(_run(monkeypatch, tmp_path, "SELECT 'yes'"), "ph_x")["v"] == ac.PASS


def test_mutation_allow_list_and_read_only_session_both_removed_the_write_lands(pg, monkeypatch, tmp_path):
    """Both guards off (validator returns None, the read-only path replaced by the plain one): the DELETE runs and the data is gone. This is the
    test of the tests: it proves `_untouched` above could fail, and that it is the two guards - not luck - that keep the data intact."""
    sql = "WITH d AS (DELETE FROM t_guard RETURNING 1) SELECT true"
    monkeypatch.setattr(ac, "_integrity_statement", lambda s: (None, s))
    monkeypatch.setattr(ac, "psql_read_only", lambda s, *a, **k: ac.psql(s))
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    assert c["v"] == ac.PASS
    assert pg.psql("SELECT count(*) FROM t_guard") == "0"                           # the guard table was emptied: both guards are load-bearing


def test_mutation_allow_list_only_removed_the_read_only_session_still_blocks(pg, monkeypatch, tmp_path):
    sql = "WITH d AS (DELETE FROM t_guard RETURNING 1) SELECT true"
    monkeypatch.setattr(ac, "_integrity_statement", lambda s: (None, s))
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    assert c["v"] == ac.PARTIAL
    assert pg.psql("SELECT count(*) FROM t_guard") == "3"


def test_mutation_read_only_session_removed_the_allow_list_still_blocks(pg, monkeypatch, tmp_path):
    spy = _Spy(monkeypatch)
    monkeypatch.setattr(ac, "psql_read_only", lambda s, *a, **k: ac.psql(s))
    c = _cell(_run(monkeypatch, tmp_path, "WITH d AS (DELETE FROM t_guard RETURNING 1) SELECT true"), "ph_x")
    assert c["v"] == ac.PARTIAL and "REFUSED" in c["measured"] and not spy.ran("DELETE")
    assert pg.psql("SELECT count(*) FROM t_guard") == "3"


def test_mutation_errors_escaping_would_kill_the_census(pg, monkeypatch, tmp_path):
    """The outcome helper swallows a runner exception into `unrunnable`; without that, one bad SQL raises out of measure()."""
    monkeypatch.setattr(ac, "psql_read_only", lambda *a, **k: (_ for _ in ()).throw(ac.Unknown("boom")))
    assert _cell(_run(monkeypatch, tmp_path, "SELECT true"), "ph_x")["v"] == ac.PARTIAL
    real = ac._integrity_outcome
    def unguarded(sql):
        return dict(state="holds", detail=str(ac.psql_read_only(sql)))
    monkeypatch.setattr(ac, "_integrity_outcome", unguarded)
    with pytest.raises(ac.Unknown):
        _run(monkeypatch, tmp_path, "SELECT true")
    monkeypatch.setattr(ac, "_integrity_outcome", real)


# ═════════════════════════ SECURITY PASS (review of PR #3038): the SERVER is the independent guard ═════════════════════════
import hashlib  # noqa: E402
import inspect  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
import textwrap  # noqa: E402

NP = "n99_np"          # a NON-superuser login that OWNS the guarded objects: only the server-side guards stand between it and a write


@pytest.fixture
def pg_np(pg, monkeypatch):
    """`pg` plus a non-superuser login that owns t_guard / seq_guard / t_audit and may CREATE in public (so a write, a sequence advance or a
    SELECT INTO would SUCCEED for it unless a guard stops it), and two objects it may NOT read (the census-role shapes: a table and a function)."""
    pg.psql(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{NP}') THEN CREATE ROLE {NP} LOGIN NOSUPERUSER; END IF; END $$")
    pg.psql(f"DROP TABLE IF EXISTS t_audit, charts CASCADE; DROP FUNCTION IF EXISTS bodha_signal_identity(); "
            f"CREATE TABLE t_audit(a int); ALTER TABLE t_guard OWNER TO {NP}; ALTER SEQUENCE seq_guard OWNER TO {NP}; ALTER TABLE t_audit OWNER TO {NP}; "
            f"ALTER TABLE t_prog OWNER TO {NP}; GRANT CREATE, USAGE ON SCHEMA public TO {NP}; "
            "CREATE TABLE charts(id int); REVOKE ALL ON charts FROM PUBLIC; "
            "CREATE FUNCTION bodha_signal_identity() RETURNS int LANGUAGE sql AS 'SELECT 1'; REVOKE EXECUTE ON FUNCTION bodha_signal_identity() FROM PUBLIC")
    monkeypatch.setenv("PGUSER", NP)
    assert ac.psql(f"SELECT current_user, (SELECT rolsuper FROM pg_roles WHERE rolname = current_user)::text") == [[NP, "false"]]
    return pg


def _state(pg):
    return pg.psql("SELECT concat_ws('|', (SELECT count(*) FROM t_guard), (SELECT last_value::text || is_called::text FROM seq_guard), "
                   "(SELECT count(*) FROM t_audit), to_regclass('public.t_new') IS NULL, (SELECT count(*) FROM pg_locks WHERE locktype = 'advisory'))")


CLEAN_STATE = "3|1false|0|t|0"


def _assert_clean(pg):
    assert _state(pg) == CLEAN_STATE


def _mutant(monkeypatch, fname, old, new):
    """Source-patch ONE guard out of `asset_census.<fname>` and install the result: the test then proves its scenario FAILS without the guard."""
    src = textwrap.dedent(inspect.getsource(getattr(ac, fname)))
    assert old in src, f"{fname}: the guarded line moved: {old!r}"
    ns = dict(vars(ac))
    exec(src.replace(old, new, 1), ns)           # noqa: S102 - test-only source mutation
    monkeypatch.setattr(ac, fname, ns[fname])


_OLD_MASK_SRC = r"""def _integrity_mask(sql: str) -> str:
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c == "-" and sql[i:i + 2] == "--":
            j = sql.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        elif c == "/" and sql[i:i + 2] == "/*":
            depth, j = 1, i + 2
            while j < n and depth:
                if sql[j:j + 2] == "/*":
                    depth, j = depth + 1, j + 2
                elif sql[j:j + 2] == "*/":
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            if depth:
                raise Unknown("unterminated /* comment")
            i = j
            out.append(" ")
        elif c == "'":
            esc = i > 0 and sql[i - 1] in "Ee" and (i < 2 or not (sql[i - 2].isalnum() or sql[i - 2] == "_"))
            j = i + 1
            while True:
                if j >= n:
                    raise Unknown("unterminated string literal")
                if esc and sql[j] == "\\":
                    j += 2
                    continue
                if sql[j] == "'":
                    if sql[j + 1:j + 2] == "'":
                        j += 2
                        continue
                    break
                j += 1
            out.append("''")
            i = j + 1
        elif c == '"':
            j = i + 1
            while True:
                if j >= n:
                    raise Unknown("unterminated quoted identifier")
                if sql[j] == '"':
                    if sql[j + 1:j + 2] == '"':
                        j += 2
                        continue
                    break
                j += 1
            out.append('"_"')
            i = j + 1
        elif c == "$":
            m = re.match(r"\$([A-Za-z_\u0080-￿][A-Za-z0-9_\u0080-￿]*)?\$", sql[i:])
            if m and not (i > 0 and (sql[i - 1].isalnum() or sql[i - 1] == "_")):
                tag = m.group(0)
                j = sql.find(tag, i + len(tag))
                if j < 0:
                    raise Unknown(f"unterminated dollar-quoted string {tag}")
                out.append("''")
                i = j + len(tag)
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)
"""


def _old_mask(monkeypatch):
    """The PRE-REVIEW lexer (the one PR #3038 first carried): `--` ends only at \n; a `$` after a python-isalnum char is not an opener."""
    ns = dict(vars(ac))
    exec(_OLD_MASK_SRC, ns)                      # noqa: S102
    monkeypatch.setattr(ac, "_integrity_mask", ns["_integrity_mask"])


# the reviewer's repros, verbatim
S1_CR_COMMENT = "SELECT 1 --x\r; COMMIT; DELETE FROM t_guard; SELECT 1"
S2_NONASCII_DOLLAR = "SELECT 1 AS ×$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS ×$$"
S2_ASCII_DOLLAR = "SELECT 1 AS a$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS a$$"
S2_ESTRING = "SELECT 1 AS ×E'\\'; COMMIT; DELETE FROM t_guard; SELECT '"
S3_COMMIT_INSIDE = "SELECT 1; COMMIT; DELETE FROM t_guard; SELECT 1"
S4_QUOTED = ['SELECT pg_catalog."pg_advisory_xact_lock"(42) IS NULL', 'SELECT "pg_terminate_backend"(1)',
             'SELECT "set_config"(\'default_transaction_read_only\', \'off\', false) = \'off\'', 'SELECT pg_catalog . "nextval"(\'seq_guard\') > 0',
             'SELECT "pg_advisory_lock" /* c */ (1) IS NULL', 'SELECT U&"\\0070g_advisory_lock"(1) IS NULL']


@pytest.mark.parametrize("sql,frag", [
    (S1_CR_COMMENT, "carriage return"),
    (S2_NONASCII_DOLLAR, "non-ASCII"),
    (S2_ASCII_DOLLAR, "'$' follows"),
    ("SELECT 1 AS ·$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS ·$$", "non-ASCII"),
    ("SELECT 1 AS 😀$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS 😀$$", "non-ASCII"),
    ("SELECT 1 AS x1$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS x1$$", "'$' follows"),
    ("SELECT 1 AS x_$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS x_$$", "'$' follows"),
    ("SELECT 1 AS a$b$; COMMIT; DELETE FROM t_guard; SELECT 1 AS a$b$", "'$' follows"),
    (S2_ESTRING, "non-ASCII"),
    ("SELECT 1 --x\n; COMMIT; DELETE FROM t_guard; SELECT 1", "more than one statement"),
    ("SELECT 1 --x\x00; COMMIT", "NUL"),
    ("SELECT 'ok'\\n", "backslash"),
] + [(q, "QUOTED") for q in S4_QUOTED[:5]] + [(S4_QUOTED[5], "Unicode-escaped")])
def test_reviewer_repros_are_refused_by_the_lexer(sql, frag):
    why = ac.integrity_sql_problem(sql)
    assert why is not None and frag in why, (sql, why)


def test_s1_cr_terminated_comment_is_a_real_lexer_bypass_only_without_the_fix_and_never_reaches_a_write(pg_np, monkeypatch, tmp_path):
    """S1. With the PRE-REVIEW lexer the string is ACCEPTED (the review's bypass); the wrapped subquery still makes the server see a syntax error,
    so nothing is written; with the fixed lexer it is refused before any psql."""
    _old_mask(monkeypatch)
    assert ac.integrity_sql_problem(S1_CR_COMMENT) is None, "the old lexer was expected to accept the repro (that was the bug)"
    c = _cell(_run(monkeypatch, tmp_path, S1_CR_COMMENT), "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"] and "syntax error" in c["measured"], c
    _assert_clean(pg_np)


def test_s2_nonascii_before_dollar_is_a_real_lexer_bypass_only_without_the_fix_and_never_reaches_a_write(pg_np, monkeypatch, tmp_path):
    for sql in (S2_NONASCII_DOLLAR, "SELECT 1 AS ·$$; COMMIT; DELETE FROM t_guard; SELECT 1 AS ·$$"):
        monkeypatch.setattr(ac, "integrity_sql_problem", ac.integrity_sql_problem)
        _old_mask(monkeypatch)
        assert ac.integrity_sql_problem(sql) is None, "the old lexer was expected to accept the repro (that was the bug)"
        c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
        assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"], c
        _assert_clean(pg_np)


BREAKOUT = "SELECT 1) AS x; COMMIT; BEGIN READ WRITE; DELETE FROM t_guard; COMMIT; SELECT * FROM (SELECT 1"       # an explicit READ WRITE block beats the session default
BREAKOUT_RW = "SELECT 1\n) AS x; COMMIT; SET default_transaction_read_only = off; COMMIT; BEGIN READ WRITE; DELETE FROM t_guard; COMMIT; SELECT * FROM (SELECT 1"
_SERVER_REFUSES = ("syntax error", "42601", "multi-query plan")


@pytest.mark.parametrize("sql", [S1_CR_COMMENT, S2_NONASCII_DOLLAR, S2_ASCII_DOLLAR, S2_ESTRING, S3_COMMIT_INSIDE,
                                 "SELECT 1; BEGIN READ WRITE; DELETE FROM t_guard; COMMIT; SELECT 1", "SELECT 1; SET default_transaction_read_only = off; DELETE FROM t_guard",
                                 BREAKOUT, BREAKOUT_RW])
def test_s3_psql_read_only_called_DIRECTLY_with_a_commit_inside_writes_nothing(pg_np, sql):
    """S3: the previous 'independent second guard' was not independent: a `COMMIT;` inside the stored SQL ended the READ ONLY block and the next
    statement ran read-write. Called directly (no allow-list) as a login that OWNS the table, the server itself rejects the text: a syntax error
    from the subquery wrapper, or (for a text that closes the wrapper early with an unbalanced `)`) 'cannot open multi-query plan as cursor'."""
    with pytest.raises(ac.Unknown) as ei:
        ac.psql_read_only(sql)
    assert any(x in str(ei.value) for x in _SERVER_REFUSES), str(ei.value)
    _assert_clean(pg_np)


def _patched_read_only(monkeypatch, *, wrapper=True, cursor=True, session=True):
    """Install `psql_read_only` with the named server-side guard(s) source-removed."""
    src = textwrap.dedent(inspect.getsource(ac.psql_read_only))
    if not wrapper:
        old = 'wrapped = f"SELECT * FROM ({stmt}\\n) AS _integrity LIMIT 1"'
        assert old in src, "the wrapper line moved"
        src = src.replace(old, "wrapped = stmt")
    if not cursor:
        old = 'run_sql = "DO $" + outer + "$ " + body + " $" + outer + "$"'
        assert old in src, "the DO line moved"
        src = src.replace(old, "run_sql = wrapped")
    if not session:
        old = '"SET default_transaction_read_only = on", '
        assert old in src, "the session-default line moved"
        src = src.replace(old, '"SELECT 1", ')
    ns = dict(vars(ac))
    exec(src, ns)                                  # noqa: S102 - test-only source mutation
    monkeypatch.setattr(ac, "psql_read_only", ns["psql_read_only"])


def _try(sql):
    try:
        ac.psql_read_only(sql)
    except ac.Unknown as exc:
        return str(exc)
    return None


def test_each_server_guard_alone_is_enough_against_the_escape_it_targets(pg_np, monkeypatch):
    """Remove ONE guard at a time: every escape repro is still stopped by another, so none is a single point of failure."""
    for kw in (dict(wrapper=False), dict(session=False), dict(cursor=False, session=True)):
        with monkeypatch.context() as m:
            _patched_read_only(m, **kw)
            for sql in (S3_COMMIT_INSIDE, S1_CR_COMMENT, S2_NONASCII_DOLLAR, "SELECT 1; BEGIN READ WRITE; DELETE FROM t_guard; COMMIT; SELECT 1"):
                _try(sql)
                _assert_clean(pg_np)


def test_mutation_cursor_layer_removed_the_unbalanced_paren_breakout_with_set_off_lands(pg_np, monkeypatch):
    """The hole of the subquery wrapper ALONE (the review's design): `)` closes the wrapper early and the text continues with its own statements.
    Without the single-statement dynamic cursor inside an atomic DO block the COMMIT + SET ... off + DELETE sequence writes as the table owner."""
    assert "multi-query plan" in _try(BREAKOUT)
    _assert_clean(pg_np)
    _patched_read_only(monkeypatch, cursor=False)
    _try(BREAKOUT)
    assert pg_np.psql("SELECT count(*) FROM t_guard") == "0", "the break-out should have landed with the cursor guard removed"


def test_mutation_wrapper_removed_alone_the_cursor_still_refuses_the_multi_statement_plan(pg_np, monkeypatch):
    _patched_read_only(monkeypatch, wrapper=False)
    assert "multi-query plan" in _try(S3_COMMIT_INSIDE)
    _assert_clean(pg_np)


def test_mutation_session_default_removed_alone_everything_is_still_refused(pg_np, monkeypatch):
    _patched_read_only(monkeypatch, session=False)
    assert any(x in (_try(S3_COMMIT_INSIDE) or "") for x in _SERVER_REFUSES)
    _assert_clean(pg_np)


def test_mutation_wrapper_cursor_and_session_default_all_removed_the_commit_escape_lands(pg_np, monkeypatch):
    """The test of the tests: with every server-side guard gone, S3 deletes the guard table as a login that owns it."""
    _patched_read_only(monkeypatch, wrapper=False, cursor=False, session=False)
    _try(S3_COMMIT_INSIDE)
    assert pg_np.psql("SELECT count(*) FROM t_guard") == "0", "the escape should have landed with every guard removed"


def test_the_unique_dollar_tag_cannot_be_closed_by_the_text_or_its_edges():
    for text in ("x", "$n99q0$", "a$n99q0", "$n99q0", "n99q0$", "$n99q0$ ; DELETE", "$n99q0$n99q1$"):
        tag = ac._unique_dollar_tag("n99q", text)
        d = f"${tag}$"
        assert (text + d).find(d) == len(text) and d not in text, (text, tag)


def test_a_text_containing_the_dollar_tag_it_would_get_still_cannot_escape(pg_np):
    nasty = "SELECT $n99q0$ ; COMMIT; DELETE FROM t_guard; $n99q0$ = ''"
    _try(nasty)
    _assert_clean(pg_np)
    _try("SELECT 1 /* $n99q0 */ AS a$n99q0")
    _assert_clean(pg_np)


@pytest.mark.parametrize("sql", S4_QUOTED[:5])
def test_s4_quoted_function_names_are_refused_and_never_run(pg_np, monkeypatch, tmp_path, sql):
    spy = _Spy(monkeypatch)
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    assert c["v"] == ac.PARTIAL and "REFUSED (never run)" in c["measured"] and "QUOTED" in c["measured"], c
    assert not any("BEGIN READ ONLY" in x for x in spy.sent)
    _assert_clean(pg_np)


def test_mutation_quoted_identifier_rule_removed_s4_is_accepted(monkeypatch):
    for sql in S4_QUOTED[:5]:
        assert ac.integrity_sql_problem(sql) is not None
    _mutant(monkeypatch, "_integrity_statement", """if re.search(r'"Q*"\\s*\\(', body) or re.search(r'\\.\\s*"Q*"', body):""", "if False:")
    assert [ac.integrity_sql_problem(q) for q in S4_QUOTED[:5]] == [None] * 5


def test_mutation_cr_comment_terminator_removed_s1_is_accepted(monkeypatch):
    assert ac.integrity_sql_problem(S1_CR_COMMENT) is not None
    _mutant(monkeypatch, "_integrity_mask", 'while j < n and sql[j] not in "\\n\\r":', 'while j < n and sql[j] != "\\n":')
    assert ac.integrity_sql_problem(S1_CR_COMMENT) is None


def test_mutation_dollar_prefix_rule_M19_removed_the_ascii_repro_is_accepted(monkeypatch):
    """M19: the `$` after-identifier rule. Alone it is what stops `a$$ ... a$$` (PG: one identifier; the lexer: a dollar-quoted string)."""
    assert "'$' follows" in ac.integrity_sql_problem(S2_ASCII_DOLLAR)
    _mutant(monkeypatch, "_integrity_mask", "if i > 0 and _ident_char(sql[i - 1]):", "if False:")
    assert ac.integrity_sql_problem(S2_ASCII_DOLLAR) is None


def test_s2_is_defended_twice_each_rule_alone_still_refuses_and_both_removed_accepts(monkeypatch):
    with monkeypatch.context() as m:
        _mutant(m, "_integrity_mask", "elif ord(c) >= 128:", "elif False:")
        assert "'$' follows" in ac.integrity_sql_problem(S2_NONASCII_DOLLAR)          # the prefix rule (non-ASCII IS an identifier char) still refuses
    with monkeypatch.context() as m:
        _mutant(m, "_integrity_mask", "if i > 0 and _ident_char(sql[i - 1]):", "if False:")
        assert "non-ASCII" in ac.integrity_sql_problem(S2_NONASCII_DOLLAR)           # the non-ASCII rule still refuses
    src = textwrap.dedent(inspect.getsource(ac._integrity_mask)).replace("elif ord(c) >= 128:", "elif False:").replace("if i > 0 and _ident_char(sql[i - 1]):", "if False:")
    ns = dict(vars(ac))
    exec(src, ns)                                                                    # noqa: S102
    monkeypatch.setattr(ac, "_integrity_mask", ns["_integrity_mask"])
    assert ac.integrity_sql_problem(S2_NONASCII_DOLLAR) is None


def test_mutation_non_ascii_rule_removed_a_non_ascii_identifier_is_accepted(monkeypatch):
    assert "non-ASCII" in ac.integrity_sql_problem("SELECT 1 AS ×")
    _mutant(monkeypatch, "_integrity_mask", "elif ord(c) >= 128:", "elif False:")
    assert ac.integrity_sql_problem("SELECT 1 AS ×") is None


def test_non_ascii_inside_strings_comments_and_dollar_bodies_is_fine():
    for ok in ("SELECT 'a×b' <> ''", "SELECT 1 -- ×·😀", "SELECT 1 /* × */", "SELECT $$×$$ <> ''", "SELECT E'×\\'' <> ''"):
        assert ac.integrity_sql_problem(ok) is None, ok


def test_mutation_paren_balance_removed_an_early_close_is_accepted(monkeypatch):
    bad = "SELECT 1) AS x UNION SELECT * FROM (SELECT 1"
    assert "unbalanced" in ac.integrity_sql_problem(bad)
    _mutant(monkeypatch, "_integrity_statement", "if depth < 0:", "if False:")
    assert ac.integrity_sql_problem(bad) is None


# ───────────────────────── (c) pg_sleep and friends; (d) oversize; (e) audit trail; (f) result parsing ─────────────────────────

def test_pg_sleep_is_refused_and_so_are_the_other_pg_functions_that_lock_or_signal():
    for fn in ("pg_sleep(1)", "pg_advisory_lock(1)", "pg_try_advisory_xact_lock(1)", "pg_terminate_backend(1)", "pg_cancel_backend(1)", "pg_notify('a','b')",
               "pg_read_file('x')", "pg_ls_dir('.')", "pg_reload_conf()", "pg_stat_reset()", "pg_create_restore_point('x')", "pg_switch_wal()"):
        why = ac.integrity_sql_problem(f"SELECT {fn} IS NULL")
        assert why and fn.split("(")[0] in why, (fn, why)


def test_oversize_sql_is_refused_with_an_explicit_reason_independent_of_the_host(pg, monkeypatch, tmp_path):
    big = "SELECT true /* " + "x" * 130_000 + " */"
    assert len(big.encode()) > ac.INTEGRITY_MAX_BYTES
    spy = _Spy(monkeypatch)
    c = _cell(_run(monkeypatch, tmp_path, big), "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"] and "integrity SQL too large to run via psql -c" in c["measured"], c
    assert not spy.sent, "an oversize SQL must never reach psql"
    with pytest.raises(ac.Unknown, match="too large"):
        ac.psql_read_only(big)
    ok = "SELECT true /* " + "x" * 100_000 + " */"            # under the limit: runs (host-independent: the cap is ours, not the OS')
    assert ac.integrity_sql_problem(ok) is None
    assert _cell(_run(monkeypatch, tmp_path, ok), "ph_x")["v"] == ac.PASS


def test_mutation_oversize_limit_removed_the_lexer_accepts_a_203kb_sql(monkeypatch):
    big = "SELECT true /* " + "x" * 203_000 + " */"
    assert "too large" in ac.integrity_sql_problem(big)
    _mutant(monkeypatch, "_integrity_statement", "> INTEGRITY_MAX_BYTES", "> 10**9")
    assert ac.integrity_sql_problem(big) is None


def test_the_measured_text_carries_the_sql_hash_and_elapsed_seconds(pg, monkeypatch, tmp_path):
    sql = "SELECT count(*) = 3 FROM t_guard"
    sha = hashlib.sha256(sql.encode()).hexdigest()[:12]
    for q, want in ((sql, ac.PASS), ("SELECT count(*) = 99 FROM t_guard", ac.PARTIAL), ("DELETE FROM t_guard", ac.PARTIAL), ("SELECT 1/0 = 1", ac.PARTIAL)):
        c = _cell(_run(monkeypatch, tmp_path, q), "ph_x")
        h = hashlib.sha256(q.encode()).hexdigest()[:12]
        assert c["v"] == want and re.search(rf"\[integrity_check_sql sha256:{h}, \d+(\.\d+)?s\]", c["measured"]), c
    assert sha != hashlib.sha256(b"SELECT 1").hexdigest()[:12]


@pytest.mark.parametrize("val", ["NaN", "nan", "Infinity", "-Infinity", "inf", "-inf", "+infinity"])
def test_non_finite_numbers_are_not_holding(val):
    ok, why = ac._integrity_holds([[val]])
    assert ok is False and "finite" in why


def test_nan_and_infinity_from_a_real_server_read_not_holding(pg, monkeypatch, tmp_path):
    for q in ("SELECT 'NaN'::float8", "SELECT 'Infinity'::float8", "SELECT '-Infinity'::numeric"):
        c = _cell(_run(monkeypatch, tmp_path, q), "ph_x")
        assert c["v"] == ac.PARTIAL and "does NOT hold" in c["measured"] and "finite" in c["measured"], (q, c)


def test_an_empty_string_reads_empty_and_a_multiline_value_is_not_a_scalar(pg, monkeypatch, tmp_path):
    ok, why = ac._integrity_holds([[""]])
    assert not ok and "empty" in why
    c = _cell(_run(monkeypatch, tmp_path, "SELECT ''"), "ph_x")
    assert c["v"] == ac.PARTIAL and "empty" in c["measured"]
    c = _cell(_run(monkeypatch, tmp_path, "SELECT E't\\nf'"), "ph_x")
    assert c["v"] == ac.PARTIAL and "spans several lines" in c["measured"], c
    assert ac._integrity_holds([["t"], ["f"]])[0] is False


def test_mutation_finite_check_removed_nan_holds(monkeypatch):
    assert ac._integrity_holds([["NaN"]])[0] is False
    _mutant(monkeypatch, "_integrity_holds", "if not math.isfinite(num):", "if False:")
    assert ac._integrity_holds([["NaN"]])[0] is True


def test_only_the_first_column_of_the_first_row_decides(pg, monkeypatch, tmp_path):
    assert _cell(_run(monkeypatch, tmp_path, "SELECT true, false, 'zzz'"), "ph_x")["v"] == ac.PASS
    assert _cell(_run(monkeypatch, tmp_path, "SELECT false, true"), "ph_x")["v"] == ac.PARTIAL


# ───────────────────────── M26: the client-side timeout kill ─────────────────────────

def test_the_client_side_timeout_kills_psql_when_the_server_timeout_cannot_fire(pg):
    t0 = time.time()
    with pytest.raises(ac.CheckTimeout, match="client-side timeout"):
        ac._psql_run(["SELECT pg_sleep(6)"], "\x1f", 1, None)
    assert time.time() - t0 < 4


def test_mutation_M26_client_timeout_removed_the_kill_never_happens(pg, monkeypatch):
    _mutant(monkeypatch, "_psql_run", "timeout=limit", "timeout=None")
    t0 = time.time()
    rows = ac._psql_run(["SELECT pg_sleep(3)"], "\x1f", 1, None)           # no CheckTimeout: the run just completes
    assert time.time() - t0 >= 2.9 and rows == [[""]]


# ───────────────────────── permission denied under the census role → NO_DETECTOR ─────────────────────────

TRACK_I = "Track I: rewrite the check to need neither charts nor the identity function; do NOT widen the census role"


@pytest.mark.parametrize("sql,msg", [("SELECT bodha_signal_identity() = 1", "permission denied for function bodha_signal_identity"),
                                     ("SELECT count(*) >= 0 FROM charts", "permission denied for table charts")])
def test_permission_denied_reads_no_detector_with_the_track_i_hint(pg_np, monkeypatch, tmp_path, sql, msg):
    c = _cell(_run(monkeypatch, tmp_path, sql), "ph_x")
    assert c["v"] == ac.NO_DET, c
    assert "integrity not measurable under the census role: ERROR:" in c["measured"] and msg in c["measured"] and TRACK_I in c["measured"], c
    assert "42501" in c["measured"] and re.search(r"sha256:[0-9a-f]{12}", c["measured"]) and "rows_written=5 = live=5" in c["measured"]
    _assert_clean(pg_np)


def test_other_failures_stay_partial_could_not_be_run_and_a_false_result_stays_does_not_hold(pg_np, monkeypatch, tmp_path):
    for q in ("SELECT 1/0 = 1", "SELECT count(*) FROM no_such_table", "SELECT 1 FROM", "SELECT CAST('permission denied' AS int)"):
        c = _cell(_run(monkeypatch, tmp_path, q), "ph_x")
        assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"] and "not measurable" not in c["measured"], (q, c)
    c = _cell(_run(monkeypatch, tmp_path, "SELECT false"), "ph_x")
    assert c["v"] == ac.PARTIAL and "does NOT hold" in c["measured"]
    c = _cell(_run(monkeypatch, tmp_path, "DELETE FROM t_guard"), "ph_x")
    assert c["v"] == ac.PARTIAL and "REFUSED" in c["measured"]


def test_permission_denied_message_must_be_the_sqlstate_42501_error_line_not_any_text_containing_it():
    assert ac._PERMISSION_DENIED.match("ERROR: 42501: permission denied for table charts")
    assert not ac._PERMISSION_DENIED.match('ERROR: 22P02: invalid input syntax for type integer: "permission denied"')
    assert not ac._PERMISSION_DENIED.match("ERROR: 42P01: relation \"permission denied\" does not exist")


def test_mutation_permission_denied_detector_removed_it_reads_partial(pg_np, monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "_PERMISSION_DENIED", re.compile(r"^(?!)"))
    c = _cell(_run(monkeypatch, tmp_path, "SELECT bodha_signal_identity() = 1"), "ph_x")
    assert c["v"] == ac.PARTIAL and "could NOT be run" in c["measured"]


@pytest.mark.parametrize("layer", ["L2", "L3", "L4"])
@pytest.mark.parametrize("other", [ac.PASS, ac.PARTIAL, ac.NO_DET, ac.ERRORED, ac.FAIL])
def test_a_no_detector_completion_never_moves_the_build_gate_up(layer, other):
    """Rollup (E6.2: worst of FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS): turning a PASS Build.completion into NO_DETECTOR can only move the Build
    gate DOWN or leave it where another check already holds it - for every verdict another Build check may carry. (The saved census of 2026-10-02: bo_laksana
    Build FAIL stays FAIL; ka_jivana_parva Build PARTIAL moves to NO_DETECTOR, i.e. down.)"""
    ms = {c: dict(v=ac.PASS, measured="x") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    ms["Build.dag"] = dict(v=other, measured="x")
    before = ac.rollup_asset(layer, {k: dict(v) for k, v in ms.items()})["Build"]["v"]
    ms["Build.completion"] = dict(v=ac.NO_DET, measured="NO_DETECTOR - integrity not measurable under the census role: x")
    after = ac.rollup_asset(layer, ms)["Build"]["v"]
    assert ac.ROLLUP_ORDER.index(after) <= ac.ROLLUP_ORDER.index(before), (before, after)
    assert after in (ac.NO_DET, ac.ERRORED, ac.FAIL), after


# ───────────────────────── FUZZ: the server executes exactly ONE read-only statement, for a login that could write ─────────────────────────

FUZZ_FRAGMENTS = ["\r", "\n", "--", "/*", "*/", "'", '"', "$$", "$a$", "×", "·", "😀", ";", "E", "\\", "(", ")", " ", "x", "1", "U&", ".", "$", "\t",
                  " ; COMMIT; ", " ; DELETE FROM t_guard; ", " ; COMMIT; BEGIN READ WRITE; DELETE FROM t_guard; COMMIT; SELECT 1 ", " ; INSERT INTO t_audit SELECT 1 WHERE current_setting('transaction_read_only') = 'off'; ",
                  " ; SELECT nextval('seq_guard'); ", " ; SET default_transaction_read_only = off; ", " ; BEGIN READ WRITE; ", " ; CREATE TABLE t_new(a int); "]
FUZZ_PREFIXES = ["SELECT 1", "SELECT true", "SELECT 1 AS x", "(SELECT 1", "WITH a AS (SELECT 1) SELECT 1", "SELECT 1 AS ×", "SELECT 1 AS a"]
FUZZ_SUFFIXES = ["", "", ")", "\nSELECT 1", " SELECT 1", " $$", " --", "\r"]


FUZZ_ATTACKS = [S1_CR_COMMENT, S2_NONASCII_DOLLAR, S2_ASCII_DOLLAR, S3_COMMIT_INSIDE, BREAKOUT, BREAKOUT_RW,
                "SELECT 1; COMMIT; BEGIN READ WRITE; DELETE FROM t_guard; COMMIT; SELECT 1", "SELECT 1; COMMIT; INSERT INTO t_audit VALUES (1); SELECT 1",
                "SELECT 1); COMMIT; SELECT nextval('seq_guard'); SELECT (1", "SELECT 1 --x\r; COMMIT; DELETE FROM t_guard; SELECT 1 --\r"]


def _fuzz_strings(seed, n):
    rng = random.Random(seed)
    return FUZZ_ATTACKS + [rng.choice(FUZZ_PREFIXES) + "".join(rng.choice(FUZZ_FRAGMENTS) for _ in range(rng.randint(1, 9))) + rng.choice(FUZZ_SUFFIXES) for _ in range(n)]


def test_fuzz_every_string_the_allow_list_accepts_runs_as_exactly_one_read_only_statement(pg_np):
    """Seeded fuzz over the review's alphabet (\\r \\n -- /* */ ' " $$ × ; E \\ ( ) plus attack payloads). For EVERY string the lexer ACCEPTS, run it
    through the real path as a NON-superuser that owns the guarded objects; afterwards the guard table, sequence, audit table (whose INSERT only fires if
    the transaction were read-write), advisory locks and the namespace must be untouched. Non-vacuous: a minimum number of strings must be accepted."""
    accepted = 0
    for s in _fuzz_strings(20260903, 5000):
        if ac.integrity_sql_problem(s) is not None:
            continue
        accepted += 1
        if accepted > 150:
            break
        try:
            ac.psql_read_only(ac._integrity_statement(s)[1])
        except ac.Unknown:
            pass
        assert _state(pg_np) == CLEAN_STATE, f"state changed after: {s!r}"
    assert accepted >= 100, accepted


def test_fuzz_the_server_guards_alone_hold_for_every_string_even_the_ones_the_lexer_refuses(pg_np):
    """Layers 2+3 without the lexer: EVERY generated string (accepted or not) goes straight to psql_read_only. The wrapped subquery and the
    read-only session must keep the owner of the objects from changing anything."""
    for s in _fuzz_strings(77, 400):
        try:
            ac.psql_read_only(s)
        except ac.Unknown:
            pass
        assert _state(pg_np) == CLEAN_STATE, f"state changed after: {s!r}"


def test_mutation_fuzz_has_teeth_with_the_server_guards_removed_it_finds_a_write(pg_np, monkeypatch):
    """Every server-side guard removed: the same fuzz alphabet changes state - the fuzz can fail."""
    _patched_read_only(monkeypatch, wrapper=False, cursor=False, session=False)
    changed = False
    for s in _fuzz_strings(77, 400):
        try:
            ac.psql_read_only(s)
        except ac.Unknown:
            pass
        if _state(pg_np) != CLEAN_STATE:
            changed = True
            break
    assert changed


# ═════════════════════════ HARDENING PASS (verification review of PR #3038) ═════════════════════════

# 1. index-maintenance and string-executing functions: refused (they write physical state or run SQL even in a READ ONLY transaction)
@pytest.mark.parametrize("fn", ["brin_summarize_new_values('i'::regclass)", "brin_summarize_range('i'::regclass, 0)", "brin_desummarize_range('i'::regclass, 0)",
                                "gin_clean_pending_list('i'::regclass)", "public.brin_summarize_new_values('i'::regclass)", "brin_summarize_new_values /* c */ ('i'::regclass)",
                                "ts_stat('select 1')", "ts_rewrite('a'::tsquery, 'select 1')", "gist_page_items(1)", "bt_metap('i')", "hash_metapage_info(1)", "heap_page_items(1)",
                                "txid_current()", "setseed(0.5)", "current_query()", "pgstattuple('t')"])
def test_index_maintenance_and_string_executing_functions_are_refused(fn):
    why = ac.integrity_sql_problem(f"SELECT {fn} IS NOT NULL")
    assert why and "refused" in why and fn.split("(")[0].split(".")[-1].split()[0] in why, (fn, why)


def test_the_deny_list_was_chosen_over_a_positive_function_allow_list_because_the_corpus_needs_non_functions_and_user_functions():
    """Why not a positive allow-list: the real literals call user-defined identity functions (bodha_signal_identity, phala_anchor_identity ...), and
    aliases / CTE column lists / keywords all look like `name (` to a lexer-level check (z1(, sign_idx(, exists(, in(, filter(). Every refused prefix
    is asserted NOT to appear in any real literal, so the deny-list costs no legitimate verdict."""
    lits, _ = _migration_literals()
    hits = []
    for f, b in lits:
        for fn in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", ac._integrity_mask(b)):
            f_ = fn.lower()
            if f_ in ac._INTEGRITY_WRITE_FUNCS or f_.startswith(ac._INTEGRITY_REFUSED_PREFIXES):
                hits.append((f, f_))
    assert hits == [], hits[:5]


def test_mutation_refused_prefixes_removed_brin_and_gin_are_accepted(monkeypatch):
    assert ac.integrity_sql_problem("SELECT brin_summarize_new_values('i'::regclass) > 0")
    monkeypatch.setattr(ac, "_INTEGRITY_REFUSED_PREFIXES", ("lo_",))
    monkeypatch.setattr(ac, "_INTEGRITY_WRITE_FUNCS", frozenset())
    assert ac.integrity_sql_problem("SELECT brin_summarize_new_values('i'::regclass) > 0") is None
    assert ac.integrity_sql_problem("SELECT gin_clean_pending_list('i'::regclass) > 0") is None


# 2. a huge value never becomes a huge cell / a huge read
def test_a_10mb_value_costs_the_census_a_short_text_not_10mb(pg, monkeypatch, tmp_path):
    c = _cell(_run(monkeypatch, tmp_path, "SELECT repeat('x', 10000000)"), "ph_x")
    assert c["v"] == ac.PARTIAL and "does NOT hold" in c["measured"] and len(c["measured"]) < 1200, len(c["measured"])
    rows = ac.psql_read_only("SELECT repeat('x', 10000000)")
    assert len(rows[0][0]) < 300 and "10000002 characters" in rows[0][0], rows[0][0][-60:]


def test_the_shown_value_is_truncated_to_120_characters():
    ok, why = ac._integrity_holds([["y" * 5000]])
    assert not ok and len(why) < 250 and "..." in why


def test_a_big_value_in_a_later_column_does_not_hide_a_short_true_first_column(pg, monkeypatch, tmp_path):
    assert _cell(_run(monkeypatch, tmp_path, "SELECT true, repeat('x', 5000000)"), "ph_x")["v"] == ac.PASS


def test_a_huge_error_line_is_cut_and_psql_output_is_read_through_a_cap(pg, monkeypatch):
    with pytest.raises(ac.Unknown) as ei:
        ac.psql_read_only("SELECT ('" + "x" * 100_000 + "')::int")
    assert len(str(ei.value)) <= 400
    with pytest.raises(ac.ReadError, match="exceeds the 100-byte cap"):
        ac._psql_run(["SELECT repeat('x', 100000)"], "\x1f", 30, None, cap=100)
    kept = ac._run_capped(["psql", "-qtAX", "-c", "SELECT repeat('x', 3000000)"], dict(os.environ), 30, 1000)
    assert len(kept.stdout) == 1000 and kept.over is True


def test_mutation_value_truncation_removed_the_big_value_comes_back_whole(pg, monkeypatch):
    _mutant(monkeypatch, "_integrity_holds", 'shown = repr(v if len(v) <= 120 else v[:120] + "...")', "shown = repr(v)")
    assert len(ac._integrity_holds([["y" * 5000]])[1]) > 5000


# 3. the read-back cannot be forged by the stored text
def _forger(pg, name="f_forge"):
    pg.psql(f"CREATE OR REPLACE FUNCTION {name}() RETURNS boolean LANGUAGE plpgsql AS $f$ DECLARE q text := current_query(); g text; BEGIN "
            "g := substring(q from 'n99\\.i_[0-9a-f]+'); IF g IS NOT NULL THEN PERFORM set_config(g, 'row 4 true', true); END IF; "
            "PERFORM set_config('n99.integrity', 'row {\"a\":true}', true); PERFORM set_config('n99.i_00', 'row 4 true', true); RETURN false; END $f$")


def test_a_function_that_sets_the_guessed_or_leaked_setting_cannot_forge_holds(pg_np):
    _forger(pg_np)
    pg_np.psql(f"GRANT EXECUTE ON FUNCTION f_forge() TO {NP}")
    assert ac.psql_read_only("SELECT true WHERE f_forge()") == []                   # zero rows: the sentinel (written after the stored query) wins
    got = ac.psql_read_only("SELECT f_forge()")                                      # one row, false: the real first value wins
    assert ac._integrity_holds(got)[0] is False and got == [["f"]]
    _assert_clean(pg_np)


def test_each_run_uses_a_fresh_unguessable_setting_name(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "_psql_run", lambda cmds, *a, **k: seen.append(cmds[3]) or [["none"]])
    ac.psql_read_only("SELECT true"); ac.psql_read_only("SELECT true")
    names = [re.search(r"n99\.i_[0-9a-f]{24}", c).group(0) for c in seen]
    assert len(set(names)) == 2 and "n99.integrity" not in seen[0]
    assert "set_config('" + names[0] + "', 'none', true)" in seen[0] and seen[0].index("none") < seen[0].index("EXECUTE")


def test_mutation_final_write_removed_a_forger_can_forge_holds(pg_np, monkeypatch):
    _forger(pg_np)
    pg_np.psql(f"GRANT EXECUTE ON FUNCTION f_forge() TO {NP}")
    src = textwrap.dedent(inspect.getsource(ac.psql_read_only))
    old = """PERFORM set_config('" + guc + "', v, true); END")"""
    assert old in src
    ns = dict(vars(ac)); exec(src.replace(old, 'END")'), ns)                         # noqa: S102
    monkeypatch.setattr(ac, "psql_read_only", ns["psql_read_only"])
    # without the post-loop write the forger's own value (set while the stored query ran) is what is read back
    got = ac.psql_read_only("SELECT true WHERE f_forge()")
    assert got != [] and ac._integrity_holds(got)[0] is True


# 4. both timeouts exist, and the client kill is the backstop when the server one is gone
def test_both_the_server_and_the_client_timeout_are_in_what_is_sent(monkeypatch):
    sent = {}
    monkeypatch.setattr(ac, "_psql_run", lambda cmds, sep, limit, *a, **k: sent.update(cmds=cmds, limit=limit) or [["none"]])
    ac.psql_read_only("SELECT true", timeout=7)
    assert sent["limit"] == 7 and "SET LOCAL statement_timeout = 6300" in sent["cmds"], sent
    assert sent["cmds"][:3] == ["SET default_transaction_read_only = on", "BEGIN READ ONLY", "SET LOCAL statement_timeout = 6300"] and sent["cmds"][-1] == "ROLLBACK"


def test_the_client_side_kill_is_the_backstop_when_the_server_timeout_is_gone(pg, monkeypatch):
    src = textwrap.dedent(inspect.getsource(ac.psql_read_only))
    old = 'f"SET LOCAL statement_timeout = {ms}"'
    assert old in src
    ns = dict(vars(ac)); exec(src.replace(old, '"SELECT 1"'), ns)                   # noqa: S102 - mutant: no server-side timeout
    monkeypatch.setattr(ac, "psql_read_only", ns["psql_read_only"])
    t0 = time.time()
    with pytest.raises(ac.CheckTimeout, match="client-side timeout after 1s"):
        ac.psql_read_only("SELECT count(*) > 0 FROM generate_series(1, 2000000000)", timeout=1)
    assert time.time() - t0 < 6


def test_mutation_client_kill_removed_from_the_capped_runner_it_never_fires(pg, monkeypatch):
    _mutant(monkeypatch, "_run_capped", "p.wait(timeout=limit)", "p.wait(timeout=None)")
    t0 = time.time()
    ac._run_capped(["psql", "-qtAX", "-c", "SELECT pg_sleep(3)"], dict(os.environ), 1, 100)
    assert time.time() - t0 >= 2.9


# 5. the dollar-quote tags cannot be closed by the stored text. The injected code builds its marker at run time ('PWN' || 'ED_N99'), so the marker
# appears in an error message only if the injected PL/pgSQL really RAN (a syntax error echoes the text, which never contains the joined word).
def _breakout_inner(tag):
    return f"SELECT 1) x ${tag}$ LOOP EXIT; END LOOP; RAISE EXCEPTION '%', 'PWN' || 'ED_N99'; FOR r IN EXECUTE ${tag}$ SELECT * FROM (SELECT 1"


def _breakout_outer(itag, otag):
    """Closes the inner quote, ends the DO body validly, then runs its own DO block (and swallows the original tail in a string)."""
    return (f"SELECT 1) AS x LIMIT 1${itag}$ LOOP EXIT; END LOOP; END ${otag}$; DO ${otag}$ BEGIN RAISE EXCEPTION '%', 'PWN' || 'ED_N99'; END ${otag}$; SELECT ${otag}$")


@pytest.mark.parametrize("k", range(7))
def test_inner_tag_collisions_never_close_the_inner_quote(pg_np, k):
    txt = "SELECT 1) x " + " ".join(f"$n99q{i}$ LOOP EXIT; END LOOP; RAISE EXCEPTION '%', 'PWN' || 'ED_N99'; FOR r IN EXECUTE $n99q{i}$ SELECT * FROM (SELECT 1" for i in range(k + 1))
    err = _try(txt) or ""
    assert "PWNED_N99" not in err, err
    _assert_clean(pg_np)
    for i in range(k + 1):
        err = _try(_breakout_inner(f"n99q{i}")) or ""
        assert "PWNED_N99" not in err, (i, err)


@pytest.mark.parametrize("k", range(7))
def test_outer_tag_collisions_never_close_the_do_block(pg_np, k):
    for itag in (f"n99q{i}" for i in range(7)):
        err = _try(_breakout_outer(itag, f"n99d{k}")) or ""
        assert "PWNED_N99" not in err, (itag, k, err)
    _assert_clean(pg_np)


def test_mutation_inner_tag_fixed_the_injected_plpgsql_runs(pg_np, monkeypatch):
    src = textwrap.dedent(inspect.getsource(ac.psql_read_only))
    old = 'tag = _unique_dollar_tag("n99q", wrapped)'
    assert old in src
    ns = dict(vars(ac)); exec(src.replace(old, 'tag = "n99q0"'), ns)                # noqa: S102
    monkeypatch.setattr(ac, "psql_read_only", ns["psql_read_only"])
    assert "PWNED_N99" in (_try(_breakout_inner("n99q0")) or "")


def test_mutation_outer_tag_fixed_the_injected_do_block_runs(pg_np, monkeypatch):
    src = textwrap.dedent(inspect.getsource(ac.psql_read_only))
    for old, new in (('tag = _unique_dollar_tag("n99q", wrapped)', 'tag = "n99q0"'), ('outer = _unique_dollar_tag("n99d", body)', 'outer = "n99d0"')):
        assert old in src
        src = src.replace(old, new)
    ns = dict(vars(ac)); exec(src, ns)                                                # noqa: S102   (inner pinned too, so the attack is expressible)
    monkeypatch.setattr(ac, "psql_read_only", ns["psql_read_only"])
    assert "PWNED_N99" in (_try(_breakout_outer("n99q0", "n99d0")) or "")


def test_the_real_tag_choice_survives_the_same_attacks(pg_np):
    for t in (_breakout_inner("n99q0"), _breakout_outer("n99q0", "n99d0"), _breakout_outer("n99q1", "n99d1")):
        assert "PWNED_N99" not in (_try(t) or "")
    _assert_clean(pg_np)
