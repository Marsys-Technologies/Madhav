"""test_n350_gestalt_ayanamsha_count_measured.py: SS N-341/N-347, PR-H1 item 8.

`bo_chart_gestalt._write_aya` stored `"ayanamsha_count": len(CANONICAL_AYAS)` (always 5) in headline_epistemic_jsonb whatever the build actually wrote: a count that read as
measured though nothing counted it (§N.8). It now stores None at write time and the post-loop `_assess_fragility` / `_patch_fragility` pass writes the number of distinct
ayanamsha rows the build really wrote (None when that read failed). Each test fails if the constant comes back.
"""
from __future__ import annotations

import ast
import json
import pathlib

from pipeline.orchestrator.writers import bo_chart_gestalt as W


class _Cursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if isinstance(params, list) and params and "headline_epistemic_jsonb" in sql:
            self._conn.updated.append(params)


class _Conn:
    def __init__(self):
        self.updated = []

    def cursor(self):
        return _Cursor(self)


def _router(ayanamsha_ids):
    def route(conn, sql, params):
        if "SELECT ayanamsha_id, domain_verdict_map_jsonb" in sql:
            return [{"ayanamsha_id": a, "domain_verdict_map_jsonb": {"career": {"evidence": {"benefic_count": 6, "malefic_count": 4}}}} for a in ayanamsha_ids]
        if "SELECT gestalt_id, headline_epistemic_jsonb" in sql:
            return [{"gestalt_id": "g-1", "headline_epistemic_jsonb": json.dumps({"ayanamsha_count": None, "fragility_class": None, "note": "placeholder"})}]
        raise AssertionError("unexpected query: " + sql[:80])
    return route


def _patched(monkeypatch, ayanamsha_ids):
    monkeypatch.setattr(W, "_fetch_dict", _router(ayanamsha_ids))
    conn = _Conn()
    result = W._assess_fragility(conn, "chart-1", "build-1")
    W._patch_fragility(conn, "chart-1", "build-1", result)
    return result, json.loads(conn.updated[0][0])


def test_the_patched_count_is_the_number_of_rows_the_build_wrote(monkeypatch):
    for ids in (["lahiri_chitrapaksha"], ["lahiri_chitrapaksha", "raman"], ["a", "b", "c"], ["a", "b", "c", "d", "e"]):
        result, final = _patched(monkeypatch, ids)
        assert result["ayanamsha_count"] == len(ids) and final["ayanamsha_count"] == len(ids), ids


def test_a_single_row_build_is_not_reported_as_five(monkeypatch):
    _, final = _patched(monkeypatch, ["lahiri_chitrapaksha"])
    assert final["ayanamsha_count"] == 1 and final["ayanamsha_count"] != len(W.CANONICAL_AYAS)


def test_distinct_ayanamshas_are_counted_once(monkeypatch):
    result, final = _patched(monkeypatch, ["raman", "raman", "lahiri_chitrapaksha"])
    assert result["ayanamsha_count"] == 2 and final["ayanamsha_count"] == 2


def test_an_unreadable_build_leaves_the_count_none_not_a_default(monkeypatch):
    def boom(conn, sql, params):
        if "SELECT ayanamsha_id, domain_verdict_map_jsonb" in sql:
            raise RuntimeError("read failed")
        return [{"gestalt_id": "g-1", "headline_epistemic_jsonb": json.dumps({"ayanamsha_count": None})}]
    monkeypatch.setattr(W, "_fetch_dict", boom)
    conn = _Conn()
    result = W._assess_fragility(conn, "chart-1", "build-1")
    assert result["ayanamsha_count"] is None
    W._patch_fragility(conn, "chart-1", "build-1", result)
    assert json.loads(conn.updated[0][0])["ayanamsha_count"] is None


def test_the_source_never_stores_the_canonical_list_size_as_the_count():
    tree = ast.parse(pathlib.Path(W.__file__).read_text(encoding="utf-8"))
    dicts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict)
             and any(isinstance(t, ast.Name) and t.id == "headline_epistemic" for t in n.targets)]
    assert len(dicts) == 1, "the write-time headline_epistemic dict moved: update this guard"
    values = [v for k, v in zip(dicts[0].keys, dicts[0].values) if isinstance(k, ast.Constant) and k.value == "ayanamsha_count"]
    assert len(values) == 1
    assert isinstance(values[0], ast.Constant) and values[0].value is None, "ayanamsha_count must be None at write time (the post-loop pass patches the measurement)"
