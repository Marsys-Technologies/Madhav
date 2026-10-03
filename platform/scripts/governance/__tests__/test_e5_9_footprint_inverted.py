"""test_e5_9_footprint_inverted.py -- Suvarna E5.9 / FP2 review round: the CLOSED allow-list (inverted default).

The first FP2 pass patched SHAPES; the adversarial review found more shapes. The default is now inverted: SQL handed to an
execute-like call is `clean` only when it is positively recognised as made of this file's own literals (a literal, an
f-string / `+` / format / join of clean parts, a name every binding of which is clean, a parameter whose in-file call sites ALL
pass clean values, a loop variable over a clean literal container, a class attribute assigned once in the class body, a local
function that returns only clean values). Everything else is NOT SCANNED with a named reason. Also here: SQL comments are
whitespace (F1/F4), UPDATE / COPY with a runtime tail (F3), the resolver work cap and its hostile files (F5), the lookahead /
branch pins (F6), and the cheap F7 forms.

Offline: writers are tmp-dir fixtures; nothing is imported or executed (ast only).
"""
from __future__ import annotations

import pathlib
import sys
import textwrap
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_level_wave as slw  # noqa: E402

REAL_REPO = HERE.parents[3]
WRITERS = slw.WRITERS_REL
OWN = 'OWN = "INSERT INTO t_a (x) VALUES (1)"\n'
IMP = "from sqls import Q\n"


def write(repo: pathlib.Path, rel: str, body: str) -> pathlib.Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "platform/python-sidecar/ga_writers/_idempotency.py", "def noop():\n    return 1\n")
    write(tmp_path, "platform/python-sidecar/bodha_writers/_idempotency.py", "def noop():\n    return 1\n")
    return tmp_path


def scan(repo, body, asset="a_x"):
    write(repo, f"{WRITERS}/{asset}.py", body)
    return slw.scan_writer_tables(asset, repo)


def partial(repo, body, reason=None):
    res = scan(repo, body)
    assert "tables" not in res, ("read COMPLETE: " + body, res)
    if reason:
        assert res["not_scanned"].startswith(reason), (body, res)
    return res["not_scanned"]


def complete(repo, body, expected=("public.t_a",)):
    res = scan(repo, body)
    assert res.get("tables") == list(expected), (body, res)


# ───────────────────── F1 / F4: SQL comments are whitespace ─────────────────────

@pytest.mark.parametrize("sql,expected", [
    ('"TRUNCATE a /* x */, b"', ["public.a", "public.b"]),
    ('"TRUNCATE a -- x\\n , b"', ["public.a", "public.b"]),
    ('"TRUNCATE a/*c*/,b"', ["public.a", "public.b"]),
    ('"TRUNCATE /* c */ a, /* d */ b -- e"', ["public.a", "public.b"]),
    ('"TRUNCATE a /* c /* nested */ still */, b"', ["public.a", "public.b"]),
    ('"INSERT /* c */ INTO a (x) VALUES (1)"', ["public.a"]),
    ('"INSERT -- c\\n INTO a (x) VALUES (1)"', ["public.a"]),
    ('"DELETE /* c */ FROM a"', ["public.a"]),
    ('"DELETE -- c\\n FROM a"', ["public.a"]),
    ('"INSERT INTO ONLY /* c */ a (x) VALUES (1)"', ["public.a"]),
    ('"INSERT INTO /* c */ a (x) VALUES (1)"', ["public.a"]),
    ('"UPDATE /* c */ a SET x = 1"', ["public.a"]),
    ('"UPDATE a /* c */ SET x = 1"', ["public.a"]),
    ('"COPY /* c */ a (x) FROM STDIN"', ["public.a"]),
    ('"INSERT/**/INTO a (x) VALUES (1)"', ["public.a"]),
    ('"SELECT 1 /* INSERT INTO b */; DELETE FROM a"', ["public.a", "public.b"]),     # raw text still names b (over-report only)
])
def test_a_sql_comment_is_whitespace_so_it_cannot_hide_a_verb_or_a_list_item(repo, sql, expected):
    res = scan(repo, f"x = {sql}\n")
    assert res.get("tables") == expected, res


@pytest.mark.parametrize("sql,label", [
    ('"CREATE /* c */ TABLE t_new (x int)"', "CREATE TABLE"),
    ('"CREATE -- c\\n TABLE t_new (x int)"', "CREATE TABLE"),
    ('"DROP /* c */ TABLE t_old"', "DROP TABLE"),
    ('"DROP -- c\\n TABLE t_old"', "DROP TABLE"),
    ('"ALTER /**/ TABLE t_a ADD COLUMN x int"', "ALTER TABLE"),
    ('"REFRESH /* c */ MATERIALIZED VIEW mv_x"', "REFRESH MATERIALIZED VIEW"),
    ('"REFRESH -- c\\n MATERIALIZED -- d\\n VIEW mv_x"', "REFRESH MATERIALIZED VIEW"),
    ('"MERGE /*c*/ INTO t_m USING s ON t_m.id = s.id WHEN MATCHED THEN DELETE"', "MERGE INTO"),
    ('"SELECT a /* c */ INTO t_new FROM src"', "SELECT ... INTO"),
])
def test_a_comment_cannot_hide_an_unanalysed_write_form(repo, sql, label):
    res = scan(repo, OWN + f"x = {sql}\n")
    assert "tables" not in res and label in res["not_scanned"], res


@pytest.mark.parametrize("sql", [
    '"SELECT EXTRACT(year FROM d) INTO newt FROM src"',
    '"SELECT a, EXTRACT(year FROM d) INTO newt FROM src"',
    '"SELECT a, (SELECT max(b) FROM t2) INTO x FROM t"',
    '"SELECT (SELECT 1 FROM t3) INTO x"',
    '"SELECT a INTO newt FROM src"',
    '"SELECT a FROM src; SELECT EXTRACT(year FROM d) INTO newt2 FROM src"',
])
def test_select_into_is_flagged_even_when_a_function_or_subquery_has_its_own_from(repo, sql):
    res = scan(repo, OWN + f"x = {sql}\n")
    assert "tables" not in res and "SELECT ... INTO" in res["not_scanned"], res


@pytest.mark.parametrize("sql", [
    '"INSERT INTO t_a (x) SELECT EXTRACT(year FROM d) FROM src"',
    '"SELECT a FROM t WHERE b IN (SELECT c FROM d)"',
    '"SELECT EXTRACT(year FROM d) FROM src"',
    '"SELECT a FROM src; INSERT INTO t_a (x) VALUES (1)"',
    '"WITH s AS (SELECT 1) INSERT INTO t_a (x) SELECT * FROM s"',
])
def test_select_into_positive_controls(repo, sql):
    assert slw._select_into(sql.strip('"')) is False
    assert scan(repo, OWN + f"x = {sql}\n")["tables"] == ["public.t_a"]


def test_comment_normalisation_helper_is_exact():
    f = slw._strip_sql_comments
    assert f("a/*x*/b") == "a b" and f("a -- x\nb") == "a  \nb" and f("a /* x /* y */ z */ b") == "a   b"
    assert f("a /* open") == "a  " and f("a */ b") == "a */ b" and f("x -- c") == "x  " and f("plain") == "plain"
    assert f("a /* c -- d */ b") == "a   b"                      # `--` inside a block comment is not a line comment
    assert f("a -- c /* d\nb") == "a  \nb"                       # `/*` inside a line comment does not open a block


def test_comment_normalisation_is_linear_on_hostile_input(repo):
    for text in ("/*" * 30000, "*/" * 30000, "--" * 30000, "/* --" * 12000, "-- /*\n" * 9000):
        t0 = time.perf_counter()
        slw._strip_sql_comments(text)
        assert time.perf_counter() - t0 < 0.2, text[:6]
    write(repo, f"{WRITERS}/a_x.py", OWN + "SQL = " + repr("/*" * 30000) + "\n")
    t0 = time.perf_counter()
    slw.scan_writer_tables("a_x", repo)
    assert time.perf_counter() - t0 < 0.5


def test_commented_out_sql_in_a_literal_over_reports_but_never_under_reports(repo):
    res = scan(repo, 'x = "INSERT INTO t_a (x) VALUES (1) -- DELETE FROM old_t"\n')
    assert res["tables"] == ["public.old_t", "public.t_a"]


@pytest.mark.parametrize("sql", [
    '"SELECT \'--\'; CREATE TABLE t_new (x int)"',
    '"SELECT \'/*\'; DROP TABLE t_old; SELECT \'*/\'"',
    '"SELECT \'--\'; REFRESH MATERIALIZED VIEW mv_x"',
    '"SELECT \'--\'; MERGE INTO t_m USING s ON t_m.id = s.id WHEN MATCHED THEN DELETE"',
])
def test_a_comment_marker_inside_a_string_cannot_hide_a_tripwire(repo, sql):
    res = scan(repo, OWN + f"x = {sql}\n")
    assert "tables" not in res and res["not_scanned"].startswith("write_form_not_analysed"), res


def test_a_comment_marker_inside_a_string_cannot_hide_a_written_table(repo):
    res = scan(repo, "x = \"SELECT '--'; DELETE FROM t_b\"\n")
    assert res["tables"] == ["public.t_b"], res


def test_a_comment_does_not_make_a_clean_statement_unparseable(repo):
    complete(repo, 'x = "UPDATE t_a /* why */ SET x = 1 -- done"\n')
    complete(repo, 'x = "INSERT INTO t_a /* ins */ (x) VALUES (1) /* end"\n')


# ───────────────────── F2: the closed allow-list for what reaches execute() ─────────────────────

F2_SHAPES = {
    # containers and loops
    "loop_over_list_literal_with_imported": IMP + "def r(cur):\n    for q in [Q, 'DELETE FROM a']:\n        cur.execute(q)\n",
    "loop_over_imported_list": "from sqls import L\ndef r(cur):\n    for q in L:\n        cur.execute(q)\n",
    "tuple_unpack_literal_pair": IMP + "def r(cur):\n    a, b = Q, 'x'\n    cur.execute(a)\n",
    "tuple_unpack_second_item": IMP + "def r(cur):\n    a, b = 'x', Q\n    cur.execute(b)\n",
    "dict_subscript": IMP + "QS = {'x': Q}\ndef r(cur):\n    cur.execute(QS['x'])\n",
    "dict_literal_item_assign": IMP + "QS = {}\nQS['x'] = Q\ndef r(cur):\n    cur.execute(QS['x'])\n",
    "container_append": IMP + "QS = []\nQS.append(Q)\ndef r(cur):\n    for q in QS:\n        cur.execute(q)\n",
    "container_update": IMP + "QS = {}\nQS.update(a=Q)\ndef r(cur):\n    cur.execute(QS['a'])\n",
    "container_extend": "from sqls import L\nQS = []\nQS.extend(L)\ndef r(cur):\n    cur.execute(QS[0])\n",
    "generator_join": IMP + "def r(cur):\n    cur.execute(';'.join(x for x in [Q, 'SELECT 1']))\n",
    "list_comp_join": IMP + "def r(cur):\n    cur.execute(';'.join([x for x in (Q, 'SELECT 1')]))\n",
    "items_loop": IMP + "D = {'a': Q}\ndef r(cur):\n    for k, q in D.items():\n        cur.execute(q)\n",
    "values_loop": IMP + "D = {'a': Q}\ndef r(cur):\n    for q in D.values():\n        cur.execute(q)\n",
    "enumerate_loop": IMP + "def r(cur):\n    for i, q in enumerate([Q]):\n        cur.execute(q)\n",
    "zip_loop": IMP + "def r(cur):\n    for a, q in zip([1], [Q]):\n        cur.execute(q)\n",
    "class_attribute": IMP + "class W:\n    SQL = Q\n    def r(self, cur):\n        cur.execute(self.SQL)\n",
    "class_attribute_via_class_name": IMP + "class W:\n    SQL = Q\ndef r(cur):\n    cur.execute(W.SQL)\n",
    # helpers
    "helper_param_imported": IMP + "def h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, Q)\n",
    "helper_param_module_attr": "import sqls\ndef h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, sqls.Q)\n",
    "helper_param_call_result": "from x import mk\ndef h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, mk())\n",
    "helper_param_keyword": IMP + "def h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, q=Q)\n",
    "helper_param_second_site_only": IMP + "def h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, 'SELECT 1')\n    h(cur, Q)\n",
    "helper_param_no_call_site": "def h(cur, q):\n    cur.execute(q)\n",
    "helper_param_default_imported": IMP + "def h(cur, q=Q):\n    cur.execute(q)\ndef r(cur):\n    h(cur)\n",
    "helper_param_default_not_clean_call": "def h(cur, q=mk()):\n    cur.execute(q)\ndef r(cur):\n    h(cur)\n",
    "helper_param_star_call": "def h(cur, q):\n    cur.execute(q)\ndef r(cur, a):\n    h(*a)\n",
    "helper_param_kwargs_call": "def h(cur, q):\n    cur.execute(q)\ndef r(cur, a):\n    h(cur, **a)\n",
    "helper_param_aliased": "def h(cur, q):\n    cur.execute(q)\nf = h\ndef r(cur):\n    f(cur, 'SELECT 1')\n",
    "helper_param_partial": "from functools import partial\ndef h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    partial(h, cur)('SELECT 1')\n    h(cur, 'x')\n",
    "helper_param_missing_arg": "def h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur)\n",
    "helper_method_param_imported": IMP + "class W:\n    def h(self, cur, q):\n        cur.execute(q)\n    def r(self, cur):\n        self.h(cur, Q)\n",
    "helper_kwonly_param": IMP + "def h(cur, *, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, q=Q)\n",
    "helper_vararg_param": "def h(cur, *q):\n    cur.execute(q[0])\ndef r(cur):\n    h(cur, 'x')\n",
    "helper_returns_imported": IMP + "def g():\n    return Q\ndef r(cur):\n    cur.execute(g())\n",
    "helper_returns_call_result": "from x import mk\ndef g():\n    return mk()\ndef r(cur):\n    cur.execute(g())\n",
    "helper_returns_nothing": "def g():\n    pass\ndef r(cur):\n    cur.execute(g())\n",
    "helper_generator": "def g():\n    yield 'SELECT 1'\ndef r(cur):\n    cur.execute(g())\n",
    "helper_one_of_two_returns_imported": IMP + "def g(f):\n    if f:\n        return 'SELECT 1'\n    return Q\ndef r(cur):\n    cur.execute(g(1))\n",
    "helper_name_collision_rebound": "from x import g\ndef g():\n    return 'SELECT 1'\ndef r(cur):\n    cur.execute(g())\n",
    "helper_method_returns_imported": IMP + "class W:\n    def g(self):\n        return Q\n    def r(self, cur):\n        cur.execute(self.g())\n",
    # string composition
    "prefix_comment": IMP + "def r(cur):\n    cur.execute('-- tag\\n' + Q)\n",
    "prefix_with": IMP + "def r(cur):\n    cur.execute('WITH t AS (SELECT 1) ' + Q)\n",
    "fstring_explain": IMP + "def r(cur):\n    cur.execute(f'EXPLAIN ANALYZE {Q}')\n",
    "const_plus_space_plus_q": IMP + "P = 'SELECT 1;'\ndef r(cur):\n    cur.execute(P + ' ' + Q)\n",
    "fstring_two_values": IMP + "V = 'x'\ndef r(cur):\n    cur.execute(f'{V} {Q}')\n",
    "format_positional": IMP + "def r(cur):\n    cur.execute('{}'.format(Q))\n",
    "format_keyword": IMP + "def r(cur):\n    cur.execute('{q}'.format(q=Q))\n",
    "percent_format": IMP + "def r(cur):\n    cur.execute('%s' % Q)\n",
    "percent_format_tuple": IMP + "def r(cur):\n    cur.execute('%s %s' % ('x', Q))\n",
    "replace": IMP + "def r(cur):\n    cur.execute('X'.replace('X', Q))\n",
    "implicit_concat_with_name": IMP + "def r(cur):\n    cur.execute('SELECT 1; ' + Q)\n",
    "join_with_imported_separator": "from sqls import SEP\ndef r(cur):\n    cur.execute(SEP.join(['a', 'b']))\n",
    "star_in_format": IMP + "A = [Q]\ndef r(cur):\n    cur.execute('{}'.format(*A))\n",
    "binop_mult": IMP + "def r(cur):\n    cur.execute(Q * 2)\n",
    "ifexp_else_branch": IMP + "def r(cur, f):\n    cur.execute('DELETE FROM a' if f else Q)\nr(None, 1)\n",
    "annotated_assignment": IMP + "q: str = Q\ndef r(cur):\n    cur.execute(q)\n",
    "walrus": IMP + "def r(cur):\n    cur.execute((q := Q))\n",
    "await_expr": IMP + "async def g():\n    return Q\nasync def r(cur):\n    cur.execute(await g())\n",
    "unary": IMP + "def r(cur):\n    cur.execute(+Q)\n",
    "bool_op": IMP + "def r(cur):\n    cur.execute(Q or 'SELECT 1')\n",
    # argument shapes
    "star_args": "ARGS = ('SELECT 1',)\ndef r(cur):\n    cur.execute(*ARGS)\n",
    "star_call_result": "from x import mk\ndef r(cur):\n    cur.execute(*mk())\n",
    "double_star": "K = {'query': 'SELECT 1'}\ndef r(cur):\n    cur.execute(**K)\n",
    "keyword_operation": IMP + "def r(cur):\n    cur.execute(operation=Q)\n",
    "keyword_stmt": IMP + "def r(cur):\n    cur.execute(stmt=Q)\n",
    "keyword_query": IMP + "def r(cur):\n    cur.execute(query=Q)\n",
    "unknown_keyword_only": IMP + "def r(cur):\n    cur.execute(qry=Q)\n",
    # execute-like calls the scan did not know
    "method_alias": IMP + "def r(cur):\n    ex = cur.execute\n    ex(Q)\n",
    "functools_partial": IMP + "from functools import partial\ndef r(cur):\n    partial(cur.execute, Q)()\n",
    "map_execute": IMP + "def r(cur):\n    list(map(cur.execute, [Q]))\n",
    "imported_alias_execute_values": IMP + "from psycopg2.extras import execute_values as ev\ndef r(cur, rows):\n    ev(cur, Q, rows)\n",
    "extras_execute_values": IMP + "from psycopg2 import extras\ndef r(cur, rows):\n    extras.execute_values(cur, Q, rows)\n",
    "asyncpg_fetch": IMP + "async def r(conn):\n    await conn.fetch(Q)\n",
    "asyncpg_fetchrow": IMP + "async def r(conn):\n    await conn.fetchrow(Q)\n",
    "asyncpg_fetchval": IMP + "async def r(conn):\n    await conn.fetchval(Q)\n",
    "asyncpg_fetchmany": IMP + "async def r(conn):\n    await conn.fetchmany(Q, [])\n",
    "exec_driver_sql": IMP + "def r(conn):\n    conn.exec_driver_sql(Q)\n",
    "prepare": IMP + "async def r(conn):\n    await conn.prepare(Q)\n",
    "run_method": IMP + "def r(runner):\n    runner.run(Q)\n",
    "execute_function_imported": "from helpers import execute\ndef r(cur):\n    execute(cur, 'SELECT 1')\n",
    "execute_values_aliased_value": "from psycopg2.extras import execute_values\nev = execute_values\ndef r(cur, rows):\n    ev(cur, 'SELECT 1', rows)\n",
    # name collision / attribute matching
    "attr_of_param_with_unrelated_name": "sql = 'SELECT 1'\ndef r(cur, ctx):\n    cur.execute(ctx.sql)\n",
    "attr_of_local_with_unrelated_name": "SQL = 'SELECT 1'\nclass A:\n    SQL = 'SELECT 2'\ndef r(cur, ctx):\n    cur.execute(ctx.SQL)\n",
    "attr_assigned_in_method": "class W:\n    def __init__(self, sql):\n        self.sql = sql\n    def r(self, cur):\n        cur.execute(self.sql)\n",
    "attr_assigned_twice": "class W:\n    SQL = 'SELECT 1'\n    SQL = 'SELECT 2'\n    def r(self, cur):\n        cur.execute(self.SQL)\n",
    "attr_class_attr_overridden_on_instance": "class W:\n    SQL = 'SELECT 1'\n    def __init__(self, s):\n        self.SQL = s\n    def r(self, cur):\n        cur.execute(self.SQL)\n",
    "attr_not_assigned": "class W:\n    def r(self, cur):\n        cur.execute(self.SQL)\n",
    "attr_dunder": "def r(cur):\n    cur.execute(r.__doc__)\n",
    "attr_of_call": "def r(cur, c):\n    cur.execute(c().sql)\n",
    "unbound_name": "def r(cur):\n    cur.execute(MISSING)\n",
    "name_bound_to_a_function": "def q():\n    return 'SELECT 1'\ndef r(cur):\n    cur.execute(q)\n",
    "name_bound_to_a_class": "class q:\n    pass\ndef r(cur):\n    cur.execute(q)\n",
    "generator_with_return": "def g():\n    yield 1\n    return 'SELECT 1'\ndef r(cur):\n    cur.execute(g())\n",
    "lambda_argument": "def r(cur):\n    cur.execute(lambda: 'SELECT 1')\n",
    "clean_name_also_bound_by_with": "q = 'SELECT 1'\ndef r(cur, f):\n    with f() as q:\n        pass\n    cur.execute(q)\n",
    "clean_name_also_bound_by_except": "q = 'SELECT 1'\ndef r(cur):\n    try:\n        pass\n    except Exception as q:\n        pass\n    cur.execute(q)\n",
    "clean_name_also_declared_global": "q = 'SELECT 1'\ndef r(cur):\n    global q\n    cur.execute(q)\n",
    "clean_name_also_a_match_capture": "q = 'SELECT 1'\ndef r(cur, v):\n    match v:\n        case q:\n            pass\n    cur.execute(q)\n",
    "clean_name_also_a_vararg": "q = 'SELECT 1'\ndef h(*q):\n    pass\ndef r(cur):\n    h()\n    cur.execute(q)\n",
    "clean_name_also_a_kwonly_param": IMP + "q = 'SELECT 1'\ndef h(*, q):\n    pass\ndef r(cur):\n    h(q=Q)\n    cur.execute(q)\n",
    "clean_name_also_a_kwargs": "q = 'SELECT 1'\ndef h(**q):\n    pass\ndef r(cur):\n    h()\n    cur.execute(q)\n",
    "clean_name_also_deleted": "q = 'SELECT 1'\ndef r(cur):\n    del q\n    cur.execute(q)\n",
    "clean_name_also_a_lambda_param": "q = 'SELECT 1'\nf = lambda q: q\ndef r(cur):\n    cur.execute(q)\n",
    "placeholder_after_update_in_prose": "T = 'a'\nx = f'UPDATE {T} whatever follows here'\n",
    "items_loop_over_unbound_mapping": "def r(cur):\n    for k, v in UNBOUND.items():\n        cur.execute(k)\n",
    "items_loop_over_imported_keys": "from x import D\ndef r(cur):\n    for k, v in D.items():\n        cur.execute(k)\n",
    "items_loop_key_stored_from_import": IMP + "D = {}\nD[Q] = 'x'\ndef r(cur):\n    for k, v in D.items():\n        cur.execute(k)\n",
    "items_loop_non_literal_mapping_binding": "from x import mk\nD = mk()\ndef r(cur):\n    for k, v in D.items():\n        cur.execute(k)\n",
    "with_target": "def r(cur, f):\n    with f() as q:\n        cur.execute(q)\n",
    "except_target": "def r(cur):\n    try:\n        pass\n    except Exception as q:\n        cur.execute(q)\n",
    "global_declared": "def r(cur):\n    global q\n    cur.execute(q)\n",
    "match_capture": "def r(cur, v):\n    match v:\n        case q:\n            cur.execute(q)\n",
    "lambda_param": "def r(cur):\n    f = lambda q: cur.execute(q)\n    f('SELECT 1')\n",
    "del_name": "q = 'SELECT 1'\ndef r(cur):\n    del q\n    cur.execute(q)\n",
    "subscript_of_unknown": "def r(cur, d):\n    cur.execute(d['a'])\n",
    "subscript_of_call": "def r(cur):\n    cur.execute(mk()[0])\n",
    "unpack_of_call_result": "def r(cur):\n    a, b = mk()\n    cur.execute(a)\n",
    "unpack_of_non_literal_name": "def r(cur, pair):\n    a, b = pair\n    cur.execute(a)\n",
    "unpack_starred": "def r(cur):\n    a, *b = mk()\n    cur.execute(b[0])\n",
    "bytes_arg": "def r(cur):\n    cur.execute(b'SELECT 1')\n",
    "list_arg_with_unknown": "def r(cur, x):\n    cur.execute([x])\n",
}


@pytest.mark.parametrize("name", sorted(F2_SHAPES))
def test_every_sql_argument_shape_that_is_not_provably_in_file_reads_partial_never_complete(repo, name):
    partial(repo, OWN + F2_SHAPES[name])


@pytest.mark.parametrize("name,reason", [
    ("loop_over_list_literal_with_imported", "imported_sql_constant"), ("tuple_unpack_literal_pair", "imported_sql_constant"),
    ("dict_subscript", "imported_sql_constant"), ("items_loop", "imported_sql_constant"), ("class_attribute", "imported_sql_constant"),
    ("helper_param_imported", "imported_sql_constant"), ("helper_param_keyword", "imported_sql_constant"),
    ("helper_returns_imported", "imported_sql_constant"), ("prefix_comment", "imported_sql_constant"),
    ("fstring_explain", "imported_sql_constant"), ("format_keyword", "imported_sql_constant"), ("percent_format", "imported_sql_constant"),
    ("replace", "imported_sql_constant"), ("keyword_operation", "imported_sql_constant"), ("asyncpg_fetch", "imported_sql_constant"),
    ("imported_alias_execute_values", "imported_sql_constant"), ("helper_param_no_call_site", "unresolved_sql_parameter"),
    ("helper_param_call_result", "sql_from_call_result"), ("helper_returns_call_result", "sql_from_call_result"),
    ("star_args", "unresolved_sql_arguments"), ("double_star", "unresolved_sql_arguments"),
    ("unknown_keyword_only", "unresolved_sql_arguments"), ("method_alias", "execute_method_used_as_value"),
    ("functools_partial", "execute_method_used_as_value"), ("map_execute", "execute_method_used_as_value"),
    ("execute_function_imported", "execute_function_imported"), ("attr_of_param_with_unrelated_name", "unresolved_sql_attribute"),
    ("attr_dunder", "sql_from_dunder_attribute"), ("unbound_name", "unresolved_sql_name"), ("bytes_arg", "bytes_sql_literal"),
    ("subscript_of_unknown", "sql_from_subscript"), ("helper_param_aliased", "unresolved_sql_parameter"),
])
def test_the_named_reason_for_each_family(repo, name, reason):
    partial(repo, OWN + F2_SHAPES[name], reason)


F2_CLEAN = {
    "module_constant": "def r(cur):\n    cur.execute(OWN)\n",
    "literal": "def r(cur):\n    cur.execute('SELECT 1')\n",
    "fstring_of_resolved_names": "T = 't_a'\nV = 'x'\ndef r(cur):\n    cur.execute(f'DELETE FROM {T} WHERE v = {V!r}')\n",
    "plus_of_clean": "P = 'SELECT 1;'\ndef r(cur):\n    cur.execute(P + ' ' + OWN)\n",
    "implicit_concat": "def r(cur):\n    cur.execute('SELECT 1; ' 'SELECT 2')\n",
    "format_of_clean": "A = 'x'\ndef r(cur):\n    cur.execute('SELECT {}'.format(A))\n",
    "percent_of_clean": "A = 'x'\ndef r(cur):\n    cur.execute('SELECT %s' % A)\n",
    "replace_of_clean": "def r(cur):\n    cur.execute('SELECT X'.replace('X', '1'))\n",
    "join_of_clean_list": "COLS = ['a', 'b']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(COLS) + ' FROM t_b')\n",
    "join_of_comprehension": "COLS = ['a', 'b']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(c + '1' for c in COLS))\n",
    "placeholders_len": "IDS = [1, 2]\ndef r(cur):\n    cur.execute(f\"SELECT 1 WHERE x IN ({','.join(['%s'] * len(IDS))})\", IDS)\n",
    "number_builtins": "def r(cur, rows):\n    cur.execute(f'SELECT {len(rows)}, {int(3)}')\nr(None, [])\n",
    "param_all_sites_clean": "def h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, 'SELECT 1')\n    h(cur, OWN)\n    h(cur, q='SELECT 3')\n",
    "param_default_clean": "def h(cur, q='SELECT 1'):\n    cur.execute(q)\ndef r(cur):\n    h(cur)\n",
    "batch_insert_pattern": "def _batch_insert(cur, rows, sql):\n    cur.executemany(sql, rows)\ndef r(cur):\n    _batch_insert(cur, [], 'INSERT INTO t_a (x) VALUES (%s)')\n    _batch_insert(cur, [], OWN)\n",
    "method_param_all_sites_clean": "class W:\n    def h(self, cur, q):\n        cur.execute(q)\n    def r(self, cur):\n        self.h(cur, 'SELECT 1')\n        self.h(cur, q=OWN)\n",
    "static_method_param": "class W:\n    @staticmethod\n    def h(cur, q):\n        cur.execute(q)\n    def r(self, cur):\n        W.h(cur, 'SELECT 1')\n",
    "class_method_via_class": "class W:\n    def h(self, cur, q):\n        cur.execute(q)\ndef r(cur, w):\n    W.h(w, cur, 'SELECT 1')\n",
    "loop_over_literal_container": "QS = ('SELECT 1', OWN)\ndef r(cur):\n    for q in QS:\n        cur.execute(q)\n",
    "loop_over_dict_values": "QS = {'a': 'SELECT 1', 'b': OWN}\ndef r(cur):\n    for q in QS.values():\n        cur.execute(q)\n",
    "items_loop_clean": "QS = {'a': 'SELECT 1'}\ndef r(cur):\n    for k, q in QS.items():\n        cur.execute(q)\n",
    "items_loop_with_unclean_values_clean_keys": "from x import mk\nD = {}\nD['a'] = mk()\ndef r(cur):\n    for k, v in D.items():\n        cur.execute(f'SELECT 1 /* {k} */')\n",
    "dict_subscript_clean": "QS = {'a': 'SELECT 1'}\ndef r(cur):\n    cur.execute(QS['a'])\n",
    "dict_item_assign_clean": "QS = {}\nQS['a'] = 'SELECT 1'\ndef r(cur):\n    cur.execute(QS['a'])\n",
    "staticmethod_called_through_self": "class W:\n    @staticmethod\n    def h(cur, q):\n        cur.execute(q)\n    def r(self, cur):\n        self.h(cur, 'SELECT 1')\n",
    "staticmethod_whose_first_parameter_is_named_self": "class W:\n    @staticmethod\n    def h(self, q):\n        self.execute(q)\n    def r(self, cur):\n        self.h(cur, 'SELECT 1')\n",
    "copy_to_with_placeholder_is_an_export": "def r(c, t):\n    c.execute(f'COPY {t} TO STDOUT')\nr(None, 'a')\n",
    "tuple_unpack_elementwise_unrelated_name": IMP + "def r(cur):\n    a, b = Q, 'SELECT 1'\n    cur.execute(b)\n",
    "unpack_literal_pair": "def r(cur):\n    a, b = 'SELECT 1', OWN\n    cur.execute(b)\n",
    "unpack_clean_container": "PAIR = ('SELECT 1', 'SELECT 2')\ndef r(cur):\n    a, b = PAIR\n    cur.execute(a)\n",
    "class_attribute_once": "class W:\n    SQL = 'SELECT 1'\n    def r(self, cur):\n        cur.execute(self.SQL)\n",
    "class_attribute_cls": "class W:\n    SQL = 'SELECT 1'\n    @classmethod\n    def r(cls, cur):\n        cur.execute(cls.SQL)\n",
    "class_attribute_via_class_name": "class W:\n    SQL = 'SELECT 1'\ndef r(cur):\n    cur.execute(W.SQL)\n",
    "local_function_returns_clean": "def g():\n    return 'SELECT 1'\ndef r(cur):\n    cur.execute(g())\n",
    "local_method_returns_clean": "class W:\n    def g(self):\n        return 'SELECT 1'\n    def r(self, cur):\n        cur.execute(self.g())\n",
    "local_function_returning_param": "def g(x):\n    return x\ndef r(cur):\n    cur.execute(g('SELECT 1'))\n",
    "textwrap_dedent": "import textwrap\ndef r(cur):\n    cur.execute(textwrap.dedent('SELECT 1'))\n",
    "sqlalchemy_text": "from sqlalchemy import text\ndef r(cur):\n    cur.execute(text('SELECT 1'))\n",
    "str_wrapper": "def r(cur):\n    cur.execute(str('SELECT 1'))\n",
    "ifexp_both_clean": "def r(cur):\n    cur.execute('SELECT 1' if 1 else 'SELECT 2')\n",
    "reassigned_all_clean": "q = 'SELECT 1'\nq = 'SELECT 2'\ndef r(cur):\n    cur.execute(q)\n",
    "augassign_clean": "q = 'SELECT 1'\nq += ' WHERE 1 = 1'\ndef r(cur):\n    cur.execute(q)\n",
    "walrus_clean": "def r(cur):\n    cur.execute((q := 'SELECT 1'))\n",
    "annotated_clean": "q: str = 'SELECT 1'\ndef r(cur):\n    cur.execute(q)\n",
    "mutual_cycle_clean": "a = 'SELECT 1'\nb = a\na = b\ndef r(cur):\n    cur.execute(a)\n",
    "keyword_query_clean": "def r(cur):\n    cur.execute(query='SELECT 1')\n",
    "execute_values_clean": "from psycopg2.extras import execute_values\ndef r(cur, rows):\n    execute_values(cur, 'INSERT INTO t_a (x) VALUES %s', rows)\n",
    "execute_values_alias_clean": "from psycopg2.extras import execute_values as ev\ndef r(cur, rows):\n    ev(cur, 'INSERT INTO t_a (x) VALUES %s', rows)\n",
    "extras_attr_clean": "from psycopg2 import extras\ndef r(cur, rows):\n    extras.execute_values(cur, 'INSERT INTO t_a (x) VALUES %s', rows)\n",
    "fetch_family_clean": "async def r(conn):\n    await conn.fetch('SELECT 1')\n    await conn.fetchrow('SELECT 1')\n    await conn.fetchval('SELECT 1')\n    await conn.prepare('SELECT 1')\n",
    "fetchmany_int": "def r(cur):\n    cur.fetchmany(100)\n    cur.fetchmany(size=10)\n    cur.fetchone()\n",
    "copy_module_functions": "import copy, shutil\ndef r(a, b):\n    return copy.copy(a), shutil.copy(a, b)\n",
    "dict_copy_no_args": "def r(d):\n    return d.copy()\n",
    "subprocess_run": "import subprocess\ndef r(x):\n    subprocess.run(['ls', x])\n",
    "savepoint_with_runtime_suffix": "def r(cur, graha):\n    cur.execute(f'SAVEPOINT sp_{graha[:6]}')\n    cur.execute(f'RELEASE SAVEPOINT sp_{graha[:6]}')\n    cur.execute(f'ROLLBACK TO SAVEPOINT sp_{graha[:6]}')\n",
    "params_are_not_sql": "def r(cur, rows, x):\n    cur.execute('SELECT 1 WHERE a = %s', (x, rows))\n    cur.executemany('INSERT INTO t_a (x) VALUES (%s)', rows)\n",
}


@pytest.mark.parametrize("name", sorted(F2_CLEAN))
def test_positive_controls_provably_in_file_sql_stays_complete(repo, name):
    complete(repo, OWN + F2_CLEAN[name])


def test_a_savepoint_statement_is_only_recognised_when_the_whole_statement_is_verb_plus_identifier(repo):
    partial(repo, OWN + "def r(cur, x):\n    cur.execute(f'SAVEPOINT a; DELETE FROM b; {x}')\n")
    partial(repo, OWN + "def r(cur, x):\n    cur.execute(f'{x} SAVEPOINT a')\n")
    partial(repo, OWN + "def r(cur, x):\n    cur.execute('SAVEPOINT sp; ' + x)\n")


def test_a_parameter_is_clean_only_when_every_call_site_is_not_just_the_first(repo):
    partial(repo, OWN + IMP + "def h(cur, q):\n    cur.execute(q)\nfor _ in range(2):\n    h(None, 'SELECT 1')\nh(None, Q)\n", "imported_sql_constant")


def test_the_same_name_bound_unclean_anywhere_in_the_module_is_unclean_everywhere(repo):
    partial(repo, OWN + IMP + "def a(cur):\n    q = 'SELECT 1'\n    cur.execute(q)\ndef b(cur):\n    q = Q\n", "imported_sql_constant")


# ───────────────────── F3: UPDATE and COPY with a runtime target or tail ─────────────────────

F3_SHAPES = [
    "def r(c, t, s):\n    c.execute('UPDATE ' + t + ' ' + s)\nr(None, 'a', 'SET x = 1')\n",
    "def r(c, t):\n    c.execute('UPDATE ' + t)\nr(None, 'a')\n",
    "def r(c, t):\n    c.execute('COPY ' + t)\nr(None, 'a')\n",
    "def r(c, t):\n    c.execute(f'COPY {t}')\nr(None, 'a')\n",
    "T = 'a'\ndef r(c, s):\n    c.execute(f'UPDATE {T} {s}')\nr(None, 'SET x = 1')\n",
    "SETCLAUSE = 'SET x = 1'\ndef r(c):\n    c.execute('UPDATE a ' + SETCLAUSE)\n",
    "q = 'UPDATE a'\nq += ' SET x = 1'\ndef r(c):\n    c.execute(q)\n",
    "FR = 'FROM STDIN'\ndef r(c):\n    c.execute('COPY a ' + FR)\n",
    "def r(c, r_):\n    c.execute('UPDATE ONLY a t ' + r_)\nr(None, 'SET x = 1')\n",
    "x = 'UPDATE a'\n",
    "x = 'UPDATE ONLY a t '\n",
    "x = 'COPY a (x, y) '\n",
    "x = 'COPY a'\n",
    "x = 'UPDATE a * '\n",
    "x = 'UPDATE public.a AS t'\n",
    "x = 'UPDATE %s SET x = 1'\n",
    "x = 'COPY %s FROM STDIN'\n",
]


@pytest.mark.parametrize("src", F3_SHAPES)
def test_update_and_copy_with_a_runtime_tail_or_target_read_partial(repo, src):
    partial(repo, OWN + src)


@pytest.mark.parametrize("src", [
    "x = 'UPDATE a SET x = 1'\n",
    "x = 'UPDATE a t SET x = 1 WHERE t.i = 1'\n",
    "x = 'COPY a FROM STDIN'\n",
    "x = 'COPY a (x, y) FROM STDIN'\n",
    "x = 'COPY a TO STDOUT'\n",
    "x = 'COPY (SELECT 1) TO STDOUT'\n",
    "x = 'Update asset_throughput after the copy of rows'\n",
    "x = 'copy of rows is skipped'\n",
    "x = 'Update asset_throughput'\n",
    "x = 'Copy rows'\n",
    "x = 'SELECT 1 FOR UPDATE'\n",
    "x = 'SELECT 1 FOR UPDATE OF t'\n",
    "x = 'INSERT INTO t_a (x) VALUES (1) ON CONFLICT DO UPDATE SET x = 2'\n",
    "x = 'UPDATE'\n",
    "x = 'would UPDATE structural_role + attempt re-resolution'\n",
    "x = 'update skipped: %s'\n",
    "x = 'AFTER INSERT OR UPDATE ON t'\n",
])
def test_update_and_copy_positive_controls_stay_complete(repo, src):
    res = scan(repo, OWN + src)
    assert res.get("tables") in (["public.t_a"], ["public.a", "public.t_a"]), (src, res)


# ───────────────────── F5: memoised resolution and the hard work cap ─────────────────────

def _reviewer_dag(b: int = 10, levels: int = 7) -> str:
    """A layered DAG of `n = n' + n' + ...` assignments: unmemoised resolution costs b**levels."""
    out = ["from sqls import Q"]
    for lv in range(levels - 1, -1, -1):
        names = [f"n{lv}_{i}" for i in range(b)]
        for i, nm in enumerate(names):
            rhs = "Q" if lv == levels - 1 else " + ".join(f"n{lv + 1}_{j}" for j in range(b))
            out.append(f"{nm} = {rhs}")
    out.append("def r(cur):\n    cur.execute(n0_0)")
    return "\n".join(out) + "\n"


def test_the_layered_dag_hostile_file_is_bounded_and_never_complete(repo):
    body = OWN + _reviewer_dag(10, 7)
    assert body.count("\n") >= 70
    t0 = time.perf_counter()
    res = scan(repo, body)
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.0, elapsed
    assert "tables" not in res and res["not_scanned"].startswith("imported_sql_constant"), res


def test_a_clean_layered_dag_resolves_in_linear_time(repo):
    body = _reviewer_dag(10, 7).replace("from sqls import Q", "Q = 'SELECT 1'")
    t0 = time.perf_counter()
    res = scan(repo, OWN + body)
    assert time.perf_counter() - t0 < 1.0
    assert res.get("tables") == ["public.t_a"], res


def test_many_assignments_of_one_name_each_followed_by_an_execute_are_linear(repo):
    n = 8000
    body = OWN + "def r(cur):\n" + "".join(f"    q = 'DELETE FROM a'\n    cur.execute(q)\n" for _ in range(n))
    t0 = time.perf_counter()
    res = scan(repo, body)
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.0, elapsed
    assert res.get("tables") == ["public.a", "public.t_a"] or res["not_scanned"].startswith("resolver_work_cap"), res


def test_a_file_that_exceeds_the_work_cap_falls_back_to_not_scanned_with_a_named_reason(repo):
    n = 25_000                                                     # ~3 steps per statement: well over the 60k cap
    body = OWN + "def r(cur):\n" + "".join("    q = 'SELECT 1'\n    cur.execute(q)\n" for _ in range(n))
    t0 = time.perf_counter()
    res = scan(repo, body)
    assert time.perf_counter() - t0 < 4.0
    assert "tables" not in res and res["not_scanned"].startswith("resolver_work_cap"), res


def test_a_file_just_under_the_work_cap_still_resolves_normally(repo):
    n = 6000                                                       # ~3 steps per statement: well under the 60k cap
    body = OWN + "def r(cur):\n" + "".join("    q = 'SELECT 1'\n    cur.execute(q)\n" for _ in range(n))
    res = scan(repo, body)
    assert res.get("tables") == ["public.t_a"], res


def test_the_work_cap_is_a_class_constant_and_a_cap_error_never_reads_complete(repo, monkeypatch):
    assert slw._WriteScan.MAX_RESOLVER_STEPS == 60_000
    monkeypatch.setattr(slw._WriteScan, "MAX_RESOLVER_STEPS", 3)
    res = scan(repo, OWN + "def r(cur):\n    q = 'SELECT 1'\n    cur.execute(q)\n    cur.execute(OWN)\n")
    assert "tables" not in res and res["not_scanned"].startswith("resolver_work_cap"), res
    rep = slw.footprint_scope([{"asset_id": "a_x", "target_table": "t_a"}], ["t_a"], repo)
    assert rep["footprint_scope"] == "partial" and rep["assets_not_scanned"][0]["reason"].startswith("resolver_work_cap")


def test_a_cycle_between_names_neither_loops_forever_nor_hides_an_unclean_binding(repo):
    partial(repo, OWN + IMP + "a = b\nb = a\nb = Q\ndef r(cur):\n    cur.execute(a)\n", "imported_sql_constant")
    complete(repo, OWN + "a = b\nb = a\na = 'SELECT 1'\ndef r(cur):\n    cur.execute(a)\n")


# ───────────────────── F6: pins for branches the first review round left unkilled ─────────────────────

@pytest.mark.parametrize("sql", [
    '"INSERT INTO db.s.a (x) VALUES (1)"',
    '"DELETE FROM db.s.a"',
    '"TRUNCATE db.s.a, b"',
    '"INSERT INTO a.b.c.d (x) VALUES (1)"',
])
def test_a_three_part_name_is_not_truncated_to_two_parts(repo, sql):
    res = scan(repo, OWN + f"x = {sql}\n")
    assert "tables" not in res, res


def test_adjacent_and_suffixed_placeholders_are_not_half_resolved(repo):
    partial(repo, OWN + 'A = "x"\nB = "y"\ndef r(c):\n    c.execute(f"INSERT INTO {A}{B} (x) VALUES (1)")\n', ("unresolved_table_expression", "unparseable_write_target"))
    partial(repo, OWN + 'A = "x"\ndef r(c):\n    c.execute(f"INSERT INTO {A}_log (x) VALUES (1)")\n', ("unresolved_table_expression", "unparseable_write_target"))
    partial(repo, OWN + 'A = "x"\ndef r(c):\n    c.execute(f"INSERT INTO public.{A}_log (x) VALUES (1)")\n', ("unresolved_table_expression", "unparseable_write_target"))
    partial(repo, OWN + "x = 'INSERT INTO \"a\"\"b\" (x) VALUES (1)'\n", ("unresolved_table_expression", "unparseable_write_target"))
    partial(repo, OWN + "x = 'INSERT INTO \"a\"b (x) VALUES (1)'\n")


def test_a_schema_placeholder_with_a_parameter_table_is_not_resolved_to_the_schema_alone(repo):
    body = OWN + 'S = "sch"\ndef w(c, t):\n    c.execute(f"DELETE FROM {S}.{t} WHERE x = 1")\ndef r(c):\n    w(c, "t_z")\n'
    partial(repo, body, "unresolved_table_expression")


def test_a_parametric_helper_called_twice_reports_both_tables(repo):
    body = ('def w(c, t):\n    c.execute(f"DELETE FROM {t} WHERE x = 1")\n'
            'def r(c):\n    w(c, "t_a")\n    w(c, "t_z")\n')
    res = scan(repo, body)
    assert res["tables"] == ["public.t_a", "public.t_z"], res


def test_a_bytes_literal_over_the_cap_is_not_scanned(repo):
    big = "B = b'" + "x" * (slw.MAX_SQL_LITERAL_CHARS + 10) + "'\n"
    partial(repo, OWN + big, "sql_literal_too_long")
    complete(repo, OWN + "B = b'" + "x" * 1000 + "'\n")


@pytest.mark.parametrize("cols,expect_scanned", [
    (", ".join(f"c{i}" for i in range(300)), True),                  # ~1.8 KB list: resolved
    (", ".join(f"c{i}" for i in range(1200)), False),                # > 4000 chars: the bounded column-list pattern gives up: not scanned
])
def test_the_copy_column_list_length_bound(repo, cols, expect_scanned):
    res = scan(repo, f'x = "COPY t_b ({cols}) FROM STDIN"\n')
    assert ("tables" in res) is expect_scanned, res
    if expect_scanned:
        assert res["tables"] == ["public.t_b"]
    else:
        assert res["not_scanned"].startswith("unparseable_write_target")


def test_a_copy_column_list_with_nested_parentheses_is_not_read(repo):
    res = scan(repo, 'x = "COPY t_b (a, (b)) FROM STDIN"\n')
    assert "tables" not in res and res["not_scanned"].startswith("unparseable_write_target"), res


def test_other_binary_operators_on_an_imported_name_are_not_clean(repo):
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(Q * 2)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(Q % ())\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(Q + Q)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(-Q)\n", "imported_sql_constant")


def test_ifexp_branches_and_bool_operands_are_each_judged(repo):
    partial(repo, OWN + IMP + "def r(c, f):\n    c.execute('DELETE FROM a' if f else Q)\nr(None, 1)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c, f):\n    c.execute(Q if f else 'DELETE FROM a')\nr(None, 1)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c):\n    c.execute('x' or Q)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(Q and 'x')\n", "imported_sql_constant")


def test_f_string_format_specs_and_conversions_are_judged(repo):
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(f'{1:{Q}}')\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(c):\n    c.execute(f'{Q!r}')\n", "imported_sql_constant")


# ───────────────────── F7: the cheap forms ─────────────────────

@pytest.mark.parametrize("sql,expected", [
    ('"INSERT INTO s . a (x) VALUES (1)"', ["s.a"]),
    ('"INSERT INTO s .a (x) VALUES (1)"', ["s.a"]),
    ('"INSERT INTO s. a (x) VALUES (1)"', ["s.a"]),
    ('"DELETE FROM s . a"', ["s.a"]),
    ('"UPDATE s . a SET x = 1"', ["s.a"]),
    ('"COPY s . a (x) FROM STDIN"', ["s.a"]),
    ('"TRUNCATE s . a, b"', ["public.b", "s.a"]),
    ('"TRUNCATE s\\n.\\na , s . b"', ["s.a", "s.b"]),
    ("'INSERT INTO \"s\" . \"a\" (x) VALUES (1)'", ["s.a"]),
])
def test_whitespace_around_the_dot_of_a_qualified_name_is_allowed(repo, sql, expected):
    assert scan(repo, f"x = {sql}\n").get("tables") == expected


@pytest.mark.parametrize("sql", [
    "'INSERT INTO \"a.b\" (x) VALUES (1)'",
    "'INSERT INTO \"Foo\" (x) VALUES (1)'",
    "'INSERT INTO U&\"\\\\0061\" (x) VALUES (1)'",
    "'INSERT INTO \"A\" (x) VALUES (1)'",
    "'INSERT INTO \"a b\" (x) VALUES (1)'",
    "'INSERT INTO \"1a\" (x) VALUES (1)'",
    "'TRUNCATE \"a.b\", c'",
    "'TRUNCATE \"Foo\"'",
    "'DELETE FROM \"Foo\"'",
    "'DELETE FROM s.\"Foo\"'",
    "'TRUNCATE set, a'",
    "'TRUNCATE a, only'",
    "'TRUNCATE TABLE values'",
])
def test_a_quoted_name_that_is_not_a_plain_lowercase_identifier_is_not_scanned(repo, sql):
    res = scan(repo, OWN + f"x = {sql}\n")
    assert "tables" not in res, res


def test_plain_lowercase_quoted_names_still_resolve(repo):
    assert scan(repo, "x = 'INSERT INTO \"t_a\" (x) VALUES (1)'\ny = 'DELETE FROM \"public\".\"t_b\"'\n")["tables"] == ["public.t_a", "public.t_b"]


def test_a_method_helper_called_through_self_attributes_the_right_argument(repo):
    body = ('class W:\n    def clear(self, t, mode):\n        self.c.execute(f"DELETE FROM {t} WHERE m = 1")\n'
            '    def r(self):\n        self.clear("t_a", "mode_b")\n')
    res = scan(repo, body)
    assert res["tables"] == ["public.t_a"], res
    body = ('class W:\n    def clear(self, t, mode):\n        self.c.execute(f"DELETE FROM {t} WHERE m = 1")\n'
            'def r(w):\n    W.clear(w, "t_a", "mode_b")\n')
    assert scan(repo, body)["tables"] == ["public.t_a"]
    body = ('class W:\n    @staticmethod\n    def clear(t, mode):\n        print(f"DELETE FROM {t} WHERE m = 1")\n'
            'def r():\n    W.clear("t_a", "mode_b")\n')
    assert scan(repo, body)["tables"] == ["public.t_a"]


def test_the_table_helper_alias_rule_stands_on_its_own_without_an_execute_call(repo):
    base = 'def clear(c, t):\n    print(f"DELETE FROM {t} WHERE x = 1")\n'
    partial(repo, OWN + base + "f = clear\ndef r(c):\n    f(c, 'b')\n    clear(c, 'a')\n", "unresolved_table_argument")
    assert scan(repo, OWN + base + "def r(c):\n    clear(c, 'b')\n")["tables"] == ["public.b", "public.t_a"]


def test_a_parametric_helper_that_is_aliased_or_passed_on_is_not_resolved(repo):
    base = 'def clear(c, t):\n    c.execute(f"DELETE FROM {t} WHERE x = 1")\n'
    partial(repo, OWN + base + "f = clear\ndef r(c):\n    f(c, 'b')\n    clear(c, 'a')\n", ("unresolved_table_argument", "unresolved_sql_parameter"))
    partial(repo, OWN + base + "def r(c):\n    list(map(clear, [c], ['b']))\n    clear(c, 'a')\n", ("unresolved_table_argument", "unresolved_sql_parameter"))
    partial(repo, OWN + base + "def r(c, a):\n    clear(*a)\n", ("unresolved_table_argument", "unresolved_sql_arguments"))
    partial(repo, OWN + base + "def r(c, a):\n    clear(c, **a)\n", ("unresolved_table_argument", "unresolved_sql_arguments"))


@pytest.mark.parametrize("body", [
    'class W:\n    source_paths = ["a.py"]\nx = source_paths\n',
    'class W:\n    source_paths = ["a.py"]\n    y = source_paths\n',
    'class W:\n    source_paths = ["a.py"]\n    y = list.append(source_paths, "b.py")\n',
    'class W:\n    source_paths = ["a.py"]\n    y = [source_paths]\n',
    'class W:\n    source_paths = ["a.py"]\nW2 = W\nW2.source_paths.append("b.py")\n',
    'class W:\n    source_paths = ["a.py"]\ngetattr(W, "source_paths").append("b.py")\n',
    'class W:\n    source_paths = ["a.py"]\nsetattr(W, "source_paths", ["b.py"])\n',
    'class W:\n    source_paths = ["a.py"]\nvars(W)["source_paths"] = ["b.py"]\n',
    'class W:\n    source_paths = ["a.py"]\nsource_paths, other = ["b.py"], 1\n',
    'class W:\n    source_paths = ["a.py"]\n(source_paths, other) = (["b.py"], 1)\n',
    'class W:\n    source_paths = ["a.py"]\nfor source_paths in [["b.py"]]:\n    pass\n',
    'class W:\n    source_paths = ["a.py"]\n    def r(self):\n        s = self.source_paths\n        s.append("b.py")\n',
    'class W:\n    source_paths = ["a.py"]\n    def r(self):\n        return self.source_paths.append("b.py")\n',
])
def test_a_source_paths_that_is_aliased_or_mutated_in_any_way_is_not_followed(repo, body):
    write(repo, "platform/python-sidecar/ga_writers/a.py", 'SQL = "INSERT INTO t_a (x) VALUES (1)"\n')
    write(repo, "platform/python-sidecar/ga_writers/b.py", 'SQL = "INSERT INTO t_b (x) VALUES (1)"\n')
    body = body.replace('"a.py"', '"platform/python-sidecar/ga_writers/a.py"').replace('"b.py"', '"platform/python-sidecar/ga_writers/b.py"')
    res = scan(repo, body + OWN)
    assert "tables" not in res and res["not_scanned"] == "source_paths_mutated_at_runtime", (body, res)


def test_source_paths_read_for_its_length_or_iterated_is_still_followed(repo):
    write(repo, "platform/python-sidecar/ga_writers/a.py", 'SQL = "INSERT INTO t_a (x) VALUES (1)"\n')
    body = ('class W:\n    source_paths = ["platform/python-sidecar/ga_writers/a.py"]\n'
            '    def r(self):\n        n = len(self.source_paths)\n        for p in self.source_paths:\n            print(p)\n'
            '        return sorted(self.source_paths), self.source_paths[0], "x" in self.source_paths\n')
    assert scan(repo, body)["tables"] == ["public.t_a"]


@pytest.mark.parametrize("src", [
    "g = globals()\ng['T'] = 'b'\n",
    "def r():\n    g = locals()\n    g['T'] = 'b'\n",
    "def r():\n    d = vars()\n    return d\n",
    "import sys\nsys.modules[__name__].__dict__['T'] = 'b'\n",
    "import sys\nsys.modules[__name__].T = 'b'\n",
    "import sys\nsys.modules['x'].T = 'b'\n",
    "def r(f):\n    return f(globals())\n",
])
def test_aliasing_the_namespace_dict_or_reaching_another_module_is_runtime_rebinding(repo, src):
    partial(repo, OWN + src, "runtime_rebinding")


@pytest.mark.parametrize("src", [
    "def r():\n    return globals().get('T'), locals().keys()\n",
    "def r(x):\n    return 'a {y}'.format(**locals())\n",
    "def r():\n    return globals()['T']\n",
    "def r(o, v):\n    o.__dict__['k'] = v\n",
])
def test_reading_the_namespace_is_not_rebinding_it(repo, src):
    complete(repo, OWN + src)


@pytest.mark.parametrize("src", [
    "V = 'DELETE'\ndef r(c):\n    c.execute(f'{V} FROM a')\n",
    "V = 'DELETE'\ndef r(c):\n    c.execute(V + ' FROM a')\n",
    "V = 'DELETE'\nx = f'{V} FROM a'\n",
    "V = 'INSERT'\nx = f'{V} INTO a (x) VALUES (1)'\n",
    "V = 'TRUNCATE'\nx = f'{V} TABLE a'\n",
    "V = 'UPDATE'\nT = 'a'\nx = f'{V} {T} SET x = 1'\n",
    "x = '{} FROM a'.format('DELETE')\n",
    "x = '%s FROM a' % 'DELETE'\n",
    "V = 'DELETE'\nx = f'SELECT 1; {V} FROM a'\n",
])
def test_a_statement_whose_verb_comes_from_a_name_is_not_scanned(repo, src):
    partial(repo, OWN + src)


def test_a_leading_placeholder_that_is_not_a_missing_verb_is_fine(repo):
    complete(repo, OWN + "COLS = 'a'\nx = f'{COLS} FROM t'\n")        # a name holding a non-verb: not a hidden verb
    partial(repo, OWN + "def go(c, v):\n    c.execute(f'{v} FROM t')\ngo(None, 'x')\n", "unparseable_write_target")   # a parameter + SQL words
    complete(repo, OWN + "COLS = 'a'\nx = f'{COLS} from t'\n")        # lowercase: prose-like, no verb keyword
    complete(repo, OWN + "def r(n):\n    return f'{n} from {n}'\nr('x')\n")
    complete(repo, OWN + "P = 'SELECT 1 '\nx = P + 'FROM t_b'\n")


# ───────────────────── the real tree under the strict default ─────────────────────

def test_real_tree_strict_default_scans_without_exception_and_keeps_the_known_clean_writers():
    helpers = slw.helper_write_effects(REAL_REPO)
    scanned, flipped = {}, {}
    for f in sorted((REAL_REPO / WRITERS).glob("*.py")):
        res = slw.scan_writer_tables(f.stem, REAL_REPO, helpers)
        assert ("tables" in res) != ("not_scanned" in res), (f.name, res)
        (scanned if "tables" in res else flipped)[f.stem] = res
    assert len(scanned) >= 70
    # the real `_batch_insert(cur, rows, sql)` and `for view in [...]` patterns stay complete
    for asset in ("bo_karanajala", "bo_sangati", "bo_upaya", "mi_darshana", "ka_avadhi", "ga_dashas", "ga_condition", "ga_tajaka", "bo_laksana"):
        assert asset in scanned, (asset, flipped.get(asset))
    # the writers that pass a SQL-running callback out of the file, or import a module by path at runtime, do not
    for asset in ("bg_gochara_arcs", "ka_gochara", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate"):
        assert asset in flipped, asset
