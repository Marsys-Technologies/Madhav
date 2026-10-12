"""test_s3_plus_join_column_list.py: S3 (SS N-551): the census scanner reads the `+` form of a literal column-list join.

  `"INSERT INTO t (" + ", ".join(_COLS) + ") VALUES (...)"` is read as ONE statement text, exactly as the f-string form `f"INSERT INTO t ({', '.join(_COLS)}) ..."`
  already is (bo_samskara.py:85-87, `_MULTI_INSERT_HEAD`; before S3 the chain was cut at the join and the head read as an unclosed `(`: "unbalanced column list").

  §N.8: the change makes the scanner read MORE, never excuse more. A name is joined ONLY when it is a MODULE-LEVEL LITERAL list/tuple of str constants, bound once in the
  whole module, never mutated/rebound/imported/shadowed. Every acceptance test below is paired with MUTANTS: the same source with ONE dynamic change, which must read
  EXACTLY as it did before S3 (the join stays unread: the chain is cut and `written_columns` is None). The mutants are what a loosened guard (accept any name, accept a
  mutated list, accept a local) would break; tests/mutation_checks are described in the PR.
"""
from __future__ import annotations

import ast
import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

GOOD_TEXT = "INSERT INTO t (id, story) VALUES (%s, %s)"
HEAD = '''
INSERT_HEAD = "INSERT INTO t (" + ", ".join(_COLS) + ") VALUES (%s, %s)"
'''
COLS = '_COLS = ("id", "story")\n'


def _units(src):
    tree = ast.parse(textwrap.dedent(src))
    return [dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")]


def _texts(src):
    return [t for t, _ in ac._sql_texts(_units(src)[0])]


def _read(src) -> bool:
    """True iff the `+` chain was read as one statement with the joined column list in it."""
    return GOOD_TEXT in _texts(src)


def _cols(src):
    return ac.written_columns(_units(src), ["t"])


def _assert_unread(src):
    """What the scanner did before S3: the chain is cut at the join, the head is an unclosed `(`, the written columns are unknown."""
    assert not _read(src), _texts(src)
    assert not any("id, story" in t for t in _texts(src)), _texts(src)
    assert _cols(src) is None


# ───────────────────────────── acceptance: the shapes S3 reads ─────────────────────────────

def test_tuple_module_literal_is_read():
    src = COLS + HEAD
    assert _read(src), _texts(src)
    assert _cols(src) == {"t": {"id", "story"}}


def test_list_module_literal_with_inert_uses_is_read():
    src = '_COLS = ["id", "story"]\n' + HEAD + '''
_N = len(_COLS)
_FLAT = [r[c] for r in ROWS for c in _COLS]
for _c in _COLS:
    pass
_FIRST = _COLS[0]
'''
    assert _read(src), _texts(src)
    assert _cols(src) == {"t": {"id", "story"}}


def test_annotated_tuple_literal_and_other_separator_and_longer_chain():
    src = '_COLS: tuple = ("id", "story")\nH = "INSERT INTO t (\\n  " + ", ".join(_COLS) + "\\n) VALUES (%s, %s)"\n'
    assert "INSERT INTO t (\n  id, story\n) VALUES (%s, %s)" in _texts(src)
    assert _cols(src) == {"t": {"id", "story"}}


def test_join_used_inside_a_function_body_is_read_too():
    src = COLS + '''
def _sql():
    return "INSERT INTO t (" + ", ".join(_COLS) + ") VALUES (%s, %s)"
'''
    assert _read(src), _texts(src)


def test_f_string_form_is_unchanged():
    src = COLS + 'H = f"INSERT INTO t ({\', \'.join(_COLS)}) VALUES (%s, %s)"\n'
    assert GOOD_TEXT in _texts(src)


def test_the_real_bo_samskara_head_is_read():
    """The writer that motivated S3: `_MULTI_INSERT_HEAD` now reads as a whole statement, so the writer's written columns are known."""
    p = HERE.parents[2] / "python-sidecar" / "pipeline" / "orchestrator" / "writers" / "bo_samskara.py"
    tree = ast.parse(p.read_text(encoding="utf-8"))
    unit = dict(rel="bo_samskara.py", path=p, tree=tree, nodes=[tree], hop=0, via="bo_samskara.py")
    texts = [t for t, _ in ac._sql_texts(unit)]
    head = [t for t in texts if t.startswith("INSERT INTO public.bodha_signal_embeddings (\n  ") and ") VALUES" in t]
    assert head, [t[:60] for t in texts if "bodha_signal_embeddings" in t]
    assert head[0].count("embedding_input_summary") == 1 and head[0].endswith("\n) VALUES\n")
    cols = ac.written_columns([unit], ["bodha_signal_embeddings"])
    assert cols and "embedding_input_summary" in cols["bodha_signal_embeddings"] and len(cols["bodha_signal_embeddings"]) == 10


# ───────────────────────────── paired mutants: the dynamic variants must stay unread ─────────────────────────────

BUILT = {
    "generator_call": '_COLS = tuple(c for c in ("id", "story"))\n',
    "list_comprehension": '_COLS = [c for c in ("id", "story")]\n',
    "open_call": '_COLS = tuple(open("x").read().split())\n',
    "sorted_call": '_COLS = sorted(("id", "story"))\n',
    "tuple_concat_literals": '_COLS = ("id",) + ("story",)\n',
    "tuple_concat_nonliteral": '_COLS = ("id",) + OTHER\n',
    "list_times": '_COLS = ["id", "story"] * 1\n',
    "empty": '_COLS = ()\n',
    "non_str_member": '_COLS = ("id", 1)\n',
    "name_member": '_COLS = ("id", STORY)\n',
    "fstring_member": '_COLS = ("id", f"{x}")\n',
    "starred_member": '_COLS = ("id", *OTHER)\n',
    "set_literal": '_COLS = {"id", "story"}\n',
    "dict_literal": '_COLS = {"id": 1, "story": 2}\n',
    "alias_of_other": '_COLS = OTHER_COLS\n',
    "imported_only": 'from other import _COLS\n',
    "conditional_binding": 'if FLAG:\n    _COLS = ("id", "story")\n',
    "try_binding": 'try:\n    _COLS = ("id", "story")\nexcept Exception:\n    pass\n',
    "annotation_only": '_COLS: tuple\n',
}


@pytest.mark.parametrize("name", sorted(BUILT))
def test_mutant_name_not_a_literal_sequence_stays_unread(name):
    _assert_unread(BUILT[name] + HEAD)


MUTATED_LIST = {
    "append": '_COLS.append("x")\n',
    "extend": '_COLS.extend(["x"])\n',
    "insert": '_COLS.insert(0, "x")\n',
    "remove": '_COLS.remove("id")\n',
    "pop": '_COLS.pop()\n',
    "clear": '_COLS.clear()\n',
    "sort": '_COLS.sort()\n',
    "reverse": '_COLS.reverse()\n',
    "iadd": '_COLS += ["x"]\n',
    "index_store": '_COLS[0] = "x"\n',
    "slice_store": '_COLS[0:1] = ["x", "y"]\n',
    "del_index": 'del _COLS[0]\n',
    "del_name": 'del _COLS\n',
    "alias_then_mutate": '_ALIAS = _COLS\n_ALIAS.append("x")\n',
    "alias_alone": '_ALIAS = _COLS\n',
    "call_argument": '_helper(_COLS)\n',
    "zip_use": '_Z = dict(zip(_COLS, range(2)))\n',
    "method_use": '_I = _COLS.index("id")\n',
    "in_function_mutation": 'def _grow():\n    _COLS.append("x")\n',
    "returned_from_function": 'def _get():\n    return _COLS\n',
}


@pytest.mark.parametrize("name", sorted(MUTATED_LIST))
def test_mutant_mutated_or_escaping_list_stays_unread(name):
    _assert_unread('_COLS = ["id", "story"]\n' + HEAD + MUTATED_LIST[name])
    # the same use of an immutable TUPLE cannot change it, but a rebind-type use (below) still does; only the list is use-checked
    ok_for_tuple = {"alias_alone", "call_argument", "zip_use", "returned_from_function"}
    if name in ok_for_tuple:
        assert _read(COLS + HEAD + MUTATED_LIST[name]), name


REBOUND = {
    "second_assignment": '_COLS = ("id", "story", "extra")\n',
    "reassigned_after": '_COLS = tuple(_COLS)\n',
    "augassign_tuple": '_COLS += ("x",)\n',
    "global_rebind_in_function": 'def _reset():\n    global _COLS\n    _COLS = ("a",)\n',
    "global_declared_only": 'def _reset():\n    global _COLS\n',
    "nonlocal_rebind": 'def _o():\n    _COLS = 1\n    def _i():\n        nonlocal _COLS\n        _COLS = 2\n',
    "for_target": 'for _COLS in OTHERS:\n    pass\n',
    "with_target": 'with OPEN() as _COLS:\n    pass\n',
    "walrus": '(_COLS := ("x",))\n',
    "comprehension_target": '_L = [1 for _COLS in OTHERS]\n',
    "tuple_unpack": '_A, _COLS = OTHER_PAIR\n',
    "later_import": 'from other import _COLS\n',
    "later_import_as": 'import other as _COLS\n',
    "def_same_name": 'def _COLS():\n    pass\n',
    "class_same_name": 'class _COLS:\n    pass\n',
    "except_alias": 'try:\n    pass\nexcept Exception as _COLS:\n    pass\n',
    "function_local_shadow": 'def _f():\n    _COLS = ("a", "b")\n    return _COLS\n',
    "parameter_shadow": 'def _f(_COLS):\n    return _COLS\n',
    "kwonly_parameter_shadow": 'def _f(*, _COLS=()):\n    return _COLS\n',
    "lambda_parameter_shadow": '_F = lambda _COLS: _COLS\n',
    "class_attribute_rebind": 'class _K:\n    _COLS = ("z",)\n',
    "star_import": 'from other import *\n',
    "globals_call": '_G = globals()\n',
    "exec_call": 'exec("x")\n',
    "eval_call": '_V = eval("x")\n',
    "match_capture": 'match OTHER:\n    case [_COLS]:\n        pass\n',
}


@pytest.mark.parametrize("name", sorted(REBOUND))
def test_mutant_rebound_shadowed_or_blinded_name_stays_unread(name):
    _assert_unread(COLS + HEAD + REBOUND[name])


def test_mutant_function_local_literal_stays_unread():
    src = '''
def _sql():
    cols = ("id", "story")
    return "INSERT INTO t (" + ", ".join(cols) + ") VALUES (%s, %s)"
'''
    _assert_unread(src)


def test_mutant_function_local_name_shadowing_a_module_literal_stays_unread():
    src = COLS + '''
def _sql(_COLS):
    return "INSERT INTO t (" + ", ".join(_COLS) + ") VALUES (%s, %s)"
'''
    _assert_unread(src)


def test_mutant_class_attribute_stays_unread():
    src = '''
class W:
    _COLS = ("id", "story")
    HEAD = "INSERT INTO t (" + ", ".join(_COLS) + ") VALUES (%s, %s)"
'''
    _assert_unread(src)
    src2 = COLS + '''
class W:
    def sql(self):
        return "INSERT INTO t (" + ", ".join(self._COLS) + ") VALUES (%s, %s)"
'''
    _assert_unread(src2)


def test_mutant_inline_literal_and_non_name_arguments_stay_unread():
    for arg in ('("id", "story")', '["id", "story"]', "_COLS + ('x',)", "list(_COLS)", "sorted(_COLS)", "_COLS[:]", "(c for c in _COLS)", "OTHER.cols"):
        _assert_unread(COLS + f'H = "INSERT INTO t (" + ", ".join({arg}) + ") VALUES (%s, %s)"\n')


def test_mutant_non_literal_separator_or_extra_arguments_stay_unread():
    for call in ("SEP.join(_COLS)", "str.join(', ', _COLS)", "', '.join(_COLS, 1)", "', '.join(iterable=_COLS)", "(', ' + X).join(_COLS)", "', '.joinx(_COLS)", "', '.split(_COLS)"):
        _assert_unread(COLS + f'H = "INSERT INTO t (" + {call} + ") VALUES (%s, %s)"\n')


def test_mutant_imported_from_non_literal_code_stays_unread():
    _assert_unread('from other import _COLS\n' + HEAD)
    _assert_unread('import other\n_COLS = other.COLS\n' + HEAD)
    _assert_unread('import json\n_COLS = tuple(json.load(open("c.json")))\n' + HEAD)


def test_mutant_non_join_call_operand_stays_unread():
    for call in ("_fmt(_COLS)", "str(_COLS)", "', '.upper()", "_COLS.join(', ')"):
        _assert_unread(COLS + f'H = "INSERT INTO t (" + {call} + ") VALUES (%s, %s)"\n')


def test_mutant_fstring_with_a_non_literal_part_keeps_its_unresolved_marker():
    """An f-string operand keeps the scanner's own reading: a non-literal `{x}` is the marker `{?}`, never a resolved name."""
    src = COLS + 'H = "INSERT INTO t (" + ", ".join(_COLS) + f") VALUES ({x})"\n'
    assert "INSERT INTO t (id, story) VALUES ({?})" in _texts(src)
    only_fstring = COLS + 'H = f"INSERT INTO t ({x}) VALUES (%s, %s)"\n'
    assert _texts(only_fstring).count("INSERT INTO t ({?}) VALUES (%s, %s)") == 1
    assert _cols(only_fstring) is None


def test_mutant_a_chain_with_a_dynamic_operand_is_not_extended_by_it():
    """`<literal chain> + _suffix()` is not one text: the literal part is read on its own (as the scanner always did for a chain cut by a call), the dynamic operand adds nothing."""
    for tail in ("+ _suffix()", "+ str(n)", "+ OTHER", "+ x.y"):
        texts = _texts(COLS + f'H = "INSERT INTO t (" + ", ".join(_COLS) + ") VALUES (%s, %s)" {tail}\n')
        assert [t for t in texts if t.startswith("INSERT")] == [GOOD_TEXT], texts
        assert not any("{?}" in t for t in texts), texts


def test_a_fresh_module_with_the_same_name_does_not_inherit_a_cached_answer():
    """The per-module cache is keyed by the parsed tree: a second module that rebinds the name is judged on its own."""
    assert _read(COLS + HEAD)
    _assert_unread(COLS + HEAD + REBOUND["second_assignment"])
    assert _read(COLS + HEAD)


def test_a_cache_entry_left_by_a_dead_tree_with_a_reused_id_is_not_trusted():
    """The per-module answer is cached by `id(tree)`; an entry whose stored tree is not THIS tree (a freed tree's id was reused) must be recomputed, never served."""
    unit = _units(COLS + REBOUND["second_assignment"] + HEAD)[0]
    ac._PLUS_JOIN_NAMES[id(unit["tree"])] = (object(), {"_COLS": ["id", "story"]})   # the stale answer says: resolvable
    texts = [t for t, _ in ac._sql_texts(unit)]
    assert GOOD_TEXT not in texts, texts
