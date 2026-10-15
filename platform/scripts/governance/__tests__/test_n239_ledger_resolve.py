"""test_n239_ledger_resolve.py: the LEDGER source read of bo_anveshana was unbounded in cost (SS N-239).

Reproduced on a disposable PostgreSQL: 3000 discovery rows x 5 signal ids over 130 000 signals + 150 000 facts took 316 s (the exact read hit the statement timeout, then the existence read crawled): the resolution
predicate compared `ms.signal_id::text = x`, casting the INDEXED uuid primary key to text, so every id sequentially scanned bodha_msr_signals. Now `ms.signal_id = <x as uuid>` (guarded cast) uses the primary key:
0.18 s on the same data. The semantics are UNCHANGED and pinned here: a missing source in ANY row still turns the cell red, by the exact read and by the existence read.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

LDGR = "Ldgr.source_presence"
A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"          # a signal whose constituent fact does not exist
D = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"          # a signal with an empty constituent array
MISSING = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"    # no such signal
SRC = dict(level="row", columns=[dict(column="refs", kinds=["LEDGER"], path="$.signal_ids", resolves_to="bodha_msr_signals.signal_id")],
           why="each row lists the signal ids it rests on and each resolves through its constituent facts", evidence="platform/scripts/governance/asset_census.py:1")


def _world(monkeypatch, pg, rows):
    point_psql_at(pg, monkeypatch)
    for t in ("n239_bd", "bodha_msr_signals", "chart_facts"):
        ac.psql(f"DROP TABLE IF EXISTS {t}")
    ac.psql("CREATE TABLE chart_facts (fact_id text UNIQUE NOT NULL)")
    ac.psql("CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, constituent_facts_array text[] NOT NULL)")
    ac.psql("INSERT INTO chart_facts VALUES ('F1'), ('F2')")
    ac.psql(f"INSERT INTO bodha_msr_signals VALUES ('{A}', ARRAY['F1']), ('{B}', ARRAY['F1','F2']), ('{C}', ARRAY['F1','NOPE']), ('{D}', ARRAY[]::text[])")
    ac.psql("CREATE TABLE n239_bd (id int PRIMARY KEY, refs jsonb)")
    for i, r in enumerate(rows):
        ac.psql(f"INSERT INTO n239_bd VALUES ({i + 1}, {r})")


def _drop():
    for t in ("n239_bd", "bodha_msr_signals", "chart_facts"):
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def _refs(*ids):
    return "'" + ac.json.dumps({"signal_ids": list(ids)}) + "'::jsonb"


def _exact():
    return ac.source_declared_check("bo_x", SRC, "n239_bd", ["id", "refs"], keys=[["id"]])[LDGR]


def _presence():
    """The EXISTENCE read on the same predicate (what runs for a big table / after a timeout)."""
    ktypes = {c: ac.source_column_kind(t) for c, t in ac.source_fetch_column_types("n239_bd", ["refs"]).items()}
    pred, _why = ac.source_entry_lacking(SRC["columns"][0], ktypes)
    return ac.source_fetch_presence("n239_bd", pred, ["id"])


def test_every_id_resolving_is_a_source_by_both_reads(monkeypatch, disposable_pg):
    _world(monkeypatch, disposable_pg, [_refs(A, B), _refs(B)])
    try:
        r = _exact()
        assert r["v"] == ac.PASS and r["source"]["rows"] == 2 and r["source"]["lacking"] == 0, r
        p = _presence()
        assert p["lacking_at_least"] == 0 and p["sourced"] is True, p
    finally:
        _drop()


@pytest.mark.parametrize("bad", [
    _refs(A, MISSING),                                   # an id no signal carries
    _refs(A, "not-a-uuid"),                              # a non-uuid string: no error, no resolution
    _refs(A, A.upper()),                                 # the canonical form is lower-case: an upper-case spelling never resolved and still does not
    _refs(A, C),                                         # the signal exists but its constituent fact does not (the chain must reach L1)
    _refs(A, D),                                         # the signal has no constituent facts
    _refs(),                                             # no ids at all
    "NULL",                                              # no document
    "'{\"signal_ids\": [\"" + A + "\", 7]}'::jsonb",    # a non-string element
])
def test_MUTATION_one_bad_row_turns_the_cell_red_by_both_reads(monkeypatch, disposable_pg, bad):
    _world(monkeypatch, disposable_pg, [_refs(A, B), _refs(B), bad])
    try:
        r = _exact()
        assert r["v"] == ac.PARTIAL and r["source"]["lacking"] == 1, r             # the clean rows source, one row does not: not a PASS
        p = _presence()
        assert p["lacking_at_least"] == 1 and p["sourced"] is True, p
    finally:
        _drop()


def test_a_table_where_no_row_resolves_is_a_fail(monkeypatch, disposable_pg):
    _world(monkeypatch, disposable_pg, [_refs(MISSING), _refs("x")])
    try:
        assert _exact()["v"] == ac.FAIL
        assert _presence()["sourced"] is False
    finally:
        _drop()


def test_the_resolution_uses_the_signal_primary_key_index_not_a_sequential_scan(monkeypatch, disposable_pg):
    """The regression pinned structurally (a timing assertion would flake): with enough signals the plan of the lack predicate must use bodha_msr_signals_pkey."""
    _world(monkeypatch, disposable_pg, [_refs(A, B)])
    try:
        ac.psql("INSERT INTO bodha_msr_signals SELECT gen_random_uuid(), ARRAY['F1'] FROM generate_series(1, 60000)")
        ac.psql("ANALYZE bodha_msr_signals; ANALYZE n239_bd; ANALYZE chart_facts")
        ktypes = {c: ac.source_column_kind(t) for c, t in ac.source_fetch_column_types("n239_bd", ["refs"]).items()}
        pred, _w = ac.source_entry_lacking(SRC["columns"][0], ktypes)
        plan = "\n".join(r[0] for r in ac.psql(f"EXPLAIN SELECT 1 FROM n239_bd WHERE {pred}"))
        assert "bodha_msr_signals_pkey" in plan, plan
        assert "Seq Scan on bodha_msr_signals" not in plan, plan
    finally:
        _drop()


def test_the_predicate_text_no_longer_casts_the_key_to_text():
    sql = ac._ledger_resolves("x", "bodha_msr_signals.signal_id")
    assert "signal_id::text" not in sql and "ms.signal_id = (CASE WHEN" in sql and "::uuid" in sql
