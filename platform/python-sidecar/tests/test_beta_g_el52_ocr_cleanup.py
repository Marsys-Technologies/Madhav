"""
test_beta_g_el52_ocr_cleanup.py — Elevation Campaign v2.1, Stream β, Lane G (EL-52)

Tests the deterministic OCR-confidence scorer and the hand-vetted cleanup registry added in
brahmagyan/ocr_cleanup.py. No real DB connection (MagicMock conn/cursor).
"""
from __future__ import annotations

from unittest.mock import MagicMock

from brahmagyan.ocr_cleanup import (
    HAND_CLEANED_CHUNKS,
    LOW_CONFIDENCE_THRESHOLD,
    apply_ocr_cleanup,
    score_ocr_confidence,
)

# The exact garbled text reproduced live from ref_remedies_chart_get(affliction="Venus"),
# remedy_id=sweep_venus_japa_1b8a46b9 — the EL-52 named example.
_GARBLED_DEVANAGARI_SEGMENT = "3Tr?Ctrqqqad\nEI€TITfEfrffTq I\n589\nfadtqs.aat*\naflunftqr<r{\n?6{ler\nqfilqfa llqqll"
_LEGIBLE_TRANSLATION_SEGMENT = (
    "88-8g.SimilararetheeffectsofVenusinhissub.periods.\nIf Venus belord of the 2nd or "
    "the 7th(two maraka houses)' there\nwill'be during his Dasa, physical pains and "
    "troubles' To get\nalleviation from those troubles the native should"
)
_CLEAN_ENGLISH = (
    "the 3rd and 8th are the two houses of longevity. The houses related to death are "
    "the 12th from each of these, i.e. the 2nd and 7th are Maraka houses."
)


def test_garbled_devanagari_segment_scores_low():
    score = score_ocr_confidence(_GARBLED_DEVANAGARI_SEGMENT)
    assert score < LOW_CONFIDENCE_THRESHOLD


def test_clean_english_scores_high():
    score = score_ocr_confidence(_CLEAN_ENGLISH)
    assert score >= LOW_CONFIDENCE_THRESHOLD


def test_full_row_including_devanagari_scores_below_threshold():
    """The full raw row (Devanagari noise + legible tail) must still score low overall —
    the garbled portion must not be diluted away by the legible portion into a false-high
    score, since a consumer reading the WHOLE row would still hit the noise."""
    full_row = _GARBLED_DEVANAGARI_SEGMENT + "\n" + _LEGIBLE_TRANSLATION_SEGMENT
    score = score_ocr_confidence(full_row)
    assert score < LOW_CONFIDENCE_THRESHOLD


def test_empty_text_scores_zero():
    assert score_ocr_confidence("") == 0.0
    assert score_ocr_confidence("   ") == 0.0


def test_score_never_exceeds_bounds():
    for text in (_CLEAN_ENGLISH, _GARBLED_DEVANAGARI_SEGMENT, "a", "", "Om Namah Shivaya"):
        s = score_ocr_confidence(text)
        assert 0.0 <= s <= 1.0


def test_named_example_is_hand_cleaned_with_devanagari_unset():
    """B.10 check: the Devanagari segment for the named EL-52 example must be None (not
    guessed), never a fabricated reconstruction."""
    entry = HAND_CLEANED_CHUNKS.get("bphs_pg0581_c01")
    assert entry is not None
    assert entry["cleaned_devanagari_text"] is None
    assert entry["low_confidence_flag"] is True
    assert "maraka" in entry["cleaned_translation_text"].lower()
    assert "not recoverable" in entry["ocr_review_note"].lower() or "not guessed" in entry["ocr_review_note"].lower()


def test_hand_cleaned_translation_matches_live_reproduced_text():
    """Regression pin against the exact live G0 reproduction — the cleaned text must be a
    de-spaced version of what was actually observed, not a paraphrase."""
    entry = HAND_CLEANED_CHUNKS["bphs_pg0581_c01"]
    cleaned = entry["cleaned_translation_text"]
    assert "lord of" in cleaned
    assert "2nd or the 7th" in cleaned
    assert "two maraka houses" in cleaned


def _mock_conn(select_rows):
    conn = MagicMock()
    select_result = MagicMock()
    select_result.fetchall.return_value = select_rows
    conn.execute.return_value = select_result
    cursor_cm = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor_cm
    return conn, cursor_cm


def test_apply_ocr_cleanup_hand_cleans_the_named_chunk_and_scores_others():
    rows = [
        ("bphs_pg0581_c01", _GARBLED_DEVANAGARI_SEGMENT + "\n" + _LEGIBLE_TRANSLATION_SEGMENT),
        ("bphs_pg0439_c01", _CLEAN_ENGLISH),
    ]
    conn, cursor = _mock_conn(rows)
    result = apply_ocr_cleanup(conn, chunk_ids=["bphs_pg0581_c01", "bphs_pg0439_c01"])
    assert result == {"scored": 2, "hand_cleaned": 1}
    assert cursor.execute.call_count == 2


def test_apply_ocr_cleanup_bounds_query_to_given_chunk_ids():
    conn, _cursor = _mock_conn([])
    apply_ocr_cleanup(conn, chunk_ids=["a", "b", "c"])
    select_call = conn.execute.call_args_list[0]
    assert "WHERE chunk_id IN" in select_call.args[0]
    assert select_call.args[1] == ["a", "b", "c"]
