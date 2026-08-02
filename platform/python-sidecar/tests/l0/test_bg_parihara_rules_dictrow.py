"""
Regression tests for the two production defects the 2026-08-02 L0 global build
(run 6fd72ed9, execution brahma-build-pipeline-job-k622x) exposed in
bg_parihara_rules:

1. dict_row crash — fetch_parihara_rows indexed rows numerically
   (`text_titles[row[0]] = row[1]`) while the orchestrator connection's
   row_factory is dict_row (pipeline/orchestrator/db.py:26) → KeyError: 1.
   These tests run the writer against a dict-row connection, the production
   configuration the old tests never exercised.

2. §N.8 swallow-into-success — run()'s except branches logged the failure and
   returned a success-shaped WriterResult(rows_inserted=0, notes="failed: ...").
   The orchestrator treats any non-raising run() as OK, so the asset was lit
   while all three tables sat at 0 rows. A computation or insert failure must
   RAISE so the runner's savepoint rollback + error-state path fires.
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_parihara_rules import (
    BgPariharaRulesWriter,
    fetch_parihara_rows,
)
from tests.l0._dictrow_fakes import FakeDictRowConnection

# ── Fixture data: minimal real-shaped corpus rows ────────────────────────────

_TEXT_COLS = ["text_id", "title_en"]
_TEXT_ROWS = [("bphs", "Brihat Parasara Hora Sastra")]

_DOSHA_COLS = [
    "canonical_id", "name_en", "category",
    "cancellation_conditions", "classical_citations",
]
_DOSHA_ROWS = [
    (
        "manglik_dosha", "Manglik Dosha", "graha_dosha",
        {"bhanga": ["Mars in own sign", "Both partners Manglik"]},
        [{"text_id": "bphs", "chapter": 9}],
    ),
]


def _conn(**kwargs) -> FakeDictRowConnection:
    return FakeDictRowConnection(
        tables=[
            ("from classical_texts", _TEXT_COLS, _TEXT_ROWS),
            ("from brahma_dosha_catalog", _DOSHA_COLS, _DOSHA_ROWS),
        ],
        **kwargs,
    )


def _ctx(conn, dry_run: bool = False) -> ContextSpec:
    return ContextSpec(
        asset_id="bg_parihara_rules",
        build_id="test-build-6fd72ed9",
        db_conn=conn,
        dry_run=dry_run,
    )


# ── Defect 1: dict_row (production row factory) ──────────────────────────────

def test_fetch_parihara_rows_completes_under_dict_row():
    """Reproduces the production KeyError: 1 — fetch must work on dict rows."""
    rows = fetch_parihara_rows(_conn(), "test-build-6fd72ed9")
    assert len(rows) == 2  # two cancellation conditions, flattened
    assert [r["cancellation_index"] for r in rows] == [1, 2]
    assert rows[0]["dosha_canonical_id"] == "manglik_dosha"
    assert rows[0]["cancellation_condition_text"] == "Mars in own sign"
    # text_titles join resolved by column name, not position
    assert rows[0]["source_citation"] == "Brihat Parasara Hora Sastra (bphs), ch.9"
    assert rows[0]["source_text_id"] == "bphs"
    assert rows[0]["source_chapter"] == 9
    assert rows[0]["build_id"] == "test-build-6fd72ed9"


def test_run_completes_end_to_end_under_dict_row():
    """The whole computation phase (all three tables) under production config."""
    writer = BgPariharaRulesWriter()
    result = writer.run(_ctx(_conn()))
    # 2 corpus parihara rows + 1 hand-curated ADJUDICATION-10 row, plus the
    # 329-ish activity rows and the census register — all upserted.
    assert result.rows_inserted > 3
    assert "parihara_rules=3" in result.notes
    assert "failed" not in result.notes


# ── Defect 2: §N.8 — failures must raise, never return success-shaped ────────

def test_computation_failure_raises_instead_of_success_shaped_result():
    conn = _conn(fail_on="from classical_texts")
    writer = BgPariharaRulesWriter()
    with pytest.raises(RuntimeError, match="injected failure"):
        writer.run(_ctx(conn))


def test_insert_failure_raises_instead_of_partial_success_result():
    conn = _conn(fail_on="insert into bg_muhurta_activity_rules")
    writer = BgPariharaRulesWriter()
    with pytest.raises(RuntimeError, match="injected failure"):
        writer.run(_ctx(conn))


def test_dry_run_still_returns_without_writing():
    conn = _conn()
    writer = BgPariharaRulesWriter()
    result = writer.run(_ctx(conn, dry_run=True))
    assert result.rows_inserted == 0
    assert result.notes == "dry_run"
    assert conn.executed == []
