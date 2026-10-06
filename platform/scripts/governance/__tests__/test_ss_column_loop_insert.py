"""test_ss_column_loop_insert.py -- residual detector D4: the Null writer scan reads an INSERT whose VALUES list is built in a COLUMN LOOP.

ga_tajaka's `_insert_rows` writes `INSERT INTO t (<', '.join(_COLUMNS)>) VALUES (<", ".join(["%s"] * len(_COLUMNS))>)` and binds a list filled by
`for c in _COLUMNS: v = r[c]; (wrap); vals.append(v)`. The scan used to stop at "18 column(s) but 1 value(s)" and "the parameters are the name vals": the prose column
`citation_human` had no write path. It now (1) resolves the placeholder join to one `%s` per listed column, and (2) reads the loop as the row's entry of the same name (exactly a
named `%(column)s` parameter), under a closed shape: any deviation stays unresolved. Also pinned here: an execute call in ANOTHER function that happens to use the variable name `sql`
is not bound to the statement. Offline; synthetic sources plus the real ga_tajaka writer.
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

LS = ac._lint_module("writer_literal_scan")
TABLE = "t_prose"

GOOD = '''
_COLUMNS = ["id", "story", "payload"]


def build_row(n, who):
    return {"id": n, "story": f"Row {n} for {who}", "payload": {"k": 1}}


def _insert_rows(conn, rows):
    placeholders = ", ".join(["%s"] * len(_COLUMNS))
    sql = (f"INSERT INTO t_prose ({', '.join(_COLUMNS)}) "
           f"VALUES ({placeholders})")
    for r in rows:
        vals = []
        for c in _COLUMNS:
            v = r[c]
            if c in ("payload",):
                v = json.dumps(v)
            vals.append(v)
        conn.execute(sql, vals)
'''


def _scan(src, entry="story"):
    tree = ast.parse(src)
    units = [dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")]
    return LS.scan(units, [entry], {entry: {TABLE}}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)


def test_a_column_loop_insert_resolves_and_reads_clean():
    ws = _scan(GOOD)
    assert ws["v"] == "PASS" and ws["unresolved"] == [] and ws["entries"]["story"]["writes"] == 1 and ws["entries"]["story"]["sources"] == 1, ws


def test_the_value_source_is_the_rows_own_entry_so_a_literal_fallback_there_is_a_finding():
    bad = GOOD.replace('f"Row {n} for {who}"', '(who or "n/a")')
    ws = _scan(bad)
    assert ws["v"] == "PARTIAL" and ws["problems"] and "n/a" in ws["problems"][0]["text"], ws


def test_a_constant_written_to_the_column_is_a_finding():
    ws = _scan(GOOD.replace('f"Row {n} for {who}"', '"unknown"'))
    assert ws["v"] == "PARTIAL" and ws["problems"], ws


@pytest.mark.parametrize("mutate,why", [
    (lambda s: s.replace('        vals = []\n', '        vals = [0]\n'), "not assigned exactly once to an empty list"),
    (lambda s: s.replace('            vals.append(v)\n', '            vals.append(v)\n            vals.append(v)\n'), "other than by one"),
    (lambda s: s.replace('            v = r[c]\n', '            v = r[c] or "n/a"\n'), "is not read as"),
    (lambda s: s.replace('                v = json.dumps(v)\n', '                v = v or "x"\n'), "re-assigned to something other than a one-argument wrapper"),
    (lambda s: s.replace('for c in _COLUMNS:\n            v', 'for c in ["id", "story", "payload"]:\n            v'), "not `for <name> in <name>`"),
    # the statement's column list is typed out in a different order than the loop list: position k of the values is not column k of the statement
    (lambda s: s.replace("({', '.join(_COLUMNS)})", "(id, payload, story)").replace('_COLUMNS = ["id", "story", "payload"]', '_COLUMNS = ["id", "story", "payload"]'), "order"),
])
def test_any_deviation_from_the_closed_shape_stays_unresolved(mutate, why):
    ws = _scan(mutate(GOOD))
    assert ws["v"] == "PARTIAL" and ws["unresolved"], ws
    # the pre-D4 reading stands for the deviation (the parameter list is a name the function mutates / a count that does not match): unresolved, never read clean


def test_reordering_the_one_shared_list_is_consistent_and_still_reads_clean():
    assert _scan(GOOD.replace('_COLUMNS = ["id", "story", "payload"]', '_COLUMNS = ["id", "payload", "story"]'))["v"] == "PASS"


def test_the_loop_list_must_be_the_statements_own_column_list():
    src = GOOD.replace("({', '.join(_COLUMNS)})", "(id, story, payload)").replace('["%s"] * len(_COLUMNS)', '["%s"] * 3')
    ws = _scan(src)
    assert ws["v"] == "PARTIAL" and ws["unresolved"], ws        # the placeholder join is not over a literal list: not resolved, never guessed


def test_an_execute_with_the_same_variable_name_in_another_function_is_not_bound_to_the_statement():
    src = GOOD + '\n\ndef _delete(conn, sql, params):\n    conn.execute(sql, params)\n'
    ws = _scan(src)
    assert ws["v"] == "PASS" and ws["unresolved"] == [], ws


def test_a_module_level_statement_constant_is_still_bound_by_name_from_a_function():
    src = ('SQL = "INSERT INTO t_prose (id, story) VALUES (%s, %s)"\n\n\ndef w(conn, n):\n    conn.execute(SQL, (n, f"Row {n}"))\n')
    ws = _scan(src)
    assert ws["v"] == "PASS" and ws["entries"]["story"]["sources"] == 1, ws


def test_a_subscript_store_of_a_len_does_not_make_the_row_construction_opaque():
    src = GOOD + '\n\ndef count(rows):\n    counts = {}\n    for k in rows:\n        counts[k] = len(rows)\n    return counts\n'
    assert _scan(src)["v"] == "PASS"
    src2 = GOOD + '\n\ndef count(rows, extra):\n    out = {}\n    for k in rows:\n        out[k] = extra\n    return out\n'
    ws = _scan(src2)
    assert ws["v"] == "PARTIAL" and any("subscript store with a non-literal key" in u for u in ws["unresolved"]), ws    # still opaque for anything but a len()


def test_the_placeholder_join_resolves_only_over_a_literal_list_of_strings():
    tree = ast.parse('COLS = ["a", "b", "c"]\n\n\ndef f(conn):\n    ph = ", ".join(["%s"] * len(COLS))\n    conn.execute(f"INSERT INTO t (a, b, c) VALUES ({ph})")\n')
    u = dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")
    texts = [t for t, _ in ac._sql_texts(u)]
    assert any("VALUES (%s, %s, %s)" in x for x in texts), texts
    tree2 = ast.parse('def f(conn, COLS):\n    ph = ", ".join(["%s"] * len(COLS))\n    conn.execute(f"INSERT INTO t (a) VALUES ({ph})")\n')
    u2 = dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree2, nodes=[tree2], hop=0, via="w.py")
    assert any("{?}" in x for x in [t for t, _ in ac._sql_texts(u2)]) and not any("VALUES (%s" in x for x in [t for t, _ in ac._sql_texts(u2)])


# ───────────── the real writer that motivated it ─────────────

def test_the_real_ga_tajaka_insert_now_has_a_write_path_for_its_prose_column():
    units, beyond = ac.writer_scan_scope("ga_tajaka", ac.registered_ids("ga_")["ga_tajaka"])
    ws = LS.scan(units, ["citation_human"], {"citation_human": {"l1_tajik_varsha_year_lords"}}, is_placeholder=ac.ldgr_placeholder_py,
                 sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field, beyond=beyond)
    e = ws["entries"]["citation_human"]
    assert e["writes"] == 1 and e["sources"] == 1, e                      # was: writes 0 ("no statement writes the column") and 3 unresolved
    assert not any("18 column(s) but 1 value" in u or "the name `vals`" in u or "_idempotency" in u for u in ws["unresolved"]), ws["unresolved"]
    # SS R-b: the `'.'` terminator of the conditional suffix is not a fallback, so it is no longer a finding; what remains is only the conservative `**` unpack of the birth parameters
    assert ws["problems"] == [], ws["problems"]
    assert any("dict display with a ** unpack" in u for u in ws["unresolved"]), ws["unresolved"]


# ───────────── SS R-b: a lone punctuation literal that terminates a composed sentence is not a placeholder ─────────────

SUFFIX = '''
def build(n, flag):
    return {"id": n, "story": f"Row {n} done" + ("; flagged." if flag else ".")}

SQL = "INSERT INTO t_prose (id, story) VALUES (%(id)s, %(story)s)"

def w(conn, rows):
    conn.execute(SQL, rows)
'''


def test_rb_a_punctuation_terminator_in_a_conditional_suffix_is_not_a_finding():
    ws = _scan(SUFFIX)
    assert ws["v"] == "PASS" and ws["problems"] == [], ws


@pytest.mark.parametrize("lit", ["N/A", "unknown", "none", "n.a.", "-"])
def test_rb_a_word_or_dash_placeholder_in_the_same_position_is_still_a_finding(lit):
    ws = _scan(SUFFIX.replace('else ".")', f'else "{lit}")'))
    assert ws["problems"] and "conditional expression" in ws["problems"][0]["text"], (lit, ws)


@pytest.mark.parametrize("term", [".", "!", "?", "...", "\u2026"])
def test_rb_each_sentence_terminator_is_exempt_only_as_the_last_operand_with_a_literal_other_branch(term):
    assert _scan(SUFFIX.replace('else ".")', f'else "{term}")'))["problems"] == [], term


def _rb(expr):
    return _scan(SUFFIX.replace('f"Row {n} done" + ("; flagged." if flag else ".")', expr))


@pytest.mark.parametrize("expr", [
    'f"Row {n} lord " + (who if who else "-")',                       # a dash beside a COMPUTED value
    'f"Row {n} lord " + (who if who else "?")',                       # a terminator character beside a computed value: the other branch is not a literal
    'f"Row {n} lord " + (who if who else "...")',
    'f"Row {n} lord " + (who if who else ".")',
    'f"Row {n} {who if who else \'.\'} done"',                       # inside an f-string, not a suffix
    '("; flagged." if flag else ".") + f"Row {n} done"',              # first operand of the chain, not the last
    'f"Row {n}" + ("; x" if flag else ".") + f" done {n}"',            # in the MIDDLE of the chain
    '(f"Row {n}" + ("; x" if flag else ".")) + " tail"',               # the chain continues after it
    '"." if flag else "x"',                                            # the whole value
    'who or "."',                                                      # `or` fallback
])
def test_rb_these_stay_findings(expr):
    ws = _rb(expr.replace("who", "n"))
    assert ws["problems"], (expr, ws)


def test_rb_a_punctuation_literal_that_is_the_WHOLE_value_is_still_a_finding():
    src = SUFFIX.replace('f"Row {n} done" + ("; flagged." if flag else ".")', '("." if flag else None)')
    ws = _scan(src)
    assert ws["problems"], ws                               # role `value`, not a fragment of a composed sentence


def test_rb_the_rule_does_not_reach_a_missing_value_default_with_words():
    src = SUFFIX.replace('f"Row {n} done" + ("; flagged." if flag else ".")', 'f"Row {n} done" + (flag if flag else "no data available")')
    assert _scan(src)["problems"], "a literal default sentence for a missing value stays a finding"


# ───────────── column-loop escapes: the closed shape refuses every way a value can bypass the row ─────────────

def _loop(body_change):
    return _scan(body_change(GOOD))


@pytest.mark.parametrize("name,mutate", [
    ("continue", lambda s: s.replace('            v = r[c]\n', '            v = r[c]\n            if c == "story":\n                continue\n')),
    ("break", lambda s: s.replace('            v = r[c]\n', '            v = r[c]\n            if c == "story":\n                break\n')),
    ("return", lambda s: s.replace('            v = r[c]\n', '            v = r[c]\n            if c == "story":\n                return\n')),
    ("raise", lambda s: s.replace('            v = r[c]\n', '            v = r[c]\n            if c == "story":\n                raise ValueError()\n')),
    ("loop else", lambda s: s.replace('            vals.append(v)\n', '            vals.append(v)\n        else:\n            vals[1] = "N/A"\n')),
    ("del item", lambda s: s.replace('        conn.execute(sql, vals)\n', '        del vals[1]\n        conn.execute(sql, vals)\n')),
    ("alias then item store", lambda s: s.replace('        conn.execute(sql, vals)\n', '        w = vals\n        w[1] = "N/A"\n        conn.execute(sql, vals)\n')),
    ("helper call on the list", lambda s: s.replace('        conn.execute(sql, vals)\n', '        _x(vals)\n        conn.execute(sql, vals)\n')),
    ("slice store", lambda s: s.replace('        conn.execute(sql, vals)\n', '        vals[:] = ["N/A"] * 3\n        conn.execute(sql, vals)\n')),
    ("extend", lambda s: s.replace('        conn.execute(sql, vals)\n', '        vals.extend(["N/A"])\n        conn.execute(sql, vals)\n')),
    ("a nested function mutates it", lambda s: s.replace('        conn.execute(sql, vals)\n', '        def _g():\n            vals[1] = "N/A"\n        _g()\n        conn.execute(sql, vals)\n')),
    ("opaque wrapper", lambda s: s.replace('                v = json.dumps(v)\n', '                v = _fill(v)\n')),
    ("wrapper that is not one of json.dumps/str/int/float", lambda s: s.replace('                v = json.dumps(v)\n', '                v = coalesce(v)\n')),
    ("walrus", lambda s: s.replace('            vals.append(v)\n', '            vals.append(v := r[c] or "N/A")\n')),
    ("the loop variable is rebound", lambda s: s.replace('            v = r[c]\n', '            c = "id"\n            v = r[c]\n')),
    ("the value is assigned before the read", lambda s: s.replace('            v = r[c]\n', '            v = "x"\n            v = r[c]\n')),
    ("the append is nested in an if", lambda s: s.replace('            vals.append(v)\n', '            if c != "story":\n                vals.append(v)\n')),
])
def test_loop_escape_stays_unresolved(name, mutate):
    src = mutate(GOOD)
    assert src != GOOD, name
    ws = _scan(src)
    assert ws["v"] == "PARTIAL" and ws["unresolved"], (name, ws)


@pytest.mark.parametrize("w", ["json.dumps(v)", "str(v)", "int(v)", "float(v)", "json.dumps(v, ensure_ascii=False)"])
def test_the_four_value_preserving_wrappers_still_resolve(w):
    assert _scan(GOOD.replace("json.dumps(v)", w))["v"] == "PASS", w


def test_a_wrapper_with_an_extra_argument_is_not_accepted():
    ws = _scan(GOOD.replace("json.dumps(v)", "str(v, 'x')"))
    assert ws["v"] == "PARTIAL", ws


# ───────────── review (second pass): rebinding forms, the row name, json.dumps hooks, an empty first operand ─────────────

_ROW_DEFS = '_DEF = {"id": 1, "story": "N/A", "payload": {}}\n'


@pytest.mark.parametrize("name,mutate", [
    ("with ... as v", lambda s: s.replace('            vals.append(v)\n', '            with _cm() as v:\n                pass\n            vals.append(v)\n')),
    ("except ... as v", lambda s: s.replace('            vals.append(v)\n', '            try:\n                pass\n            except ValueError as v:\n                pass\n            vals.append(v)\n')),
    ("import ... as v", lambda s: s.replace('            vals.append(v)\n', '            import json as v\n            vals.append(v)\n')),
    ("from m import v", lambda s: s.replace('            vals.append(v)\n', '            from m import v\n            vals.append(v)\n')),
    ("case v", lambda s: s.replace('            vals.append(v)\n', '            match c:\n                case v:\n                    pass\n            vals.append(v)\n')),
    ("del v", lambda s: s.replace('            vals.append(v)\n', '            del v\n            vals.append(v)\n')),
    ("global vals", lambda s: s.replace('    placeholders = ', '    global vals\n    placeholders = ')),
    ("nonlocal v", lambda s: s.replace('    placeholders = ', '    def _n():\n        nonlocal v\n    placeholders = ')),
    ("except ... as vals", lambda s: s.replace('        conn.execute(sql, vals)\n', '        try:\n            pass\n        except ValueError as vals:\n            pass\n        conn.execute(sql, vals)\n')),
    ("a comprehension rebinding v", lambda s: s.replace('            vals.append(v)\n', '            _z = [v for v in (1,)]\n            vals.append(v)\n')),
    ("a def named like the value", lambda s: s.replace('            vals.append(v)\n', '            def v(): pass\n            vals.append(v)\n')),
    ("the value read from a module constant `_DEF[c]`", lambda s: _ROW_DEFS + s.replace("v = r[c]", "v = _DEF[c]")),
    ("the value read from the parameter `rows[c]`", lambda s: s.replace("v = r[c]", "v = rows[c]")),
    ("the row rebound to a defaultdict", lambda s: s.replace('        vals = []\n', '        r = defaultdict(lambda: "N/A")\n        vals = []\n')),
    ("the row mutated by .update", lambda s: s.replace('        vals = []\n', '        r.update({"story": "N/A"})\n        vals = []\n')),
    ("the row rebound by a second loop", lambda s: s.replace('        conn.execute(sql, vals)\n', '        for r in other:\n            pass\n        conn.execute(sql, vals)\n')),
    ("the row assigned", lambda s: s.replace('        vals = []\n', '        r = {"story": "N/A"}\n        vals = []\n')),
    ("json.dumps default lambda", lambda s: s.replace("json.dumps(v)", 'json.dumps(v, default=lambda o: "N/A")')),
    ("json.dumps default a named hook", lambda s: s.replace("json.dumps(v)", "json.dumps(v, default=_ph)")),
    ("json.dumps unknown keyword", lambda s: s.replace("json.dumps(v)", "json.dumps(v, cls=_Enc)")),
    ("json.dumps non-literal indent", lambda s: s.replace("json.dumps(v)", "json.dumps(v, indent=_i())")),
])
def test_loop_rebinding_and_row_escapes_stay_unresolved(name, mutate):
    src = mutate(GOOD)
    assert src != GOOD, name
    ws = _scan(src)
    assert ws["v"] == "PARTIAL" and ws["unresolved"], (name, ws)


def test_the_row_loop_form_still_resolves_with_the_row_bound_to_the_enclosing_loop():
    assert _scan(GOOD)["v"] == "PASS"


@pytest.mark.parametrize("w", ["json.dumps(v, default=str)", "json.dumps(v, default=str, ensure_ascii=False, indent=2)", "json.dumps(v, sort_keys=True, separators=(',', ':'))"])
def test_json_dumps_with_default_str_or_literal_formatting_keywords_still_resolves(w):
    assert _scan(GOOD.replace("json.dumps(v)", w))["v"] == "PASS", w


@pytest.mark.parametrize("expr", [
    '"" + ("." if flag else "!")',                                   # nothing precedes the terminator: the value IS a lone punctuation literal
    '"  " + ("." if flag else "?")',
    '"-" + ("." if flag else "!")',                                  # punctuation only before it
    'f"" + ("." if flag else "!")',
])
def test_rb_an_empty_or_punctuation_only_first_operand_keeps_the_terminator_a_finding(expr):
    assert _rb(expr)["problems"], expr


def test_rb_a_real_sentence_before_the_terminator_still_passes():
    assert _rb('"Done " + ("." if flag else "!")')["problems"] == []
    assert _rb('who + ("." if flag else "!")')["problems"] == []               # a computed first operand


# ───────────── review (third pass): the rows iterated are the function's own untouched parameter; the module column list is never changed ─────────────

@pytest.mark.parametrize("name,mutate", [
    ("a call as the iterable", lambda s: s.replace("    for r in rows:\n", "    for r in _ext(rows):\n")),
    ("an attribute as the iterable", lambda s: s.replace("    for r in rows:\n", "    for r in self.rows:\n")),
    ("rows rebound by map", lambda s: s.replace("    for r in rows:\n", "    rows = map(_fill, rows)\n    for r in rows:\n")),
    ("rows rebound by a comprehension assignment", lambda s: s.replace("    for r in rows:\n", "    rows = [dict(x, story='N/A') for x in rows]\n    for r in rows:\n")),
    ("rows augmented", lambda s: s.replace("    for r in rows:\n", "    rows += _more()\n    for r in rows:\n")),
    ("rows mutated by append", lambda s: s.replace("    for r in rows:\n", "    rows.append({'id': 1, 'story': 'N/A', 'payload': {}})\n    for r in rows:\n")),
    ("rows mutated by extend", lambda s: s.replace("    for r in rows:\n", "    rows.extend(_fake())\n    for r in rows:\n")),
    ("iterating a local list not a parameter", lambda s: s.replace("def _insert_rows(conn, rows):", "def _insert_rows(conn, other):").replace("    for r in rows:\n", "    rows = other\n    for r in rows:\n")),
    ("iterating a module constant", lambda s: s.replace("    for r in rows:\n", "    for r in _DEFAULT_ROWS:\n")),
    ("an item store to the module column list", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    _COLUMNS[1] = 'x'\n\n\ndef build_row(n, who):")),
    ("a slice store to the module column list", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    _COLUMNS[:] = ['id']\n\n\ndef build_row(n, who):")),
    ("del of a module column list item", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    del _COLUMNS[0]\n\n\ndef build_row(n, who):")),
    ("append to the module column list", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    _COLUMNS.append('z')\n\n\ndef build_row(n, who):")),
    ("a global rebind of the module column list", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    global _COLUMNS\n    _COLUMNS = ['id']\n\n\ndef build_row(n, who):")),
    ("augmented module column list", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    global _COLUMNS\n    _COLUMNS += ['z']\n\n\ndef build_row(n, who):")),
])
def test_loop_input_and_column_list_escapes_stay_unresolved(name, mutate):
    src = mutate(GOOD)
    assert src != GOOD, name
    ws = _scan(src)
    assert ws["v"] == "PARTIAL" and ws["unresolved"], (name, ws)


def test_the_rows_parameter_form_still_resolves_and_an_unrelated_function_may_use_a_same_named_local():
    assert _scan(GOOD)["v"] == "PASS"
    assert _scan(GOOD + "\n\ndef other(rows):\n    rows = [1]\n    return rows\n")["v"] == "PASS"


# ───────────── review (fourth pass): a call over the row / column list, an alias, and the dynamic namespace ─────────────

def _in_loop(stmt):
    return lambda s: s.replace("            vals.append(v)\n", f"            {stmt}\n            vals.append(v)\n")


@pytest.mark.parametrize("name,mutate", [
    ("operator.setitem on the row", lambda s: s.replace("        vals = []\n", "        operator.setitem(r, 'story', 'n/a')\n        vals = []\n")),
    ("a helper called with the row", lambda s: s.replace("        vals = []\n", "        _fill(r)\n        vals = []\n")),
    ("a keyword argument carrying the row", lambda s: s.replace("        vals = []\n", "        _fill(row=r)\n        vals = []\n")),
    ("setdefault via a call over the rows parameter", lambda s: s.replace("    for r in rows:\n", "    _normalise(rows)\n    for r in rows:\n")),
    ("an alias of the column list then reverse", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    c = _COLUMNS\n    c.reverse()\n\n\ndef build_row(n, who):")),
    ("an alias of the column list in the writer itself", lambda s: s.replace("    placeholders =", "    cols = _COLUMNS\n    placeholders =")),
    ("the column list as a call argument", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    operator.setitem(_COLUMNS, 1, 'x')\n\n\ndef build_row(n, who):")),
    ("sorted in place by a helper", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    _sort_in_place(_COLUMNS)\n\n\ndef build_row(n, who):")),
    ("globals() subscript rebind", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    globals()['_COLUMNS'] = ['id']\n\n\ndef build_row(n, who):")),
    ("globals().update", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    globals().update(_COLUMNS=['id'])\n\n\ndef build_row(n, who):")),
    ("locals() use", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    locals()['x'] = 1\n\n\ndef build_row(n, who):")),
    ("vars() of the module", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    vars(sys.modules[__name__])['_COLUMNS'] = ['id']\n\n\ndef build_row(n, who):")),
    ("the module __dict__", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    sys.modules[__name__].__dict__['_COLUMNS'] = ['id']\n\n\ndef build_row(n, who):")),
    ("exec", lambda s: s.replace("def build_row(n, who):", "def _patch():\n    exec('_COLUMNS = []')\n\n\ndef build_row(n, who):")),
])
def test_loop_call_alias_and_dynamic_namespace_escapes_stay_unresolved(name, mutate):
    src = mutate(GOOD)
    assert src != GOOD, name
    ws = _scan(src)
    assert ws["v"] == "PARTIAL" and ws["unresolved"], (name, ws)


def test_the_two_read_only_uses_of_the_column_list_and_a_harmless_dict_attribute_still_resolve():
    assert _scan(GOOD)["v"] == "PASS"                                                 # len(_COLUMNS) and ', '.join(_COLUMNS) are the statement's own uses
    assert _scan(GOOD + "\n\ndef other(o):\n    return o.__dict__\n")["v"] == "PASS"   # an unrelated object's __dict__ is not the module namespace
