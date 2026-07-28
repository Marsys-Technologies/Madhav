"""Regression test for P0-N1 (ŚUDDHA-VĀCA parked finding, native-authorized fix):
`_load_shadbala_and_bhava_fact_ids` in ga_structural_writer.py selected
`graha_shadbala_total` / `house_bhava_bala_total` facts by `fact_category` alone,
with no `fact_key` pin and no `ORDER BY` — the exact D1_MISSELECT shape as P0-5
(bo_laksana.py), against the SAME `graha_shadbala_total` category, which is
confirmed (live DB) to carry 3 fact_key variants per graha: 'rupa' (raw achieved),
'ratio' (achieved/required), 'required_rupa' (INVARIANT ayanamsha only). Without a
pin, which variant survives the dict-overwrite in `shadbala[subj] = (...)` depends
entirely on Postgres's unordered row-return order — SUN could resolve to 1.694
(ratio) or 8.47 (rupa) depending on physical row order, silently.

The fake cursor below actually parses the executed SQL's WHERE clause (category +
optional fact_key) and filters its canned multi-variant fact table accordingly —
a cursor that just returns a fixed row list regardless of SQL text would not
distinguish "pinned" from "unpinned" queries and would not catch a regression.
"""
from __future__ import annotations

import re

import psycopg.rows

from ga_writers import ga_structural_writer as sut

# Simulates the live chart_facts rows actually observed for chart 482012f1,
# ayanamsha lahiri_chitrapaksha (fact_subject, fact_category, fact_key, value, fact_id).
# Order matters: 'ratio' is listed BEFORE 'rupa' for SUN to prove an unpinned query's
# result is order-dependent, not just "happens to be right by luck".
_FACT_TABLE = [
    ("SUN", "graha_shadbala_total", "ratio", 1.694, "fid_sun_ratio"),
    ("SUN", "graha_shadbala_total", "rupa", 8.47, "fid_sun_rupa"),
    ("MOON", "graha_shadbala_total", "rupa", 5.65, "fid_moon_rupa"),
    ("MOON", "graha_shadbala_total", "ratio", 0.941667, "fid_moon_ratio"),
    ("SUN", "house_bhava_bala_total", "total", 12.3, "fid_sun_house"),
]


class _WhereAwareCursor:
    def __init__(self, table):
        self._table = table
        self._result: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        assert re.search(r"fact_category\s*=", sql), "query must filter by fact_category"
        fact_key_pinned = re.search(r"fact_key\s*=\s*'", sql) is not None
        category = None
        # The real function inlines the category literal in SQL text (never
        # parametrized) — recover it by matching against the fake table's categories.
        for cat in ("graha_shadbala_total", "house_bhava_bala_total"):
            if f"'{cat}'" in sql or cat in sql:
                category = cat
                break
        rows = [r for r in self._table if r[1] == category]
        if fact_key_pinned:
            pinned_key_match = re.search(r"fact_key\s*=\s*'([^']+)'", sql)
            assert pinned_key_match, "fact_key filter present but no literal key found in SQL"
            pinned_key = pinned_key_match.group(1)
            rows = [r for r in rows if r[2] == pinned_key]
        self._result = [(subj, val, fid) for subj, _cat, _key, val, fid in rows]

    def fetchall(self):
        return self._result


class _FakeConn:
    def __init__(self, table):
        self._table = table

    def cursor(self, *a, row_factory=None, **k):
        return _WhereAwareCursor(self._table)


def test_unpinned_query_shape_would_be_order_dependent_if_regressed():
    """Sanity-check the fake harness itself: if the SQL had NO fact_key filter,
    fetchall() would return BOTH the ratio and rupa rows for SUN (in table order),
    and a naive `shadbala[subj] = (...)` loop would silently keep whichever came
    last — proving the pre-fix shape was a real, order-dependent bug, not a
    theoretical one. This test targets the fake cursor directly, not the writer,
    to document the exact failure mode the real fix (fact_key pin in SQL) closes."""
    cur = _WhereAwareCursor(_FACT_TABLE)
    cur.execute(
        "SELECT fact_subject, fact_value_num, fact_id FROM chart_facts "
        "WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_shadbala_total'",
        ("chart", "lahiri_chitrapaksha"),
    )
    rows = cur.fetchall()
    sun_rows = [r for r in rows if r[0] == "SUN"]
    assert len(sun_rows) == 2, "unpinned query returns both fact_key variants for SUN"
    # Last-wins dict-overwrite semantics (the actual pre-fix writer logic):
    last_wins = {}
    for subj, val, fid in rows:
        last_wins[subj] = (val, fid)
    assert last_wins["SUN"] == (8.47, "fid_sun_rupa"), (
        "table order has 'rupa' last; an unpinned query's dict-overwrite result "
        "depends entirely on this incidental order, not on any real filtering"
    )


def test_load_shadbala_and_bhava_fact_ids_pins_fact_key_rupa_for_shadbala():
    """The real fix: the shadbala query must filter to fact_key='rupa' at the SQL
    level, so SUN resolves to the raw achieved value (8.47), not the pre-computed
    ratio (1.694) — matching the same 'rupa' convention already established by the
    bo_laksana.py (P0-5) and registry_bridge.ts (P0-1..4) fixes."""
    conn = _FakeConn(_FACT_TABLE)
    shadbala, _bhava = sut._load_shadbala_and_bhava_fact_ids(
        conn, "chart-id", "lahiri_chitrapaksha"
    )
    assert shadbala["SUN"] == (8.47, "fid_sun_rupa")
    assert shadbala["MOON"] == (5.65, "fid_moon_rupa")


def test_load_shadbala_and_bhava_fact_ids_pins_fact_key_total_for_bhava_bala():
    """house_bhava_bala_total has only one fact_key ('total') live today, but the
    query must pin it explicitly anyway (defense-in-depth per the N.7 Narration
    Fidelity Principle: a future second fact_key on this category must not
    silently reintroduce the same order-dependent overwrite)."""
    conn = _FakeConn(_FACT_TABLE)
    _shadbala, bhava = sut._load_shadbala_and_bhava_fact_ids(
        conn, "chart-id", "lahiri_chitrapaksha"
    )
    assert bhava["SUN"] == (12.3, "fid_sun_house")


def test_load_shadbala_query_text_pins_fact_key_explicitly():
    """Direct guard against silent regression back to category-only selection
    (the C.7 fact-category-pin-lint CI guard's own defect class): assert the
    literal SQL text pins fact_key for both queries."""
    import inspect

    src = inspect.getsource(sut._load_shadbala_and_bhava_fact_ids)
    shadbala_clause = src.split("house_bhava_bala_total")[0]
    bhava_clause = src.split("house_bhava_bala_total")[1] if "house_bhava_bala_total" in src else ""
    assert "fact_key" in shadbala_clause and "'rupa'" in shadbala_clause, (
        "graha_shadbala_total query must pin fact_key = 'rupa'"
    )
    assert "fact_key" in bhava_clause and "'total'" in bhava_clause, (
        "house_bhava_bala_total query must pin fact_key = 'total'"
    )
