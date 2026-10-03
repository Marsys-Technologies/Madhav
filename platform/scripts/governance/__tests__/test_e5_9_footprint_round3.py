"""test_e5_9_footprint_round3.py -- Suvarna E5.9 / FP2 review round 3.

F1  a comment marker inside a SQL STRING must not hide a dynamic write target (the stripper is quote-aware, and the raw and the
    comment-free passes are UNIONED: every table and every not-scanned reason of either pass is kept)
F2  a name bound to a mutable container is provable only while every use of it is a read (aliasing, passing on, a bound method,
    a mutation through an attribute receiver, returning ... => container_escapes)
F3  a class attribute is provable only on a plain undecorated class with no base, no local subclass, no constructor argument,
    assigned exactly once at the top level of the class body (dataclass / NamedTuple defaults, subclass overrides, `+=`, `if`
    rebinding, `__dict__` ... are not)
LOW dispatch by string (getattr / globals / sys.modules / __import__ / importlib / frames), `sum`, classmethod offsets, imported
    decorators, a verb split over names, and the test gaps the review found.

The reviewer's corpus (cases12/13/15/16/17/18) is embedded verbatim in _fp2r3_corpus.py. Offline: ast only.
"""
from __future__ import annotations

import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import suvarna_level_wave as slw  # noqa: E402
from _fp2r3_corpus import COMMENT_PARTIAL, COMMENT_SETS, PARTIAL  # noqa: E402

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


# ───────────────────────── the reviewer's corpus ─────────────────────────

@pytest.mark.parametrize("cid", sorted(PARTIAL))
def test_reviewer_corpus_every_false_complete_reads_partial(repo, cid):
    partial(repo, PARTIAL[cid])


@pytest.mark.parametrize("cid", sorted(COMMENT_PARTIAL))
def test_reviewer_comment_corpus_dynamic_targets_read_partial(repo, cid):
    partial(repo, COMMENT_PARTIAL[cid])


@pytest.mark.parametrize("cid", sorted(COMMENT_SETS))
def test_reviewer_comment_corpus_literal_statements_keep_exactly_their_tables(repo, cid):
    src, truth = COMMENT_SETS[cid]
    expected = sorted({t if "." in t else f"public.{t}" for t in truth})
    res = scan(repo, src)
    assert res.get("tables") == expected, (cid, res)


# ───────────────────────── F1: quote-aware comments, union of both passes ─────────────────────────

@pytest.mark.parametrize("sql", [
    "INSERT INTO c VALUES ('--'); DELETE FROM {T}",
    "INSERT INTO c VALUES ('/*'); DELETE FROM {T}",
    "SELECT '--'; UPDATE {T} SET x = 1",
    "SELECT '/*'; COPY {T} FROM STDIN",
    "SELECT '--'; TRUNCATE {T}, c",
    "SELECT $$--$$; DELETE FROM {T}",
    "SELECT $q$/*$q$; DELETE FROM {T}",
    "SELECT E'\\\\'--'; DELETE FROM {T}",
    'SELECT "--"; DELETE FROM {T}',
    "SELECT '--' -- x\n; DELETE FROM {T}",
])
def test_a_comment_marker_inside_a_string_never_hides_a_dynamic_write_target(repo, sql):
    body = OWN + "T = 'a'\nif 1:\n    T = 'b'\ndef r(cur):\n    cur.execute(f" + repr(sql) + ")\n"
    partial(repo, body)


def test_the_stripper_is_quote_aware():
    f = slw._strip_sql_comments
    assert f("SELECT '--'; DELETE FROM t") == "SELECT '--'; DELETE FROM t"
    assert f("SELECT '/*'; DELETE FROM t") == "SELECT '/*'; DELETE FROM t"
    assert f("SELECT 'it''s -- not'; x -- y") == "SELECT 'it''s -- not'; x  "
    assert f("SELECT E'a\\'--b'; z") == "SELECT E'a\\'--b'; z"                       # backslash escape in an E string
    assert f("SELECT e'a\\'--b' -- c\nz") == "SELECT e'a\\'--b'  \nz"
    assert f("SELECT 'a\\'--b' -- c") == "SELECT 'a\\' "                                  # plain string: a backslash is not an escape
    assert f('SELECT "a--b", c -- d') == 'SELECT "a--b", c  '
    assert f("SELECT $$ -- $$ x -- y") == "SELECT $$ -- $$ x  "
    assert f("SELECT $t$ /* $t$ x /* c */ y") == "SELECT $t$ /* $t$ x   y"
    assert f("a /* c */ b") == "a   b" and f("a -- c\nb") == "a  \nb" and f("a --c\r\nb") == "a  \r\nb"
    assert f("a 'unterminated -- b") == "a 'unterminated -- b"
    assert f("x \x01'--'\x02 y -- z") == "x \x01'--'\x02 y  "                          # a placeholder is opaque
    assert f("x \x01'\x02 y /* c */ z") == "x \x01'\x02 y   z"                          # even when it holds an unbalanced quote
    assert f("a 'it''s' b -- c") == "a 'it''s' b  " and f("a 'it''s -- c") == "a 'it''s -- c"   # a doubled quote stays inside the run
    assert f("a \"x\"\"y -- z\" b") == "a \"x\"\"y -- z\" b"


@pytest.mark.parametrize("sql,label", [
    ("x -- y'; CREATE TABLE t_new (x int)", "CREATE TABLE"),                      # a fragment that starts INSIDE a string of its neighbour
    ("x /* y'; DROP TABLE t_old; */ z", "DROP TABLE"),
    ("x -- y'; REFRESH MATERIALIZED VIEW mv_x", "REFRESH MATERIALIZED VIEW"),
])
def test_the_raw_pass_still_sees_a_tripwire_the_stripper_hid_by_misreading_a_fragment(repo, sql, label):
    res = scan(repo, OWN + f"x = {sql!r}\n")
    assert "tables" not in res and label in res["not_scanned"], res


def test_a_fragment_that_starts_inside_a_string_still_names_its_table(repo):
    res = scan(repo, "x = \"x -- y'; DELETE FROM t_b\"\n")
    assert res["tables"] == ["public.t_b"], res


def test_the_stripper_is_linear_on_hostile_quote_input():
    import time
    for text in ("'" * 30000, '"' * 30000, "$a$" * 10000, "E'" * 15000, "'--" * 10000, "$$" * 15000, "\\'" * 15000):
        t0 = time.perf_counter()
        slw._strip_sql_comments(text)
        assert time.perf_counter() - t0 < 0.3, text[:6]


def test_the_two_passes_are_unioned_so_a_comment_only_ever_adds(repo):
    res = scan(repo, "x = \"SELECT '--'; DELETE FROM t_b -- x\\n; DELETE FROM t_c\"\n")
    assert res["tables"] == ["public.t_b", "public.t_c"]
    sc = slw._WriteScan(__import__("ast").parse("T = 'a'\nif 1:\n    T = 'b'\nx = f\"SELECT '--'; DELETE FROM {T}\"\n"))
    assert any(r.startswith("unresolved_table_expression") for r in sc.unresolved), sc.unresolved


# ───────────────────────── F2: containers escape ─────────────────────────

F2_ESCAPES = {
    "alias": IMP + "QL = ['DELETE FROM a']\nQ2 = QL\nQ2.append(Q)\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "bound_method": IMP + "QL = ['x']\nap = QL.append\nap(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "helper_parameter": IMP + "QL = ['x']\ndef add(l):\n    l.append(Q)\nadd(QL)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "helper_two_args": IMP + "QL = ['x']\ndef fill(l, v):\n    l.append(v)\nfill(QL, Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "self_attribute_receiver": IMP + "class W:\n    L = ['x']\n    def go(self, cur):\n        self.L.append(Q)\n        cur.execute(self.L[0])\n",
    "class_attribute_receiver": IMP + "class W:\n    L = ['x']\n    def go(self, cur):\n        cur.execute(self.L[0])\ndef g():\n    W.L.append(Q)\n",
    "instance_attribute_receiver": IMP + "class W:\n    L = ['x']\n    def go(self, cur):\n        cur.execute(self.L[0])\ndef g(w):\n    w.L.extend([Q])\n",
    "attribute_item_store": IMP + "class W:\n    L = ['x']\n    def go(self, cur):\n        cur.execute(self.L[0])\ndef g(w):\n    w.L[0] = Q\n",
    "map_bound_append": IMP + "QS = [Q]\nQL = ['x']\nlist(map(QL.append, QS))\ndef r(cur):\n    cur.execute(QL[0])\n",
    "operator_setitem": IMP + "QL = ['x']\ndef r(cur):\n    import operator\n    operator.setitem(QL, 0, Q)\n    cur.execute(QL[0])\n",
    "dunder_setitem": IMP + "QL = {'k': 'x'}\ndef r(cur):\n    QL.__setitem__('k', Q)\n    cur.execute(QL['k'])\n",
    "dunder_iadd": IMP + "QS = [Q]\nQL = ['x']\nQL.__iadd__(QS)\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "list_append_unbound": IMP + "QL = ['x']\nlist.append(QL, Q)\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "returned": IMP + "def mk():\n    QL = ['x']\n    return QL\ndef r(cur):\n    for q in mk():\n        cur.execute(q)\n",
    "returned_then_mutated": IMP + "QL = ['x']\ndef get():\n    return QL\ndef r(cur):\n    get().append(Q)\n    cur.execute(QL[0])\n",
    "stored_in_another_container": IMP + "QL = ['x']\nBOX = {'l': QL}\nBOX['l'].append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "stored_in_list": IMP + "QL = ['x']\nBOX = [QL]\nBOX[0].append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "stored_on_attribute": IMP + "QL = ['x']\nclass H:\n    pass\nH.l = QL\nH.l.append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "starred_call": IMP + "QL = ['x']\ndef f(*a):\n    a[0].append(Q)\nf(*QL)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "sum_of_container": IMP + "QS = [['x']]\ndef r(cur):\n    cur.execute(sum(QS, [])[0])\n",
    "yielded": IMP + "QL = ['x']\ndef g():\n    yield QL\ndef r(cur):\n    for l in g():\n        l.append(Q)\n    cur.execute(QL[0])\n",
    "lambda_alias": IMP + "QL = ['x']\nf = lambda: QL\nf().append(Q)\ndef r(cur):\n    cur.execute(QL[0])\n",
    "nested_mutable": "QS = {'a': ['x']}\ndef r(cur):\n    cur.execute(QS['a'][0])\n",
    "nested_alias_mutation": IMP + "QS = {'a': []}\ninner = QS['a']\ninner.append(Q)\ndef r(cur):\n    cur.execute(QS['a'][0])\n",
    "dict_alias_through_get": IMP + "QS = {'a': ['x']}\ndef r(cur):\n    QS.get('a').append(Q)\n    cur.execute(QS['a'][0])\n",
    "container_copy_alias": IMP + "QL = ['x']\nQ2 = list(QL)\nQ3 = Q2\nQ3.append(Q)\ndef r(cur):\n    for q in Q2:\n        cur.execute(q)\n",
    "container_in_class_aliased": IMP + "class W:\n    L = ['x']\n    def go(self, cur):\n        l = self.L\n        l.append(Q)\n        cur.execute(self.L[0])\n",
}


@pytest.mark.parametrize("name", sorted(F2_ESCAPES))
def test_a_container_that_is_aliased_passed_on_or_mutated_out_of_sight_is_not_provable(repo, name):
    partial(repo, OWN + F2_ESCAPES[name])


def test_container_escape_has_its_own_named_reason(repo):
    partial(repo, OWN + F2_ESCAPES["alias"], "container_escapes")
    partial(repo, OWN + F2_ESCAPES["self_attribute_receiver"], "container_escapes")
    partial(repo, OWN + F2_ESCAPES["nested_mutable"], "container_escapes")


F2_READS = {
    "iteration": "QL = ['SELECT 1', 'SELECT 2']\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "subscript_load": "QL = ['SELECT 1']\ndef r(cur):\n    cur.execute(QL[0])\n",
    "dict_items": "D = {'a': 'SELECT 1'}\ndef r(cur):\n    for k, q in D.items():\n        cur.execute(q)\n",
    "dict_values_keys_get": "D = {'a': 'SELECT 1'}\ndef r(cur):\n    for q in D.values():\n        cur.execute(q)\n    for k in D.keys():\n        pass\n    cur.execute(D.get('a'))\n",
    "len_and_in": "QL = ['SELECT 1']\ndef r(cur):\n    if 'x' in QL and len(QL) > 0:\n        cur.execute(QL[0])\n",
    "truthiness": "QL = ['SELECT 1']\ndef r(cur):\n    if QL:\n        cur.execute(QL[0])\n    while not QL:\n        pass\n",
    "join_argument": "COLS = ['a', 'b']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(COLS) + ' FROM t_b')\n",
    "pure_builtins": "QL = ['SELECT 1']\ndef r(cur):\n    for i, q in enumerate(sorted(QL)):\n        cur.execute(q)\n    print(list(QL), set(QL), min(QL), tuple(QL))\n",
    "comprehension_source": "QL = ['SELECT 1']\ndef r(cur):\n    cur.execute(';'.join(x for x in QL))\n",
    "fstring_of_container": "QL = ['SELECT 1']\ndef r(cur):\n    cur.execute(f'SELECT {QL}')\n",
    "unpacking": "PAIR = ['SELECT 1', 'SELECT 2']\ndef r(cur):\n    a, b = PAIR\n    cur.execute(a)\n",
    "starred_in_literal": "QL = ['SELECT 1']\ndef r(cur):\n    for q in [*QL, 'SELECT 2']:\n        cur.execute(q)\n",
    "bare_mutator_with_clean_value": "QL = []\nQL.append('SELECT 1')\nQL.extend(['SELECT 2'])\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "bare_item_store_clean": "D = {}\nD['a'] = 'SELECT 1'\ndef r(cur):\n    cur.execute(D['a'])\n",
    "bare_update_from_clean_container": "A = {'a': 'SELECT 1'}\nD = {}\nD.update(A)\ndef r(cur):\n    cur.execute(D['a'])\n",
    "harmless_mutators": "QL = ['SELECT 1', 'SELECT 2']\nQL.sort()\nQL.reverse()\nQL.pop()\nQL.remove('SELECT 1')\nQL.clear()\ndef r(cur):\n    for q in QL:\n        cur.execute(q)\n",
    "class_container_read_only": "class W:\n    L = ['SELECT 1']\n    def go(self, cur):\n        for q in self.L:\n            cur.execute(q)\n",
    "dict_comp_value_read": "D = {k: 'SELECT 1' for k in 'ab'}\ndef r(cur):\n    cur.execute(D['a'])\n",
    "copy_then_iterate": "QL = ['SELECT 1']\ndef r(cur):\n    for q in QL.copy():\n        cur.execute(q)\n",
    "dict_double_star": "A = {'a': 'SELECT 1'}\nD = {**A}\ndef r(cur):\n    cur.execute(D['a'])\n",
    "concat_new_list": "A = ['SELECT 1']\nB = A + ['SELECT 2']\ndef r(cur):\n    for q in B:\n        cur.execute(q)\n",
}


@pytest.mark.parametrize("name", sorted(F2_READS))
def test_a_container_that_is_only_read_stays_provable(repo, name):
    complete(repo, OWN + F2_READS[name])


# ───────────────────────── F3: class attributes ─────────────────────────

F3_NOT_PROVABLE = {
    "dataclass_default": IMP + "from dataclasses import dataclass\n@dataclass\nclass Step:\n    sql: str = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    Step(sql=Q).go(cur)\n",
    "namedtuple_default": IMP + "from typing import NamedTuple\nclass Step(NamedTuple):\n    sql: str = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    Step(Q).go(cur)\n",
    "subclass_override": IMP + "class A:\n    sql = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\nclass B(A):\n    sql = Q\nB().go(None)\n",
    "nested_subclass_override": IMP + "class A:\n    sql = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    class Sub(A):\n        sql = Q\n    Sub().go(cur)\n",
    "class_body_augassign": IMP + "class A:\n    sql = 'DELETE FROM a'\n    sql += Q\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_if": IMP + "class A:\n    sql = 'DELETE FROM a'\n    if QS:\n        sql = Q\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_try": IMP + "class A:\n    try:\n        sql = Q\n    except Exception:\n        sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_only_in_if": IMP + "class A:\n    if 1:\n        sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_for_target": IMP + "class A:\n    sql = 'SELECT 1'\n    for sql in [Q]:\n        pass\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_with_target": IMP + "class A:\n    sql = 'SELECT 1'\n    with open('f') as sql:\n        pass\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_def_same_name": "class A:\n    sql = 'SELECT 1'\n    def sql(self):\n        return 'x'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_import_same_name": "class A:\n    sql = 'SELECT 1'\n    import os as sql\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_annotated": "class A:\n    sql: str = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_body_annotation_only_plus_assign": "class A:\n    sql: str\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "dict_item_override": IMP + "class A:\n    sql = 'DELETE FROM a'\n    def set(self):\n        self.__dict__['sql'] = Q\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "dict_update_in_init": IMP + "class Step:\n    sql = 'DELETE FROM a'\n    def __init__(self, **kw):\n        self.__dict__.update(kw)\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    Step(sql=Q).go(cur)\n",
    "dict_read_anywhere": "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\nA.__dict__\n",
    "instance_assignment": IMP + "class A:\n    sql = 'SELECT 1'\n    def __init__(self, s):\n        self.sql = s\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "instance_assignment_outside": IMP + "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(a):\n    a.sql = Q\n",
    "constructed_with_argument": IMP + "class A:\n    sql = 'SELECT 1'\n    def __init__(self, x):\n        pass\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    A(Q).go(cur)\n",
    "constructed_with_keyword": "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    A(x=1).go(cur)\n",
    "other_object_as_self": IMP + "import types\nclass Step:\n    sql = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    Step.go(types.SimpleNamespace(sql=Q), cur)\n",
    "unbound_call_with_any_object": "class Step:\n    sql = 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur, other):\n    Step.go(other, cur)\n",
    "decorated_class": "import functools\n@functools.total_ordering\nclass A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_with_base": "class Base:\n    pass\nclass A(Base):\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_with_imported_base": "from lib import Base\nclass A(Base):\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class_with_metaclass": "class A(metaclass=type):\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "enum_member": "import enum\nclass A(enum.Enum):\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql.value)\n",
    "class_defined_twice": "class A:\n    sql = 'SELECT 1'\nclass A:\n    sql = 'SELECT 2'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "self_outside_a_class": "def go(self, cur):\n    cur.execute(self.sql)\n",
    "global_in_class_body": "class A:\n    global sql\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
}


@pytest.mark.parametrize("name", sorted(F3_NOT_PROVABLE))
def test_a_class_attribute_that_something_could_override_is_not_provable(repo, name):
    partial(repo, OWN + F3_NOT_PROVABLE[name])


@pytest.mark.parametrize("src", [
    "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class A(object):\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class A:\n    sql = 'SELECT 1'\n    @classmethod\n    def go(cls, cur):\n        cur.execute(cls.sql)\n",
    "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(A.sql)\n",
    "class A:\n    SQL = OWN\n    def go(self, cur):\n        cur.execute(self.SQL)\n",
    "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\ndef r(cur):\n    A().go(cur)\n",
    "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\nclass B:\n    sql = 'SELECT 2'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
    "class A:\n    sql = 'SELECT 1'\n    other = 'x'\n    other += 'y'\n    def go(self, cur):\n        cur.execute(self.sql)\n",
])
def test_a_plain_class_attribute_assigned_once_stays_provable(repo, src):
    complete(repo, OWN + src)


# ───────────────────────── LOW ─────────────────────────

LOW_PARTIAL = {
    "sum_builtin": IMP + "def r(cur):\n    cur.execute(f'SELECT {sum([Q], [])}')\n",
    "sum_of_clean_strings": "def r(cur):\n    cur.execute(sum(['a'], ''))\n",
    "getattr_literal_dispatch": IMP + "class W:\n    def go(self, cur, q='DELETE FROM a'):\n        cur.execute(q)\n    def r(self, cur):\n        self.go(cur)\n        getattr(self, 'go')(cur, Q)\n",
    "getattr_literal_held_then_called": IMP + "def go(cur, q='DELETE FROM a'):\n    cur.execute(q)\ndef r(cur):\n    go(cur)\n    f = getattr(__import__('sys').modules[__name__], 'go')\n    f(cur, Q)\n",
    "getattr_runtime_name": "def r(o, name, cur):\n    getattr(o, name)(cur)\n",
    "getattr_runtime_name_two_args": "def r(o, name):\n    return getattr(o, name)\n",
    "getattr_runtime_name_then_called": "def r(o, name, cur):\n    fn = getattr(o, name, None)\n    fn(cur)\n",
    "getattr_literal_called_straight_away": "def r(o):\n    return getattr(o, 'close', None)()\n",
    "globals_lookup_call": IMP + "def f(cur, q='DELETE FROM a'):\n    cur.execute(q)\ndef r(cur):\n    f(cur)\n    globals()['f'](cur, Q)\n",
    "globals_get_call": IMP + "def f(cur, q='DELETE FROM a'):\n    cur.execute(q)\ndef r(cur):\n    f(cur)\n    globals().get('f')(cur, Q)\n",
    "locals_lookup_call": IMP + "def f(cur, q='DELETE FROM a'):\n    cur.execute(q)\ndef r(cur):\n    f(cur)\n    locals()['f'](cur, Q)\n",
    "vars_lookup_call": IMP + "def f(cur, q='DELETE FROM a'):\n    cur.execute(q)\ndef r(cur):\n    f(cur)\n    vars()['f'](cur, Q)\n",
    "globals_aliased": "T = 'a'\ng = globals\ndef r(cur):\n    g()['T'] = 'b'\n",
    "getattr_aliased": "g = getattr\ndef r(o):\n    return g(o, 'x')\n",
    "sys_modules_read": "import sys\ndef r():\n    return sys.modules.get('x')\n",
    "sys_modules_alias": IMP + "import sys\nT = 'DELETE FROM a'\ndef r(cur):\n    me = sys.modules[__name__]\n    me.T = Q\n    cur.execute(T)\n",
    "import_dunder": "def r():\n    return __import__('os')\n",
    "importlib_import": "import importlib\ndef r():\n    return importlib.import_module('x')\n",
    "import_module_call": "from importlib import import_module\ndef r(m):\n    return import_module(m)\n",
    "builtins_import": "import builtins\ndef r():\n    builtins.T = 1\n",
    "main_import": "import __main__\ndef r():\n    __main__.T = 1\n",
    "frame_globals": "import sys\ndef r():\n    sys._getframe().f_globals['T'] = 1\n",
    "inspect_frame": "import inspect\ndef r():\n    inspect.currentframe().f_globals['T'] = 1\n",
    "getattribute_dunder": "def r(cur, q):\n    cur.__getattribute__('execute')(q)\n",
    "methodcaller": "import operator\ndef r(cur, q):\n    operator.methodcaller('execute', q)(cur)\n",
    "attrgetter": "import operator\ndef r(cur):\n    operator.attrgetter('execute')(cur)('x')\n",
    "classmethod_through_class": IMP + "class W:\n    @classmethod\n    def go(cls, cur, q='DELETE FROM a'):\n        cur.execute(q)\nW.go(None)\nW.go(None, Q)\n",
    "imported_decorator_on_sql_function": "from c import deco\n@deco\ndef get_sql():\n    return 'DELETE FROM a'\ndef r(cur):\n    cur.execute(get_sql())\n",
    "imported_decorator_on_method": "from c import deco\nclass W:\n    @deco\n    def sql(self):\n        return 'DELETE FROM a'\n    def go(self, cur):\n        cur.execute(self.sql())\n",
    "decorated_function_with_sql_parameter": "from c import deco\n@deco\ndef h(cur, q):\n    cur.execute(q)\ndef r(cur):\n    h(cur, 'SELECT 1')\n",
    "verb_and_from_in_two_names": "V = 'DELETE'\nF = 'FROM'\ndef r(cur):\n    cur.execute(f'{V} {F} a')\n",
    "verb_from_join": "V = 'DELETE'\nF = 'FROM'\nT = 'a'\ndef r(cur):\n    cur.execute(' '.join([V, F, T]))\n",
    "verb_from_concat": "V = 'DELETE'\nF = 'FROM'\ndef r(cur):\n    cur.execute(V + ' ' + F + ' a')\n",
    "verb_name_and_words": "V = 'INSERT'\ndef r(cur):\n    cur.execute(f'{V} INTO a (x) VALUES (1)')\n",
    "verb_name_update": "V = 'UPDATE'\nT = 'a'\ndef r(cur):\n    cur.execute(f'{V} {T} SET x = 1')\n",
    "verb_from_param_with_sql_words": "def go(cur, v):\n    cur.execute(f'{v} FROM a')\ngo(None, 'DELETE')\n",
    "getattr_names_a_local_def_not_called": "def go(cur):\n    pass\ndef r(o):\n    return getattr(o, 'go', None)\n",
    "frame_globals_attribute": "def r(fr):\n    return fr.f_globals\n",
    "from_importlib": "from importlib import util\ndef r():\n    return util.find_spec\n",
    "from_builtins": "from builtins import exec as ex\n",
    "bare_verb_name_with_a_table": "V = 'CREATE'\ndef r(cur):\n    cur.execute(f'{V} a')\n",
    "bare_verb_select_name": "V = 'SELECT'\ndef r(cur):\n    cur.execute(f'{V} 1')\n",
    "param_verb_then_keyword_name": "F = 'FROM'\ndef go(cur, v):\n    cur.execute(f'{v} {F} a')\ngo(None, 'DELETE')\n",
    "verb_from_format": "def r(cur):\n    cur.execute('{} FROM a'.format('DELETE'))\n",
}


@pytest.mark.parametrize("name", sorted(LOW_PARTIAL))
def test_low_forms_read_partial(repo, name):
    partial(repo, OWN + LOW_PARTIAL[name])


@pytest.mark.parametrize("name,reason", [
    ("getattr_literal_dispatch", "dynamic_dispatch"), ("globals_lookup_call", "dynamic_dispatch"),
    ("sys_modules_read", "dynamic_dispatch"), ("import_dunder", "dynamic_dispatch"), ("importlib_import", "dynamic_dispatch"),
    ("globals_aliased", "dynamic_dispatch"), ("getattribute_dunder", "dynamic_"), ("methodcaller", "dynamic_attribute_call"),
    ("imported_decorator_on_sql_function", "sql_from_call_result"), ("verb_and_from_in_two_names", "unparseable_write_target"),
    ("decorated_function_with_sql_parameter", "unresolved_sql_parameter"), ("frame_globals", "dynamic_"),
])
def test_low_forms_have_named_reasons(repo, name, reason):
    partial(repo, OWN + LOW_PARTIAL[name], reason)


@pytest.mark.parametrize("src", [
    "def r(o):\n    return getattr(o, 'x', None), getattr(o, 'y', 0)\n",                       # a plain read with a default
    "def r(swe, names):\n    for n in names:\n        c = getattr(swe, n, None)\n        print(c)\n",   # a runtime name, never called
    "def r(o):\n    return getattr(o, 'retrograde', False)\n",
    "def r():\n    return globals().get('T'), locals().keys(), vars().items()\n",
    "def r():\n    return globals()['T']\n",
    "import sys\ndef r():\n    return sys.argv\n",
    "def r(rows):\n    return len(rows), int('3'), float('1'), abs(-1), round(1.5), ord('a'), any(rows), all(rows)\n",
])
def test_low_positive_controls_stay_complete(repo, src):
    complete(repo, OWN + src)


def test_prose_with_a_placeholder_named_like_a_sql_word_is_not_a_hidden_verb(repo):
    complete(repo, OWN + "def r(n, TABLE):\n    return f'{n} rows inserted into {TABLE}'\n")
    complete(repo, OWN + "def r(n, SET, FROM):\n    return f'{n} {SET} {FROM}'\n")


def test_a_name_holding_a_whole_statement_followed_by_sql_words_is_not_a_hidden_verb(repo):
    complete(repo, OWN + "P = 'SELECT 1'\ndef r(cur):\n    cur.execute(P + ' FROM t_b')\n")
    complete(repo, OWN + "P = 'SELECT 1 '\ndef r(cur):\n    cur.execute(f'{P} FROM t_b WHERE x IN (SELECT 1)')\n")


def test_a_classmethod_called_through_its_class_is_indexed_with_the_right_offset(repo):
    base = "class W:\n    @classmethod\n    def go(cls, cur, q):\n        cur.execute(q)\n"
    complete(repo, OWN + base + "W.go(None, 'SELECT 1')\nW.go(None, q='SELECT 2')\n")
    partial(repo, OWN + IMP + base + "W.go(None, Q)\n", "imported_sql_constant")
    # the same through the table-parameter helper machinery
    body = ("class W:\n    @classmethod\n    def wipe(cls, c, t):\n        print(f'DELETE FROM {t} WHERE x = 1')\n"
            "def r(c):\n    W.wipe(c, 't_z')\n")
    assert scan(repo, body)["tables"] == ["public.t_z"]
    body = ("class W:\n    def wipe(self, c, t):\n        print(f'DELETE FROM {t} WHERE x = 1')\n"
            "def r(c, w):\n    W.wipe(w, c, 't_z')\n")
    assert scan(repo, body)["tables"] == ["public.t_z"]


def test_an_undecorated_or_builtin_decorated_local_function_stays_provable(repo):
    complete(repo, OWN + "class W:\n    @property\n    def sql(self):\n        return 'SELECT 1'\n    @staticmethod\n    def s():\n        return 'SELECT 2'\n"
                         "    def go(self, cur):\n        cur.execute(self.s())\n        cur.execute(W.s())\n")


# ───────────────────────── test gaps from the review (each kills a named survivor) ─────────────────────────

def test_dict_literal_keys_are_judged(repo):                          # dict_keys_off
    partial(repo, OWN + IMP + "D = {Q: 'x'}\ndef r(cur):\n    for k in D:\n        cur.execute(k)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(cur):\n    for k in {Q: 'x'}:\n        cur.execute(k)\n", "imported_sql_constant")


def test_dict_comprehension_value_and_key_are_judged(repo):          # dictcomp_value_off
    partial(repo, OWN + IMP + "D = {k: Q for k in 'ab'}\ndef r(cur):\n    cur.execute(D['a'])\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(cur):\n    cur.execute({Q: 1 for _ in 'ab'}.popitem()[0])\n")


def test_keyword_arguments_of_text_wrappers_are_judged(repo):        # textwrap_kw_off
    partial(repo, OWN + IMP + "def r(cur):\n    cur.execute(str(object=Q))\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "import textwrap\ndef r(cur):\n    cur.execute(textwrap.dedent(text=Q))\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(cur):\n    cur.execute('{}'.format(Q))\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "def r(cur):\n    cur.execute('{a}'.format(a=Q))\n", "imported_sql_constant")


def test_setdefault_and_other_value_mutators_are_tracked(repo):      # mut_setdefault_off
    partial(repo, OWN + IMP + "D = {}\nD.setdefault('a', Q)\ndef r(cur):\n    cur.execute(D['a'])\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "S = set()\nS.add(Q)\ndef r(cur):\n    for q in S:\n        cur.execute(q)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "from collections import deque\nL = deque()\nL.appendleft(Q)\ndef r(cur):\n    for q in L:\n        cur.execute(q)\n")
    partial(repo, OWN + IMP + "L = []\nL.insert(0, Q)\ndef r(cur):\n    cur.execute(L[0])\n", "imported_sql_constant")
    complete(repo, OWN + "D = {}\nD.setdefault('a', 'SELECT 1')\ndef r(cur):\n    cur.execute(D['a'])\n")


def test_an_annotated_class_attribute_is_never_provable(repo):       # classattr_ann_off
    partial(repo, OWN + "class A:\n    sql: str = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n", "unresolved_sql_attribute")
    complete(repo, OWN + "class A:\n    sql = 'SELECT 1'\n    def go(self, cur):\n        cur.execute(self.sql)\n")


def test_a_walrus_binding_is_judged(repo):                           # walrus_binding_off
    partial(repo, OWN + IMP + "def r(cur):\n    if (q := Q):\n        pass\n    cur.execute(q)\n", "imported_sql_constant")
    complete(repo, OWN + "def r(cur):\n    if (q := 'SELECT 1'):\n        pass\n    cur.execute(q)\n")


def test_iterating_a_copy_of_a_container_is_judged(repo):            # iter_copy_off
    partial(repo, OWN + IMP + "L = [Q]\ndef r(cur):\n    for q in L.copy():\n        cur.execute(q)\n", "imported_sql_constant")
    partial(repo, OWN + IMP + "D = {'a': Q}\ndef r(cur):\n    for q in D.copy().values():\n        cur.execute(q)\n", "imported_sql_constant")


# ───────────────────────── docs / real tree ─────────────────────────

def test_the_limitations_list_and_readme_state_what_is_actually_detected():
    text = "\n".join(slw.WRITE_SCAN_LIMITATIONS)
    for needle in ("container_escapes", "dynamic_dispatch", "union", "decorat", "plain class", "quote"):
        assert needle in text, needle
    readme = (HERE.parent / "README_level_wave.md").read_text()
    assert "a statement starting with a name is not scanned" not in text and "a statement starting with a name is not scanned" not in readme
    for needle in ("container_escapes", "dynamic_dispatch", "Dataclass", "UNIONED", "quote-aware"):
        assert needle in readme, needle


def test_real_tree_round3_scans_without_exception_and_keeps_the_known_clean_writers():
    helpers = slw.helper_write_effects(REAL_REPO)
    scanned, flipped = {}, {}
    for f in sorted((REAL_REPO / WRITERS).glob("*.py")):
        res = slw.scan_writer_tables(f.stem, REAL_REPO, helpers)
        assert ("tables" in res) != ("not_scanned" in res), (f.name, res)
        (scanned if "tables" in res else flipped)[f.stem] = res
    for asset in ("bo_karanajala", "bo_sangati", "bo_upaya", "mi_darshana", "ka_avadhi", "ga_dashas", "ga_condition", "ga_tajaka",
                  "bo_laksana", "bg_sky_calendar"):
        assert asset in scanned, (asset, flipped.get(asset))
    for asset in ("bg_gochara_arcs", "ka_gochara", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate"):
        assert asset in flipped, asset
