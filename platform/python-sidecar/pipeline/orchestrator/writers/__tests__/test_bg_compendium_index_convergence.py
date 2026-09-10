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
