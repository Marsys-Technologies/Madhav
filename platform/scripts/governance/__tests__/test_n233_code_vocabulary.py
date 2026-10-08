"""test_n233_code_vocabulary.py: the declared graha CODE column (SS N-235; bg_class_priors.fact_kind holds SU MO MA ME JU VE SA RA KE).

`code_vocabulary {class: graha, columns: [{table, column}], why, evidence}` credits a value as a registered abbreviation ONLY in a declared column and ONLY if it is a member of the code set READ at measure time from the
committed semantic release (the two-letter ALL-CAPS aliases of the graha identities). A code outside the nine, a case variant, or the same code in an undeclared column stays a real FAIL. Disposable PostgreSQL.
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

NINE = ["SU", "MO", "MA", "ME", "JU", "VE", "SA", "RA", "KE"]
EVID = "platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json"
WHY = "the column holds the standard nine-graha abbreviation set read by priors_config"


def _decl(table="n233cv", column="fact_kind", **over):
    d = dict(code_vocabulary=dict({"class": "graha", "columns": [{"table": table, "column": column}], "why": WHY, "evidence": EVID}, **over))
    return d


def _mk(pg, monkeypatch, table, rows, col="fact_kind"):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} (id serial, {col} text)")
    for r in rows:
        ac.psql(f"INSERT INTO {table} ({col}) VALUES ({ac._vocab_lit(r)})")


def _detect(table, col, entry):
    return ac.vocab_value_detect({table: (["id", col], {"id": "integer", col: "text"})}, None, codes=ac.code_columns_of(entry))


def test_the_code_set_is_read_from_the_release_and_is_exactly_the_nine():
    assert ac.vocab_code_set() == frozenset(NINE)                # AC (an angle, not a graha) and the three-letter aliases are not in it


def test_the_declaration_validates_and_malformed_ones_are_refused():
    assert ac.code_vocabulary_problem(_decl()) is None
    assert "class must be 'graha'" in ac.code_vocabulary_problem(_decl(**{"class": "rashi"}))
    assert "exactly the fields" in ac.code_vocabulary_problem({"code_vocabulary": {"class": "graha"}})
    assert "columns" in ac.code_vocabulary_problem(_decl(columns=[]))
    assert "listed twice" in ac.code_vocabulary_problem(_decl(columns=[{"table": "t", "column": "c"}, {"table": "t", "column": "c"}]))
    assert "evidence" in ac.code_vocabulary_problem(_decl(evidence="unverified: nobody looked"))
    assert "evidence" in ac.code_vocabulary_problem(_decl(evidence="platform/no/such/file.json"))
    with pytest.raises(ac.DeclarationsError):
        ac.validate_code_vocabulary_declaration("assets['x']", _decl(**{"class": "rashi"}))
    assert ac.code_columns_of(_decl(**{"class": "rashi"})) == {}          # a malformed declaration credits nothing


def test_REAL_SQL_the_nine_codes_in_the_declared_column_are_credited(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, "n233cv", NINE)
    try:
        assert _detect("n233cv", "fact_kind", {})["v"] == ac.FAIL                       # undeclared: the same data is a real FAIL
        rec = _detect("n233cv", "fact_kind", _decl())
        assert rec["v"] == ac.PASS, rec["measured"]
        assert set(rec["vocab_values"]["found"][0]["registered"]) == set(NINE) and rec["vocab_values"]["found"][0]["spellings"] == []
    finally:
        ac.psql("DROP TABLE IF EXISTS n233cv")


@pytest.mark.parametrize("bad", ["AC", "Su", "mo"])
def test_REAL_SQL_FORGERY_a_code_outside_the_nine_or_in_another_case_stays_a_fail(monkeypatch, disposable_pg, bad):
    _mk(disposable_pg, monkeypatch, "n233cv", NINE + [bad])
    try:
        rec = _detect("n233cv", "fact_kind", _decl())
        assert rec["v"] == ac.FAIL and repr(bad) in rec["measured"], rec["measured"]
    finally:
        ac.psql("DROP TABLE IF EXISTS n233cv")


def test_REAL_SQL_FORGERY_the_same_codes_in_a_column_that_is_not_declared_are_not_credited(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, "n233cv", NINE, col="state_code")
    try:
        assert _detect("n233cv", "state_code", _decl(column="fact_kind"))["v"] == ac.FAIL              # another column of the table declared
        assert _detect("n233cv", "state_code", _decl(table="other_table", column="state_code"))["v"] == ac.FAIL     # the right column name on another table
        assert _detect("n233cv", "state_code", _decl(column="state_code"))["v"] == ac.PASS
    finally:
        ac.psql("DROP TABLE IF EXISTS n233cv")
