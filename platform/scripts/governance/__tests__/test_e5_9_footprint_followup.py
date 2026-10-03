"""test_e5_9_footprint_followup.py -- E5.9 footprint scan, the three residual LOWs of the FP2 re-review (E6.1 follow-up, item 6).

All three are false-COMPLETE reads (a writer's tables read as fully known while a statement was hidden from the scan); the fixes only move readings from "complete" to "not scanned":

  (a) A STARRED unpack target (`first, *rest = SRC`) bound a LIST but read as an immutable value (its elements are), so an alias of it could be mutated unpoliced
      (`alias = rest; alias.append(x)`; `mutate(rest)`; `return rest`). It now has its own binding tag: cleaned like an iteration, never immutable, its uses policed.
  (b) The nested-container refusal looked ONE level down: `[('a', ['b'])]` read as flat (a TUPLE element is not a container value) so `inner = Q[0][1]; inner.append(x)` mutated
      the inner list with nothing tying it to `Q`. The refusal now recurses through tuples, starred elements, `if`/`or` branches, `+` / `*`, and the container constructors.
  (c) CONSTANT-ONLY text that no reading can reconstruct: `'%c%c' % (68, 69)`, `'%(v)s FROM hidden' % {'v': 'DELETE'}`, `'%-6s ...' % 'DELETE'`, `'ETELED'[::-1]`, `' '.join(w for w in (...))`,
      `'x' * 3`. The statement they run is in no literal of the file. A closed list: a template / slice / str-method call over literals only, which neither the placeholder renderer nor
      `_walk`'s evaluator reads, is NOT SCANNED; every form the renderer / evaluator reads (plain `%s`, `.replace`, `.strip`, a list-literal join, f-strings) and every non-constant-only
      expression (a name is judged by its own bindings) is exactly as before.

Real-tree check (recorded in the commit): every writer of the orchestrator and all 1,636 python files under platform/ read identically before and after (no verdict moved there).
Offline: ast only. Mutation tests: each fix is undone in place and the same source must read COMPLETE again, so the partial assertions can fail."""
from __future__ import annotations

import ast
import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import suvarna_level_wave as slw  # noqa: E402

WRITERS = slw.WRITERS_REL
OWN = 'OWN = "INSERT INTO t_a (x) VALUES (1)"\n'


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
    write(repo, f"{WRITERS}/{asset}.py", OWN + body)
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


# ───────────────────────── (a) starred unpack targets ─────────────────────────

STAR_PARTIAL = {
    "alias_then_mutate": "first, *rest = ['SELECT 1', 'SELECT 2']\nalias = rest\nalias.append(HIDDEN)\ndef r(cur):\n    cur.execute(rest[1])\n",
    "passed_to_a_mutator": "first, *rest = ['SELECT 1', 'SELECT 2']\ndef mut(x, v):\n    x.append(v)\nmut(rest, hidden_sql())\ndef r(cur):\n    cur.execute(rest[1])\n",
    "returned_to_a_caller": "first, *rest = ['SELECT 1', 'SELECT 2']\ndef g():\n    return rest\ndef r(cur):\n    g().append(hidden_sql())\n    cur.execute(rest[0])\n",
    "stored_in_a_container": "first, *rest = ('SELECT 1', 'SELECT 2')\nHOLD = [rest]\nHOLD[0].append(hidden_sql())\ndef r(cur):\n    cur.execute(rest[1])\n",
    "star_in_a_for_target": "for first, *rest in [('a', 'SELECT 1', 'SELECT 2')]:\n    alias = rest\n    alias.append(HIDDEN)\ndef r(cur):\n    cur.execute(rest[1])\n",
    "star_in_a_nested_target": "(first, *rest), tail = ('a', 'SELECT 1'), 'SELECT 2'\nalias = rest\nalias.append(HIDDEN)\ndef r(cur):\n    cur.execute(rest[0])\n",
    "mutated_through_its_own_name": "first, *rest = ['SELECT 1', 'SELECT 2']\nrest.append(hidden_sql())\ndef r(cur):\n    cur.execute(rest[1])\n",
}

STAR_COMPLETE = {
    "iterated": "first, *rest = ['SELECT 1', 'SELECT 2']\ndef r(cur):\n    for q in rest:\n        cur.execute(q)\n",
    "indexed": "first, *rest = ('SELECT 1', 'SELECT 2')\ndef r(cur):\n    cur.execute(rest[0])\n    cur.execute(first)\n",
    "in_a_for_target": "for first, *rest in [('a', 'SELECT 1', 'SELECT 2')]:\n    pass\ndef r(cur):\n    for q in rest:\n        cur.execute(q)\n",
    "plain_tuple_unpack_is_untouched": "a, b = 'SELECT 1', 'SELECT 2'\nalias = [a, b]\ndef r(cur):\n    cur.execute(a)\n",
}


@pytest.mark.parametrize("name", sorted(STAR_PARTIAL))
def test_a_starred_unpack_target_is_a_mutable_list_whose_uses_are_policed(repo, name):
    partial(repo, STAR_PARTIAL[name])


@pytest.mark.parametrize("name", sorted(STAR_COMPLETE))
def test_starred_unpack_controls_that_only_read_the_list_stay_complete(repo, name):
    complete(repo, STAR_COMPLETE[name])


def test_the_star_reason_names_the_escape(repo):
    assert "rest is aliased" in partial(repo, STAR_PARTIAL["alias_then_mutate"], "container_escapes")
    assert "rest is returned" in partial(repo, STAR_PARTIAL["returned_to_a_caller"], "container_escapes")


def test_MUTATION_a_starred_target_bound_like_an_iteration_reads_the_alias_case_as_complete(repo, monkeypatch):
    for name in ("alias_then_mutate", "passed_to_a_mutator", "returned_to_a_caller"):
        partial(repo, STAR_PARTIAL[name])
    orig = slw._WriteScan._bind_iter_target

    def old(self, target, iter_node, tag="iter"):                # the previous behaviour: a Starred target keeps the enclosing tag ("iter": immutable when the elements are)
        if isinstance(target, ast.Starred):
            return orig(self, target.value, iter_node, tag)
        return orig(self, target, iter_node, tag)
    monkeypatch.setattr(slw._WriteScan, "_bind_iter_target", old)
    for name in ("alias_then_mutate", "passed_to_a_mutator", "returned_to_a_caller"):
        complete(repo, STAR_PARTIAL[name])


# ───────────────────────── (b) nested containers, any depth ─────────────────────────

NEST_PARTIAL = {
    "tuple_in_list": "Q = [('SELECT 1', ['SELECT 2'])]\ninner = Q[0][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1][1])\n",
    "tuple_in_tuple": "Q = (('SELECT 1', ['SELECT 2']),)\ninner = Q[0][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1][1])\n",
    "tuple_in_dict": "Q = {'k': ('SELECT 1', ['SELECT 2'])}\ninner = Q['k'][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q['k'][1][1])\n",
    "tuple_in_comprehension": "Q = [(['SELECT 1'],) for _ in range(2)]\ninner = Q[0][0]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][0][1])\n",
    "two_tuples_deep": "Q = [(('a', ['SELECT 2']),)]\ninner = Q[0][0][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][0][1][1])\n",
    "starred_element_that_holds_a_list": "Q = [*[['SELECT 1']]]\ninner = Q[0]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1])\n",
    "if_branch_tuple": "Q = [('a', ['SELECT 1']) if X else ('b', ['SELECT 3'])]\ninner = Q[0][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1][1])\n",
    "dict_constructor_keyword": "Q = dict(k=['SELECT 1'])\ninner = Q['k']\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q['k'][1])\n",
    "dict_constructor_tuple_value": "Q = dict(k=('SELECT 1', ['x']))\ninner = Q['k'][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q['k'][1][0])\n",
    "dict_constructor_pairs": "Q = dict([('k', ['SELECT 1'])])\ninner = Q['k']\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q['k'][1])\n",
    "list_constructor_nested": "Q = list([('a', ['SELECT 1'])])\ninner = Q[0][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1][1])\n",
    "repeated_nested_list": "Q = [['SELECT 1']] * 2\ninner = Q[0]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[1][1])\n",
    "concatenated_nested": "Q = [['SELECT 1']] + [['SELECT 2']]\ninner = Q[0]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1])\n",
    "item_store_of_a_tuple_holding_a_list": "Q = {}\nQ['k'] = ('a', ['SELECT 1'])\ninner = Q['k'][1]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q['k'][1][1])\n",
    "one_level_still": "Q = [['SELECT 1']]\ninner = Q[0]\ninner.append(hidden_sql())\ndef r(cur):\n    cur.execute(Q[0][1])\n",
}

NEST_COMPLETE = {
    "flat_list": "Q = ['SELECT 1', 'SELECT 2']\ndef r(cur):\n    cur.execute(Q[0])\n",
    "tuple_of_immutables": "Q = [('SELECT 1', ('x', 'y'))]\ndef r(cur):\n    cur.execute(Q[0][0])\n",
    "tuples_in_a_loop": "Q = [('SELECT 1', 'a'), ('SELECT 2', 'b')]\ndef r(cur):\n    for q, n in Q:\n        cur.execute(q)\n",
    "dict_of_strings": "Q = {'k': 'SELECT 1', 'j': ('SELECT 2', 'z')}\ndef r(cur):\n    cur.execute(Q['k'])\n",
    "list_constructor_flat": "Q = list(['SELECT 1', 'SELECT 2'])\ndef r(cur):\n    cur.execute(Q[0])\n",
    "dict_constructor_flat": "Q = dict(k='SELECT 1')\ndef r(cur):\n    cur.execute(Q['k'])\n",
    "dict_of_tuple_keys": "Q = {('a', 'b'): 'SELECT 1'}\ndef r(cur):\n    cur.execute(Q[('a', 'b')])\n",
    "repeat_of_a_flat_list": "Q = ['SELECT 1'] * 2\ndef r(cur):\n    cur.execute(Q[1])\n",
}


@pytest.mark.parametrize("name", sorted(NEST_PARTIAL))
def test_a_container_that_carries_another_mutable_container_at_any_depth_is_not_provable(repo, name):
    assert "holds another mutable container" in partial(repo, NEST_PARTIAL[name], "container_escapes")


@pytest.mark.parametrize("name", sorted(NEST_COMPLETE))
def test_flat_and_immutable_nested_containers_stay_complete(repo, name):
    complete(repo, NEST_COMPLETE[name])


def test_the_nesting_depth_is_bounded_and_fails_closed():
    deep = "(" * 40 + "['x']" + ",)" * 40
    assert slw._holds_mutable(ast.parse(deep, mode="eval").body) is True          # past the depth cap: the answer is yes, never an unbounded walk
    assert slw._has_nested_container(ast.parse("[" + deep + "]", mode="eval").body) is True
    assert slw._has_nested_container(ast.parse("[('a', ('b', ('c',)))]", mode="eval").body) is False


def test_the_helper_agrees_with_the_one_level_definition_where_that_was_right_and_goes_deeper():
    chk = lambda src: slw._has_nested_container(ast.parse(src, mode="eval").body)      # noqa: E731
    assert chk("[['a']]") and chk("{'k': ['a']}") and chk("[{'a'}]") and chk("[[1] for _ in y]") and chk("{k: [v] for k, v in y}")          # one level: as before
    assert not chk("['a', 'b']") and not chk("{'k': 'v'}") and not chk("('a', 'b')") and not chk("[1, 2, 3]") and not chk("[x for x in y]")
    assert chk("[(['a'],)]") and chk("{'k': ('a', ['b'])}") and chk("[[['a']]]") and chk("[('a',) + (['b'],)]")                              # the new depth


def test_MUTATION_the_one_level_definition_reads_every_nested_case_as_complete(repo, monkeypatch):
    for name in ("tuple_in_list", "tuple_in_dict", "dict_constructor_keyword", "repeated_nested_list"):
        partial(repo, NEST_PARTIAL[name])

    def one_level(node, depth=0):                                  # the previous definition, verbatim in behaviour
        if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            return any(slw._is_container_value(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return any(v is not None and slw._is_container_value(v) for v in node.values)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return slw._is_container_value(node.elt)
        if isinstance(node, ast.DictComp):
            return slw._is_container_value(node.value)
        return False
    monkeypatch.setattr(slw, "_has_nested_container", one_level)
    monkeypatch.setattr(slw, "_holds_mutable", lambda node, depth=0: slw._is_container_value(node))
    for name in ("tuple_in_list", "tuple_in_dict", "dict_constructor_keyword", "repeated_nested_list"):
        complete(repo, NEST_PARTIAL[name])
    partial(repo, NEST_PARTIAL["one_level_still"])                  # the case the old definition did catch is still caught


# ───────────────────────── (c) constant-only text no reading can reconstruct ─────────────────────────

CONST_PARTIAL = {
    "percent_c_char_codes": "def r(cur):\n    cur.execute('%c%c%c%c%c%c FROM hidden' % (68, 69, 76, 69, 84, 69))\n",
    "percent_c_in_a_name": "Q = '%c%c%c%c%c%c FROM hidden' % (68, 69, 76, 69, 84, 69)\ndef r(cur):\n    cur.execute(Q)\n",
    "percent_named_dict": "def r(cur):\n    cur.execute('%(v)s FROM hidden' % {'v': 'DELETE'})\n",
    "percent_named_dict_in_a_name": "Q = '%(v)s FROM hidden' % {'v': 'DELETE'}\ndef r(cur):\n    cur.execute(Q)\n",
    "percent_width_flag": "def r(cur):\n    cur.execute('%-6s FROM hidden' % 'DELETE')\n",
    "percent_precision": "def r(cur):\n    cur.execute('%.6s FROM hidden' % 'DELETE_ALL')\n",
    "reversed_slice": "def r(cur):\n    cur.execute('ETELED'[::-1] + ' FROM hidden')\n",
    "plain_slice": "def r(cur):\n    cur.execute('xxDELETE FROM hidden'[2:])\n",
    "join_of_a_generator": "def r(cur):\n    cur.execute(' '.join(w for w in ('DELETE', 'FROM', 'hidden')))\n",
    "join_of_a_generator_in_a_name": "Q = ' '.join(w for w in ('DELETE', 'FROM', 'hidden'))\ndef r(cur):\n    cur.execute(Q)\n",
    "join_of_a_list_comprehension": "def r(cur):\n    cur.execute(' '.join([w for w in ('DELETE', 'FROM', 'hidden')]))\n",
    "join_of_chr_codes": "def r(cur):\n    cur.execute(''.join(chr(c) for c in (68, 69, 76, 69, 84, 69)) + ' FROM hidden')\n",
    "join_of_a_slice_of_a_literal": "def r(cur):\n    cur.execute(' '.join(('DELETE', 'FROM', 'hidden', 'x')[:3]))\n",
    "string_repeat": "def r(cur):\n    cur.execute('DELETE FROM hidden' * 1)\n",
    "format_spec": "def r(cur):\n    cur.execute('{:s} FROM hidden'.format('DELETE'))\n",
    "format_index": "def r(cur):\n    cur.execute('{0[0]} FROM hidden'.format(['DELETE']))\n",
    "translate": "def r(cur):\n    cur.execute('DELETE FROM hidden'.translate({}))\n",
    "nested_in_a_larger_expression": "def r(cur):\n    cur.execute('SELECT 1; ' + ('%c%c%c%c%c%c FROM hidden' % (68, 69, 76, 69, 84, 69)))\n",
    "nested_in_an_fstring": "def r(cur):\n    cur.execute(f\"{'%(v)s FROM hidden' % {'v': 'DELETE'}}\")\n",
}

CONST_COMPLETE = {
    "plain_percent_str": "def r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y = %s' % 'z')\n",
    "plain_percent_int": "def r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y = %s' % 1)\n",
    "percent_tuple": "def r(cur):\n    cur.execute('SELECT %s, %s FROM t_b' % ('a', 'b'))\n",
    "plain_format": "def r(cur):\n    cur.execute('SELECT {} FROM t_b'.format('a'))\n",
    "named_format": "def r(cur):\n    cur.execute('SELECT {c} FROM t_b'.format(c='a'))\n",
    "list_literal_join": "def r(cur):\n    cur.execute(' '.join(['SELECT', 'x', 'FROM', 't_b']))\n",
    "replace_of_a_literal_is_evaluated_and_scanned": "def r(cur):\n    cur.execute('DELETE FROM xx'.replace('xx', 't_c'))\n",
    "strip_of_a_literal": "def r(cur):\n    cur.execute('  SELECT 1  '.strip())\n",
    "lower_of_a_literal": "def r(cur):\n    cur.execute('SELECT X FROM T_B'.lower())\n",
    "a_numeric_constant_product_in_an_fstring": "LIMIT = 10 * 5\ndef r(cur):\n    cur.execute(f'SELECT x FROM t_b LIMIT {LIMIT}')\n",
    "a_name_join_is_judged_by_its_bindings": "COLS = ['a', 'b']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(COLS) + ' FROM t_b')\n",
    "a_name_slice_is_judged_by_its_bindings": "COLS = ['a', 'b', 'c']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(COLS[:2]) + ' FROM t_b')\n",
    "a_slice_of_numbers_is_no_sql_text": "N = (1, 2, 3)[1:]\ndef r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y = %s', N)\n",
    "an_fstring": "T = 't_b'\ndef r(cur):\n    cur.execute(f'SELECT x FROM {T}')\n",
}


@pytest.mark.parametrize("name", sorted(CONST_PARTIAL))
def test_a_constant_only_text_no_reading_can_reconstruct_is_not_scanned(repo, name):
    reason = partial(repo, CONST_PARTIAL[name])
    assert reason.startswith(("write_form_not_analysed: a constant-only template", "unparseable_write_target", "sql_from_call_result")), reason


# a statement that LEADS with the unreadable part is also caught earlier by the placeholder-start rule (`unparseable_write_target`); both are not-scanned readings
LED_BY_THE_FORM = {"format_index", "format_spec", "join_of_chr_codes", "reversed_slice"}


@pytest.mark.parametrize("name", sorted(set(CONST_PARTIAL) - LED_BY_THE_FORM))
def test_the_constant_only_reason_is_the_named_one_where_nothing_else_caught_it(repo, name):
    assert partial(repo, CONST_PARTIAL[name]).startswith("write_form_not_analysed: a constant-only template whose text this scan cannot read"), name


@pytest.mark.parametrize("name", sorted(CONST_COMPLETE))
def test_the_forms_the_renderer_and_the_evaluator_read_stay_exactly_as_before(repo, name):
    res = scan(repo, CONST_COMPLETE[name])
    assert "tables" in res and "public.t_a" in res["tables"], (name, res)


def test_constant_only_is_a_closed_list_of_literals_only():
    sc = slw._WriteScan(ast.parse("x = 1\n"))
    co = lambda src: sc._const_only(ast.parse(src, mode="eval").body)      # noqa: E731
    assert co("'%c' % (68,)") and co("' '.join(w for w in ('a', 'b'))") and co("'ab'[::-1]") and co("{'v': 'D'}") and co("[chr(c) for c in (1, 2)]")
    assert not co("NAME") and not co("obj.attr") and not co("f(1)") and not co("' '.join(COLS)") and not co("'%s' % name") and not co("open('x').read()")
    assert not co("[x for x in COLS]") and not co("{**d}") and not co("(lambda: 1)()")


def test_MUTATION_without_the_constant_only_classification_every_case_reads_complete(repo, monkeypatch):
    names = ("percent_c_char_codes", "percent_named_dict", "percent_width_flag", "reversed_slice", "join_of_a_generator", "join_of_a_list_comprehension", "string_repeat")
    for n in names:
        partial(repo, CONST_PARTIAL[n])
    monkeypatch.setattr(slw._WriteScan, "_unreadable_constant_form", lambda self, node: None)
    for n in names:
        res = scan(repo, CONST_PARTIAL[n])
        assert "tables" in res or "unparseable_write_target" in res["not_scanned"], (n, res)      # the previous reading: complete (the verb is in no literal), or caught only by luck
    assert sum("tables" in scan(repo, CONST_PARTIAL[n]) for n in names) >= 5                       # most of them read COMPLETE: the classification is what refuses them


def test_the_unreadable_form_check_is_charged_to_the_work_cap(repo, monkeypatch):
    """`_const_only` counts a step per node it visits, so a hostile deeply-nested constant expression cannot make the new check an unbounded cost: it is part of the resolver's
    work counter and stops at the same cap."""
    sc = slw._WriteScan(ast.parse("x = 1\n"))
    before = sc.work_steps
    assert sc._const_only(ast.parse("'%c' % (68, 69)", mode="eval").body) is True
    assert sc.work_steps > before
    monkeypatch.setattr(slw._WriteScan, "MAX_RESOLVER_STEPS", 12)
    big = "def r(cur):\n    cur.execute(" + "'%s' % (" * 25 + "'x'" + ",)" * 25 + ")\n"
    assert scan(repo, big)["not_scanned"].startswith("resolver_work_cap")                         # a long nest of constant templates reaches the cap and is NOT scanned
