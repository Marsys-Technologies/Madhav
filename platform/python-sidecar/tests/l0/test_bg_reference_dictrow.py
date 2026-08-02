"""
Regression tests for bg_reference's production KeyError: 0 (2026-08-02 L0
global build, run 6fd72ed9).

Root cause: the orchestrator connection's row_factory is dict_row
(pipeline/orchestrator/db.py:26), but the delegate
brahmagyan.l0_reference.seed_reference indexes fetched rows numerically
(l0_reference.py:1418 — `{r[0] for r in cur.fetchall()}` on the
brahma_ontology FK-validation query) → KeyError: 0. bg_reference correctly
re-raised, so the asset landed in error state (unlike bg_parihara_rules'
swallow) — but the crash itself was never caught by tests because the old
tests only exercised tuple-row/mock shapes.

l0_reference.py is outside this lane's file contract, so the fix lives at the
bg_reference boundary: pin `row_factory=tuple_row` on the connection for the
duration of the seed_reference call and restore the caller's factory in a
finally. These tests run the REAL seed_reference against a fake connection
whose default row factory is dict_row, like production.
"""
from __future__ import annotations

import pytest
import psycopg.rows

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_reference import ReferenceWriter
from tests.l0._dictrow_fakes import FakeDictRowConnection

_ONTOLOGY_COLS = ["canonical_id"]
_ONTOLOGY_ROWS = [("sun",), ("moon",), ("mars",)]


def _conn(ontology_rows=_ONTOLOGY_ROWS, **kwargs) -> FakeDictRowConnection:
    return FakeDictRowConnection(
        tables=[("from brahma_ontology", _ONTOLOGY_COLS, ontology_rows)],
        **kwargs,
    )


def _ctx(conn, dry_run: bool = False) -> ContextSpec:
    return ContextSpec(
        asset_id="bg_reference",
        build_id="test-build-6fd72ed9",
        db_conn=conn,
        dry_run=dry_run,
    )


def test_run_completes_under_dict_row_connection():
    """Reproduces the production KeyError: 0 — run() must survive dict_row."""
    conn = _conn()
    result = ReferenceWriter().run(_ctx(conn))
    assert result.rows_inserted > 0
    assert "reference_planets" in result.notes


def test_row_factory_restored_after_success():
    conn = _conn()
    ReferenceWriter().run(_ctx(conn))
    assert conn.row_factory is psycopg.rows.dict_row


def test_failure_raises_and_row_factory_restored():
    """§N.8: a delegate failure propagates (no success-shaped swallow), and the
    connection's row factory is restored even on the failure path."""
    conn = _conn(ontology_rows=[])  # empty brahma_ontology → seed_reference raises
    with pytest.raises(ValueError, match="brahma_ontology is empty"):
        ReferenceWriter().run(_ctx(conn))
    assert conn.row_factory is psycopg.rows.dict_row


def test_dry_run_returns_counts_without_writing():
    conn = _conn()
    result = ReferenceWriter().run(_ctx(conn, dry_run=True))
    assert result.rows_inserted > 0  # dry_run counts the in-memory corpus
    assert conn.executed == []
