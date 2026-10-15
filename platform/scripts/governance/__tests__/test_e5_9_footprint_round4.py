"""test_e5_9_footprint_round4.py -- Suvarna E5.9 / FP2 review round 4.

MEDIUM-1  a statement whose keywords are split by a comment INSIDE a string / dollar body disappeared from both passes of round 3:
          a THIRD reading (every comment marker stripped wherever it sits) joins the union
LOW-1     `$` inside an identifier (`a$b$`) and non-ASCII dollar tags (`$é$`) no longer misread the text
MEDIUM-2  container policing is INVERTED: a name is policed as a possible container UNLESS it is provably immutable
LOW-4     the class-attribute lookup indexes each class once and is charged to the work cap (5000 attributes / 5000 classes)
LOW       class-name rebinding, type(...), __setattr__/__getattribute__, any globals()/locals()/vars()/__builtins__, gc, DROP SCHEMA,
          templates of constants read as the statement they run (%, .format, str methods, tuple-unpacked constants)
GAPS      the survivors the review named

The reviewer corpus (cases19-34) is embedded in _fp2r4_corpus.py. Offline: ast only.
"""
from __future__ import annotations

import pathlib
import sys
import textwrap
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import suvarna_level_wave as slw  # noqa: E402
from _fp2r4_corpus import HIDDEN, PARTIAL, SETS  # noqa: E402

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


# ───────────────────────── the reviewer's corpus (cases19-34) ─────────────────────────

@pytest.mark.parametrize("cid", sorted(PARTIAL))
def test_reviewer_corpus_round4_every_false_complete_reads_partial(repo, cid):
    partial(repo, PARTIAL[cid])


@pytest.mark.parametrize("cid", sorted(HIDDEN))
def test_reviewer_corpus_round4_a_constant_template_is_read_as_the_statement_it_runs(repo, cid):
    res = scan(repo, HIDDEN[cid])
    assert "not_scanned" in res or "public.hidden" in res["tables"], res


@pytest.mark.parametrize("cid", sorted(SETS))
def test_reviewer_corpus_round4_controls_keep_exactly_their_tables(repo, cid):
    src, truth = SETS[cid]
    res = scan(repo, src)
    assert res.get("tables") == truth, (cid, res)


# ───────────────────────── MEDIUM-1: the third reading ─────────────────────────

@pytest.mark.parametrize("sql", [
    "DO $$ BEGIN DELETE /*x*/ FROM hidden; END $$",
    "DO $t$ BEGIN INSERT --x\n INTO hidden VALUES (1); END $t$",
    "SELECT run_sql('DELETE /*x*/ FROM hidden')",
    "SELECT 'MERGE /*x*/ INTO hidden USING s ON true WHEN MATCHED THEN DELETE'",
    "SELECT 'DROP /*x*/ TABLE hidden'",
    "SELECT 'DROP /*x*/ SCHEMA hidden CASCADE'",
    "SELECT 'REFRESH /*x*/ MATERIALIZED VIEW hidden'",
    "SELECT 'CREATE /*x*/ TABLE hidden (x int)'",
    "SELECT 'ALTER /*x*/ TABLE hidden ADD COLUMN y int'",
    "SELECT 'CREATE TEMP /*x*/ TABLE hidden (x int)'",
    "DO $$ BEGIN WITH d AS (DELETE /*x*/ FROM hidden RETURNING *) SELECT 1; END $$",
    "SELECT 'a' || 'DELETE /*x*/ FROM hidden'",
    "PREPARE p AS SELECT 1; EXECUTE 'DELETE /*x*/ FROM hidden'",
    "CREATE FUNCTION f() RETURNS void AS $$ BEGIN UPDATE /*x*/ hidden SET a = 1; END $$ LANGUAGE plpgsql",
    "SELECT $$ x $$ || 'TRUNCATE /*x*/ hidden'",
])
def test_a_keyword_split_by_a_comment_inside_a_string_or_dollar_body_is_still_seen(repo, sql):
    res = scan(repo, OWN + f"def r(cur):\n    cur.execute({sql!r})\n")
    assert "not_scanned" in res or "public.hidden" in res["tables"], (sql, res)


def test_the_third_reading_strips_every_marker_wherever_it_sits():
    f = slw._strip_sql_comments
    assert f("DO $$ DELETE /*x*/ FROM t $$", quote_aware=False) == "DO $$ DELETE   FROM t $$"
    assert f("DO $$ DELETE /*x*/ FROM t $$", quote_aware=True) == "DO $$ DELETE /*x*/ FROM t $$"
    assert f("a 'x -- y' b", quote_aware=False) == "a 'x  "
    assert f("a /* c */ b", quote_aware=False) == f("a /* c */ b", quote_aware=True)


def test_the_three_readings_are_unioned_in_scan_text(repo):
    sc = slw._WriteScan(__import__("ast").parse("x = 'DO $$ BEGIN DELETE /*x*/ FROM hidden; END $$'\n"))
    assert "public.hidden" in sc.tables, sc.tables


# ───────────────────────── LOW-1: the lexer ─────────────────────────

def test_a_dollar_inside_an_identifier_does_not_open_a_dollar_quote():
    f = slw._strip_sql_comments
    assert f("SELECT a$b$ ; DELETE /*x*/ FROM hidden") == "SELECT a$b$ ; DELETE   FROM hidden"
    assert f("SELECT a$$ ; DELETE /*x*/ FROM hidden") == "SELECT a$$ ; DELETE   FROM hidden"
    assert f("SELECT é$t$ x -- c") == "SELECT é$t$ x  "
    assert f("SELECT $a$ -- $a$ y -- c") == "SELECT $a$ -- $a$ y  "                       # a real dollar quote
    assert f("SELECT x.$a$ -- c") == "SELECT x.$a$ -- c"                                  # after a `.`: a real (unterminated) dollar quote


def test_dollar_tag_and_identifier_edge_forms():
    f = slw._strip_sql_comments
    assert f("SELECT $1$ -- c") == "SELECT $1$  "                                         # a tag cannot start with a digit
    assert f("SELECT a_$b$ x -- c") == "SELECT a_$b$ x  "                                 # `_` continues an identifier too
    assert f("SELECT a1$b$ x -- c") == "SELECT a1$b$ x  "
    assert f("SELECT \u20ac$b$ x -- c") == "SELECT \u20ac$b$ x  "                             # any non-ASCII character continues an identifier
    assert f("SELECT (a)$b$ x -- c") == "SELECT (a)$b$ x -- c"                            # after `)` it IS a dollar quote (unterminated)


def test_a_non_ascii_dollar_tag_is_a_dollar_quote():
    f = slw._strip_sql_comments
    assert f("SELECT $é$ -- $é$; x -- c") == "SELECT $é$ -- $é$; x  "
    assert f("SELECT $日本$ /* $日本$ y /* c */") == "SELECT $日本$ /* $日本$ y  "
    assert f("SELECT $1 -- c") == "SELECT $1  "                                           # $1 is a parameter, not a tag


def test_an_unterminated_dollar_quote_runs_to_the_end_and_the_third_reading_covers_it(repo):
    f = slw._strip_sql_comments
    assert f("SELECT $tag$ $; DELETE /*x*/ FROM hidden") == "SELECT $tag$ $; DELETE /*x*/ FROM hidden"
    res = scan(repo, OWN + "x = 'SELECT $tag$ $; DELETE /*x*/ FROM hidden'\n")
    assert "not_scanned" in res or "public.hidden" in res["tables"]


def test_an_e_string_prefix_must_not_follow_an_identifier_character():
    f = slw._strip_sql_comments
    # DATE'\\' is a plain string (the E belongs to DATE): the backslash is not an escape, so the string ends at the 2nd quote
    assert f("SELECT DATE'\\'; DELETE FROM t -- c") == "SELECT DATE'\\'; DELETE FROM t  "
    assert f("SELECT E'\\'; DELETE FROM t -- c") == "SELECT E'\\'; DELETE FROM t -- c"     # a real E string: escaped quote, unterminated
    assert f("SELECT e'a\\'b' -- c") == "SELECT e'a\\'b'  "


def test_hostile_65kb_quote_dollar_and_comment_input_is_linear():
    n = 65000
    pats = {
        "quotes": "'" * n, "dq": '"' * n, "e_quotes": "E'" * (n // 2), "e_bs": "E'" + "\\" * (n - 4) + "'",
        "dollar_pairs": "$a$ x $a$ " * (n // 10), "dollar_open_many": "$a$" * (n // 3),
        "dollar_nest": "".join(f"$t{i}$ " for i in range(n // 8)), "dollar_unclosed_alt": "$a$ $b$ " * (n // 8),
        "comment_open": "/*" * (n // 2), "line_comments": "--\n" * (n // 3), "dashes": "-" * n, "stars": "/*/" * (n // 3),
        "mix": "'--' /* ' */ " * (n // 14), "ident_dollars": "a$b$" * (n // 4), "unicode_tags": "$é$ x " * (n // 6),
    }
    for name, text in pats.items():
        for qa in (True, False):
            t0 = time.perf_counter()
            slw._strip_sql_comments(text, qa)
            assert time.perf_counter() - t0 < 3.0, (name, qa)


# ───────────────────────── MEDIUM-2: immutable or policed ─────────────────────────

M2_ESCAPES = {
    "call_result_alias": IMP + "def make():\n    return ['DELETE FROM a']\nQL = make()\nR = QL\nR.append(Q)\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "call_result_helper_param": IMP + "def make():\n    return ['x']\nQL = make()\ndef add(l):\n    l.append(Q)\nadd(QL)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "slice_copy_alias": IMP + "QL = ['x'][:]\nR = QL\nR.append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "identity_function": IMP + "def make(l):\n    return l\nQL = make(['x'])\nR = QL\nR.append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "class_body_alias": IMP + "def make():\n    return ['x']\nQL = make()\nclass K:\n    q = QL\nK.q.append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "tuple_holding_a_list": IMP + "T = (['x'],)\nL = T[0]\nL.append(Q)\ndef r(cur):\n    cur.execute(T[0][0])\n",
    "tuple_holding_a_list_loop": IMP + "T = (['x'],)\nfor l in T:\n    l.append(Q)\ndef r(cur):\n    cur.execute(T[0][0])\n",
    "tuple_holding_a_list_passed": IMP + "T = (['x'],)\ndef f(l):\n    l.append(Q)\nf(T[0])\ndef r(cur):\n    cur.execute(T[0][0])\n",
    "setdefault_list": IMP + "D = {}\nl = D.setdefault('k', [])\nl.append(Q)\ndef r(cur):\n    for q in D['k']:\n        cur.execute(q)\n",
    "dict_item_list_values_loop": IMP + "D = {}\nD['k'] = ['x']\nfor v in D.values():\n    v.append(Q)\ndef r(cur):\n    for q in D['k']:\n        cur.execute(q)\n",
    "dict_from_call_alias": IMP + "def make():\n    return {'k': 'x'}\nD = make()\nE = D\nE['z'] = Q\ndef r(cur):\n    for q in D.values():\n        cur.execute(q)\n",
    "attribute_call_result": IMP + "def make():\n    return ['x']\nclass H:\n    q = make()\nH.q.append(Q)\ndef r(cur):\n    for q in H.q:\n        cur.execute(q)\n",
    "list_in_list": "QS = [['x']]\ndef r(cur):\n    cur.execute(QS[0][0])\n",
    "list_if_list": IMP + "QS = {'a': [] if 1 else []}\ndef r(cur):\n    cur.execute(QS['a'][0])\n",
    "list_or_list": "QS = [[] or []]\ndef r(cur):\n    cur.execute(QS[0][0])\n",
    "list_plus_list": "QS = {'a': [] + ['x']}\ndef r(cur):\n    cur.execute(QS['a'][0])\n",
    "keyword_escape": IMP + "QL = ['x']\ndef add(l):\n    l.append(Q)\nadd(l=QL)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "unknown_receiver_method": IMP + "QL = ['x']\nQL.custom(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "ifexp_with_a_mutable_branch": IMP + "def make():\n    return ['x']\nq = 'a' if 1 else make()\nR = q\nR.append(Q)\ndef r(cur):\n    cur.execute(q[0])\n",
    "boolop_with_a_mutable_branch": IMP + "def make():\n    return ['x']\nq = 'a' or make()\nR = q\nR.append(Q)\ndef r(cur):\n    cur.execute(q[0])\n",
    "mixed_tuple_holding_a_list": IMP + "T = ('a', ['x'])\nL = T[1]\nL.append(Q)\ndef r(cur):\n    cur.execute(T[1][0])\n",
    "split_result_aliased": IMP + "W = 'a b'.split()\nR = W\nR.append(Q)\ndef r(cur):\n    cur.execute(W[0])\n",
    "partition_result_aliased": IMP + "W = 'a b'.partition(' ')\nR = list(W)\nW2 = W\nW2 += (Q,)\ndef r(cur):\n    cur.execute(W[0])\n",
    "param_with_mutable_argument_aliased": IMP + "def h(cur, l):\n    R = l\n    R.append(Q)\n    cur.execute(l[0])\nh(None, ['x'])\n",
    "param_ok_but_container_passed_on": "def log(x):\n    pass\ndef h(cur, l):\n    log(l)\n    cur.execute(l[0])\nh(None, ['x'])\n",
    "param_from_call_result": IMP + "def make():\n    return ['x']\ndef h(cur, l):\n    l.append(Q)\n    cur.execute(l[0])\nh(None, make())\n",
    "loop_var_over_list_of_lists": "QS = [['x'], ['y']]\ndef r(cur):\n    for l in QS:\n        cur.execute(l[0])\n",
}


@pytest.mark.parametrize("name", sorted(M2_ESCAPES))
def test_a_value_that_is_not_provably_immutable_is_policed_as_a_possible_container(repo, name):
    partial(repo, OWN + M2_ESCAPES[name])


M2_CLEAN = {
    "string_params": "def h(cur, q):\n    cur.execute(q)\nh(None, 'SELECT 1')\nh(None, OWN)\n",
    "loop_over_list_of_strings": "QS = ['SELECT 1', 'SELECT 2']\ndef r(cur):\n    for q in QS:\n        cur.execute(q)\n",
    "local_function_returning_str": "def g(n):\n    return 'SELECT ' + str(n)\ndef r(cur):\n    cur.execute(g(1))\n",
    "local_function_returning_tuple_of_str": "def g():\n    return ('SELECT 1', 'SELECT 2')\ndef r(cur):\n    a, b = g()\n    cur.execute(a)\n",
    "tuple_of_strings": "T = ('SELECT 1', 'SELECT 2')\ndef r(cur):\n    for q in T:\n        cur.execute(q)\n    cur.execute(T[0])\n",
    "tuple_of_tuples": "T = (('a', 'SELECT 1'), ('b', 'SELECT 2'))\ndef r(cur):\n    for k, q in T:\n        cur.execute(q)\n",
    "frozenset_of_strings": "S = frozenset(['SELECT 1'])\ndef r(cur):\n    for q in S:\n        cur.execute(q)\n",
    "dict_of_strings_values": "D = {'a': 'SELECT 1'}\ndef r(cur):\n    for q in D.values():\n        cur.execute(q)\n",
    "built_up_string": "q = 'SELECT 1'\nq += ' WHERE 1 = 1'\nq = q + ' AND 2 = 2'\ndef r(cur):\n    cur.execute(q)\n",
    "string_methods": "def r(cur):\n    q = 'select 1'.upper().strip()\n    cur.execute(q)\n",
    "number_results": "def r(cur, rows):\n    n = len(rows)\n    cur.execute(f'SELECT {n}')\nr(None, [])\n",
    "class_str_attribute": "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "list_mutated_with_strings_on_the_bare_name": "QL = []\nQL.append('SELECT 1')\nQL.extend(['SELECT 2'])\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "dict_item_store_of_strings": "D = {}\nD['a'] = 'SELECT 1'\ndef r(cur):\n    cur.execute(D['a'])\n",
    "container_passed_to_execute_as_params": "P = [1, 2]\ndef r(cur):\n    cur.execute('SELECT %s, %s', P)\n    cur.executemany('SELECT %s', [P])\n",
    "string_used_as_a_receiver": "q = 'select 1'\ndef r(cur):\n    cur.execute(q.upper())\n    cur.execute(q.format())\n",
    "string_in_comparison_and_fstring": "q = 'SELECT 1'\ndef r(cur):\n    if q == 'x':\n        pass\n    cur.execute(f'{q} -- c')\n",
    "string_passed_to_an_unknown_call": "def log(x):\n    pass\nq = 'SELECT 1'\ndef r(cur):\n    log(q)\n    cur.execute(q)\n",
    "fstring_value_passed_on": "def log(x):\n    pass\nq = f'SELECT {1}'\ndef r(cur):\n    log(q)\n    cur.execute(q)\n",
    "percent_value_passed_on": "def log(x):\n    pass\nq = 'SELECT %s' % 'x'\ndef r(cur):\n    log(q)\n    cur.execute(q)\n",
    "number_result_passed_on": "def log(x):\n    pass\ndef r(cur, rows):\n    n = len(rows)\n    log(n)\n    cur.execute(f'SELECT {n}')\nr(None, [])\n",
    "frozenset_passed_on": "def log(x):\n    pass\nS = frozenset(['SELECT 1'])\nlog(S)\ndef r(cur):\n    for q in S:\n        cur.execute(q)\n",
    "loop_variable_over_dict_values_passed_on": "def log(x):\n    pass\nD = {'a': 'SELECT 1'}\ndef r(cur):\n    for q in D.values():\n        log(q)\n        cur.execute(q)\n",
    "loop_variable_over_comprehension_passed_on": "def log(x):\n    pass\ndef r(cur):\n    for q in [x for x in ('SELECT 1', 'SELECT 2')]:\n        log(q)\n        cur.execute(q)\n",
    "dict_key_passed_on": "def log(x):\n    pass\ndef r(cur):\n    for k, v in {'SELECT 1': 1}.items():\n        log(k)\n        cur.execute(k)\n",
    "policed_value_handed_to_execute": "QL = ['SELECT 1']\ndef h(cur, q):\n    cur.execute(q)\nh(None, QL[0])\n",
    "policed_value_as_a_str_receiver": "QL = ['select 1']\nq = QL[0]\ndef r(cur):\n    cur.execute(q.upper())\n",
    "policed_value_in_a_concatenation": "QL = ['SELECT 1']\nq = QL[0]\ndef r(cur):\n    cur.execute(q + ' -- c')\n",
    "string_passed_to_pure_builtins": "q = 'SELECT 1'\ndef r(cur):\n    print(len(q), str(q))\n    cur.execute(q)\n",
}


@pytest.mark.parametrize("name", sorted(M2_CLEAN))
def test_provably_immutable_values_and_read_only_containers_stay_provable(repo, name):
    complete(repo, OWN + M2_CLEAN[name])


def test_immutability_helpers_directly():
    ast = __import__("ast")
    sc = slw._WriteScan(ast.parse("A = 'x'\nB = ('x', 1, None, b'y')\nC = ['x']\nD = (['x'],)\nE = A + 'y'\nF = (A, B)\n"
                                  "def mk():\n    return 'x'\ndef mkl():\n    return ['x']\nG = mk()\nH = mkl()\nI = {'a': 'b'}\n"))
    assert sc._name_immutable("A") and sc._name_immutable("B") and sc._name_immutable("E") and sc._name_immutable("F")
    assert sc._name_immutable("G")
    assert not sc._name_immutable("C") and not sc._name_immutable("D") and not sc._name_immutable("H") and not sc._name_immutable("I")
    assert not sc._name_immutable("unbound")
    assert sc._elements_immutable(ast.parse("['a', ('b', 1)]", mode="eval").body)
    assert not sc._elements_immutable(ast.parse("[['a']]", mode="eval").body)


# ───────────────────────── LOW-4: performance of the class-attribute lookup ─────────────────────────

def test_one_class_with_thousands_of_sql_attributes_is_fast_or_capped(repo):
    n = 5000
    body = "class B:\n" + "".join(f"    s{i}='DELETE FROM a{i}'\n" for i in range(n)) + "def run(cur):\n" + "".join(f"    cur.execute(B.s{i})\n" for i in range(n))
    t0 = time.perf_counter()
    res = scan(repo, body)
    assert time.perf_counter() - t0 < 8.0  # wall-clock guard against quadratic/exponential blow-ups (seconds when broken); loose for loaded CI
    assert "tables" in res or res["not_scanned"].startswith("resolver_work_cap"), res


def test_thousands_of_classes_sharing_a_method_name_are_fast_or_capped(repo):
    n = 5000
    body = ("".join(f"class C{i}:\n    sql='DELETE FROM a{i}'\n    def go(self, cur):\n        cur.execute(self.sql)\n" for i in range(n))
            + "def run(cur):\n" + "".join(f"    C{i}().go(cur)\n" for i in range(n)))
    t0 = time.perf_counter()
    res = scan(repo, body)
    assert time.perf_counter() - t0 < 10.0  # wall-clock guard against quadratic/exponential blow-ups (seconds when broken); loose for loaded CI
    assert "tables" in res or res["not_scanned"].startswith("resolver_work_cap"), res


def test_class_bodies_are_walked_once_and_charged_to_the_cap(repo, monkeypatch):
    monkeypatch.setattr(slw._WriteScan, "MAX_RESOLVER_STEPS", 40)
    body = "class B:\n" + "".join(f"    s{i}='x{i}'\n" for i in range(200)) + "def run(cur):\n    cur.execute(B.s1)\n"
    res = scan(repo, OWN + body)
    assert "tables" not in res and res["not_scanned"].startswith("resolver_work_cap"), res


def test_a_class_is_indexed_once_per_file():
    ast = __import__("ast")
    sc = slw._WriteScan(ast.parse("class B:\n    a = 'x'\n    b = 'y'\n"))
    sc._class_info("B")
    steps = sc._steps
    for _ in range(50):
        sc._class_attr_value("B", "a")
        sc._class_attr_value("B", "b")
    assert sc._steps == steps


# ───────────────────────── LOW: class and dispatch residuals ─────────────────────────

CL = "class A:\n    sql = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\n"
LOW_CLASS = {
    "type_subclass": IMP + CL + "Sub = type('Sub', (A,), {'sql': Q})\ndef r(cur):\n    Sub().go(cur)\n",
    "type_replacement": IMP + CL + "A = type('A', (), {'sql': Q})\ndef r(cur):\n    cur.execute(A.sql)\n",
    "type_anywhere": CL + "def r(n):\n    return type(n, (), {})\n",
    "class_name_rebound_to_import": IMP + CL + "A = Q\n",
    "class_name_rebound_to_other": "from c import Other\n" + CL + "A = Other\ndef r(cur):\n    A().go(cur)\n",
    "class_name_imported_again": "from c import A\n" + CL.replace("class A", "class A"),
    "class_name_imported_after": CL + "from c import A\n",
    "class_name_defined_as_function": CL + "def A():\n    pass\n",
    "class_name_is_a_parameter": CL + "def r(cur, A):\n    A().go(cur)\n",
    "class_name_is_a_loop_variable": "from c import Other\n" + CL + "for A in [Other]:\n    pass\n",
    "class_name_global_rebound": "from c import Other\n" + CL + "def f():\n    global A\n    A = Other\n",
    "getattribute_override": IMP + CL.replace("    def go", "    def __getattribute__(self, n):\n        return Q\n    def go"),
    "setattr_override": IMP + CL.replace("    def go", "    def __setattr__(self, n, v):\n        pass\n    def go"),
    "setattr_call_on_instance": IMP + CL + "def r(cur):\n    s = A()\n    s.__setattr__('sql', Q)\n    s.go(cur)\n",
    "setattr_call_on_class": IMP + CL + "A.__setattr__(A, 'sql', Q)\n",
    "type_setattr": IMP + CL + "type.__setattr__(A, 'sql', Q)\n",
    "delattr": CL + "def r(a):\n    a.__delattr__('sql')\n",
    "init_subclass_hook": CL.replace("    def go", "    def __init_subclass__(cls):\n        pass\n    def go"),
}


@pytest.mark.parametrize("name", sorted(LOW_CLASS))
def test_class_attributes_are_not_provable_when_the_class_or_its_name_can_be_replaced(repo, name):
    partial(repo, OWN + LOW_CLASS[name])


def test_class_residual_controls_stay_provable(repo):
    complete(repo, OWN + CL + "def r(cur):\n    A().go(cur)\n    cur.execute(A.sql)\n", ("public.a", "public.t_a"))
    complete(repo, OWN + CL.replace("    def go", "    def __getattr__(self, n):\n        return 1\n    def go"), ("public.a", "public.t_a"))   # only for MISSING attributes
    complete(repo, OWN + CL + "def r(n):\n    return type(n)\n", ("public.a", "public.t_a"))                    # one-argument type()


LOW_DISPATCH = {
    "globals_read": "def r():\n    return globals().get('T')\n",
    "globals_item": "def r():\n    return globals()['T']\n",
    "locals_keys": "def r():\n    return locals().keys()\n",
    "vars_items": "def r():\n    return vars().items()\n",
    "locals_format": "def r(x):\n    return 'a {x}'.format(**locals())\n",
    "builtins_name": "def r():\n    return __builtins__\n",
    "builtins_dict": "def r():\n    return __builtins__.__dict__['globals']\n",
    "globals_mutates_list": IMP + "QL = ['x']\nglobals()['QL'].append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "vars_get": IMP + "QL = ['x']\nvars().get('QL').append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "globals_values_unpack": IMP + "QL = ['x']\n[*globals().values()][0].append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "globals_getitem": IMP + "QL = ['x']\nglobals().__getitem__('QL').append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "gc_get_objects": "import gc\ndef r():\n    return gc.get_objects()\n",
    "gc_get_referrers": "import gc\ndef r(o):\n    return gc.get_referrers(o)\n",
    "gc_get_referents": "import gc\ndef r(o):\n    return gc.get_referents(o)\n",
}


@pytest.mark.parametrize("name", sorted(LOW_DISPATCH))
def test_any_use_of_the_namespace_dicts_builtins_or_gc_is_dynamic_dispatch(repo, name):
    partial(repo, OWN + LOW_DISPATCH[name], "dynamic_dispatch")


def test_drop_schema_is_a_tripwire(repo):
    for sql in ("DROP SCHEMA hidden CASCADE", "drop /*x*/ schema if exists hidden", "DO $$ BEGIN DROP SCHEMA hidden; END $$"):
        res = scan(repo, OWN + f"x = {sql!r}\n")
        assert "tables" not in res and "DROP SCHEMA" in res["not_scanned"], (sql, res)


# ───────────────────────── templates of constants are read as the statement they run ─────────────────────────

TEMPLATES = {
    "percent_tuple": "V = 'DELETE'\nF = 'FROM'\ndef r(cur):\n    cur.execute('%s %s hidden' % (V, F))\n",
    "percent_literals": "def r(cur):\n    cur.execute('%s %s hidden' % ('DELETE', 'FROM'))\n",
    "format_positional": "V = 'DELETE'\nF = 'FROM'\ndef r(cur):\n    cur.execute('{} {} hidden'.format(V, F))\n",
    "format_indexed": "def r(cur):\n    cur.execute('{1} {0} hidden'.format('FROM', 'DELETE'))\n",
    "format_named": "def r(cur):\n    cur.execute('{v} {f} hidden'.format(v='DELETE', f='FROM'))\n",
    "tuple_unpacked_constants": "v, f = 'DELETE', 'FROM'\ndef r(cur):\n    cur.execute(f'{v} {f} hidden')\n",
    "split_keyword": "V = 'DEL'\ndef r(cur):\n    cur.execute(f'{V}ETE FROM hidden')\n",
    "split_keyword_concat": "V = 'DEL'\ndef r(cur):\n    cur.execute(V + 'ETE FROM hidden')\n",
    "strip_then_concat": "def r(cur):\n    cur.execute('DELETE FROM'.strip() + ' hidden')\n",
    "rstrip_name": "V = 'DELETE FROM '\ndef r(cur):\n    cur.execute(V.rstrip() + ' hidden')\n",
    "replace_literal": "def r(cur):\n    cur.execute('DELETE FROM xx'.replace('xx', 'hidden'))\n",
    "replace_constants": "T = 'hidden'\ndef r(cur):\n    cur.execute('DELETE FROM xx'.replace('xx', T))\n",
    "upper_lower_mix": "def r(cur):\n    cur.execute('de' + 'lete'.upper() + ' from hidden')\n",
    "collapse_spaces": "def r(cur):\n    cur.execute('DELETE   FROM'.replace('  ', ' ') + ' hidden')\n",
    "join_constants": "V, F, T = 'DELETE', 'FROM', 'hidden'\ndef r(cur):\n    cur.execute(' '.join([V, F, T]))\n",
    "nested_fstring": "V = 'DELETE'\nT = 'hidden'\ndef r(cur):\n    cur.execute(f'{V} FROM {T}')\n",
    "fstring_expr_concat": "V = 'DEL'\ndef r(cur):\n    cur.execute(f\"{V + 'ETE'} FROM hidden\")\n",
    "fstring_expr_percent": "V = 'DEL'\ndef r(cur):\n    cur.execute(f\"{'%sETE' % V} FROM hidden\")\n",
    "fstring_expr_join": "V = 'DELETE'\nF = 'FROM'\ndef r(cur):\n    cur.execute(f\"{' '.join([V, F])} hidden\")\n",
    "fstring_expr_method": "V = 'delete'\ndef r(cur):\n    cur.execute(f\"{V.upper()} FROM hidden\")\n",
    "fstring_expr_nested_fstring": "V = 'DEL'\ndef r(cur):\n    cur.execute(f\"{f'{V}ETE'} FROM hidden\")\n",
}


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_a_template_of_constants_is_scanned_as_the_statement_it_runs(repo, name):
    res = scan(repo, OWN + TEMPLATES[name])
    assert "not_scanned" in res or "public.hidden" in res["tables"], (name, res)


def test_rendering_helpers():
    ast = __import__("ast")
    r = slw._render_sql_node
    assert r(ast.parse("'%s x %s' % (a, 'b')", mode="eval").body) == "\x01a\x02 x b"
    assert r(ast.parse("'%s%%' % a", mode="eval").body) == "\x01a\x02%"
    assert r(ast.parse("'%d %s' % (a,)", mode="eval").body) is None                    # arity mismatch
    assert r(ast.parse("'%(k)s' % d", mode="eval").body) is None                       # mapping key: not supported
    assert r(ast.parse("'{} and {}'.format(a, 'b')", mode="eval").body) == "\x01a\x02 and b"
    assert r(ast.parse("'{0}{1}{0}'.format('x', y)", mode="eval").body) == "x\x01y\x02x"
    assert r(ast.parse("'{a.b}'.format(a=x)", mode="eval").body) is None              # attribute field
    assert r(ast.parse("'{:>5}'.format(x)", mode="eval").body) is None                 # format spec
    assert r(ast.parse("'{}'.format(*xs)", mode="eval").body) is None
    sc = slw._WriteScan(ast.parse("V = 'DEL'\nF = 'FROM'\n"))
    ev = lambda src: sc._eval_const(ast.parse(src, mode="eval").body, 0)  # noqa: E731
    assert ev("V + 'ETE ' + F") == "DELETE FROM" and ev("'%s-%s' % (V, F)") == "DEL-FROM"
    assert ev("'a'.zfill(3)") == "00a" and ev("'x'.replace('x', V)") == "DEL" and ev("', '.join([V, F])") == "DEL, FROM"
    assert ev("unknown") is None and ev("os.getcwd()") is None and ev("'a'.format(os.sep)") is None


def test_eval_const_reads_nested_fstrings_and_decorated_functions_are_not_immutable():
    ast = __import__("ast")
    sc = slw._WriteScan(ast.parse("V = 'DEL'\nfrom c import deco\n@deco\ndef mk():\n    return 'x'\ndef mk2():\n    return 'x'\n"))
    assert sc._eval_const(ast.parse("f\"{f'{V}ETE'} FROM\"", mode="eval").body, 0) == "DELETE FROM"
    assert sc._eval_const(ast.parse("f'{V!r}'", mode="eval").body, 0) is None
    assert not sc._immutable_expr(ast.parse("mk()", mode="eval").body) and sc._immutable_expr(ast.parse("mk2()", mode="eval").body)


def test_tuple_unpack_binds_each_name_its_own_literal_and_other_unpacking_binds_none():
    ast = __import__("ast")
    sc = slw._WriteScan(ast.parse("a, b = 'x', 'y'\n(c, (d, e)) = 'p', ('q', 'r')\nf, g = h()\n*i, j = 'u', 'v'\n"))
    assert sc._resolve_const("a") == "x" and sc._resolve_const("b") == "y"
    assert sc._resolve_const("c") == "p" and sc._resolve_const("d") == "q" and sc._resolve_const("e") == "r"
    assert sc._resolve_const("f") is None and sc._resolve_const("g") is None and sc._resolve_const("i") is None


# ───────────────────────── the survivors the review named ─────────────────────────

def test_raw_pass_defers_only_for_real_comment_adjacent_verbs(repo):                  # raw_flag_true
    partial(repo, OWN + "x = \"UPDATE %s SET a='--'\"\n", "unparseable_write_target")
    partial(repo, OWN + "x = \"COPY %s FROM STDIN WITH (NULL '--')\"\n", "unparseable_write_target")
    complete(repo, OWN + "x = 'UPDATE t_a /* c */ SET a = 1'\n")


def test_keyword_argument_escape_of_a_container(repo):                                # c_keyword_off
    partial(repo, OWN + M2_ESCAPES["keyword_escape"], "container_escapes")


def test_receiver_of_an_unknown_method_escapes(repo):                                 # c_receiver_off
    partial(repo, OWN + M2_ESCAPES["unknown_receiver_method"], "container_escapes")


def test_nested_container_forms_are_refused(repo):                                    # c_ctr_* / c_nested_list_off
    for name in ("list_in_list", "list_if_list", "list_or_list", "list_plus_list"):
        partial(repo, OWN + M2_ESCAPES[name], "container_escapes")


def test_exact_boundaries_of_the_work_cap_and_literal_cap():
    assert slw._WriteScan.MAX_RESOLVER_STEPS == 60_000 and slw.MAX_SQL_LITERAL_CHARS == 64 * 1024


# ───────────────────────── real tree ─────────────────────────

def test_real_tree_round4_scans_without_exception_and_keeps_the_known_clean_writers():
    helpers = slw.helper_write_effects(REAL_REPO)
    scanned, flipped = {}, {}
    for f in sorted((REAL_REPO / WRITERS).glob("*.py")):
        res = slw.scan_writer_tables(f.stem, REAL_REPO, helpers)
        assert ("tables" in res) != ("not_scanned" in res), (f.name, res)
        (scanned if "tables" in res else flipped)[f.stem] = res
    for asset in ("bo_karanajala", "bo_sangati", "bo_upaya", "mi_darshana", "ga_dashas", "ga_condition", "ga_tajaka",
                  "bo_laksana", "bg_sky_calendar", "ga_vichara"):
        assert asset in scanned, (asset, flipped.get(asset))
    # K1-2 now delegates candidate writes to an unsupported kala_core helper.
    assert flipped["ka_avadhi"] == {"not_scanned": "no_write_statement_found (delegates to another module, or read-only: not distinguishable)"}
    for asset in ("bg_gochara_arcs", "ka_gochara", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate"):
        assert asset in flipped, asset
