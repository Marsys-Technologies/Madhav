"""test_formgap_scan_limits.py: FORM-GAP item 7 (SS N-191; the detector limits Exec's #3218 left): the writer-source scan (writer_literal_scan.py) resolves three shapes it used to give up on, HONESTLY.

  * bg_compendium_index: `chapter_rows, topic_rows = _build_desired_rows(...)` then `executemany(SQL, chapter_rows)`: the rows are built in a helper, each list from `[]` by `.append((<tuple display>))` and
    returned in a tuple. The scan now follows exactly that shape, position by position (so the f-string that fills `significance` is classified), and refuses everything else with the old reason.
  * ga_vargas: the key name `citation_human` appeared once as a value, in `row.get("citation_human", "")` (a READ in the narration linter). A read cannot make a run-time key appear in a row, so it no longer
    makes every dynamic construct of the file (33 in ga_vargas) a possible supplier of the column.
  * ga_tajaka: the key name appeared once as a member of the literal column list `_COLUMNS`, used only as `len(_COLUMNS)`, `", ".join(_COLUMNS)` (SQL text) and `for c in _COLUMNS: v = r[c]` (a READ index).
    A literal list whose every use is inert can drive no key; any other use (a store, a zip, a call argument, a dict-display key) leaves it a possible key source and the dynamic constructs opaque as before.

Every relaxation has its mutation: the same source with ONE changed use must read unresolved again. The three real writers are pinned at what the scan finds in them today.
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

WLS = ac._lint_module("writer_literal_scan")


def _units(src, name="w.py"):
    tree = ast.parse(textwrap.dedent(src))
    return [dict(rel=name, path=pathlib.Path(name), tree=tree, nodes=[tree], hop=0, via=name)]


def _scan(src, entries=("significance",), table="t"):
    holders = {ac.parse_prose_field(e)[0]: [table] for e in entries}
    return WLS.scan(_units(src), list(entries), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)


# ───────────────────────────── rows returned by a helper through a tuple-unpacking assignment ─────────────────────────────

HELPER = '''
def _build(chunks):
    chapter_rows = []
    topic_rows = []
    for c in chunks:
        chapter_rows.append((c["text_id"], c["chapter"], c["lo"], c["hi"], c["syn"], f"{c['text_id']} chapter {c['chapter']}: {c['n']} passage(s)", 0.5))
    for c in chunks:
        topic_rows.append((c["text_id"], c["topic"], c["lo"], c["hi"], c["syn"], f"{c['text_id']} covers {c['topic']} in {c['n']} passage(s)", 0.5))
    return chapter_rows, topic_rows


def run(conn, chunks):
    chapter_rows, topic_rows = _build(chunks)
    cur = conn.cursor()
    cur.executemany("""INSERT INTO t (text_id, chapter_num, verse_start, verse_end, chunk_ids, summary_text, significance, score)
                       VALUES (%s, %s, %s, %s, ARRAY[]::BIGINT[], %s, %s, %s)""", chapter_rows)
    cur.executemany("""INSERT INTO t (text_id, topic_id, verse_start, verse_end, chunk_ids, summary_text, significance, score)
                       VALUES (%s, %s, %s, %s, ARRAY[]::BIGINT[], %s, %s, %s)""", topic_rows)
'''


def test_the_helper_built_rows_are_followed_position_by_position_and_the_scan_reads_clean():
    r = _scan(HELPER)
    assert r["v"] == "PASS" and r["entries"]["significance"]["writes"] == 2 and r["entries"]["significance"]["sources"] == 2 and not r["problems"] and not r["unresolved"], r


def test_the_position_is_the_placeholder_not_the_column_so_an_array_literal_in_the_values_does_not_shift_it():
    """`ARRAY[]::BIGINT[]` takes the fifth column but no %s: `significance` is the SIXTH placeholder (index 5) = the f-string, and a fallback at THAT index is found."""
    r = _scan(HELPER.replace('f"{c[\'text_id\']} chapter {c[\'chapter\']}: {c[\'n\']} passage(s)"', 'c["sig"] or "n/a"'))
    assert r["v"] == "PARTIAL" and any(p["kind"] == "literal_fallback" for p in r["problems"]), r
    r = _scan(HELPER.replace('c["syn"], f"{c[\'text_id\']} covers', '"a constant synopsis", f"{c[\'text_id\']} covers'))      # a constant at ANOTHER position is not significance's
    assert r["v"] == "PASS", r


@pytest.mark.parametrize("mutate", [
    lambda s: s.replace("    return chapter_rows, topic_rows", "    chapter_rows.extend(topic_rows)\n    return chapter_rows, topic_rows"),         # another way to fill the list
    lambda s: s.replace("    return chapter_rows, topic_rows", "    chapter_rows += topic_rows\n    return chapter_rows, topic_rows"),
    lambda s: s.replace("    return chapter_rows, topic_rows", "    chapter_rows.insert(0, ('x',))\n    return chapter_rows, topic_rows"),
    lambda s: s.replace("    return chapter_rows, topic_rows", "    fill(chapter_rows)\n    return chapter_rows, topic_rows"),               # handed to a callable that could change it
    lambda s: s.replace("    return chapter_rows, topic_rows", "    chapter_rows[0] = ('x',)\n    return chapter_rows, topic_rows"),
    lambda s: s.replace("    return chapter_rows, topic_rows", "    chapter_rows = []\n    return chapter_rows, topic_rows"),                   # initialised twice
    lambda s: s.replace("    chapter_rows = []\n", "    chapter_rows = list(chunks)\n", 1),                                                      # not built from an empty literal
    lambda s: s.replace("    return chapter_rows, topic_rows", "    return chapter_rows, topic_rows, 1"),                                       # the tuple shape differs from the unpacking
    lambda s: s.replace("    return chapter_rows, topic_rows", "    return [], topic_rows"),                                                    # a non-Name element at that position
    lambda s: s.replace("    return chapter_rows, topic_rows", "    if chunks:\n        return chapter_rows, topic_rows\n    return None"),
    lambda s: s.replace("    chapter_rows, topic_rows = _build(chunks)", "    chapter_rows, topic_rows = _build(chunks)\n    chapter_rows.append(('late',))"),                   # the caller adds a row after the helper returned
    lambda s: s.replace("    chapter_rows, topic_rows = _build(chunks)", "    chapter_rows, topic_rows = _build(chunks)\n    chapter_rows, other = _build(chunks)"),                # unpacked twice in the caller
    lambda s: s + "\n\ndef _build(chunks):\n    return [], []\n",                                                                                 # the helper name is defined twice: which one runs is not known
    lambda s: s.replace("    chapter_rows, topic_rows = _build(chunks)", "    chapter_rows, topic_rows = obj.build(chunks)"),                                    # an attribute call is not a resolvable helper
    lambda s: s.replace("    chapter_rows, topic_rows = _build(chunks)", "    (chapter_rows, *topic_rows) = _build(chunks)"),                                   # a starred unpacking
])
def test_MUTATION_any_other_shape_stays_unresolved_with_the_old_reason(mutate):
    r = _scan(mutate(HELPER))
    assert r["v"] == "PARTIAL" and any("positional values not read" in u or "not a literal tuple" in u or "cannot enumerate" in u or "mutates" in u or "no assignment" in u for u in r["unresolved"]), (r["v"], r["unresolved"][:3], r["problems"][:2])


def test_a_fallback_inside_the_helpers_tuple_is_a_problem_not_a_pass():
    r = _scan(HELPER.replace("f\"{c['text_id']} covers {c['topic']} in {c['n']} passage(s)\"", '""'))
    assert r["v"] == "PARTIAL" and r["problems"], r


# ───────────────────────────── a READ of the key is not a key supplier ─────────────────────────────

LINT = '''
SQL = "INSERT INTO t (chart_id, citation_human) VALUES (%(chart_id)s, %(citation_human)s)"

def _rows(items):
    rows = []
    for i in items:
        rows.append({"chart_id": i["c"], "citation_human": f"House {i['h']} lord: {i['l']}"})
    return rows

def _other(items):
    by = {i["name"]: i for i in items}            # a dict comprehension
    m = {}
    for k in items:
        m[k] = 1                                   # a subscript store with a non-literal key
    return by, m

def _check(rows):
    for row in rows:
        ch = row.get("citation_human", "")         # a READ of the key
        if "forbidden" in ch:
            raise ValueError(ch)

def run(conn, items):
    rows = _rows(items)
    _check(rows)
    for row in rows:
        conn.execute(SQL, row)
'''


def test_a_get_read_of_the_key_does_not_make_the_files_dynamic_constructs_suppliers():
    r = _scan(LINT, ("citation_human",))
    assert r["v"] == "PASS" and not r["unresolved"] and r["entries"]["citation_human"]["writes"] == 1, r


@pytest.mark.parametrize("variant", [
    'ch = row.setdefault("citation_human", "")',                                        # a store
    'ch = getattr(row, "citation_human", "")',                                          # not a dict read
    'ch = row.get("citation_human", "", 1)',                                            # not the .get shape
    'ch = row.get("citation_human", default="")',
    'COLS = ["citation_human"]\n        ch = ""',                                      # the name as a list member that is never used inert (an unused list is not proof of anything)
    'ch = str("citation_human")',                                                       # the key name handed to a call
    'ch = {"x": "citation_human"}["x"]',                                                # the key name as a dict VALUE
])
def test_MUTATION_any_other_use_of_the_key_name_makes_the_dynamic_constructs_suppliers_again(variant):
    r = _scan(LINT.replace('ch = row.get("citation_human", "")         # a READ of the key', variant), ("citation_human",))
    assert r["v"] == "PARTIAL" and any("dynamic row construction" in u for u in r["unresolved"]), (variant, r["unresolved"][:2])


# ───────────────────────────── a literal column list that can drive no key ─────────────────────────────

COLS = '''
_COLUMNS = ["chart_id", "citation_human", "computed_at"]


def _build(rows_in):
    by = {r["n"]: r for r in rows_in}               # dynamic constructs in the same file
    seen = {}
    for r in rows_in:
        seen[r["n"]] = 1
    return [{"chart_id": r["c"], "citation_human": f"Muntha in {r['sign']} ({r['n']})", "computed_at": 1} for r in rows_in]


def _insert(conn, rows):
    placeholders = ", ".join(["%s"] * len(_COLUMNS))
    sql = (f"INSERT INTO t ({', '.join(_COLUMNS)}) "
           f"VALUES ({placeholders})")
    for r in rows:
        vals = []
        for c in _COLUMNS:
            v = r[c]
            if c in ("computed_at",):
                v = int(v)
            vals.append(v)
        conn.execute(sql, vals)


def run(conn, rows_in):
    _insert(conn, _build(rows_in))
'''


def test_a_column_list_that_is_only_counted_joined_and_read_by_index_is_inert():
    r = _scan(COLS, ("citation_human",))
    assert r["v"] == "PASS" and not r["unresolved"] and r["entries"]["citation_human"]["writes"] == 1, r


@pytest.mark.parametrize("mutate,why", [
    (lambda s: s.replace("            v = r[c]\n", "            r[c] = r.get(c, '')\n            v = r[c]\n"), "a store keyed by the loop variable"),
    (lambda s: s.replace("            v = r[c]\n", "            r.setdefault(c, '')\n            v = r[c]\n"), "setdefault keyed by the loop variable"),
    (lambda s: s.replace("            v = r[c]\n", "            v = getattr(r, c)\n"), "the loop variable handed to getattr"),
    (lambda s: s.replace("            v = r[c]\n", "            r.update({c: 1})\n            v = r[c]\n"), "a dict display keyed by the loop variable"),
    (lambda s: s.replace("            v = r[c]\n", "            r = {**r, c: 1}\n            v = r[c]\n"), "a re-wrapped row"),
    (lambda s: s.replace("    sql = (f\"INSERT", "    d = dict(zip(_COLUMNS, [0, 0, 0]))\n    sql = (f\"INSERT"), "the list zipped into a dict"),
    (lambda s: s.replace("    sql = (f\"INSERT", "    cols = _COLUMNS\n    sql = (f\"INSERT"), "the list aliased"),
    (lambda s: s.replace("    sql = (f\"INSERT", "    register(_COLUMNS)\n    sql = (f\"INSERT"), "the list handed to a callable"),
    (lambda s: s.replace("    placeholders = ", "    extra = {c: None for c in _COLUMNS}\n    placeholders = "), "a dict comprehension keyed by the list"),
    (lambda s: s.replace("    placeholders = ", "    cols2 = [c for c in _COLUMNS]\n    placeholders = "), "the list iterated into another list"),
    (lambda s: s.replace("_COLUMNS = [", "_COLUMNS = x = ["), "the list bound to a second name"),
    (lambda s: s + "\n_COLUMNS = _COLUMNS + ['extra']\n", "the list reassigned"),
])
def test_MUTATION_any_other_use_of_the_column_list_leaves_it_a_possible_key_source(mutate, why):
    """The resolver's own judgement (the key name is still an enumerated value) AND the end result (the scan is no longer clean)."""
    src = mutate(COLS)
    assert WLS._Scope(_units(src)).enumerated("citation_human"), why
    assert _scan(src, ("citation_human",))["v"] == "PARTIAL", why


def test_the_unmutated_list_is_inert_by_the_resolvers_own_judgement():
    assert WLS._Scope(_units(COLS)).enumerated("citation_human") == []


# ───────────────────────────── the three real writers, pinned at what the scan finds in them ─────────────────────────────

def _real(aid, table, entries):
    files = ac.registered_ids("")[aid]
    units, beyond = ac.writer_scan_scope(aid, files)
    holders = {ac.parse_prose_field(e)[0]: [table] for e in entries}
    return WLS.scan(units, list(entries), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field, beyond=beyond), units


def test_REAL_WRITER_bg_compendium_index_reads_clean_on_significance():
    r, _u = _real("bg_compendium_index", "brahma_compendium_index", ["significance"])
    assert r["v"] == "PASS" and r["entries"]["significance"]["writes"] == 2 and r["entries"]["significance"]["sources"] == 2 and not r["unresolved"] and not r["problems"], r


def test_REAL_WRITER_ga_tajaka_reads_clean_on_citation_human():
    r, _u = _real("ga_tajaka", "l1_tajik_varsha_year_lords", ["citation_human"])
    assert r["v"] == "PASS" and r["entries"]["citation_human"]["writes"] == 1 and not r["unresolved"] and not r["problems"], r


def test_REAL_WRITER_ga_vargas_has_exactly_one_finding_left_the_d81_sentinel_constant():
    """What remains in ga_vargas is a CONSTANT, not a dynamic row: the scope-cap sentinel row for D81 writes the fixed sentence at ga_vargas_writer.py:3327. No dynamic-row finding is left."""
    r, _u = _real("ga_vargas", "chart_divisionals", ["citation_human"])
    assert r["v"] == "PARTIAL" and not r["unresolved"], r["unresolved"]
    assert [(p["kind"], p["where"].rsplit(":", 1)[0], "D81" in p["text"]) for p in r["problems"]] == [("constant_write", "ga_writers/ga_vargas_writer.py", True)], r["problems"]


def test_REAL_WRITER_ga_vargas_mutation_a_second_use_of_the_key_as_a_value_brings_the_dynamic_rows_back():
    path = ac.SIDECAR / "ga_writers" / "ga_vargas_writer.py"
    src = path.read_text(encoding="utf-8")
    assert src.count('row.get("citation_human", "")') == 1
    tree_units, _ = ac.writer_scan_scope("ga_vargas", ac.registered_ids("")["ga_vargas"])
    base = [u for u in tree_units if u["rel"].endswith("ga_vargas_writer.py")]
    mutated = ast.parse(src.replace('row.get("citation_human", "")', 'row.setdefault("citation_human", "")'))
    units = [dict(u, tree=mutated, nodes=[mutated]) if u in base else u for u in tree_units]
    got = WLS.scan(units, ["citation_human"], {"citation_human": ["chart_divisionals"]}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)
    assert any("dynamic row construction" in u for u in got["unresolved"]), got["unresolved"][:2]
