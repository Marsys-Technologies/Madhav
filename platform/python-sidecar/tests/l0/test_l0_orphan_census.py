"""TI-L0-25 (CF-12): the read-only orphan census for upsert-only L0 writers.

Failing-first design (INDEX section 4 item 8): a fixture table with one extra row the writer
does not produce -> the census reads FAIL and NAMES it; with the row gone -> PASS. Mutation
proof lives in the PR body (each mutant of the census is killed by a test below).
"""
from __future__ import annotations

import json

import pytest

import brahmagyan.l0_orphan_census as oc
from brahmagyan.l0_orphan_census import TableCensus, census_table, overall_verdict, run_census
from pipeline.orchestrator.writers.bg_parihara_rules import (
    build_activity_rule_rows,
    build_census_rows,
)
from tests.l0._dictrow_fakes import FakeDictRowConnection

# ── pure arithmetic ──────────────────────────────────────────────────────────────

def test_orphans_are_live_minus_produced_and_missing_are_produced_minus_live() -> None:
    c = census_table("t", ("a", "b"), produced_keys=[(1, 1), (1, 2), (2, 1)],
                     live_keys=[(1, 1), (2, 1), (9, 9)])
    assert c.orphans == ((9, 9),)
    assert c.missing == ((1, 2),)
    assert (c.produced_count, c.live_count) == (3, 3)
    assert c.verdict == "FAIL"


def test_no_orphan_is_a_pass_even_when_a_produced_key_is_not_yet_live() -> None:
    c = census_table("t", ("a",), [(1,), (2,)], [(1,)])
    assert c.orphans == () and c.missing == ((2,),)
    assert c.verdict == "PASS"


def test_a_writer_that_emits_a_key_twice_is_reported() -> None:
    c = census_table("t", ("a",), [(1,), (1,), (2,)], [(1,), (2,)])
    assert c.duplicate_produced == ((1,),)
    assert c.produced_count == 2          # distinct keys


def test_nothing_produced_is_NO_READING_never_PASS() -> None:
    """If the writer produced no key, an empty live table cannot read PASS (CLAUDE.md N.8)."""
    empty = census_table("t", ("a",), [], [])
    assert empty.verdict == "NO_READING"
    # ...and live rows with nothing produced are all orphans: FAIL, not NO_READING
    assert census_table("t", ("a",), [], [(1,)]).verdict == "FAIL"
    assert overall_verdict([]) == "NO_READING"
    assert overall_verdict([empty, census_table("t", ("a",), [(1,)], [(1,)])]) == "NO_READING"


def test_overall_verdict_is_fail_if_any_table_has_an_orphan() -> None:
    ok = census_table("ok", ("a",), [(1,)], [(1,)])
    bad = census_table("bad", ("a",), [(1,)], [(1,), (2,)])
    assert overall_verdict([ok, bad]) == "FAIL"
    assert overall_verdict([ok, ok]) == "PASS"


# ── the bg_parihara_rules adapter against a production-shaped (dict_row) connection ────

_TEXT_COLS = ["text_id", "title_en"]
_TEXT_ROWS = [("bphs", "Brihat Parasara Hora Sastra")]
_DOSHA_COLS = ["canonical_id", "name_en", "category", "cancellation_conditions", "classical_citations"]


def _dosha_rows(n_conditions: int = 2) -> list[tuple]:
    return [(
        "manglik_dosha", "Manglik Dosha", "graha_dosha",
        {"bhanga": [f"condition {i}" for i in range(1, n_conditions + 1)]},
        [{"text_id": "bphs", "chapter": 9}],
    )]


_ACT = [(r["activity_class"], r["factor_type"], r["factor_id"]) for r in build_activity_rule_rows("x")]
_CEN = [(r["factor_family"], r["factor_name"]) for r in build_census_rows("x")]


def _conn(live_parihara, live_activity=_ACT, live_census=_CEN, dosha=None) -> FakeDictRowConnection:
    def rows(keys, cols):
        return cols, [tuple(k) for k in keys]

    pc, pr = rows(live_parihara, ["dosha_canonical_id", "cancellation_index"])
    ac, ar = rows(live_activity, ["activity_class", "factor_type", "factor_id"])
    cc, cr = rows(live_census, ["factor_family", "factor_name"])
    return FakeDictRowConnection(tables=[
        ("from classical_texts", _TEXT_COLS, _TEXT_ROWS),
        ("from brahma_dosha_catalog", _DOSHA_COLS, dosha if dosha is not None else _dosha_rows()),
        ("from bg_parihara_rules", pc, pr),
        ("from bg_muhurta_activity_rules", ac, ar),
        ("from bg_muhurta_factor_census", cc, cr),
    ])


def _by_table(tables: list[TableCensus]) -> dict[str, TableCensus]:
    return {t.table: t for t in tables}


def test_converged_tables_read_PASS() -> None:
    conn = _conn(live_parihara=[("manglik_dosha", 1), ("manglik_dosha", 2)])
    tables = run_census(conn, "bg_parihara_rules")
    assert overall_verdict(tables) == "PASS"
    assert {t.table: (t.produced_count, t.live_count) for t in tables} == {
        "bg_parihara_rules": (2, 2),
        "bg_muhurta_activity_rules": (len(set(_ACT)), len(set(_ACT))),
        "bg_muhurta_factor_census": (len(set(_CEN)), len(set(_CEN))),
    }


def test_an_extra_live_row_in_each_table_is_named_FAIL() -> None:
    """The migration-703 shape: one orphan in parihara, extras in the muhurta tables."""
    conn = _conn(
        live_parihara=[("manglik_dosha", 1), ("manglik_dosha", 2), ("ghost_dosha", 1)],
        live_activity=_ACT + [("vivah", "tithi", 9999)],
        live_census=_CEN + [("ghost_family", "ghost_factor")],
    )
    tables = _by_table(run_census(conn, "bg_parihara_rules"))
    assert overall_verdict(list(tables.values())) == "FAIL"
    assert tables["bg_parihara_rules"].orphans == (("ghost_dosha", 1),)
    assert tables["bg_muhurta_activity_rules"].orphans == (("vivah", "tithi", 9999),)
    assert tables["bg_muhurta_factor_census"].orphans == (("ghost_family", "ghost_factor"),)


def test_a_condition_removed_upstream_leaves_an_orphan_the_upsert_would_never_delete() -> None:
    """Corpus now yields 1 condition for manglik_dosha; live still holds index 2."""
    conn = _conn(live_parihara=[("manglik_dosha", 1), ("manglik_dosha", 2)],
                 dosha=_dosha_rows(n_conditions=1))
    parihara = _by_table(run_census(conn, "bg_parihara_rules"))["bg_parihara_rules"]
    assert parihara.orphans == (("manglik_dosha", 2),)
    assert parihara.verdict == "FAIL"


def test_the_census_only_ever_issues_selects() -> None:
    conn = _conn(live_parihara=[("manglik_dosha", 1), ("manglik_dosha", 2)])
    run_census(conn, "bg_parihara_rules")
    assert conn.executed, "the census ran no SQL at all"
    assert all(sql.lstrip().lower().startswith("select") for sql in conn.executed), conn.executed


def test_unknown_asset_is_refused_not_passed() -> None:
    with pytest.raises(KeyError, match="no orphan-census adapter"):
        run_census(_conn([]), "bg_not_an_asset")


# ── the CLI: read-only connection, exit codes, JSON ──────────────────────────────────

class _Closeable(FakeDictRowConnection):
    def rollback(self) -> None: ...
    def close(self) -> None: ...


def _patch_conn(monkeypatch, conn) -> None:
    monkeypatch.setattr(oc, "_connect_read_only", lambda dsn: conn)


def _as_closeable(conn: FakeDictRowConnection) -> _Closeable:
    c = _Closeable(tables=conn._tables)
    return c


def test_cli_exit_codes_and_json(monkeypatch, capsys) -> None:
    good = _as_closeable(_conn([("manglik_dosha", 1), ("manglik_dosha", 2)]))
    _patch_conn(monkeypatch, good)
    assert oc.main(["--asset", "bg_parihara_rules", "--dsn", "x"]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "PASS"

    bad = _as_closeable(_conn([("manglik_dosha", 1), ("manglik_dosha", 2), ("ghost", 1)]))
    _patch_conn(monkeypatch, bad)
    assert oc.main(["--asset", "bg_parihara_rules", "--dsn", "x"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "FAIL" and out["orphan_total"] == 1
    assert out["tables"][0]["orphans"] == [["ghost", 1]]


def test_cli_cannot_measure_is_exit_2_never_a_clean_result(monkeypatch, capsys) -> None:
    def boom(dsn):
        raise RuntimeError("no database")

    monkeypatch.setattr(oc, "_connect_read_only", boom)
    assert oc.main(["--asset", "bg_parihara_rules", "--dsn", "x"]) == 2
    assert capsys.readouterr().out == ""


def test_cli_without_a_dsn_is_exit_2(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert oc.main(["--asset", "bg_parihara_rules"]) == 2


def test_connection_is_opened_read_only(monkeypatch) -> None:
    seen = {}

    class _Conn:
        read_only = False

    def fake_connect(dsn, **kw):
        seen.update(kw, dsn=dsn)
        return _Conn()

    import psycopg
    monkeypatch.setattr(psycopg, "connect", fake_connect)
    conn = oc._connect_read_only("postgresql://u@h/db")
    assert "default_transaction_read_only=on" in seen["options"]
    assert conn.read_only is True
