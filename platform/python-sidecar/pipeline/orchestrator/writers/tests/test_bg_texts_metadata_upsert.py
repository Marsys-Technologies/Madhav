"""Unit contract for bg_texts metadata-only convergence.

The additive repair path must converge every writer-owned classical_texts
metadata column without touching chunks or pretending that old chunks were
newly ingested.
"""
from __future__ import annotations

from contextlib import contextmanager

import pytest

from brahmagyan.l0_texts import TEXTS
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_texts import (
    TextsWriter,
    _upsert_text_metadata,
    _validate_rebuild_mode,
)


class _RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple) -> None:
        self.calls.append((sql, params))


class _ModeCursor(_RecordingCursor):
    rowcount = 0

    def __init__(self) -> None:
        super().__init__()
        self.next_row = None

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.calls.append((sql, params or ()))
        self.next_row = {"n": 10_651} if "SELECT count(*) AS n" in sql else None

    def fetchone(self):
        return self.next_row


class _PartialCorpusCursor(_ModeCursor):
    def __init__(self, rows):
        super().__init__()
        self.rows = rows

    def execute(self, sql: str, params: tuple | None = None) -> None:
        super().execute(sql, params)
        if "SELECT count(*) AS n" in sql:
            self.next_row = {"n": sum(row.get("row_count", 0) for row in self.rows)}
        elif "WHERE text_id = %s" in sql and "COUNT" in sql:
            self.next_row = {"count": self.rows[0]["row_count"]}

    def fetchall(self):
        return self.rows


class _RecordingConnection:
    def __init__(self, cursor=None) -> None:
        self.cursor_instance = cursor or _RecordingCursor()

    @contextmanager
    def cursor(self):
        yield self.cursor_instance


def test_metadata_upsert_converges_all_owned_columns_but_preserves_ingestion_time():
    conn = _RecordingConnection()

    _upsert_text_metadata(conn, TEXTS[0])

    sql, params = conn.cursor_instance.calls[0]
    conflict_clause = sql.split("ON CONFLICT (text_id) DO UPDATE SET", 1)[1]
    for column in (
        "title_en", "title_sa", "author", "school", "tradition", "tier",
        "license", "license_cleared", "total_chapters", "total_verses",
        "source_edition",
    ):
        assert f"{column}" in conflict_clause
        assert f"EXCLUDED.{column}" in conflict_clause
    assert "ingested_at" not in conflict_clause
    assert params[0] == "bphs"
    assert params[1:12] == (
        TEXTS[0]["title_en"], TEXTS[0]["title_sa"], TEXTS[0]["author"],
        TEXTS[0]["school"], TEXTS[0]["tradition"], TEXTS[0]["tier"],
        TEXTS[0]["license"], TEXTS[0]["license_cleared"],
        TEXTS[0]["total_chapters"], TEXTS[0]["total_verses"],
        TEXTS[0]["source_edition"],
    )


def test_metadata_repair_uses_one_upsert_per_canonical_text():
    conn = _RecordingConnection()

    for text in TEXTS:
        _upsert_text_metadata(conn, text)

    assert len(conn.cursor_instance.calls) == 15
    assert {params[0] for _, params in conn.cursor_instance.calls} == {
        text["text_id"] for text in TEXTS
    }


def test_full_rebuild_is_quarantined_until_staged_selective_replacement_exists():
    assert _validate_rebuild_mode("metadata_only") == "metadata_only"
    assert _validate_rebuild_mode("additive") == "additive"
    with pytest.raises(ValueError, match="full rebuild is quarantined"):
        _validate_rebuild_mode("full")
    with pytest.raises(ValueError, match="unsupported"):
        _validate_rebuild_mode("unexpected")


def test_metadata_only_repairs_registry_without_reading_or_deleting_chunks(monkeypatch):
    cursor = _ModeCursor()
    conn = _RecordingConnection(cursor)
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.bg_texts._download_gcs",
        lambda _path: (_ for _ in ()).throw(AssertionError("source download must not run")),
    )

    result = TextsWriter().run(ContextSpec(
        asset_id="bg_texts",
        build_id="metadata-only-test",
        db_conn=conn,
        config={"rebuild_mode": "metadata_only"},
    ))

    statements = [sql for sql, _ in cursor.calls]
    assert result.rows_inserted == 0
    assert "preserved 10651 existing chunks" in result.notes
    assert sum("INSERT INTO classical_texts" in sql for sql in statements) == 15
    assert not any("DELETE FROM classical_text_chunks" in sql for sql in statements)
    assert not any("SELECT DISTINCT text_id FROM classical_text_chunks" in sql for sql in statements)


def test_additive_mode_rejects_partial_existing_text_instead_of_skipping_it(monkeypatch):
    """One surviving chunk must not make an incomplete canonical text look complete."""
    cursor = _PartialCorpusCursor([{"text_id": "bphs", "row_count": 1}])
    conn = _RecordingConnection(cursor)
    monkeypatch.setattr("pipeline.orchestrator.writers.bg_texts.TEXTS", [TEXTS[0]])

    with pytest.raises(RuntimeError, match="partial canonical text.*bphs"):
        TextsWriter().run(ContextSpec(
            asset_id="bg_texts",
            build_id="partial-text",
            db_conn=conn,
            config={"rebuild_mode": "additive"},
        ))


def test_additive_mode_fails_when_a_required_source_is_unavailable(monkeypatch):
    """A missing immutable source must roll back, not return CONDITIONAL success."""
    cursor = _PartialCorpusCursor([])
    conn = _RecordingConnection(cursor)
    monkeypatch.setattr("pipeline.orchestrator.writers.bg_texts.TEXTS", [TEXTS[0]])
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.bg_texts._download_gcs", lambda _path: None
    )

    with pytest.raises(RuntimeError, match="AWAITING_MANUAL_UPLOAD:bphs"):
        TextsWriter().run(ContextSpec(
            asset_id="bg_texts",
            build_id="missing-source",
            db_conn=conn,
            config={"rebuild_mode": "additive"},
        ))


def test_additive_mode_reports_zero_writes_for_an_exact_existing_text(monkeypatch):
    """Preserved rows are not newly inserted rows in build telemetry."""
    cursor = _PartialCorpusCursor([{"text_id": "bphs", "row_count": 1459}])
    conn = _RecordingConnection(cursor)
    monkeypatch.setattr("pipeline.orchestrator.writers.bg_texts.TEXTS", [TEXTS[0]])

    result = TextsWriter().run(ContextSpec(
        asset_id="bg_texts",
        build_id="exact-existing-text",
        db_conn=conn,
        config={"rebuild_mode": "additive"},
    ))

    assert result.rows_inserted == 0
    assert "bphs:1459" in result.notes
