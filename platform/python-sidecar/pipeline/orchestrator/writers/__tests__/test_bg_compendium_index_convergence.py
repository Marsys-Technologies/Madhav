"""Regression coverage for the global bg_compendium_index projection."""

from __future__ import annotations

import pytest

from pipeline.orchestrator.writers.bg_compendium_index import _build_desired_rows


def _chunk(
    chunk_id: str,
    *,
    chapter: int | None = 1,
    topic_tag: str | None = "career_general",
    content_en: str = "A classical passage",
) -> dict[str, object]:
    return {
        "id": chunk_id,
        "text_id": "bphs",
        "chapter": chapter,
        "topic_tag": topic_tag,
        "verse_start": 1,
        "verse_end": 2,
        "content_en": content_en,
    }


def test_builds_exact_chapter_and_topic_rows_in_source_order() -> None:
    chapter_rows, topic_rows = _build_desired_rows(
        [
            _chunk("0002", content_en=" second "),
            _chunk("0001", content_en=" first "),
        ],
        frozenset({"career_general"}),
    )

    assert len(chapter_rows) == 1
    assert len(topic_rows) == 1
    assert chapter_rows[0] == (
        "bphs",
        1,
        1,
        2,
        "first … second",
        "bphs chapter 1: 2 passage(s)",
        0.04,
    )
    assert topic_rows[0] == (
        "bphs",
        "career_general",
        1,
        2,
        "first … second",
        "bphs covers career_general in 2 passage(s)",
        0.04,
    )


@pytest.mark.parametrize(
    ("chunk", "message"),
    [
        (_chunk("0001", chapter=None), "NULL chapter"),
        (_chunk("0001", topic_tag="unknown_topic"), "unknown topic_tag"),
    ],
)
def test_rejects_invalid_source_before_replacement(
    chunk: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        _build_desired_rows([chunk], frozenset({"career_general"}))


class _FakeCursor:
    def __init__(self, conn: "_FakeConn") -> None:
        self.conn = conn
        self._rows: list[object] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sql: str, params: object = None) -> None:
        self.conn.statements.append(sql)
        if "FROM classical_text_chunks" in sql:
            self._rows = [_chunk("1")]
        elif "reference_topic_tags" in sql:
            self._rows = [{"canonical_id": "career_general"}]
        elif "pg_indexes" in sql:
            self._rows = [{"present": 1}] if self.conn.index_present else []
        elif "COUNT(*)" in sql:
            self._rows = [{"n": 2}]
        else:
            self._rows = []

    def executemany(self, sql: str, rows: object) -> None:
        self.conn.statements.append(sql)

    def fetchall(self) -> list[object]:
        return self._rows

    def fetchone(self) -> object:
        return self._rows[0] if self._rows else None


class _FakeConn:
    def __init__(self, index_present: bool) -> None:
        self.index_present = index_present
        self.statements: list[str] = []

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)


def _run(conn: _FakeConn):
    from types import SimpleNamespace

    from pipeline.orchestrator.writers.bg_compendium_index import CompendiumIndexWriter

    ctx = SimpleNamespace(db_conn=conn, dry_run=False)
    return CompendiumIndexWriter().run(ctx)  # type: ignore[arg-type]


def test_writer_issues_no_ddl_and_checks_index_read_only() -> None:
    conn = _FakeConn(index_present=True)
    _run(conn)
    joined = "\n".join(conn.statements).upper()
    for forbidden in ("CREATE ", "ALTER ", "DROP ", "TRUNCATE"):
        assert forbidden not in joined
    assert any("pg_indexes" in s for s in conn.statements)


def test_missing_dedup_index_fails_clearly_before_any_delete() -> None:
    conn = _FakeConn(index_present=False)
    with pytest.raises(RuntimeError, match="compendium_dedup_idx"):
        _run(conn)
    assert not any("DELETE" in s.upper() for s in conn.statements)
