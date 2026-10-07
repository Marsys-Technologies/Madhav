"""test_ss_json_leaf_uuid.py -- prose_none.closed_columns[].json_leaf_patterns: `kind: uuid` and the object-key wildcard `.*` (SS residual, W3).

L2 jsonb columns hold UUID POINTER leaves (signal ids, cell ids, node ids: bo_drishti `$.signal_ids[*]`, `$.ranked_signals[*].signal_id`, `$.wildcard_signals[*].signal_id`) and data-derived DOMAIN-NAME keys
over a constant sub-key (`$.domain_verdict_map.*.verdict_note`). Both close a path against the DATA, exactly like the timestamp kinds: a string leaf at a declared path must be shaped like its kind
(or be in its closed `values`), any other string leaf in the column is outside the closure. Real SQL on a DISPOSABLE cluster (as A's tests in test_n150_prose_none.py); shape rules offline.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n150_prose_none as n150  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

U1 = "0b6c1a52-4f0e-4c47-9d0e-3a1f8e7b2c11"
U2 = "d3f1b7a0-8c64-4e9a-a1b2-5c7d9e0f1a22"
P = ac.prose_none_problem


def _col(*items, column="payload"):
    return dict(column=column, json_leaf_patterns=list(items), why="the payload's only string leaves are pointer uuids and a closed verdict vocabulary")


def _d(*items):
    return n150._decl(_col(*items))


# ───────────── shape ─────────────

def test_uuid_kind_and_wildcard_paths_are_accepted():
    assert P(_d(dict(path="$.signal_ids[*]", kind="uuid"), dict(path="$.ranked_signals[*].signal_id", kind="uuid"))) is None
    assert P(_d(dict(path="$.domain_verdict_map.*.verdict_note", values=["strong", "weak"]))) is None
    assert P(_d(dict(path="$.m.*[*].id", kind="uuid"))) is None
    assert "uuid" in ac.PROSE_NONE_LEAF_KINDS and "uuid" in P(_d(dict(path="$.a", kind="guid")))


@pytest.mark.parametrize("path", ["$.*", "$.a.*", "$.*.*.x", "$.a.*.b"])
def test_wildcard_forms_that_are_valid(path):
    assert P(_d(dict(path=path, kind="uuid"))) is None


@pytest.mark.parametrize("path", ["$.a.**", "$.a.*x", "$.a.*[0]", "$.a..b", "$.a.[*]", "$.*[*][*]", "$.a.*.*.", "$.a.$"])
def test_malformed_wildcard_forms_are_refused(path):
    assert P(_d(dict(path=path, kind="uuid"))) is not None, path


def test_paths_that_could_match_the_same_leaf_are_refused():
    ok = P(_d(dict(path="$.a.*.b", kind="uuid"), dict(path="$.a.*.c", kind="uuid"), dict(path="$.x.y", values=["v"])))
    assert ok is None                                         # different sub-keys: no leaf can match both
    for pair in (("$.a.*.b", "$.a.k.b"), ("$.*.b", "$.a.b"), ("$.*.b", "$.*.b"), ("$.a.*", "$.a.k"), ("$.*.*.b", "$.x.y.b"), ("$.a.*.b", "$.a.*[*].b")):
        why = P(_d(dict(path=pair[0], kind="uuid"), dict(path=pair[1], values=["v"])))
        assert why and ("overlaps" in why or "duplicates" in why), (pair, why)


def test_different_depths_do_not_overlap():
    assert P(_d(dict(path="$.a.*", kind="uuid"), dict(path="$.a.*.b", kind="uuid"))) is None


def test_overlap_function_is_symmetric_and_length_sensitive():
    f = ac._leaf_paths_overlap
    assert f("$.a.*", "$.a.k") and f("$.a.k", "$.a.*") and not f("$.a.*", "$.a.k.z") and not f("$.a.b", "$.a.c")


# ───────────── real SQL ─────────────

def _outside(monkeypatch, pg, rows, items):
    setup = ["CREATE TEMP TABLE t (id int, payload jsonb) ON COMMIT DROP;"] + [f"INSERT INTO t VALUES ({i}, {r});" for i, r in enumerate(rows, 1)]
    tables = {"t": (["id", "payload"], {"id": "integer", "payload": "jsonb"}, None)}
    return n150._real_outside(monkeypatch, pg, setup, tables, dict(why=n150.WHY, closed_columns=[_col(*items)]))


def _j(s):
    return "'" + s.replace("'", "''") + "'"


def test_REAL_SQL_uuid_kind_accepts_only_canonical_uuids_at_the_declared_paths(monkeypatch, disposable_pg):
    rows = [_j(f'{{"signal_ids": ["{U1}", "{U2}"], "score": 0.5, "n": 3}}'),                                   # ok: array of uuids, non-strings ignored
            _j(f'{{"signal_ids": [], "ranked_signals": [{{"signal_id": "{U1}", "rank": 1}}]}}'),               # ok: empty array, nested pointer
            "NULL",                                                                                            # not judged
            _j('{"signal_ids": [null]}'),                                                                      # null leaf: not a string
            _j('{"signal_ids": ["not-a-uuid"]}'),                                                              # OUT: a string at the path that is not a uuid
            _j(f'{{"signal_ids": ["{U1.upper()}"]}}'),                                                         # OUT: upper-case form is not canonical
            _j(f'{{"signal_ids": ["{{{U1}}}"]}}'),                                                             # OUT: braces
            _j(f'{{"signal_ids": ["{U1.replace("-", "")}"]}}'),                                                # OUT: undashed
            _j(f'{{"signal_ids": ["{U1}"], "note": "a free sentence"}}'),                                      # OUT: another string leaf
            _j(f'{{"other": "{U1}"}}'),                                                                        # OUT: a uuid at an UNdeclared path
            _j(f'{{"ranked_signals": [{{"signal_id": "{U1}", "label": "x"}}]}}')]                             # OUT: a label beside the pointer
    items = (dict(path="$.signal_ids[*]", kind="uuid"), dict(path="$.ranked_signals[*].signal_id", kind="uuid"))
    assert _outside(monkeypatch, disposable_pg, rows, items) == {("t", "payload"): 7}
    assert _outside(monkeypatch, disposable_pg, rows, items[:1])[("t", "payload")] >= 7                      # without the second path the nested pointer row is outside too


def test_REAL_SQL_a_wildcard_over_data_derived_keys_closes_the_constant_sub_key(monkeypatch, disposable_pg):
    rows = [_j('{"domain_verdict_map": {"career": {"verdict_note": "strong", "score": 2}, "marriage": {"verdict_note": "weak"}}}'),       # ok: two domain keys
            _j('{"domain_verdict_map": {}}'),                                                                                          # ok: no keys
            _j('{"domain_verdict_map": {"health": {"verdict_note": "mixed"}}}'),                                                       # OUT: a value outside the closed list
            _j('{"domain_verdict_map": {"career": {"verdict_note": "strong", "comment": "a free sentence"}}}'),                        # OUT: another string leaf under a domain
            _j('{"domain_verdict_map": {"career": "strong"}}'),                                                                        # OUT: the wildcard member itself is a string (declared path is deeper)
            _j('{"verdict_note": "strong"}'),                                                                                          # OUT: a listed value at an undeclared path
            _j('{"domain_verdict_map": {"wealth": {"verdict_note": "weak"}}, "domain_names": ["wealth"]}')]                            # OUT: the key names listed as strings elsewhere
    items = (dict(path="$.domain_verdict_map.*.verdict_note", values=["strong", "weak"]),)
    assert _outside(monkeypatch, disposable_pg, rows, items) == {("t", "payload"): 5}
    wide = items + (dict(path="$.domain_verdict_map.*.comment", values=["a free sentence"]),)
    assert _outside(monkeypatch, disposable_pg, rows, wide) == {("t", "payload"): 4}


def test_REAL_SQL_wildcard_with_uuid_kind_and_array_unwrap(monkeypatch, disposable_pg):
    rows = [_j(f'{{"cells": {{"c1": ["{U1}", "{U2}"], "c2": []}}}}'),                  # ok
            _j(f'{{"cells": {{"c1": ["{U1}", "x"]}}}}'),                                  # OUT: one non-uuid in an array under a data key
            _j(f'{{"cells": {{"c1": "{U1}"}}}}')]                                         # ok in lax mode: [*] on a scalar is the scalar itself
    assert _outside(monkeypatch, disposable_pg, rows, (dict(path="$.cells.*[*]", kind="uuid"),)) == {("t", "payload"): 1}


def test_REAL_SQL_two_non_overlapping_paths_are_not_double_counted(monkeypatch, disposable_pg):
    rows = [_j(f'{{"a": {{"k": {{"x": "{U1}"}}}}, "b": {{"k": {{"x": "{U2}"}}}}}}'),
            _j(f'{{"a": {{"k": {{"x": "{U1}", "y": "free text"}}}}}}')]
    items = (dict(path="$.a.*.x", kind="uuid"), dict(path="$.b.*.x", kind="uuid"))
    assert _outside(monkeypatch, disposable_pg, rows, items) == {("t", "payload"): 1}


def test_the_mutant_without_the_overlap_check_would_double_count_and_mask_a_free_string(monkeypatch, disposable_pg):
    """What the overlap refusal guards: `$.a.*.x` and `$.a.k.x` both match the same uuid leaf, so the closure count (2) would equal the string-leaf total (2) while a free string sits outside:
    row = {a:{k:{x: <uuid>}}, free: 'text'} has 2 string leaves and the double-counted ok total is 2, so it would read INSIDE. The validator refuses the pair, so this can never be declared."""
    pair = _d(dict(path="$.a.*.x", kind="uuid"), dict(path="$.a.k.x", kind="uuid"))
    assert "overlaps" in P(pair)
    doc = f'{{"a": {{"k": {{"x": "{U1}"}}}}, "free": "text"}}'                                # (a local: no same-quote f-string nesting, Python 3.11)
    setup = ["CREATE TEMP TABLE t (id int, payload jsonb) ON COMMIT DROP;", f"INSERT INTO t VALUES (1, {_j(doc)});"]
    tables = {"t": (["id", "payload"], {"id": "integer", "payload": "jsonb"}, None)}
    entry = _col(dict(path="$.a.*.x", kind="uuid"), dict(path="$.a.k.x", kind="uuid"))
    got = n150._real_outside(monkeypatch, disposable_pg, setup, tables, dict(why=n150.WHY, closed_columns=[entry]))
    assert got == {("t", "payload"): 0}                    # the masking the refusal prevents (the SQL itself would be fooled)


def test_the_closure_grade_uses_the_new_kinds_like_the_old_ones():
    d = _d(dict(path="$.signal_ids[*]", kind="uuid"))
    t = {"t": (["id", "payload"], {"id": "integer", "payload": "jsonb"}, None)}
    assert ac.grade_prose_none("x_asset", d, t, "t", {("t", "payload"): 0})["Narr.agree"]["v"] == "N/A"
    bad = ac.grade_prose_none("x_asset", d, t, "t", {("t", "payload"): 3})["Narr.agree"]
    assert bad["v"] == "FAIL" and "outside the declared paths" in bad["measured"]
