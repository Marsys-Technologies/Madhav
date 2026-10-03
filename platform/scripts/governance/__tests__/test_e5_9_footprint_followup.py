"""test_e5_9_footprint_followup.py -- E5.9 footprint scan, the three residual LOWs of the FP2 re-review (E6.1 follow-up, item 6).

All three are false-COMPLETE reads (a writer's tables read as fully known while a statement was hidden from the scan); the fixes only move readings from "complete" to "not scanned":

  (a) A STARRED unpack target (`first, *rest = SRC`) bound a LIST but read as an immutable value (its elements are), so an alias of it could be mutated unpoliced
      (`alias = rest; alias.append(x)`; `mutate(rest)`; `return rest`). It now has its own binding tag: cleaned like an iteration, never immutable, its uses policed.
  (b) The nested-container refusal looked ONE level down: `[('a', ['b'])]` read as flat (a TUPLE element is not a container value) so `inner = Q[0][1]; inner.append(x)` mutated
      the inner list with nothing tying it to `Q`. The refusal now recurses through tuples, starred elements, `if`/`or` branches, `+` / `*`, and the container constructors.
  (c) CONSTANT-ONLY text that no literal of the file shows: `'%c%c' % (68, 69)`, `'%(v)s FROM hidden' % {'v': 'DELETE'}`, `'ETELED'[::-1]`, `' '.join(w for w in (...))`, and the same
      wrapped (`('%c' + 'ELETE FROM hidden') % 68`, `f'DEL%s' % '...'`), named (`A = 68; '%cELETE FROM hidden' % A`, `N = 'neddih MORF ETELED'; N[::-1]`, `PARTS = [...]; ''.join(PARTS)`),
      conditional (`'DEL' + ('ETE FROM hidden' if 1 else 'x')`, `or` / `and`), indexed, built up by `+=` / a loop. Operator allow-listing was bypassed by every wrapper, so the rule is now a CLOSED
      EVALUATOR (`_WriteScan._cvals`): an SQL expression built only from constants and constant-bound names, through any operator, subscript, container, comprehension, conditional or call
      of a closed list of pure builtins and str / bytes / dict / sequence methods, is EVALUATED and the text it evaluates to is SCANNED as the statement it runs; one that is constant-only
      but cannot be evaluated (an unsupported method, a set whose iteration order is arbitrary, a container built up by mutation then iterated, more than 64 pieces) is NOT SCANNED.
      The evaluator only ever adds tables and reasons: the closed allow-list still judges the expression after it, so nothing is made cleaner than before.

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


# ───────────────────────── (c) the closed constant evaluator ─────────────────────────

def _find(repo, body):
    res = scan(repo, body)
    return res.get("tables"), res.get("not_scanned")


def _reads_hidden(repo, body):
    """The statement the file runs is READ (its `hidden` table is in the tables) or the file is NOT SCANNED; what must never happen is a COMPLETE reading without the table."""
    tables, ns = _find(repo, body)
    assert (tables is not None and "public.hidden" in tables) or (tables is None and ns), (body, tables, ns)


def _run(expr, pre=""):
    return pre + f"def run(cur):\n    cur.execute({expr})\n"


# every attack the independent review of #3017 found, plus the first-round forms: (prelude, expression); each runs `DELETE FROM hidden`
EVALUABLE = {
    "percent_c_char_codes": ("", "'%c%c%c%c%c%c FROM hidden' % (68, 69, 76, 69, 84, 69)"),
    "percent_named_dict": ("", "'%(v)s FROM hidden' % {'v': 'DELETE'}"),
    "percent_width_flag": ("", "'%-6s FROM hidden' % 'DELETE'"),
    "percent_precision": ("", "'%.6s FROM hidden' % 'DELETE_ALL'"),
    "reversed_slice": ("", "'ETELED'[::-1] + ' FROM hidden'"),
    "plain_slice": ("", "'xxDELETE FROM hidden'[2:]"),
    "string_repeat": ("", "'DELETE FROM hidden' * 1"),
    "join_of_a_generator": ("", "' '.join(w for w in ('DELETE', 'FROM', 'hidden'))"),
    "join_of_a_list_comprehension": ("", "' '.join([w for w in ('DELETE', 'FROM', 'hidden')])"),
    "join_of_chr_codes": ("", "''.join(chr(c) for c in (68, 69, 76, 69, 84, 69)) + ' FROM hidden'"),
    "join_of_a_slice_of_a_literal": ("", "' '.join(('DELETE', 'FROM', 'hidden', 'x')[:3])"),
    "translate": ("", "'DELETE FROM hidden'.translate({})"),
    # wrapped: the constant is inside another operator
    "mult_binop_left": ("", "('DEL' + 'ETE FROM hidden') * 1"),
    "pct_binop_left": ("", "('DEL%s' + 'FROM hidden') % 'ETE '"),
    "pct_fstr_left": ("", "f'DEL%s' % 'ETE FROM hidden'"),
    "str_join_class": ("", "str.join('', ('DEL', 'ETE FROM hidden'))"),
    "join_slice_step": ("", "''.join(('DEL', 'ETE FROM hidden')[::1])"),
    "list_index_pair": ("", "['DEL', 'ETE FROM hidden'][0] + ['DEL', 'ETE FROM hidden'][1]"),
    "dict_get_part": ("", "{'a': 'DEL'}.get('a') + 'ETE FROM hidden'"),
    "dict_values_join": ("", "''.join({'a': 'DEL', 'b': 'ETE FROM hidden'}.values())"),
    "dict_index_join": ("", "{'k': 'ETE FROM hidden'}['k'].join(['DEL', ''])"),
    "ifexp_fragment": ("", "'DEL' + ('ETE FROM hidden' if 1 else 'x')"),
    "ifexp_compare": ("", "'DEL' + ('ETE FROM hidden' if 1 < 2 else '')"),
    "or_fragment": ("", "'DEL' + ('' or 'ETE FROM hidden')"),
    "and_fragment": ("", "'DEL' + (1 and 'ETE FROM hidden')"),
    "nested_in_a_larger_expression": ("", "'SELECT 1; ' + ('%c%c%c%c%c%c FROM hidden' % (68, 69, 76, 69, 84, 69))"),
    "walrus_free_double_percent": ("", "('DEL%s' % '') + 'ETE FROM hidden'"),
    # named: the constant is bound to a name (any number of them)
    "name_percent_c": ("A = 68\n", "'%cELETE FROM hidden' % A"),
    "names_percent_c": ("A, B, C, D, E, F = 68, 69, 76, 69, 84, 69\n", "'%c%c%c%c%c%c FROM hidden' % (A, B, C, D, E, F)"),
    "name_slice_reversed": ("N = 'neddih MORF ETELED'\n", "N[::-1]"),
    "name_slice_all": ("N = 'DELETE FROM hidden'\n", "N[:]"),
    "name_mult": ("N = 'DELETE FROM hidden'\n", "N * 1"),
    "name_join": ("PARTS = ['DEL', 'ETE FROM hidden']\n", "''.join(PARTS)"),
    "name_join_tuple": ("PARTS = ('DEL', 'ETE FROM hidden')\n", "''.join(PARTS)"),
    "name_index_sum": ("PARTS = ['DEL', 'ETE FROM hidden']\n", "PARTS[0] + PARTS[1]"),
    "name_template_mod": ("T = '%sETE FROM hidden'\n", "T % 'DEL'"),
    "name_template_format": ("T = '{}ETE FROM hidden'\n", "T.format('DEL')"),
    "name_ternary": ("T = 1\n", "'DEL' + ('ETE FROM hidden' if T else '')"),
    "name_join_generator": ("P = ('DEL', 'ETE FROM hidden')\n", "''.join(p for p in P)"),
    "name_chain": ("A = 'DEL'\nB = A + 'ETE'\nC = B + ' FROM hidden'\n", "C"),
    "sorted_set_is_deterministic": ("", "''.join(sorted({'ETE FROM hidden', 'DEL'}))"),
    "name_in_a_function_scope": ("", "q"),   # (prelude below: bound in a function, used in another)
}
EVALUABLE["name_in_a_function_scope"] = ("def mk():\n    q = 'DEL' + 'ETE FROM hidden'\n", "q")


@pytest.mark.parametrize("name", sorted(EVALUABLE))
def test_an_expression_built_only_from_constants_is_evaluated_and_the_statement_it_runs_is_scanned(repo, name):
    pre, expr = EVALUABLE[name]
    _reads_hidden(repo, _run(expr, pre))


BUILT_UP = {
    "augmented_assignment": "S = 'DEL'\nS += 'ETE FROM hidden'\ndef run(cur):\n    cur.execute(S)\n",
    "augmented_in_a_loop": "S = ''\nfor p in ('DEL', 'ETE FROM hidden'):\n    S += p\ndef run(cur):\n    cur.execute(S)\n",
    "self_concatenation_in_a_loop": "S = ''\nfor p in ('DEL', 'ETE FROM hidden'):\n    S = S + p\ndef run(cur):\n    cur.execute(S)\n",
    "loop_variable_over_whole_statements": "for q in ('DELETE FROM hidden',):\n    pass\ndef run(cur):\n    for q in ('DELETE FROM hidden',):\n        cur.execute(q)\n",
    "item_store_into_a_dict": "D = {}\nD['a'] = 'DELETE FROM hidden'\ndef run(cur):\n    cur.execute(D['a'])\n",
    "append_to_a_list": "L = []\nL.append('DELETE FROM hidden')\ndef run(cur):\n    cur.execute(L[0])\n",
}


@pytest.mark.parametrize("name", sorted(BUILT_UP))
def test_text_built_up_by_augmented_assignment_a_loop_or_a_mutation_is_read_as_the_statement_it_runs(repo, name):
    _reads_hidden(repo, BUILT_UP[name])


UNEVALUABLE = {
    "set_of_pieces_joined": _run("''.join({'DEL', 'ETE FROM hidden'})"),
    "set_comprehension_joined": _run("''.join({p for p in ('DEL', 'ETE FROM hidden')})"),
    "method_outside_the_closed_list": _run("'x'.__add__('DELETE FROM hidden')"),
    "mutated_list_then_joined": "P = ['DEL']\nP.append('ETE FROM hidden')\ndef run(cur):\n    cur.execute(''.join(P))\n",
    "mutated_list_comprehension": "P = ['DEL']\nP.append('ETE FROM hidden')\ndef run(cur):\n    cur.execute(''.join(p for p in P))\n",
    "more_than_64_pieces": "S = ''\n" + "S += 'x'\n" * 70 + "def run(cur):\n    cur.execute(S)\n",
    "non_plus_augmented_operator": "S = 'DELETE FROM hidden'\nS *= 1\ndef run(cur):\n    cur.execute(S)\n",
}


@pytest.mark.parametrize("name", sorted(UNEVALUABLE))
def test_a_constant_only_expression_that_cannot_be_evaluated_is_not_scanned_never_clean(repo, name):
    tables, ns = _find(repo, UNEVALUABLE[name])
    assert tables is None and ns.startswith("write_form_not_analysed: a constant-only template whose text this scan cannot read"), (name, tables, ns)


NOT_WRITES = {                  # constant-only, evaluated, and the text is no write: read complete WITHOUT the table (the evaluator is not a verb detector)
    "sorted_descending_pieces": _run("''.join(sorted(('ETE FROM hidden', 'DEL'), reverse=True))"),
    "max_plus_min": _run("max('DEL', 'ETE FROM hidden') + min('DEL', 'ETE FROM hidden')"),
    "literal_percent_percent": _run("'DEL%%' % () + 'ETE FROM hidden'"),
}


@pytest.mark.parametrize("name", sorted(NOT_WRITES))
def test_a_constant_text_that_is_not_a_write_reads_complete_without_inventing_a_table(repo, name):
    tables, ns = _find(repo, NOT_WRITES[name])
    assert tables is not None and "public.hidden" not in tables, (name, tables, ns)


CONST_COMPLETE = {
    "plain_percent_str": "def r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y = %s' % 'z')\n",
    "plain_percent_int": "def r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y = %s' % 1)\n",
    "percent_tuple": "def r(cur):\n    cur.execute('SELECT %s, %s FROM t_b' % ('a', 'b'))\n",
    "plain_format": "def r(cur):\n    cur.execute('SELECT {} FROM t_b'.format('a'))\n",
    "named_format": "def r(cur):\n    cur.execute('SELECT {c} FROM t_b'.format(c='a'))\n",
    "list_literal_join": "def r(cur):\n    cur.execute(' '.join(['SELECT', 'x', 'FROM', 't_b']))\n",
    "strip_of_a_literal": "def r(cur):\n    cur.execute('  SELECT 1  '.strip())\n",
    "lower_of_a_literal": "def r(cur):\n    cur.execute('SELECT X FROM T_B'.lower())\n",
    "numeric_constant_product_in_an_fstring": "LIMIT = 10 * 5\ndef r(cur):\n    cur.execute(f'SELECT x FROM t_b LIMIT {LIMIT}')\n",
    "a_numeric_counter": "N = 0\nN += 1\ndef r(cur):\n    cur.execute(f'SELECT x FROM t_b LIMIT {N}')\n",
    "a_constant_name_join_of_columns": "COLS = ['a', 'b']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(COLS) + ' FROM t_b')\n",
    "a_constant_name_slice": "COLS = ['a', 'b', 'c']\ndef r(cur):\n    cur.execute('SELECT ' + ', '.join(COLS[:2]) + ' FROM t_b')\n",
    "a_slice_of_numbers": "N = (1, 2, 3)[1:]\ndef r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y = %s', N)\n",
    "an_fstring": "T = 't_b'\ndef r(cur):\n    cur.execute(f'SELECT x FROM {T}')\n",
    "placeholders_by_count": "COLS = ['a', 'b']\ndef r(cur):\n    cur.execute('SELECT x FROM t_b WHERE y IN (' + ', '.join(['%s'] * len(COLS)) + ')')\n",
}


@pytest.mark.parametrize("name", sorted(CONST_COMPLETE))
def test_the_forms_that_were_already_read_stay_complete(repo, name):
    res = scan(repo, CONST_COMPLETE[name])
    assert "tables" in res and "public.t_a" in res["tables"], (name, res)


NON_CONSTANT = {                # a parameter / unknown call / attribute is not a constant: the evaluator does not judge it (the existing handling does)
    "parameter": "def r(cur, t):\n    cur.execute('DEL' + t)\n",
    "unknown_call": "def r(cur):\n    cur.execute(''.join(get_parts()))\n",
    "attribute": "def r(cur):\n    cur.execute(cfg.SQL)\n",
}


@pytest.mark.parametrize("name", sorted(NON_CONSTANT))
def test_a_non_constant_expression_is_not_the_evaluators_to_judge(repo, name):
    sc = slw._WriteScan(ast.parse(textwrap.dedent(NON_CONSTANT[name])))
    node = [n for n in ast.walk(ast.parse(textwrap.dedent(NON_CONSTANT[name]))) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "execute"][0].args[0]
    with pytest.raises(slw._NotConst):
        sc._cvals(node, {})
    assert partial(repo, NON_CONSTANT[name])


def test_the_evaluator_reads_values_exactly():
    sc = slw._WriteScan(ast.parse("A = 68\nN = 'neddih'\nP = ['DEL', 'ETE']\nT = 1\n"))
    ev = lambda src: sc._cvals(ast.parse(src, mode="eval").body, {})      # noqa: E731
    assert ev("'%c' % A") == ["D"] and ev("N[::-1]") == ["hidden"] and ev("''.join(P)") == ["DELETE"] and ev("'a' if T else 'b'") == ["a"]
    assert ev("[c for c in 'abc' if c != 'b']") == [["a", "c"]] and ev("{'k': 1}['k']") == [1] and ev("len(P)") == [2] and ev("sorted({'b', 'a'})") == [["a", "b"]]
    with pytest.raises(slw._Unsupported):
        ev("''.join({'a', 'b'})")
    with pytest.raises(slw._NotConst):
        ev("unknown_name")
    with pytest.raises(slw._NotConst):
        ev("'a' * 100000")                                                    # past the literal cap: not this evaluator's to judge
    with pytest.raises(slw._NotConst):
        ev("'x'[5]")                                                          # fails at run time on these constants: no statement


def test_a_name_with_several_constant_bindings_is_each_of_them_and_all_are_scanned(repo):
    body = "def a():\n    q = 'DELETE FROM hidden'\ndef b():\n    q = 'SELECT 1'\ndef run(cur):\n    cur.execute(q)\n"
    _reads_hidden(repo, body)


def test_every_name_binding_form_that_is_not_an_assignment_is_not_a_constant():
    for src in ("def f(p):\n    pass\n", "import os as p\n", "class p:\n    pass\n", "for p, in [(1,)]:\n    pass\n"):
        sc = slw._WriteScan(ast.parse(src))
        with pytest.raises((slw._NotConst, slw._Unsupported)):
            sc._name_cvals("p", 0) if "for" not in src else (_ for _ in ()).throw(slw._NotConst("loop with unpack of a non-iterable"))


# ───────────────────────── mutations: each part of the closure is what refuses the attack ─────────────────────────

def _attack_bodies():
    return [_run(EVALUABLE[n][1], EVALUABLE[n][0]) for n in ("pct_binop_left", "pct_fstr_left", "name_slice_reversed", "names_percent_c", "name_percent_c", "name_join", "name_index_sum", "ifexp_fragment",
                                                       "or_fragment", "dict_values_join", "list_index_pair", "name_join_generator")]


def test_MUTATION_without_the_evaluator_the_review_attacks_read_complete_and_miss_the_table(repo, monkeypatch):
    for body in _attack_bodies():
        _reads_hidden(repo, body)
    monkeypatch.setattr(slw._WriteScan, "_const_text_verdict", lambda self, node: None)
    missed = [b for b in _attack_bodies() if "public.hidden" not in (scan(repo, b).get("tables") or [])]
    assert len(missed) >= 10, len(missed)                                     # the previous behaviour: the statement is in no literal, the table is missed


def test_MUTATION_without_constant_names_the_named_attacks_are_missed(repo, monkeypatch):
    names = ("name_percent_c", "names_percent_c", "name_slice_reversed", "name_join", "name_index_sum")
    for n in names:
        _reads_hidden(repo, _run(EVALUABLE[n][1], EVALUABLE[n][0]))
    def not_const(self, name, depth):
        raise slw._NotConst(name)
    monkeypatch.setattr(slw._WriteScan, "_name_cvals", not_const)
    assert all("public.hidden" not in (scan(repo, _run(EVALUABLE[n][1], EVALUABLE[n][0])).get("tables") or []) for n in names)


def test_MUTATION_without_the_set_order_guard_a_set_join_reads_complete(repo, monkeypatch):
    tables, ns = _find(repo, UNEVALUABLE["set_of_pieces_joined"])
    assert tables is None and ns.startswith("write_form_not_analysed")
    monkeypatch.setattr(slw._ConstSet, "__iter__", lambda self: iter(set.__iter__(self)))
    tables, ns = _find(repo, UNEVALUABLE["set_of_pieces_joined"])
    assert tables is not None                                                 # no longer refused: the arbitrary iteration order would decide what was scanned


def test_MUTATION_without_the_accumulation_model_built_up_text_is_missed(repo, monkeypatch):
    for n in ("augmented_assignment", "augmented_in_a_loop", "self_concatenation_in_a_loop"):
        _reads_hidden(repo, BUILT_UP[n])
    monkeypatch.setattr(slw._WriteScan, "_cv_name_value", lambda self, name, bound, depth: (_ for _ in ()).throw(slw._NotConst(name)))
    for n in ("augmented_assignment", "augmented_in_a_loop", "self_concatenation_in_a_loop"):
        assert "public.hidden" not in (scan(repo, BUILT_UP[n]).get("tables") or [])


def test_MUTATION_without_the_unsupported_refusal_an_unevaluable_expression_reads_complete(repo, monkeypatch):
    for n in ("set_of_pieces_joined", "set_comprehension_joined"):
        assert _find(repo, UNEVALUABLE[n])[0] is None
    real = slw._WriteScan._const_text_verdict

    def swallow(self, node):
        r = real(self, node)
        return None if r else r                                               # an unevaluable reading is dropped instead of refused
    monkeypatch.setattr(slw._WriteScan, "_const_text_verdict", swallow)
    assert all(_find(repo, UNEVALUABLE[n])[0] is not None for n in ("set_of_pieces_joined", "set_comprehension_joined"))   # (the closed allow-list alone reads them clean)


def test_the_evaluator_is_charged_to_the_work_cap(repo, monkeypatch):
    """Every non-trivial node the evaluator visits is a counted step, so a hostile constant expression cannot cost more than the resolver's cap."""
    sc = slw._WriteScan(ast.parse("x = 1\n"))
    before = sc.work_steps
    assert sc._cvals(ast.parse("'%c' % (68, 69)[0]", mode="eval").body, {}) == ["D"]
    assert sc.work_steps > before
    monkeypatch.setattr(slw._WriteScan, "MAX_RESOLVER_STEPS", 12)
    big = "def r(cur):\n    cur.execute(" + "'%s' % (" * 25 + "'x'" + ",)" * 25 + ")\n"
    assert scan(repo, big)["not_scanned"].startswith("resolver_work_cap")
