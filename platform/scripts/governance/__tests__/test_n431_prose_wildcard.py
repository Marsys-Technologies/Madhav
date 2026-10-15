"""test_n431_prose_wildcard.py: SS N-448/N-450. The object-key wildcard `*` of the prose path grammar.

bo_chart_gestalt's `domain_verdict_map_jsonb` is an object keyed by domain, so the prose path grammar could not name its `verdict_note` leaves and the whole-column
declaration yielded zero checkable rows (the Null `clean` flag needs >= 1 checkable row per declared entry). `col.$.*.leaf` reads "every member value of the object
at this level". The grammar is opt-in (no existing path changes meaning), object-key only (no recursive descent), at most ONE `*` per path, never beside a `[*]`, and a
key literally named `*` cannot be declared.

Every consumer of the path grammar either handles the wildcard or refuses it by name; this file pins each:
  * parse / validate (parse_prose_field, validate_declarations: overlap with literal keys),
  * the row-count SQL (golden strings; a fake-psql end-to-end through prose_row_counts -> Narr.checkable -> Null.blank_rows `clean`; ONE real-Postgres test),
  * label_columns (label_distinct_sql, label_stray_sql, label_read, label_columns_problem): REFUSED,
  * the writer scan (writer_literal_scan.py) and the fidelity-test leaf: the wildcard is never the traced key,
  * writer_constant_phrases: an opaque declared-entry string, so a wildcard entry works by identity,
  * census_postprocess: the entry text is carried through the named-ceiling patterns.

The fake psql answers from a small PURE-PYTHON reference model of the documented semantics (`ref_counts`); the same CASES table is replayed against a real jsonb by
`test_real_pg_*` (a disposable cluster, skipped only when no PostgreSQL binaries exist), which is what ties the model to the SQL.

Run (no database):  python -m pytest platform/scripts/governance/__tests__/test_n431_prose_wildcard.py -q -k "not real_pg"
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import census_postprocess as cp  # noqa: E402

from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture: a throw-away loopback Postgres)

WLS = ac._lint_module("writer_literal_scan")
PEV = dict(prose_fields="writer file.py:1: composed / stores source text")
STAR = ac.PROSE_KEY_WILDCARD


def _doc(**assets):
    return dict(version="1.0.0", kind_enum=list(ac.DECLARED_KINDS), assets=assets)


def _validate(*fields):
    ac.validate_declarations(_doc(a=dict(prose_fields=list(fields), evidence=PEV)))


# ───────────────────────────── grammar: parse ─────────────────────────────

@pytest.mark.parametrize("entry,expected", [
    ("d.$.*.note", ("d", ("*", "note"))),                                   # wildcard at the root level of the column
    ("domain_verdict_map_jsonb.$.*.verdict_note", ("domain_verdict_map_jsonb", ("*", "verdict_note"))),
    ("d.$.a.*.b", ("d", ("a", "*", "b"))),                                  # wildcard after a key
    ("d.$.a.b.*.c.d", ("d", ("a", "b", "*", "c", "d"))),
    ("d.$.*", ("d", ("*",))),                                               # wildcard as the only / last segment: every member is itself the string
    ("d.$.a.*", ("d", ("a", "*"))),
    ("d.$.a[*]", ("d", ("a", "[*]"))),                                      # the array form is unchanged
    ("d.$.a[*].b", ("d", ("a", "[*]", "b"))),
    ("d.$.a.b", ("d", ("a", "b"))),
    ("d", ("d", None)),
])
def test_parse_prose_field_good(entry, expected):
    assert ac.parse_prose_field(entry) == expected


def test_the_two_wildcard_tokens_are_distinct_and_never_an_identifier():
    assert ac.PROSE_KEY_WILDCARD == "*" and ac.PROSE_WILDCARD == "[*]" and ac.PROSE_KEY_WILDCARD != ac.PROSE_WILDCARD
    assert not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", ac.PROSE_KEY_WILDCARD)


@pytest.mark.parametrize("entry,why", [
    ("d.$.*.*", "at most ONE"),                                             # double wildcard
    ("d.$.*.a.*", "at most ONE"),
    ("d.$.a.*.b.*.c", "at most ONE"),
    ("d.$.*.a[*]", "no `[*]`"),                                             # one wildcard per path, either kind
    ("d.$.a[*].*", "no `[*]`"),
    ("d.$.a[*].b.*", "no `[*]`"),
    ("d.$.a*.b", "whole path segment"),                                     # `*` inside a key
    ("d.$.*a.b", "whole path segment"),
    ("d.$.a.b*", "whole path segment"),
    ('d.$."*"', "whole path segment"),                                      # a literal key named "*" cannot be declared
    ("d.$.'*'.b", "whole path segment"),
    ("d.$.**", "whole path segment"),
    ("d.$.*[*]", "whole path segment"),
    ("d.$.a[**].b", "whole path segment"),
])
def test_parse_prose_field_refuses_each_malformed_star_by_name(entry, why):
    with pytest.raises(ac.DeclarationsError, match=re.escape(why)):
        ac.parse_prose_field(entry)


@pytest.mark.parametrize("entry", [
    "*", "*.$.a", "d.*.a", "d.$*.a", "d$.*.a", "d.$..*", "d.$.*.", "d.$.*..a", ".d.$.*", "d.$.*\n", "d.$.* .a", "d.$. *.a", "d.$.a.*\n",
    "d.$.[*]", "d.$.*.1a", "t.d.$.*", "d.$.＊", "d.$.*​", "d.$.a.$.*", "d[*].$.*", "", None, 1, ["d.$.*"],
])
def test_parse_prose_field_still_refuses_everything_else(entry):
    with pytest.raises(ac.DeclarationsError):
        ac.parse_prose_field(entry)


def test_wildcard_identifiers_keep_the_128_character_cap():
    ok = "c" * 128 + ".$.*." + "m" * 128
    assert ac.parse_prose_field(ok) == ("c" * 128, ("*", "m" * 128))
    for bad in ("c" * 129 + ".$.*.m", "c.$.*." + "m" * 129, "c.$." + "k" * 129 + ".*"):
        with pytest.raises(ac.DeclarationsError):
            ac.parse_prose_field(bad)


@pytest.mark.parametrize("entry,leaf", [("d.$.*.note", "note"), ("d.$.a.*", "a"), ("d.$.*", "d"), ("d.$.a[*]", "a"), ("d.$.a[*].b", "b"), ("d.$.x.*.y.z", "z"), ("d", "d")])
def test_prose_entry_leaf_is_never_the_wildcard(entry, leaf):
    assert ac.prose_entry_leaf(entry) == leaf


# ───────────────────────────── grammar: validate_declarations ─────────────────────────────

def test_a_declaration_may_name_the_wildcard_path():
    _validate("domain_verdict_map_jsonb.$.*.verdict_note", "headline_jsonb.$.note")
    _validate("d.$.*.a", "d.$.*.b")                                        # siblings under one wildcard are not overlaps
    _validate("d.$.*.a", "e.$.*.a")                                        # the same path under another column
    _validate("d.$.a.*", "d.$.b.*")


def test_the_validator_refuses_a_malformed_star_with_the_named_reason():
    for bad, why in (("d.$.*.*", "at most ONE"), ("d.$.*.a[*]", "no `[*]`"), ('d.$."*"', "whole path segment")):
        with pytest.raises(ac.DeclarationsError, match=re.escape(why)):
            _validate("x", bad)


@pytest.mark.parametrize("a,b", [
    ("d.$.*.note", "d.$.career.note"),            # the wildcard can name the same leaf as a literal key
    ("d.$.career.note", "d.$.*.note"),
    ("d.$.*", "d.$.career.note"),                 # a path and its sub-path
    ("d.$.*.note", "d.$.*.note"),                 # equal
    ("d", "d.$.*.note"),                          # the whole column covers it (the old gestalt declaration)
    ("d.$.*.note", "d"),
    ("D.$.*.Note", "d.$.x.note"),                 # case-insensitively
    ("d.$.a.*", "d.$.a.b.c"),
])
def test_a_wildcard_path_overlaps_what_it_can_match(a, b):
    with pytest.raises(ac.DeclarationsError, match="overlap"):
        _validate(a, b)


def test_a_wildcard_path_does_not_overlap_an_array_level_or_a_different_leaf():
    _validate("d.$.*.note", "d.$.a[*].note")      # an object level and an array level are not the same node
    _validate("d.$.a.*", "d.$.a[*]")
    _validate("d.$.*.note", "d.$.*.other")
    _validate("d.$.*.note", "e")


# ───────────────────────────── SQL builder: golden strings ─────────────────────────────

WS_TRIM = "'^[\\s\\u00A0\\u200B\\u2000-\\u200A\\uFEFF]+|[\\s\\u00A0\\u200B\\u2000-\\u200A\\uFEFF]+$', '', 'g'"
PLACEHOLDERS = "'', 'n/a', 'na', 'none', 'null', 'unknown', 'tbd', '-', '--', 'undefined', 'nan'"

GOLDEN_FROM = {
    "d.$.*.verdict_note": ("(SELECT v FROM jsonb_each(CASE WHEN jsonb_typeof(\"d\"::jsonb) = 'object' THEN \"d\"::jsonb ELSE '{}'::jsonb END) AS w0(k, v) ORDER BY k LIMIT 256) AS w",
                           "(w.v #> '{verdict_note}')"),
    "d.$.m.*.note": ("(SELECT v FROM jsonb_each(CASE WHEN jsonb_typeof((\"d\"::jsonb #> '{m}')) = 'object' THEN (\"d\"::jsonb #> '{m}') ELSE '{}'::jsonb END) AS w0(k, v) ORDER BY k LIMIT 256) AS w",
                     "(w.v #> '{note}')"),
    "d.$.*": ("(SELECT v FROM jsonb_each(CASE WHEN jsonb_typeof(\"d\"::jsonb) = 'object' THEN \"d\"::jsonb ELSE '{}'::jsonb END) AS w0(k, v) ORDER BY k LIMIT 256) AS w", "w.v"),
    "d.$.m.n.*.a.b": ("(SELECT v FROM jsonb_each(CASE WHEN jsonb_typeof((\"d\"::jsonb #> '{m,n}')) = 'object' THEN (\"d\"::jsonb #> '{m,n}') ELSE '{}'::jsonb END) AS w0(k, v) ORDER BY k LIMIT 256) AS w",
                      "(w.v #> '{a,b}')"),
}


@pytest.mark.parametrize("entry", sorted(GOLDEN_FROM))
def test_the_key_wildcard_source_is_pinned(entry):
    col, path = ac.parse_prose_field(entry)
    assert ac._key_wildcard_source(col, path) == GOLDEN_FROM[entry]


def test_the_cap_is_256_and_is_the_literal_limit():
    assert ac.PROSE_KEY_WILDCARD_CAP == 256
    assert "ORDER BY k LIMIT 256) AS w" in GOLDEN_FROM["d.$.*"][0]


def test_the_full_row_count_sql_for_the_gestalt_entry_is_pinned():
    frm, leaf = GOLDEN_FROM["d.$.*.verdict_note"]
    src = f"EXISTS (SELECT 1 FROM {frm} WHERE jsonb_typeof({leaf}) = 'string' AND lower(regexp_replace({leaf} #>> '{{}}', {WS_TRIM})) "
    want = (f"SELECT count(*) FILTER (WHERE {src}NOT IN ({PLACEHOLDERS})))::text, count(*) FILTER (WHERE {src}IN ({PLACEHOLDERS})))::text "
            "FROM bodha_chart_gestalt WHERE chart_id = 'x'")
    got = ac.prose_row_counts_sql("bodha_chart_gestalt", ["d.$.*.verdict_note"], " WHERE chart_id = 'x'")
    assert got == want.replace('"d"', '"d"')
    got2 = ac.prose_row_counts_sql("bodha_chart_gestalt", ["domain_verdict_map_jsonb.$.*.verdict_note"], " WHERE chart_id = 'x'")
    assert got2 == want.replace('"d"', '"domain_verdict_map_jsonb"')


def test_the_sql_carries_no_text_beyond_identifiers_and_the_integer_cap():
    sql = ac.prose_row_counts_sql("t", ["d.$.m.*.note"], "")
    stripped = sql.replace(WS_TRIM, "").replace(PLACEHOLDERS, "")
    # a key only ever appears inside a '{k,k}' text[] literal (identifier characters only)
    assert set(re.findall(r"'\{([^}']*)\}'", stripped)) == {"", "m", "note"}
    assert "%s" not in sql and "$1" not in sql and ";" not in sql
    assert sql.count("LIMIT 256") == 2 and sql.count("count(*) FILTER") == 2


def test_the_existing_forms_are_unchanged_byte_for_byte():
    sql = ac.prose_row_counts_sql("t", ["statement", "narrative.$.headline", "d.$.items[*].reason"], " WHERE chart_id = 'x'")
    assert "jsonb_path_query(\"d\"::jsonb, '$.\"items\"[*].\"reason\"')" in sql
    assert "(\"narrative\"::jsonb #>> '{headline}')" in sql and "jsonb_each" not in sql


@pytest.mark.parametrize("bad", [("d", ("a",)), ("d", ("*", "*")), ("d", ("*", "[*]")), ("d", ("[*]",))])
def test_the_source_builder_refuses_a_path_that_is_not_exactly_one_key_wildcard(bad):
    with pytest.raises(ValueError):
        ac._key_wildcard_source(*bad)


def test_row_counts_sql_still_rejects_an_unsafe_identifier_around_a_wildcard():
    for e in ['a"; DROP TABLE x; --.$.*.b', "d.$.*.b'; DROP TABLE x; --", "d.$.*.b)--"]:
        with pytest.raises((ValueError, ac.DeclarationsError)):
            ac.prose_row_counts_sql("t", [e], "")


# ───────────────────────────── reference model + cases ─────────────────────────────
# (doc, entry, checkable, blank): ONE table row per case, counted by prose_row_counts_sql's FILTERs.

def ref_counts(doc, entry, jsonb_type=True):
    """The documented semantics, pure Python: a row is CHECKABLE when some member (first PROSE_KEY_WILDCARD_CAP, in key order) of the object at the keys before the `*` carries, at the keys
    after it, a JSON string that is not blank / a placeholder; BLANK when it carries one that is. A non-object level, a missing key, a non-string leaf and an array in place of an object yield nothing."""
    col, path = ac.parse_prose_field(entry)
    if path is None:
        leaves = [doc] if (jsonb_type and isinstance(doc, str)) else []
    elif STAR not in path:                                                  # a plain key path (the reference model has no `[*]`)
        v = doc
        for k in path:
            v = v.get(k) if isinstance(v, dict) else None
        leaves = [v]
    else:
        i = path.index(STAR)
        node = doc
        for k in path[:i]:
            node = node.get(k) if isinstance(node, dict) else None
        members = [node[k] for k in sorted(node)[:ac.PROSE_KEY_WILDCARD_CAP]] if isinstance(node, dict) else []
        leaves = []
        for v in members:
            for k in path[i + 1:]:
                v = v.get(k) if isinstance(v, dict) else None
            leaves.append(v)
    strs = [re.sub(ac._WS_TRIM_PY, "", x).lower() for x in leaves if isinstance(x, str)]
    return int(any(x not in ac.PROSE_PLACEHOLDERS for x in strs)), int(any(x in ac.PROSE_PLACEHOLDERS for x in strs))


G = "c.$.*.verdict_note"
BIG = {f"k{i}": "n/a" for i in range(300)}
CASES = [
    # the gestalt shape: a domain-keyed object whose members carry the leaf
    ({"career": {"verdict_note": "x"}, "wealth": {"verdict_note": "y"}}, G, 1, 0),
    ({"career": {"verdict_note": "x", "score": 2}}, G, 1, 0),
    # honest zeros: the leaf is absent, not a string, or the level is not an object
    ({"career": {"other": "x"}, "wealth": {}}, G, 0, 0),
    ({"career": {"verdict_note": 5}, "wealth": {"verdict_note": None}, "health": {"verdict_note": ["x"]}}, G, 0, 0),
    ({"career": "verdict_note"}, G, 0, 0),                                  # the member is a string: no key `verdict_note` inside it
    ({"career": [{"verdict_note": "x"}]}, G, 0, 0),                         # an array member is NOT unwrapped (strict, not lax)
    ([{"verdict_note": "x"}], G, 0, 0),                                     # the root is an array, not an object
    ("verdict_note", G, 0, 0),
    (None, G, 0, 0),
    (5, G, 0, 0),
    ({}, G, 0, 0),
    # blank / placeholder strings are counted as blank, never checkable
    ({"career": {"verdict_note": "N/A"}}, G, 0, 1),
    ({"career": {"verdict_note": "    "}}, G, 0, 1),
    ({"career": {"verdict_note": "fine"}, "wealth": {"verdict_note": "tbd"}}, G, 1, 1),
    # a nested level before the wildcard
    ({"m": {"a": {"note": "t"}, "b": {"note": "n/a"}}}, "c.$.m.*.note", 1, 1),
    ({"m": ["x"]}, "c.$.m.*.note", 0, 0),
    ({"m": "x"}, "c.$.m.*.note", 0, 0),
    ({"n": {"a": {"note": "t"}}}, "c.$.m.*.note", 0, 0),
    # the wildcard is the last segment: every member is itself the string
    ({"a": "hello", "b": "tbd"}, "c.$.*", 1, 1),
    ({"a": {"x": "y"}}, "c.$.*", 0, 0),
    ({"a": 1}, "c.$.*", 0, 0),
    # the cap: only the first 256 members in key order are read ('zzz' sorts after all of k0..k299)
    ({k: {"note": "n/a"} for k in BIG} | {"zzz": {"note": "a real sentence"}}, "c.$.*.note", 0, 1),
    ({f"k{i:03d}": {"note": "n/a"} for i in range(255)} | {"k255": {"note": "a real sentence"}}, "c.$.*.note", 1, 1),
]


@pytest.mark.parametrize("doc,entry,checkable,blank", CASES)
def test_the_reference_model_matches_the_pinned_expectations(doc, entry, checkable, blank):
    assert ref_counts(doc, entry) == (checkable, blank)


# ───────────────────────────── fake-connection end to end ─────────────────────────────

DVM = "domain_verdict_map_jsonb"
ENTRY = f"{DVM}.$.*.verdict_note"
OTHER = "headline_jsonb.$.note"


class FakeDb:
    """A fake psql() over in-memory rows: records the SQL it is handed and answers from the reference model, one (checkable, blank) pair per entry in the SQL's own order."""

    def __init__(self, rows):
        self.rows, self.seen = rows, []

    def __call__(self, sql, *a, **k):
        self.seen.append(sql)
        out = []
        for entry in self.entries:
            col, path = ac.parse_prose_field(entry)
            counts = [ref_counts(r[col], entry) for r in self.rows]
            out += [str(sum(c[0] for c in counts)), str(sum(c[1] for c in counts))]
        return [out]


def _run(monkeypatch, rows, entries):
    db = FakeDb(rows)
    db.entries = list(entries)
    monkeypatch.setattr(ac, "psql", db)
    counts = ac.prose_row_counts("bodha_chart_gestalt", list(entries), " WHERE chart_id = 'x'", {c: "jsonb" for c in {ac.parse_prose_field(e)[0] for e in entries}})
    assert len(db.seen) == 1 and db.seen[0] == ac.prose_row_counts_sql("bodha_chart_gestalt", list(entries), " WHERE chart_id = 'x'", {c: "jsonb" for c in {ac.parse_prose_field(e)[0] for e in entries}})
    return {e: dict(v, scope="chart_id = 'x'") for e, v in counts.items()}


GESTALT_ROWS = [
    {DVM: {"career": {"verdict_note": "x"}, "wealth": {"verdict_note": "y"}}, "headline_jsonb": {"note": "n"}},
    {DVM: {"career": {"verdict_note": "z"}}, "headline_jsonb": {"note": "m"}},
    {DVM: {"career": {"score": 1}}, "headline_jsonb": {"note": "o"}},                # an object lacking the leaf: honest zero
]


def test_a_gestalt_shaped_column_yields_checkable_rows_and_null_clean_can_be_computed(monkeypatch):
    counts = _run(monkeypatch, GESTALT_ROWS, [ENTRY, OTHER])
    assert counts[ENTRY]["checkable"] == 2 and counts[ENTRY]["blank"] == 0
    assert counts[OTHER]["checkable"] == 3
    chk = ac.grade_narr_checkable([ENTRY, OTHER], counts)
    assert chk["v"] == ac.PASS and chk["checkable"][ENTRY] == 2, chk
    blank = ac.grade_null_blank_rows([ENTRY, OTHER], counts)
    assert blank["v"] == ac.PARTIAL and blank.get("clean") is True, blank


def test_the_old_whole_column_declaration_cannot_reach_clean(monkeypatch):
    counts = _run(monkeypatch, GESTALT_ROWS, [DVM, OTHER])
    assert counts[DVM] == dict(checkable=0, blank=0, scope="chart_id = 'x'")                    # a JSON object is not a string: zero checkable rows
    blank = ac.grade_null_blank_rows([DVM, OTHER], counts)
    assert "clean" not in blank, blank
    chk = ac.grade_narr_checkable([DVM, OTHER], counts)
    assert chk["v"] == ac.PARTIAL and "none or unknown on " + DVM in chk["measured"], chk


def test_objects_without_the_leaf_yield_zero_rows_and_clean_stays_off(monkeypatch):
    rows = [{DVM: {"career": {"other": "x"}}, "headline_jsonb": {"note": "n"}}, {DVM: {}, "headline_jsonb": {"note": "n"}}]
    counts = _run(monkeypatch, rows, [ENTRY, OTHER])
    assert counts[ENTRY]["checkable"] == 0
    assert "clean" not in ac.grade_null_blank_rows([ENTRY, OTHER], counts)
    assert "none or unknown on " + ENTRY in ac.grade_narr_checkable([ENTRY, OTHER], counts)["measured"]


def test_a_non_object_at_the_wildcard_level_yields_zero_rows(monkeypatch):
    rows = [{DVM: [{"verdict_note": "x"}], "headline_jsonb": {"note": "n"}}, {DVM: "verdict_note", "headline_jsonb": {"note": "n"}}, {DVM: None, "headline_jsonb": {"note": "n"}}]
    counts = _run(monkeypatch, rows, [ENTRY, OTHER])
    assert counts[ENTRY]["checkable"] == 0 and counts[ENTRY]["blank"] == 0
    assert "clean" not in ac.grade_null_blank_rows([ENTRY, OTHER], counts)


def test_a_placeholder_leaf_is_a_blank_row_and_fails_null(monkeypatch):
    rows = [{DVM: {"career": {"verdict_note": "TBD"}}, "headline_jsonb": {"note": "n"}}]
    counts = _run(monkeypatch, rows, [ENTRY, OTHER])
    assert counts[ENTRY]["blank"] == 1
    assert ac.grade_null_blank_rows([ENTRY, OTHER], counts)["v"] == ac.FAIL


def test_zero_checkable_rows_everywhere_is_inconclusive_never_pass(monkeypatch):
    counts = _run(monkeypatch, [{DVM: {}, "headline_jsonb": None}], [ENTRY, OTHER])
    chk = ac.grade_narr_checkable([ENTRY, OTHER], counts)
    assert chk["v"] == ac.NO_DET and chk.get("inconclusive") is True


# ───────────────────────────── label_columns: REFUSED ─────────────────────────────

LABEL_ENTRY = "d.$.*.kind"


def test_label_sql_builders_refuse_the_key_wildcard_instead_of_reading_it_as_a_key():
    for fn, args in ((ac.label_distinct_sql, ("t", LABEL_ENTRY)), (ac.label_stray_sql, ("t", LABEL_ENTRY, ["a"])), (ac.label_distinct_sql, ("t", "d.$.*"))):
        with pytest.raises(ValueError, match="object-key wildcard"):
            fn(*args)
    assert "{a,b}" in ac.label_distinct_sql("t", "d.$.a.b") and "[*]" in ac.label_distinct_sql("t", "d.$.a[*]")        # the supported forms still build


def test_label_read_never_issues_a_read_for_a_wildcard_entry(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("psql must not be reached for a wildcard label entry")
    monkeypatch.setattr(ac, "psql", boom)
    monkeypatch.setattr(ac, "_scope_block", lambda t: None)
    assert ac.label_read("t", LABEL_ENTRY, ["a"]) is None             # "not read" (PARTIAL), never a read of a literal `*` key


def test_label_columns_problem_refuses_the_key_wildcard_by_name():
    d = dict(column=LABEL_ENTRY, values=["a", "b"], why="a graded one-word label chosen by the writer", evidence="platform/python-sidecar/x.py:1")
    bad = ac.label_columns_problem(dict(label_columns=[d]))
    assert bad and "object-key wildcard" in bad and "label_columns[0].column" in bad
    bad2 = ac.label_columns_problem(dict(label_columns=[dict(d, column="d.$.*")]))
    assert bad2 and "object-key wildcard" in bad2


def test_the_declarations_validator_refuses_a_wildcard_label_column():
    e = dict(prose_fields=["x"], evidence=PEV, label_columns=[dict(column=LABEL_ENTRY, values=["a"], why="a graded one-word label chosen by the writer", evidence="w.py:1")])
    with pytest.raises(ac.DeclarationsError, match="object-key wildcard"):
        ac.validate_declarations(_doc(a=e))


# ───────────────────────────── writer scan, fidelity leaf, constant phrases, postprocess ─────────────────────────────

WRITER = '''
def run(conn, v):
    cur = conn.cursor()
    cur.execute("INSERT INTO t (d) VALUES (%s)", (json.dumps({"career": {"note": v}}),))
'''


def _scan(entry):
    tree = ast.parse(textwrap.dedent(WRITER))
    units = [dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")]
    return WLS.scan(units, [entry], {"d": ["t"]}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)


def test_the_writer_scan_traces_the_real_key_never_the_wildcard():
    for entry, key in (("d.$.*.verdict_note", "verdict_note"), ("d.$.absent_key.*", "absent_key")):
        res = _scan(entry)
        msgs = " | ".join(res["unresolved"])
        assert f"nested key '{key}'" in msgs and "nested key '*'" not in msgs, (entry, res["unresolved"])


def test_the_writer_scan_does_not_crash_on_a_lone_wildcard_and_says_so():
    res = _scan("d.$.*")
    assert any("no nested key to trace" in u for u in res["unresolved"]) and res["v"] == "PARTIAL"


def test_the_fidelity_structural_reading_does_not_crash_on_wildcard_entries():
    got = ac._narr_fidelity_structural(["d.$.*", "d.$.a.*", "d.$.*.note"], "platform/python-sidecar/pipeline/orchestrator/writers/bo_chart_gestalt.py:1", [])
    assert got["v"] in (ac.FAIL, ac.NO_DET, ac.PARTIAL)


def test_writer_constant_phrases_carries_a_wildcard_entry_by_identity():
    lit = "The domain verdict is a reading."
    src = f'def f():\n    return {{"career": {{"verdict_note": "{lit}"}}}}\n'
    tree = ast.parse(src)
    units = [dict(rel="w.py", tree=tree)]
    item = dict(file="w.py", entry=ENTRY, form="constant_write", literal=lit, why="the constant sentence the writer stores per domain", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_chart_gestalt.py:277")
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[item])) is None
    ws = dict(problems=[dict(where="w.py:2", entry=ENTRY, kind="constant_write", text=f"the column is written a literal: {lit!r}")])
    got = ac.constant_phrases_check([item], [ENTRY], ws, units)
    assert got["problems"] == [] and got["covered"] == {0: 1} and got["left"] == [], got
    # the entry must still be one of the declared prose entries, wildcard or not
    assert ac.constant_phrases_check([item], ["other.$.note"], ws, units)["problems"]


def test_the_named_ceiling_pattern_carries_a_wildcard_entry_text():
    text = f"checkable rows per declared entry: headline_jsonb.$.note=3, {ENTRY}=0; none or unknown on {ENTRY}"
    got = cp.m_checkable_unknown("bo_chart_gestalt", text)
    assert got and ENTRY in got


# ───────────────────────────── real Postgres: the SQL against real jsonb semantics ─────────────────────────────

@pytest.fixture
def real_pg(disposable_pg, monkeypatch):
    point_psql_at(disposable_pg, monkeypatch)
    ident = ac.psql("SELECT inet_server_port()::text, current_database()")
    assert ident == [[str(disposable_pg.port), disposable_pg.dbname]], f"refusing to run: not the disposable cluster ({ident!r})"
    return disposable_pg


def test_real_pg_key_wildcard_counts_match_jsonb_semantics(real_pg):
    """Every CASES row is inserted as a real jsonb and counted by the GENERATED SQL; the answer must equal the pinned expectation (the same one the reference model reproduces). NOT run in the
    worker that wrote it (no cluster is started there): this test is what ties the model to the SQL."""
    real_pg.psql("DROP TABLE IF EXISTS public.n431_wc")
    real_pg.psql("CREATE TABLE public.n431_wc (id integer PRIMARY KEY, c jsonb)")
    for i, (doc, entry, checkable, blank) in enumerate(CASES):
        real_pg.psql("INSERT INTO public.n431_wc VALUES (%d, $j$%s$j$::jsonb)" % (i, json.dumps(doc)))
    try:
        for i, (doc, entry, checkable, blank) in enumerate(CASES):
            got = ac.prose_row_counts("n431_wc", [entry], f" WHERE id = {i}", {"c": "jsonb"})[entry]
            assert (got["checkable"], got["blank"]) == (checkable, blank), (i, doc if len(json.dumps(doc)) < 200 else "(large)", entry, got)
        # all rows at once: the sums are the per-row sums (the FILTER counts rows, one per case)
        every = ac.prose_row_counts("n431_wc", [G], "", {"c": "jsonb"})[G]
        assert every["checkable"] == sum(c for d, e, c, b in CASES if e == G) and every["blank"] == sum(b for d, e, c, b in CASES if e == G)
    finally:
        real_pg.psql("DROP TABLE IF EXISTS public.n431_wc")
