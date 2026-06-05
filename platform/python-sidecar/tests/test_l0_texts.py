"""
test_l0_texts.py — Unit tests for brahmagyan.l0_texts (BRAHMA-BG-0-3)

Tests:
    1. Volume floor: >= 4 texts, >= 50 chunks
    2. All texts have license_cleared=True
    3. BPHS is text_id='bphs' (canonical)
    4. read_text('bphs', 'CH1:V1') resolves
    5. read_text('bphs', 'CH3:V1') resolves (exaltation chapter)
    6. read_text('bphs') returns all BPHS chunks
    7. All seed chunks have non-empty content_en
    8. All seed chunks have verse_ref derivable from chapter/verse
    9. seed_texts dry_run returns correct counts without DB
    10. read_text returns None for unknown verse_ref
    11. Topics coverage: planetary aspects covered
    12. Jaimini text present
    13. All texts have source_edition or license

No live DB required.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest


def _get_module():
    from brahmagyan import l0_texts as mod
    return mod


class TestVolumeFloor:
    def test_texts_gte_4(self):
        mod = _get_module()
        assert len(mod.TEXTS) >= 4

    def test_chunks_gte_50(self):
        mod = _get_module()
        assert len(mod.SEED_CHUNKS) >= 50, \
            f"Need >= 50 chunks, got {len(mod.SEED_CHUNKS)}"

    def test_bphs_chunks_gte_20(self):
        mod = _get_module()
        bphs_chunks = [c for c in mod.SEED_CHUNKS if c[0] == "bphs"]
        assert len(bphs_chunks) >= 20, \
            f"Need >= 20 BPHS chunks, got {len(bphs_chunks)}"


class TestTextRegistry:
    def test_bphs_present(self):
        mod = _get_module()
        text_ids = {t["text_id"] for t in mod.TEXTS}
        assert "bphs" in text_ids

    def test_all_texts_license_cleared(self):
        mod = _get_module()
        for t in mod.TEXTS:
            assert t["license_cleared"] is True, \
                f"Text {t['text_id']} not license cleared"

    def test_all_texts_have_school(self):
        mod = _get_module()
        for t in mod.TEXTS:
            assert t.get("school"), f"Missing school for text {t['text_id']}"

    def test_all_texts_have_license(self):
        mod = _get_module()
        for t in mod.TEXTS:
            assert t.get("license"), f"Missing license for {t['text_id']}"

    def test_jaimini_present(self):
        mod = _get_module()
        schools = {t["school"] for t in mod.TEXTS}
        assert "jaimini" in schools, "Need at least one Jaimini text"

    def test_bphs_is_tier_1(self):
        mod = _get_module()
        bphs = next(t for t in mod.TEXTS if t["text_id"] == "bphs")
        assert bphs["tier"] == 1


class TestReadText:
    def test_read_bphs_ch1_v1_resolves(self):
        mod = _get_module()
        result = mod.read_text("bphs", "CH1:V1")
        assert result is not None
        assert result["text_id"] == "bphs"
        assert "CH1" in result["verse_ref"]

    def test_read_bphs_ch3_v1_resolves(self):
        """CH3 = exaltation chapter — critical for position verification."""
        mod = _get_module()
        result = mod.read_text("bphs", "CH3:V1")
        assert result is not None
        assert "exalt" in result["content_en"].lower() or "exalt" in result["summary"].lower()

    def test_read_bphs_ch26_v1_resolves(self):
        """CH26 = aspects chapter."""
        mod = _get_module()
        result = mod.read_text("bphs", "CH26:V1")
        assert result is not None
        assert "aspect" in result["content_en"].lower() or "drishti" in result["content_en"].lower()

    def test_read_bphs_returns_all_chunks(self):
        mod = _get_module()
        result = mod.read_text("bphs")
        assert isinstance(result, list)
        assert len(result) >= 20

    def test_read_unknown_text_returns_empty(self):
        mod = _get_module()
        result = mod.read_text("unknown_text")
        assert result == []

    def test_read_unknown_verse_ref_returns_none(self):
        mod = _get_module()
        result = mod.read_text("bphs", "CH99:V999")
        assert result is None

    def test_read_returns_source_citation(self):
        mod = _get_module()
        result = mod.read_text("bphs", "CH1:V1")
        assert result is not None
        assert result.get("source_citation")


class TestChunkIntegrity:
    def test_all_chunks_have_content_en(self):
        mod = _get_module()
        for chunk in mod.SEED_CHUNKS:
            text_id, chapter, v_start, v_end = chunk[0], chunk[1], chunk[2], chunk[3]
            content_en = chunk[5]
            assert content_en, \
                f"Empty content_en for {text_id} CH{chapter}:V{v_start}"
            assert len(content_en) > 10, \
                f"content_en too short for {text_id} CH{chapter}:V{v_start}"

    def test_all_chunks_have_topics(self):
        mod = _get_module()
        for chunk in mod.SEED_CHUNKS:
            topics = chunk[7]
            assert topics, \
                f"Empty topics for {chunk[0]} CH{chunk[1]}:V{chunk[2]}"
            assert len(topics) >= 1

    def test_drishti_topic_covered(self):
        mod = _get_module()
        all_topics = set()
        for chunk in mod.SEED_CHUNKS:
            all_topics.update(chunk[7])
        assert "drishti" in all_topics or "aspect" in all_topics, \
            "Need at least one chunk with drishti/aspect topic"

    def test_exaltation_topic_covered(self):
        mod = _get_module()
        all_topics = set()
        for chunk in mod.SEED_CHUNKS:
            all_topics.update(chunk[7])
        assert "exaltation" in all_topics or "uccha" in all_topics, \
            "Need at least one chunk with exaltation topic"


class TestDryRun:
    def test_dry_run_counts_correct(self):
        mod = _get_module()
        result = mod.seed_texts(conn=None, dry_run=True)
        assert result["classical_texts"] >= 4
        assert result["classical_text_chunks"] >= 50

    def test_dry_run_no_db_writes(self):
        mod = _get_module()
        mock_conn = MagicMock()
        mod.seed_texts(conn=mock_conn, dry_run=True)
        mock_conn.cursor.assert_not_called()
        mock_conn.commit.assert_not_called()
