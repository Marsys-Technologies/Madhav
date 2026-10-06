"""
tests/test_ga_nakshatra_narr_golden.py -- Narr golden-value test for ga_nakshatra

``chart_facts.citation_human`` is narration: the sentence a reader sees for a nakshatra fact
(CLAUDE.md section N.7 item 5: verified fact != verified prose).

What this pins, on the pure function ``_enrich_rows`` (no database): the citation restates the
row exactly as '{subject} {key}: {value} [{category}]'. For the native's Moon in Purva
Bhadrapada, the Vimshottari nakshatra lord of Purva Bhadrapada is Jupiter (classical: the
lord of the 25th nakshatra), so the Moon's nakshatra_lord join row must read Jupiter; a
numeric row restates its number; a row with no value restates only subject, key, category.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.ga_nakshatra import _enrich_rows


def _row(subject: str, key: str, text, num) -> dict:
    return {
        "chart_id": "chart-fixture",
        "ayanamsha_id": "lahiri",
        "build_id": "build-fixture",
        "fact_category": "graha_nakshatra_join",
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": text,
        "fact_value_num": num,
        "source_calculation": "fixture",
    }


def test_nakshatra_citation_human_restates_subject_key_value_category() -> None:
    enriched = _enrich_rows(
        [
            _row("MOON", "nakshatra_lord", "Jupiter", None),
            _row("MOON", "nakshatra_id_ref", None, 25.0),
        ],
        "test-eng",
        "2026-01-01T00:00:00+00:00",
    )
    citation_human = enriched[0]["citation_human"]

    assert citation_human == "MOON nakshatra_lord: Jupiter [graha_nakshatra_join]"
    assert enriched[1]["citation_human"] == "MOON nakshatra_id_ref: 25.0 [graha_nakshatra_join]"
