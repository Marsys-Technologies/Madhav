"""test_n233_ldgr_two_columns.py: the UNSOURCED_DECLARED residual over a DECLARED SET of ledger columns (SS N-235; bo_pratijna).

bo_pratijna's writer always writes NULL to supporting_signal_ids and contradicting_signal_ids. The checked label now covers a declared set of 1 to 4 source columns: a row CARRIES a source when ANY declared column names one; the
label stands only if, over every judged row of the measured chart, ALL declared columns lack one (NULL or an empty id array), read by a bounded EXISTS statement. One non-NULL row in ANY declared column turns it red.
Disposable PostgreSQL.
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
WHY = "the writer never writes an id to either signal-id ledger column; the rows name no traceable source"
EV = "platform/scripts/governance/asset_census.py:1"
T = "n233_pratijna"


def _decl(kinds=("LEDGER", "LEDGER"), cols=("supporting_signal_ids", "contradicting_signal_ids")):
    return dict(level="row", columns=[dict(column=c, kinds=[k], **({"resolves_to": "bodha_msr_signals.signal_id"} if k == "LEDGER" else {})) for c, k in zip(cols, kinds)], citation_state="unsourced", residual=ac.UNSOURCED_DECLARED, why=WHY, evidence=EV)


def _mk(pg, monkeypatch, rows, typ="uuid[]"):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {T}")
    for t_, ddl in (("chart_facts", "fact_id text"), ("bodha_msr_signals", "signal_id uuid, constituent_facts_array text[]")):      # the tables the ordinary ledger reading resolves ids against (empty here)
        ac.psql(f"CREATE TABLE IF NOT EXISTS {t_} ({ddl})")
    ac.psql(f"CREATE TABLE {T} (id int PRIMARY KEY, supporting_signal_ids {typ}, contradicting_signal_ids {typ})")
    for i, r in enumerate(rows):
        ac.psql(f"INSERT INTO {T} VALUES ({i + 1}, {r})")


def _drop():
    for t_ in (T, "chart_facts", "bodha_msr_signals"):
        ac.psql(f"DROP TABLE IF EXISTS {t_}")


def _check(src=None):
    return ac.source_declared_check("bo_pratijna", src or _decl(), T, ["id", "supporting_signal_ids", "contradicting_signal_ids"], keys=[["id"]])[LDGR]


def test_the_two_column_declaration_is_sound_and_a_fifth_column_is_not():
    assert ac.source_declaration_problem(_decl()) is None
    assert ac.source_declaration_problem(_decl(kinds=("K1", "K1"))) is None
    assert "one to 4 entries" in ac.source_declaration_problem(dict(_decl(), columns=[dict(column=c, kinds=["K1"]) for c in "abcde"]))


def test_REAL_SQL_every_row_null_in_both_columns_earns_the_label(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, ["NULL, NULL", "NULL, NULL", "NULL, ARRAY[]::uuid[]"])
    try:
        rec = _check()
        assert rec["v"] == ac.NA and rec["cause"] == "unsourced-declared", rec
        b = rec["unsourced_declared"]
        assert b["source_columns"] == ["supporting_signal_ids", "contradicting_signal_ids"] and b["carrying_a_source"] is False and b["verified"] is True
        assert ac.unsourced_declared_na_problem(LDGR, rec) is None
        assert ac._check_contribution(LDGR, "L2", rec, None)["v"] == ac.NA
    finally:
        _drop()


@pytest.mark.parametrize("row", ["ARRAY['11111111-1111-4111-8111-111111111111']::uuid[], NULL", "NULL, ARRAY['11111111-1111-4111-8111-111111111111']::uuid[]"])
def test_REAL_SQL_MUTATION_one_non_null_row_in_either_declared_column_turns_the_label_red(monkeypatch, disposable_pg, row):
    _mk(disposable_pg, monkeypatch, ["NULL, NULL", "NULL, NULL", row])
    try:
        rec = _check()
        assert rec["v"] != ac.NA and rec["declaration_disagreements"][0]["field"] == "source.residual" and "CONTRADICTED" in rec["measured"], rec
        assert ac._check_contribution(LDGR, "L2", rec, None)["v"] != ac.NA
    finally:
        _drop()


def test_REAL_SQL_the_single_column_declaration_would_have_missed_the_second_column(monkeypatch, disposable_pg):
    """Why the SET matters: declaring only supporting_signal_ids stands even though contradicting_signal_ids carries ids; declaring both does not."""
    _mk(disposable_pg, monkeypatch, ["NULL, NULL", "NULL, ARRAY['11111111-1111-4111-8111-111111111111']::uuid[]"])
    try:
        assert _check(_decl(kinds=("LEDGER",), cols=("supporting_signal_ids",)))["v"] == ac.NA
        assert _check()["v"] != ac.NA
    finally:
        _drop()


def test_REAL_SQL_no_row_at_all_is_vacuous_no_detector(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, [])
    try:
        assert _check()["v"] == ac.NO_DET
    finally:
        _drop()


def test_REAL_SQL_a_non_array_column_declared_as_ledger_cannot_be_checked(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, ["'x', NULL"], typ="text")
    try:
        assert _check()["v"] == ac.NO_DET
    finally:
        _drop()
