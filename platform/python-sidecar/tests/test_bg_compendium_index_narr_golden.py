"""Narr golden-value test for bg_compendium_index.significance.

Pure function ``_build_desired_rows`` (no database). ``significance`` is the one-line
sentence stating how many passages a chapter / topic row aggregates; the expected
sentences below are written by hand from the writer's template, not read from it.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bg_compendium_index import _build_desired_rows


def _chunk(cid: int, text_id: str, chapter: int, topic_tag, vs: int, ve: int) -> dict:
    return {
        "id": cid,
        "text_id": text_id,
        "chapter": chapter,
        "topic_tag": topic_tag,
        "verse_start": vs,
        "verse_end": ve,
        "content_en": f"passage {cid}",
    }


def test_bg_compendium_index_significance_states_the_passage_count():
    chunks = [
        _chunk(1, "BPHS", 3, "yoga", 1, 4),
        _chunk(2, "BPHS", 3, "yoga", 5, 9),
        _chunk(3, "BPHS", 4, None, 1, 2),
    ]
    chapter_rows, topic_rows = _build_desired_rows(chunks, frozenset({"yoga"}))

    # chapter rows are sorted by (text_id, chapter): BPHS ch.3 (2 chunks) then ch.4 (1 chunk).
    # column order of the INSERT: text_id, chapter_num, verse_start, verse_end,
    # summary_text, significance, classical_significance_score
    significance = chapter_rows[0][5]
    assert significance == "BPHS chapter 3: 2 passage(s)"
    significance = chapter_rows[1][5]
    assert significance == "BPHS chapter 4: 1 passage(s)"

    # only the two tagged chunks form the topic row
    significance = topic_rows[0][5]
    assert significance == "BPHS covers yoga in 2 passage(s)"
    assert len(topic_rows) == 1
