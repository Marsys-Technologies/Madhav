"""test_e5_9_footprint_lows.py -- Suvarna E5.9 / FP2: the LOW findings of the #2972 re-review, each seeded and pinned.

The footprint write-set scan (suvarna_level_wave.scan_writer_tables) reads a writer's SOURCE TEXT with ast and must never
under-report a real write: a form it cannot resolve goes to assets_not_scanned (footprint_scope partial, has_blockers
unknown), a form it can resolve is resolved COMPLETELY, and the clean single-table writer stays complete.

  1 multi-table statements          TRUNCATE a, b (every list item), DELETE..USING / UPDATE..FROM / INSERT..SELECT (only the
                                    written table), COPY t (cols) FROM, a CTE chain with several writes, several statements
  2 imported SQL constant           execute(IMPORTED) / execute(mod.X) / call result / subscript / unbound name / attribute
                                    nothing assigns / an f-string or concatenation that STARTS with a runtime value
  3 trailing verb                   a literal that ends in INSERT INTO / DELETE FROM / TRUNCATE [TABLE] / UPDATE / COPY
  4 dotted name                     {cfg.T} / {self.T} is never read as a local constant T
  5 exotic forms                    bytes SQL, copy_from & co, fn.__doc__, setattr, globals()[..], import *, exec/eval,
                                    getattr(cur, 'execute')(...)
  6 source_paths mutation           append / += / extend / item assignment / setattr: the list is not the literal
  7 hostile input                   SELECT..INTO is linear; a literal over 64 KB is not scanned
  8 pins                            the `files` path format, async with / async def / unpacking bindings, the real tree

Offline: writers are tmp-dir fixtures; nothing is imported or executed (ast only).
"""
from __future__ import annotations

import pathlib
import re
import sys
import textwrap
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_level_wave as slw  # noqa: E402

REAL_REPO = HERE.parents[3]
WRITERS = slw.WRITERS_REL
OWN = 'OWN = "INSERT INTO t_a (x) VALUES (1)"\n'      # a clean own write: every form below is mixed with it


def write(repo: pathlib.Path, rel: str, body: str) -> pathlib.Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def writer(repo, asset_id, body):
    return write(repo, f"{WRITERS}/{asset_id}.py", body)


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "platform/python-sidecar/ga_writers/_idempotency.py", "def noop():\n    return 1\n")
    write(tmp_path, "platform/python-sidecar/bodha_writers/_idempotency.py", "def noop():\n    return 1\n")
    return tmp_path


def scan(repo, body, asset="a_x"):
    writer(repo, asset, body)
    return slw.scan_writer_tables(asset, repo)


def tables(repo, body):
    res = scan(repo, body)
    assert "tables" in res, res
    return res["tables"]


def not_scanned(repo, body, reason):
    """The writer is NOT scanned and the FIRST recorded reason starts with `reason` (a named reason, never a guess)."""
    res = scan(repo, body)
    assert "tables" not in res and res.get("not_scanned", "").startswith(reason), res
    return res["not_scanned"]


# ───────────────────────────────── 1. multi-table statements ─────────────────────────────────

@pytest.mark.parametrize("sql,expected", [
    ('"TRUNCATE t_a, t_b"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE t_a,t_b"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE TABLE t_a, t_b, t_c"', ["public.t_a", "public.t_b", "public.t_c"]),
    ('"truncate table only t_a, only t_b"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE t_a *, t_b *"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE TABLE ONLY t_a, t_b CASCADE"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE t_a, t_b RESTART IDENTITY"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE t_a, t_b CONTINUE IDENTITY RESTRICT"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE TABLE ONLY public.t_a, s.t_b RESTART IDENTITY CASCADE"', ["public.t_a", "s.t_b"]),
    ("'TRUNCATE public.\"t_a\", \"t_b\", \"s\".\"t_c\"'", ["public.t_a", "public.t_b", "s.t_c"]),
    ('"TRUNCATE t_a\\n  , t_b"', ["public.t_a", "public.t_b"]),
    ('"TRUNCATE t_a, t_a"', ["public.t_a"]),
    # a read is not a write: only the table the statement writes counts, in every multi-table form
    ('"DELETE FROM t_a USING t_b WHERE t_a.i = t_b.i"', ["public.t_a"]),
    ('"DELETE FROM ONLY t_a AS a USING t_b b, t_c c WHERE a.i = b.i"', ["public.t_a"]),
    ('"UPDATE t_a SET v = 1 FROM t_b WHERE t_a.i = t_b.i"', ["public.t_a"]),
    ('"UPDATE t_a AS a SET v = b.v FROM t_b b, t_c c WHERE a.i = b.i"', ["public.t_a"]),
    ('"UPDATE ONLY t_a * SET v = 1"', ["public.t_a"]),
    ('"INSERT INTO t_a (x) SELECT x FROM t_b JOIN t_c USING (i)"', ["public.t_a"]),
    ('"INSERT INTO t_a SELECT * FROM t_b"', ["public.t_a"]),
    ('"COPY t_a (x, y) FROM STDIN"', ["public.t_a"]),
    ('"COPY public.t_a (x, y, z) FROM \'/tmp/f.csv\' WITH (FORMAT csv)"', ["public.t_a"]),
    # every write of a CTE chain / of a multi-statement literal
    ('"WITH d AS (DELETE FROM t_a RETURNING *), u AS (UPDATE t_b SET v = 1 RETURNING *) INSERT INTO t_c SELECT * FROM d"',
     ["public.t_a", "public.t_b", "public.t_c"]),
    ('"WITH i AS (INSERT INTO t_a (x) VALUES (1) RETURNING x) INSERT INTO t_b SELECT x FROM i"', ["public.t_a", "public.t_b"]),
    ('"INSERT INTO t_a (x) VALUES (1); INSERT INTO t_b (x) VALUES (2); DELETE FROM t_c; UPDATE t_d SET v = 1"',
     ["public.t_a", "public.t_b", "public.t_c", "public.t_d"]),
    ('"DELETE FROM t_a; TRUNCATE t_b, t_c; COPY t_d FROM STDIN"', ["public.t_a", "public.t_b", "public.t_c", "public.t_d"]),
])
def test_every_written_table_of_a_statement_is_captured_and_reads_are_not(repo, sql, expected):
    assert tables(repo, f"x = {sql}\n") == expected


def test_a_multi_table_truncate_through_constants_and_f_strings_captures_every_item(repo):
    assert tables(repo, 'A = "t_a"\nB = "t_b"\ndef r(c):\n    c.execute(f"TRUNCATE {A}, public.{B} CASCADE")\n') == ["public.t_a", "public.t_b"]


@pytest.mark.parametrize("sql", [
    '"TRUNCATE t_a, %s"',
    '"TRUNCATE t_a, "',
    '"TRUNCATE t_a, {}"',
    '"TRUNCATE %s, t_b"',
    '"TRUNCATE TABLE t_a, , t_b"',
    '"TRUNCATE t_a, (t_b)"',
])
def test_a_truncate_list_item_that_is_not_a_name_makes_the_statement_unresolved(repo, sql):
    res = scan(repo, OWN + f"x = {sql}\n")
    assert "tables" not in res and res["not_scanned"].startswith(("unparseable_write_target", "trailing_write_verb")), res


def test_a_runtime_built_truncate_list_is_unresolved(repo):
    not_scanned(repo, OWN + 'def r(c, tables):\n    c.execute(f"TRUNCATE {\', \'.join(tables)}")\n', "unresolved_table_expression")
    not_scanned(repo, OWN + 'A = "t_a"\ndef r(c, other):\n    c.execute(f"TRUNCATE {A}, {other.t}")\n', "unresolved_table_expression")


def test_a_quoted_name_that_is_not_a_plain_identifier_is_unresolved_not_half_read(repo):
    not_scanned(repo, OWN + 'x = \'INSERT INTO "my table" (x) VALUES (1)\'\n', "unresolved_table_expression")
    not_scanned(repo, OWN + 'x = \'TRUNCATE "a b", t_c\'\n', "unresolved_table_expression")
    assert tables(repo, 'x = \'INSERT INTO public."t_a" (x) VALUES (1)\'\n') == ["public.t_a"]


def test_an_update_whose_target_is_not_a_name_is_unresolved_while_do_update_and_for_update_are_not(repo):
    not_scanned(repo, OWN + 'x = "UPDATE %s SET x = 1"\n', "unparseable_write_target")
    assert tables(repo, OWN + 'x = "UPDATE /* c */ t_b SET x = 1"\n') == ["public.t_a", "public.t_b"]      # a comment is whitespace
    ok = OWN + ('x = "INSERT INTO t_a (x) VALUES (1) ON CONFLICT (x) DO UPDATE SET x = 2"\n'
                'y = "SELECT x FROM t_b FOR UPDATE"\nz = "SELECT x FROM t_b FOR NO KEY UPDATE"\nlabel = "UPDATE"\n')
    assert tables(repo, ok) == ["public.t_a"]


def test_a_copy_whose_target_is_not_a_name_is_unresolved_while_an_export_is_not(repo):
    not_scanned(repo, OWN + 'x = "COPY %s FROM STDIN"\n', "unparseable_write_target")
    not_scanned(repo, OWN + 'x = "COPY {} (a, b) FROM STDIN"\n', "unparseable_write_target")
    assert tables(repo, OWN + 'x = "COPY (SELECT a FROM t_b) TO STDOUT"\ny = "COPY t_b TO STDOUT"\n') == ["public.t_a"]


def test_a_copy_column_list_built_at_runtime_still_resolves_the_table(repo):
    body = 'COLS = ["a", "b"]\ndef r(c):\n    c.copy(f"COPY chart_x ({\', \'.join(COLS)}) FROM STDIN")\n'
    assert tables(repo, body) == ["public.chart_x"]


# ───────────────────── the same forms through the footprint report (partial vs complete) ─────────────────────

def _rows(*pairs):
    return [{"asset_id": a, "target_table": t} for a, t in pairs]


def test_a_second_table_written_by_a_multi_table_truncate_makes_the_scope_partial(repo):
    writer(repo, "a_x", 'def r(c):\n    c.execute("TRUNCATE t_a, t_b")\n')
    rep = slw.footprint_scope(_rows(("a_x", "t_a")), ["t_a"], repo)
    assert rep["footprint_scope"] == "partial" and rep["assets_whose_writer_writes_other_tables"][0]["extra_tables"] == ["public.t_b"]


def test_the_clean_single_table_writer_stays_complete(repo):
    writer(repo, "a_x", OWN + 'def r(c):\n    c.execute(OWN)\n    c.execute("SELECT 1")\n    c.execute("SELECT * FROM t_b")\n')
    rep = slw.footprint_scope(_rows(("a_x", "t_a")), ["t_a"], repo)
    assert rep["footprint_scope"] == "complete" and rep["partial_reasons"] == [] and rep["assets_not_scanned"] == []


# ───────────────────────────────── 2. SQL passed to execute() that this file does not show ─────────────────────────────────

@pytest.mark.parametrize("src", [
    "from .sqls import INSERT_B\ndef r(c):\n    c.execute(INSERT_B)\n",
    "from sqls import INSERT_B as Q\ndef r(c):\n    c.execute(Q)\n",
    "import sqls\ndef r(c):\n    c.execute(sqls.INSERT_B)\n",
    "import pkg.sqls\ndef r(c):\n    c.execute(pkg.sqls.INSERT_B)\n",
    "import pkg.sqls as S\ndef r(c):\n    c.execute(S.INSERT_B)\n",
    "from pkg import sqls\ndef r(c):\n    c.execute(sqls.INSERT_B)\n",
    "from sqls import INSERT_B\ndef r(c, rows):\n    c.executemany(INSERT_B, rows)\n",
    "from sqls import INSERT_B\ndef r(conn):\n    conn.execute(INSERT_B)\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(query=INSERT_B)\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(sql=INSERT_B)\n",
    "from sqls import INSERT_B\ndef r(c, rows):\n    execute_values(c, INSERT_B, rows)\n",
    "from sqls import INSERT_B\ndef r(c, rows):\n    extras.execute_batch(c, INSERT_B, rows)\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(INSERT_B + ' ON CONFLICT DO NOTHING')\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(f'{INSERT_B} ON CONFLICT DO NOTHING')\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(INSERT_B % ())\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(INSERT_B.format(t='x'))\n",
    "from sqls import INSERT_B\ndef r(c):\n    c.execute(INSERT_B.strip())\n",
    "from sqls import INSERT_B\ncond = True\ndef r(c):\n    c.execute(cond and INSERT_B)\n",
    "from sqls import A, B\ndef r(c, f):\n    c.execute(A if f else B)\n",
    "from sqls import INSERT_B\nQ = INSERT_B\ndef r(c):\n    c.execute(Q)\n",                 # via a local alias
    "from sqls import INSERT_B\nclass W:\n    SQL = INSERT_B\n    def r(self, c):\n        c.execute(self.SQL)\n",
    "from sqls import QS\ndef r(c):\n    c.execute(QS[0])\n",
    "from sqls import A\ndef r(c):\n    c.execute(' '.join([A, 'x']))\n",
    "from sqls import A\ndef r(c):\n    c.execute((A, 'x'))\n",
    "from sqls import A\ndef r(c):\n    c.execute(str(A))\n",
    "from sqls import A\ndef r(c):\n    c.execute([A for _ in range(1)])\n",
    "from sqls import INSERT_B\ndef r(c, rows):\n    c.copy_expert(INSERT_B, rows)\n",
])
def test_an_imported_sql_constant_mixed_with_an_own_write_is_not_scanned(repo, src):
    res = scan(repo, OWN + src)
    assert "tables" not in res and res["not_scanned"].startswith("imported_sql_constant"), (src, res)


def test_the_imported_constant_reason_names_the_constant_and_reaches_the_footprint_report(repo):
    writer(repo, "a_x", OWN + "from .sqls import INSERT_B\ndef r(c):\n    c.execute(INSERT_B)\n")
    rep = slw.footprint_scope(_rows(("a_x", "t_a")), ["t_a"], repo)
    assert rep["footprint_scope"] == "partial" and rep["partial_reasons"] == ["writer_not_scanned"]
    assert rep["assets_not_scanned"] == [{"asset_id": "a_x", "reason": "imported_sql_constant: INSERT_B"}]


@pytest.mark.parametrize("src,reason", [
    ("def r(c):\n    c.execute(build_sql())\n", "sql_from_call_result"),
    ("from helpers import make\ndef r(c):\n    c.execute(make('t_b'))\n", "sql_from_call_result"),
    ("import helpers\ndef r(c):\n    c.execute(helpers.make('t_b'))\n", "sql_from_call_result"),
    ("def r(c, cfg):\n    c.execute(cfg.get('sql'))\n", "unresolved_sql_parameter"),
    ("def r(c, q):\n    c.execute(q['insert_b'])\n", "sql_from_subscript"),
    ("QS = compute()\ndef r(c):\n    c.execute(QS['b'])\n", "sql_from_subscript"),
    ("def r(c):\n    c.execute(Q[0])\n", "sql_from_subscript"),
    ("def r(c):\n    c.execute(f'{stmt} t_b')\n", "unresolved_sql_name"),
    ("def r(c):\n    c.execute(f'{STMT} t_b')\n", "unresolved_sql_name"),
    ("def r(c):\n    c.execute(f'{make()} t_b')\n", "sql_from_call_result"),
    ("def r(c):\n    c.execute(f'{cfg.stmt} t_b')\n", "unresolved_sql_attribute"),
    ("def r(c):\n    c.execute(f'SELECT 1; {make()}')\n", "sql_from_call_result"),
    ("def r(c):\n    c.execute(MISSING)\n", "unresolved_sql_name"),
    ("class W:\n    def r(self, c):\n        c.execute(self.sql)\n", "unresolved_sql_attribute"),
    ("def r(c, o):\n    c.execute(o.sql)\n", "unresolved_sql_attribute"),
    ("Q = make_sql()\ndef r(c):\n    c.execute(Q)\n", "sql_from_call_result"),
    ("def r(c):\n    q = make_sql()\n    c.execute(q)\n", "sql_from_call_result"),
    ("def r(c):\n    q = 'SELECT 1'\n    q += make_more()\n    c.execute(q)\n", "sql_from_call_result"),
    ("def r(c):\n    c.execute(b'SELECT 1')\n", "bytes_sql_literal"),
    ("def r(c, rows):\n    c.copy_expert(make(), rows)\n", "sql_from_call_result"),
])
def test_other_execute_arguments_this_file_cannot_show_are_not_scanned(repo, src, reason):
    res = scan(repo, OWN + src)
    assert "tables" not in res and res["not_scanned"].startswith(reason), (src, res)


@pytest.mark.parametrize("src", [
    "LOCAL = 'INSERT INTO t_a (x) VALUES (1)'\ndef r(c):\n    c.execute(LOCAL)\n",
    "def r(c):\n    c.execute('SELECT 1')\n",
    "def r(c, sql):\n    c.execute(sql)\nr(None, 'SELECT 1')\n",                       # a parameter every call site of which passes a literal
    "def r(c, sql, rows):\n    c.executemany(sql, rows)\nr(None, OWN, [])\nr(None, 'SELECT 2', [])\n",
    "def r(c, t):\n    c.execute(f'DELETE FROM {t} WHERE x = 1')\n    r(c, 't_a')\n",
    "T = 't_a'\ndef r(c):\n    c.execute(f'DELETE FROM {T} WHERE x = 1')\n",
    "def r(c):\n    c.execute('SELECT * FROM t_b WHERE x = %s', (1,))\n",
    "def r(c):\n    c.execute('SELECT x FROM t_b ' + 'WHERE y = 1')\n",
    "def r(c):\n    c.execute('SELECT x FROM t_b WHERE y = {}'.format(1))\n",
    "def r(c):\n    c.execute('SELECT x FROM t_b WHERE y = %s' % 1)\n",
    "import textwrap\ndef r(c):\n    c.execute(textwrap.dedent('SELECT 1'))\n",
    "from sqlalchemy import text\ndef r(c):\n    c.execute(text('SELECT 1'))\n",
    "def helper():\n    return 'SELECT 1'\ndef r(c):\n    c.execute(helper())\n",
    "class W:\n    def sql(self):\n        return 'SELECT 1'\n    def r(self, c):\n        c.execute(self.sql())\n",
    "QS = {'a': 'SELECT 1', 'b': 'SELECT 2'}\ndef r(c):\n    c.execute(QS['a'])\n",
    "QS = ('SELECT 1', 'SELECT 2')\ndef r(c):\n    for q in QS:\n        c.execute(q)\n",
    "class W:\n    SQL = 'SELECT 1'\n    def r(self, c):\n        c.execute(self.SQL)\n",
    "def r(c, f):\n    c.execute('SELECT 1' if f else 'SELECT 2')\n",
    "def r(c):\n    c.execute(','.join(['SELECT 1', 'SELECT 2']))\n",
    "def r(c, cols):\n    c.execute(f'SELECT {cols} FROM t_b')\nr(None, 'a, b')\n",
    "def r(c, ph):\n    c.execute('INSERT INTO t_a (x) VALUES (' + ph + ')')\nr(None, '%s')\n",
    "import os\ndef r():\n    return os.path.join('a', 'b')\n",                           # an import that feeds no execute()
    "def r(c, rows):\n    c.copy_expert('COPY t_a FROM STDIN', rows)\n",
    "def r(c):\n    c.execute(f'SELECT 1; SELECT 2')\n",
    "def r(o):\n    return o.copy()\n",                                                     # dict.copy() takes no SQL
])
def test_positive_controls_the_clean_single_table_writer_stays_complete(repo, src):
    writer(repo, "a_x", OWN + src)
    res = slw.scan_writer_tables("a_x", repo)
    assert res.get("tables") == ["public.t_a"], (src, res)


def test_an_imported_name_that_never_reaches_execute_does_not_make_the_writer_not_scanned(repo):
    assert tables(repo, OWN + "from sqls import INSERT_B\nimport json\ndef r(c):\n    c.execute(OWN)\n    return INSERT_B\n") == ["public.t_a"]


# ───────────────────────────────── 3. a literal that ends in a write verb ─────────────────────────────────

@pytest.mark.parametrize("src", [
    'def r(c, tbl):\n    c.execute(" ".join(["INSERT INTO", tbl, "(a) VALUES (1)"]))\n',
    'def r(c, tbl):\n    c.execute("".join(["INSERT INTO ", tbl, " (a) VALUES (1)"]))\n',
    'def r(c, tbl):\n    c.execute(" ".join(["DELETE FROM", tbl]))\n',
    'def r(c, tbl):\n    c.execute(" ".join(["TRUNCATE", tbl]))\n',
    'def r(c, tbl):\n    c.execute(" ".join(["TRUNCATE TABLE", tbl]))\n',
    'def r(c, tbl):\n    c.execute("".join(["UPDATE ", tbl, " SET x = 1"]))\n',
    'def r(c, tbl):\n    c.execute("".join(["COPY ", tbl, " FROM STDIN"]))\n',
    'def r(c, tbl):\n    c.execute("INSERT INTO " + tbl + " (a) VALUES (1)")\n',
    'def r(c, tbl):\n    c.execute("DELETE FROM %s" % tbl)\n',
    'VERB = "INSERT INTO"\n',
    'VERB = "INSERT INTO "\n',
    'VERB = "delete from"\n',
    'VERB = "TRUNCATE"\n',
    'VERB = "TRUNCATE TABLE "\n',
    'VERB = "UPDATE "\n',
    'VERB = "COPY "\n',
    'SQL = "WITH x AS (SELECT 1) INSERT INTO"\n',
    'SQL = "SELECT 1; DELETE FROM  \\n"\n',
])
def test_a_literal_that_ends_in_a_write_verb_with_no_target_is_not_scanned(repo, src):
    res = scan(repo, OWN + src)
    assert "tables" not in res and res["not_scanned"].startswith(("trailing_write_verb_without_target", "unresolved_table_expression",
                                                                   "unresolved_table_argument", "parametric_table_helper", "unresolved_sql_parameter",
                                                                   "unparseable_write_target")), (src, res)


@pytest.mark.parametrize("literal", ["INSERT INTO", "INSERT INTO ", "insert  into\n", "DELETE FROM", "delete from ", "UPDATE ", "COPY ",
                                     "WITH x AS (SELECT 1) INSERT INTO", "SELECT 1; DELETE FROM  \n", "TRUNCATE", "TRUNCATE TABLE"])
def test_the_trailing_verb_rule_itself_fires_on_each_verb_form(literal):
    sc = slw._WriteScan(__import__("ast").parse(f"X = {literal!r}\n"))
    assert any(r.startswith("trailing_write_verb_without_target") for r in sc.unresolved), (literal, sc.unresolved)


@pytest.mark.parametrize("literal", ["UPDATE", "COPY", "SELECT x FROM t FOR UPDATE", "SELECT x FROM t FOR UPDATE ", "ON CONFLICT DO UPDATE ",
                                     "AFTER INSERT OR UPDATE ", "ON UPDATE ", "BEFORE UPDATE ", "FOR NO KEY UPDATE ", "TRIGGER x UPDATE OF ",
                                     "the INSERT INTO verb is documented elsewhere", "UPDATE t SET x = 1", "DELETE FROM t"])
def test_the_trailing_verb_rule_does_not_fire_on_labels_lock_clauses_or_complete_statements(literal):
    sc = slw._WriteScan(__import__("ast").parse(f"X = {literal!r}\n"))
    assert not any(r.startswith("trailing_write_verb_without_target") for r in sc.unresolved), (literal, sc.unresolved)


def test_the_split_verb_join_is_rendered_so_a_resolvable_table_is_captured_and_a_runtime_one_is_not(repo):
    assert tables(repo, 'T = "t_b"\ndef r(c):\n    c.execute(" ".join(["INSERT", "INTO", T, "(a) VALUES (1)"]))\n') == ["public.t_b"]
    not_scanned(repo, OWN + 'def r(c, o):\n    c.execute(" ".join(["INSERT", "INTO", o.t, "(a) VALUES (1)"]))\n', "unresolved_table_expression")


def test_a_trailing_update_or_copy_that_is_not_a_statement_is_not_flagged(repo):
    ok = OWN + ('A = "SELECT x FROM t_b FOR UPDATE"\nB = "SELECT x FROM t_b FOR NO KEY UPDATE "\nC = "UPDATE"\nD = "COPY"\n'
                'E = "AFTER INSERT OR UPDATE "\nF = "ON CONFLICT DO UPDATE "\n')
    assert tables(repo, ok) == ["public.t_a"]


# ───────────────────────────────── 4. a dotted name is never a table constant ─────────────────────────────────

@pytest.mark.parametrize("src", [
    'T = "t_b"\ndef r(c, cfg):\n    c.execute(f"DELETE FROM {cfg.T} WHERE x = 1")\n',
    'T = "t_b"\ndef r(c, cfg):\n    c.execute(f"INSERT INTO public.{cfg.T} (x) VALUES (1)")\n',
    'T = "t_b"\ndef r(c, a):\n    c.execute(f"TRUNCATE {a.b.T}")\n',
    'class W:\n    T = "t_b"\n    def r(self, c):\n        c.execute(f"DELETE FROM {self.T} WHERE x = 1")\n',
    'class W:\n    T = "t_b"\n    def r(self, c):\n        c.execute(f"DELETE FROM {W.T} WHERE x = 1")\n',
    'import mod\nT = "t_b"\ndef r(c):\n    c.execute(f"DELETE FROM {mod.T} WHERE x = 1")\n',
    'T = "t_b"\ndef r(c, cfg):\n    c.execute(f"UPDATE {cfg.T} SET x = 1")\n',
])
def test_a_dotted_or_attribute_name_never_resolves_to_a_local_constant_with_the_same_last_segment(repo, src):
    not_scanned(repo, OWN + src, "unresolved_table_expression")


def test_a_dotted_argument_to_a_parametric_helper_is_not_a_literal_table(repo):
    body = OWN + ('T = "t_b"\ndef wipe(c, tbl):\n    c.execute(f"DELETE FROM {tbl} WHERE x = 1")\n'
                  'def r(c, cfg):\n    wipe(c, cfg.T)\n    wipe(c, "t_a")\n')
    writer(repo, "a_x", body)
    sc = slw._WriteScan(__import__("ast").parse((repo / WRITERS / "a_x.py").read_text()))
    sc.resolve_param_calls()
    assert any(r.startswith("unresolved_table_argument") for r in sc.unresolved), sc.unresolved
    assert "tables" not in slw.scan_writer_tables("a_x", repo)


def test_a_plain_name_constant_still_resolves(repo):
    assert tables(repo, 'T = "t_b"\ndef r(c):\n    c.execute(f"DELETE FROM {T} WHERE x = 1")\n') == ["public.t_b"]


# ───────────────────────────────── 5. exotic forms are listed as NOT SCANNED ─────────────────────────────────

@pytest.mark.parametrize("src,reason", [
    ('B = b"INSERT INTO t_b (x) VALUES (1)"\n', "bytes_sql_literal"),
    ('B = b"delete from t_b"\n', "bytes_sql_literal"),
    ('B = b"TRUNCATE t_b, t_c"\n', "bytes_sql_literal"),
    ('def r(c):\n    c.execute(b"UPDATE t_b SET x = 1")\n', "bytes_sql_literal"),
    ('def r(cur, f):\n    cur.copy_from(f, "t_b")\n', "copy_api_without_sql_text"),
    ('def r(cur, f):\n    cur.copy_from(f, TABLE)\n', "copy_api_without_sql_text"),
    ('async def r(conn, rows):\n    await conn.copy_records_to_table("t_b", records=rows)\n', "copy_api_without_sql_text"),
    ('async def r(conn):\n    await conn.copy_to_table("t_b", source="f.csv")\n', "copy_api_without_sql_text"),
    ('def r(cur):\n    cur.execute(r.__doc__)\n', "sql_from_dunder_attribute"),
    ('class W:\n    """INSERT INTO t_b (x) VALUES (1)"""\n    def r(self, cur):\n        cur.execute(W.__doc__)\n', "sql_from_dunder_attribute"),
    ('def r(cur):\n    cur.execute(inspect.getdoc(r))\n', "sql_from_call_result"),
    ('def r(o):\n    setattr(o, "SQL", "INSERT INTO t_b VALUES (1)")\n', "runtime_rebinding"),
    ('import sys\ndef r():\n    setattr(sys.modules[__name__], "OWN", "x")\n', ("runtime_rebinding", "dynamic_dispatch")),
    ('globals()["T"] = "t_b"\n', "runtime_rebinding"),
    ('def r(n, v):\n    locals()[n] = v\n', "runtime_rebinding"),
    ('def r(n, v):\n    vars()[n] = v\n', "runtime_rebinding"),
    ('globals().update(T="t_b")\n', "runtime_rebinding"),
    ('def r(d):\n    globals().setdefault("T", d)\n', "runtime_rebinding"),
    ('from helpers import *\n', "dynamic_binding"),
    ('from .helpers import *\n', "dynamic_binding"),
    ('exec("x = 1")\n', "dynamic_code"),
    ('def r(s):\n    return eval(s)\n', "dynamic_code"),
    ('def r(s):\n    return compile(s, "f", "exec")\n', "dynamic_code"),
    ('def r(cur):\n    getattr(cur, "execute")("DELETE FROM t_b")\n', "dynamic_dispatch"),
    ('def r(cur, name):\n    getattr(cur, name)("DELETE FROM t_b")\n', "dynamic_dispatch"),
    ('def r(cur):\n    fn = getattr(cur, "executemany")\n    fn("x", [])\n', "dynamic_dispatch"),
    ('def r(cur):\n    fn = getattr(cur, "copy_from")\n', "dynamic_dispatch"),
])
def test_an_exotic_write_form_is_listed_as_not_scanned_with_a_named_reason(repo, src, reason):
    res = scan(repo, OWN + src)
    assert "tables" not in res and res["not_scanned"].startswith(reason), (src, res)


@pytest.mark.parametrize("src", [
    'B = b"\\x00\\x01 not sql"\n',
    'import hashlib\nH = hashlib.sha256(b"salt").hexdigest()\n',
    'def r(o):\n    return getattr(o, "close", None)\n',                                  # a literal attribute read with a default
    'def r(o, k):\n    return o.__dict__.get(k)\n',
    'def r(idx, v):\n    idx.__dict__["_cache"] = v\n',                                   # per-object state, not module rebinding
    'def r(o):\n    return getattr(o, "x", None)\n',
    'import copy\ndef r(o):\n    return copy.copy(o)\n',
    'def r(x):\n    return compile_regex(x)\n',
    'def r(d):\n    return d.copy()\n',
])
def test_exotic_form_positive_controls_stay_complete(repo, src):
    res = scan(repo, OWN + src)
    assert res.get("tables") == ["public.t_a"], (src, res)


# ───────────────────────────────── 6. source_paths that is mutated is not followed ─────────────────────────────────

@pytest.mark.parametrize("body", [
    'class W:\n    source_paths = ["a.py"]\n    source_paths.append("b.py")\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths += ["b.py"]\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.extend(["b.py"])\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.insert(0, "b.py")\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths[0] = "b.py"\n',
    'class W:\n    source_paths = ["a.py"]\n    del source_paths[0]\n',
    'class W:\n    source_paths = ["a.py"]\n    del source_paths\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.clear()\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.pop()\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.remove("a.py")\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.sort()\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.reverse()\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths *= 2\n',
    'class W:\n    source_paths = ["a.py"]\n    source_paths.__iadd__(["b.py"])\n',
    'class W:\n    source_paths = ["a.py"]\n    (source_paths := ["b.py"])\n',
    'class W:\n    source_paths = ["a.py"]\ndef r():\n    W.source_paths.append("b.py")\n',
    'class W:\n    source_paths = ["a.py"]\n    def r(self):\n        self.source_paths += ["b.py"]\n',
    'class W:\n    source_paths = ["a.py"]\n    def r(self):\n        self.source_paths[1:] = ["b.py"]\n',
    'class W:\n    source_paths = ["a.py"]\nsetattr(W, "source_paths", ["b.py"])\n',
    'source_paths = ["a.py"]\nsource_paths.append("b.py")\n',
])
def test_a_mutated_source_paths_is_not_followed(repo, body):
    write(repo, "platform/python-sidecar/ga_writers/a.py", 'SQL = "INSERT INTO t_a (x) VALUES (1)"\n')
    write(repo, "platform/python-sidecar/ga_writers/b.py", 'SQL = "INSERT INTO t_b (x) VALUES (1)"\n')
    # the delegate sits in a.py/b.py (outside the writers dir) -- source paths are repo-relative
    body = body.replace('"a.py"', '"platform/python-sidecar/ga_writers/a.py"').replace('"b.py"', '"platform/python-sidecar/ga_writers/b.py"')
    res = scan(repo, body + OWN)
    assert "tables" not in res and res["not_scanned"] == "source_paths_mutated_at_runtime", (body, res)


def test_an_unmutated_source_paths_is_followed_and_an_attribute_form_assignment_is_a_literal_too(repo):
    write(repo, "platform/python-sidecar/ga_writers/a.py", 'SQL = "INSERT INTO t_a (x) VALUES (1)"\n')
    write(repo, "platform/python-sidecar/ga_writers/b.py", 'SQL = "INSERT INTO t_b (x) VALUES (1)"\n')
    res = scan(repo, 'class W:\n    source_paths = ["platform/python-sidecar/ga_writers/a.py"]\n'
                     'W2 = type("W2", (), {})\nW.source_paths = ["platform/python-sidecar/ga_writers/b.py"]\n')
    assert res["tables"] == ["public.t_a", "public.t_b"]
    res = scan(repo, 'class W:\n    source_paths = ["platform/python-sidecar/ga_writers/a.py"]\n    names = []\n    names.append("x")\n')
    assert res["tables"] == ["public.t_a"]
    res = scan(repo, 'class W:\n    source_paths = ["platform/python-sidecar/ga_writers/a.py"]\n    def r(self):\n        return len(self.source_paths)\n')
    assert res["tables"] == ["public.t_a"]


# ───────────────────────────────── 7. hostile input ─────────────────────────────────

def _py_literal(text: str) -> str:
    return "SQL = " + repr(text) + "\n"


HOSTILE_32K = {
    "select": "SELECT " * 4700,
    "select_into_never": "SELECT x " * 3700,
    "insert_into": "INSERT INTO " * 2700,
    "copy_open_paren": "COPY a (" * 4000,
    "copy_nested_paren": "COPY a (" + "(" * 32000,
    "update": "UPDATE a " * 3600,
    "update_set_late": "UPDATE a " * 3500 + "SET",
    "truncate_comma": "TRUNCATE a," * 2900,
    "truncate_comma_space": "TRUNCATE a, " * 2700,
    "truncate_only": "TRUNCATE " * 3600,
    "control_chars": "\x01" * 32000,
    "control_chars_mixed": "INSERT INTO \x01a" * 2400,
    "create": "CREATE " * 4600,
    "quotes": '"' * 32000,
    "insert_quote": 'INSERT INTO "' * 2500,
    "spaces": "INSERT" + " " * 32000 + "x",
    "delete_using": "DELETE FROM a USING " * 1600,
    "dots": "INSERT INTO a." * 2100,
    "with_open": "WITH x AS ( " * 2700,
    "select_insert": "SELECT INSERT " * 2300,
    "into_only": "INTO " * 6400,
    "update_words": "UPDATE " * 4600,
    "copy_words": "COPY " * 6400,
}


@pytest.mark.parametrize("name", sorted(HOSTILE_32K))
def test_a_hostile_32kb_literal_scans_in_bounded_time_and_never_reads_as_clean(repo, name):
    text = HOSTILE_32K[name]
    assert 20_000 < len(text) <= 40_000
    writer(repo, "a_x", OWN + _py_literal(text))
    t0 = time.perf_counter()
    res = slw.scan_writer_tables("a_x", repo)
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, (name, elapsed)  # wall-clock guard against quadratic/exponential blow-ups (seconds when broken); loose for loaded CI
    assert "tables" in res or "not_scanned" in res


@pytest.mark.parametrize("unit,n", [("TRUNCATE a,", 5800), ("TRUNCATE a, ", 5400), ("INSERT INTO a ", 4600), ("DELETE FROM a USING ", 3200),
                                    ("COPY a (", 8000), ("UPDATE a ", 7200), ("SELECT x ", 7200)])
def test_a_hostile_literal_just_under_the_64kb_cap_is_still_bounded(repo, unit, n):
    text = unit * n
    assert 30_000 < len(text) <= slw.MAX_SQL_LITERAL_CHARS, len(text)
    writer(repo, "a_x", OWN + _py_literal(text))
    t0 = time.perf_counter()
    slw.scan_writer_tables("a_x", repo)
    assert time.perf_counter() - t0 < 5.0  # wall-clock guard against quadratic/exponential blow-ups (seconds when broken); loose for loaded CI


def test_select_into_is_linear_on_the_reported_hostile_input(repo):
    text = "SELECT " * 4700                                       # 32.9 KB: the single regex took 1.9 s here
    assert len(text) > 32_000
    t0 = time.perf_counter()
    hit = slw._select_into(text)
    elapsed = time.perf_counter() - t0
    assert hit is False and elapsed < 0.05, elapsed
    t0 = time.perf_counter()
    assert slw._select_into("SELECT x " * 7000 + " INTO t") is True
    assert time.perf_counter() - t0 < 0.05


_OLD_SELECT_INTO = re.compile(r"\bSELECT\b(?:(?!\b(?:INSERT|FROM|UPDATE|DELETE)\b)[\s\S])*?\bINTO\b", re.IGNORECASE)


@pytest.mark.parametrize("text", [
    "SELECT a INTO t FROM s", "select a, b into temp t_new from s", "SELECT a FROM s", "INSERT INTO t SELECT a FROM s",
    "INSERT INTO t (a) SELECT a FROM s INTO", "SELECT a FROM s; SELECT b INTO t", "SELECT 1; INSERT INTO t VALUES (1)",
    "SELECT a UPDATE b INTO c", "SELECT (SELECT 1) INTO t", "WITH s AS (SELECT 1) SELECT x INTO t FROM s", "INTO", "SELECT",
    "SELECT a DELETE x INTO", "SELECT a FROM s INTO", "select into", "SELECTINTO", "SELECT x INTO_t", "SELECT intoo INTO t",
    "SELECT a FROM s WHERE b IN (SELECT c INTO d)", "FROM SELECT INTO", "INSERT SELECT INTO", "SELECT INSERT INTO t",
])
def test_the_linear_select_into_detector_agrees_with_the_regex_it_replaced(text):
    assert slw._select_into(text) == bool(_OLD_SELECT_INTO.search(text)), text


def test_a_literal_over_64kb_is_not_scanned_and_fast(repo):
    assert slw.MAX_SQL_LITERAL_CHARS == 64 * 1024
    big = "SELECT 1 /* " + "x" * 200_000 + " */"
    writer(repo, "a_x", OWN + _py_literal(big))
    t0 = time.perf_counter()
    res = slw.scan_writer_tables("a_x", repo)
    assert time.perf_counter() - t0 < 5.0  # wall-clock guard against quadratic/exponential blow-ups (seconds when broken); loose for loaded CI
    assert "tables" not in res and res["not_scanned"].startswith("sql_literal_too_long"), res
    # a long literal that WOULD have shown a write is not read as clean either
    writer(repo, "a_y", OWN + _py_literal("INSERT INTO t_b (x) VALUES (1) -- " + "z" * 200_000))
    assert slw.scan_writer_tables("a_y", repo)["not_scanned"].startswith("sql_literal_too_long")


def test_the_literal_length_limit_is_exactly_64kb(repo):
    ok = "INSERT INTO t_b (x) VALUES (1) -- " + "z" * (slw.MAX_SQL_LITERAL_CHARS - len("INSERT INTO t_b (x) VALUES (1) -- "))
    assert len(ok) == slw.MAX_SQL_LITERAL_CHARS
    writer(repo, "a_x", _py_literal(ok))
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_b"]
    writer(repo, "a_y", _py_literal(ok + "z"))
    assert slw.scan_writer_tables("a_y", repo)["not_scanned"].startswith("sql_literal_too_long")


def test_a_long_f_string_or_concatenation_is_measured_after_rendering(repo):
    parts = " + ".join(['"' + "y" * 9000 + '"'] * 8)                # 72 KB once joined
    writer(repo, "a_x", OWN + f"SQL = {parts}\n")
    assert slw.scan_writer_tables("a_x", repo)["not_scanned"].startswith("sql_literal_too_long")
    writer(repo, "a_y", OWN + 'def r(c, x):\n    c.execute(f"' + "y" * 70_000 + '{x}")\n')
    assert slw.scan_writer_tables("a_y", repo)["not_scanned"].startswith("sql_literal_too_long")


def test_a_literal_control_character_never_reads_as_a_runtime_placeholder(repo):
    # \x01 \x02 are the scan's own placeholder delimiters; a literal carrying them must not be able to forge one
    res = scan(repo, 'T = "t_b"\nx = "INSERT INTO \\x01T\\x02 (x) VALUES (1)"\n')
    assert res.get("tables") == ["public.t"], res                # the cleaned literal reads as a plain name T, never the constant


# ───────────────────────────────── 8. pins ─────────────────────────────────

def test_the_files_list_is_a_relative_posix_path_string_for_the_writer_and_each_source_path(repo):
    write(repo, "platform/python-sidecar/ga_writers/a_x_writer.py", 'SQL = "INSERT INTO t_a (x) VALUES (1)"\n')
    writer(repo, "a_x", 'class W:\n    source_paths = ["platform/python-sidecar/ga_writers/a_x_writer.py"]\n')
    res = slw.scan_writer_tables("a_x", repo)
    assert res["files"] == ["platform/python-sidecar/pipeline/orchestrator/writers/a_x.py",
                            "platform/python-sidecar/ga_writers/a_x_writer.py"]
    assert all(isinstance(f, str) and not f.startswith("/") and "\\" not in f for f in res["files"])
    writer(repo, "a_y", OWN)
    assert slw.scan_writer_tables("a_y", repo)["files"] == [f"{WRITERS}/a_y.py"]


def test_the_files_path_survives_a_relative_repo_argument(repo, monkeypatch):
    writer(repo, "a_y", OWN)
    monkeypatch.chdir(repo)
    assert slw.scan_writer_tables("a_y", ".")["files"] == [f"{WRITERS}/a_y.py"]


BINDING_FORMS = {
    "async_with": 'async def g(f):\n    async with f() as tbl:\n        pass\n',
    "async_with_tuple": 'async def g(f):\n    async with f() as (tbl, other):\n        pass\n',
    "async_for": 'async def g(it):\n    async for tbl in it:\n        pass\n',
    "async_def_name": 'async def tbl():\n    pass\n',
    "async_def_param": 'async def g(tbl):\n    pass\n',
    "async_comprehension": 'async def g(it):\n    return [tbl async for tbl in it]\n',
    "tuple_unpack": 'tbl, other = pair()\n',
    "list_unpack": '[tbl, other] = pair()\n',
    "nested_unpack": '(a, (tbl, c)), d = nested()\n',
    "starred_unpack": 'first, *tbl = pair()\n',
    "for_unpack": 'for k, tbl in pairs():\n    pass\n',
    "with_unpack": 'with ctx() as (tbl, other):\n    pass\n',
    "literal_tuple_unpack": 'tbl, other = "t_x", "t_y"\n',                          # a literal on the right is still an unpack
}


@pytest.mark.parametrize("kind", sorted(BINDING_FORMS))
def test_async_and_unpacking_bindings_make_a_constant_unresolved(repo, kind):
    res = scan(repo, 'tbl = "own"\ndef run(conn):\n    conn.execute(f"DELETE FROM {tbl} WHERE x = 1")\n' + BINDING_FORMS[kind])
    assert "tables" not in res and res["not_scanned"].startswith("unresolved_table_expression"), (kind, res)


def test_the_binding_controls_resolve_when_nothing_else_binds_the_name(repo):
    assert tables(repo, 'tbl = "own"\ndef run(conn):\n    conn.execute(f"DELETE FROM {tbl} WHERE x = 1")\n') == ["public.own"]


def test_no_opener_before_helper_remains_in_the_scan_path():
    # the finding named `_opener_before` (a nested-group decrement); this scan has no such helper, so there is nothing to pin
    assert not hasattr(slw, "_opener_before")
    assert not hasattr(slw._WriteScan, "_opener_before")


# ───────────────────────────────── real tree: read (never imported), no exception ─────────────────────────────────

def _real_writer_files():
    return sorted((REAL_REPO / WRITERS).glob("*.py"))


def test_every_real_writer_file_scans_without_an_exception_and_imports_nothing():
    files = _real_writer_files()
    assert len(files) >= 100
    before = set(sys.modules)
    helpers = slw.helper_write_effects(REAL_REPO)
    scanned = not_scanned = 0
    for f in files:
        res = slw.scan_writer_tables(f.stem, REAL_REPO, helpers)
        assert ("tables" in res) != ("not_scanned" in res), (f.name, res)
        if "tables" in res:
            scanned += 1
            assert res["tables"] and all(isinstance(t, str) and t for t in res["tables"])
            assert res["files"][0] == f"{WRITERS}/{f.name}"
        else:
            not_scanned += 1
            assert res["not_scanned"] and not res["not_scanned"].startswith("scan_error"), (f.name, res)
    assert scanned + not_scanned == len(files) and scanned > 0 and not_scanned > 0
    assert {m for m in set(sys.modules) - before if m.split(".")[0] in {"pipeline", "ga_writers", "bodha_writers"}} == set()


def test_real_ga_dashas_copy_with_a_runtime_column_list_still_resolves_its_tables():
    res = slw.scan_writer_tables("ga_dashas", REAL_REPO)
    assert "public.chart_dashas" in res["tables"], res


def test_real_ga_vichara_object_dict_assignment_is_not_runtime_rebinding():
    res = slw.scan_writer_tables("ga_vichara", REAL_REPO)
    assert res["tables"] == ["public.chart_vichara"], res


def test_the_scan_limitations_list_names_the_new_rules():
    text = "\n".join(slw.WRITE_SCAN_LIMITATIONS)
    for needle in ("imported_sql_constant", "bytes literal", "copy_from", "exec/eval/compile", "setattr", "globals()",
                   "import *", "getattr(", "ends in a write verb", "dotted or attribute name", "64 KB", "source_paths list that is mutated"):
        assert needle in text, needle
