"""
test_l0_remedy_corpus.py — Unit tests for brahmagyan.l0_remedy_corpus (BRAHMA-BG-0-9)

Tests the current generated corpus and the OCR-confidence extraction gate without
requiring a live database.
"""
from __future__ import annotations

from unittest.mock import MagicMock


def _get_mod():
    from brahmagyan import l0_remedy_corpus as mod
    return mod


PLANETS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
# `classical_tradition` added for PARIŚEṢA-V4 owner ruling R-2 (F-23 / F-182):
# the navagraha bīja class is not BPHS material and must not carry a BPHS
# source_canonical_id. It is the value PR #1429 and migration 581 already
# established for the 9 bīja matrix rows; F-182 extends it to the 11 bīja
# domain-scaffold rows. See tests/l0/test_f182_mantra_corpus_sweep.py.
VALID_SOURCES = {"BPHS", "Phaladeepika", "Tajaka", "classical_tradition"}


# ── Constants and data ────────────────────────────────────────────────────────

class TestGeneratedRemedyData:
    def test_volume_floor_gte_50(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 50

    def test_remedies_list_gte_floor(self):
        mod = _get_mod()
        assert len(mod.build_all_remedies()) >= mod.VOLUME_FLOOR

    def test_all_remedies_have_source_citation(self):
        mod = _get_mod()
        for r in mod.build_all_remedies():
            assert r.get("source_citation"), f"Missing source_citation: {r['remedy_id']}"

    def test_all_remedies_have_valid_source_canonical_id(self):
        mod = _get_mod()
        for r in mod.build_all_remedies():
            assert r.get("source_canonical_id") in VALID_SOURCES, (
                f"{r['remedy_id']}: source_canonical_id={r.get('source_canonical_id')}"
            )

    def test_all_remedies_have_valid_planet(self):
        mod = _get_mod()
        for r in mod.build_all_remedies():
            assert r["planet"] in PLANETS, (
                f"{r['remedy_id']}: planet={r['planet']}"
            )

    def test_saturn_career_remedies_gte_3(self):
        mod = _get_mod()
        saturn_career = [
            r for r in mod.build_all_remedies()
            if r["planet"] == "saturn" and r["domain"] == "career"
        ]
        assert len(saturn_career) >= 3, (
            f"Expected >= 3 Saturn/career remedies, got {len(saturn_career)}"
        )

    def test_all_planets_covered(self):
        mod = _get_mod()
        covered = {r["planet"] for r in mod.build_all_remedies()}
        assert covered == PLANETS, f"Missing planets: {PLANETS - covered}"

    def test_all_remedy_ids_unique(self):
        mod = _get_mod()
        ids = [r["remedy_id"] for r in mod.build_all_remedies()]
        assert len(ids) == len(set(ids)), "Duplicate remedy_ids found"

    def test_all_remedies_have_prescription_text(self):
        mod = _get_mod()
        for r in mod.build_all_remedies():
            assert r.get("prescription_text"), f"Missing prescription_text: {r['remedy_id']}"

    def test_all_confidences_in_range(self):
        mod = _get_mod()
        for r in mod.build_all_remedies():
            conf = r.get("confidence", 0)
            assert 0.0 <= conf <= 1.0, (
                f"{r['remedy_id']}: confidence={conf} out of [0,1]"
            )


# ── check_volume ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    def test_dry_run_matches_current_generated_live_projection(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        expected_live = sum(
            r.get("scaffold_status") == "live" for r in mod.build_all_remedies()
        )
        expected_status = "GREEN" if expected_live >= mod.CAMPAIGN_FLOOR else "AMBER"
        assert result["status"] == expected_status
        assert result["asset"] == "brahmagyan.remedy_corpus"
        assert result["actual_rows"] == expected_live

    def _make_mock_conn(
        self,
        total_count: int,
    ):
        cursor = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.return_value = (total_count,)
        return conn

    def test_empty_when_zero_rows(self):
        mod = _get_mod()
        conn = self._make_mock_conn(0)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "EMPTY"

    def test_amber_when_below_floor(self):
        mod = _get_mod()
        conn = self._make_mock_conn(10)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "AMBER"

    def test_green_when_at_floor(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.CAMPAIGN_FLOOR)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "GREEN"

# ── F-144: sweep_classical_text_chunks OCR-confidence gating ──────────────────
#
# Prior behaviour: scaffold_status was gated only on marker/planet uniqueness,
# never on whether the extracted text was legible at all. Live production check
# (2026-08-21, corrected post-GA5-re-review -- the original "29/49" estimate in
# an earlier version of this PR did not reproduce and is not used here) found
# 35/49 corpus_sweep rows score below the already-established
# LOW_CONFIDENCE_THRESHOLD (0.55, from brahmagyan.ocr_cleanup, EL-52), 31 of
# them currently served scaffold_status='live' -- including the EL-52
# hand-documented named example (sweep_venus_japa_1b8a46b9 / chunk
# bphs_pg0581_c01, "3Tr?Ctrqqqad
# EI€TITfEfrffTq"), which a prior lane had already flagged as garbled OCR.

class TestSweepOcrConfidenceGating:
    def _row(self, conn, content_en, chunk_id="test_chunk_c01", source_citation="Test Ch.1"):
        cur = MagicMock()
        cur.fetchall.return_value = [(chunk_id, "text_id_1", source_citation, content_en)]
        conn.cursor.return_value.__enter__.return_value = cur
        mod = _get_mod()
        return mod.sweep_classical_text_chunks(conn)

    def test_garbled_ocr_text_never_promoted_to_live(self):
        # The actual EL-52 named-example garbled text (single marker "mantra",
        # single planet "Venus" -- would previously have auto-promoted to 'live'
        # purely on uniqueness).
        garbled = (
            "Chapter 47\n3Tr?Ctrqqqad\nEI€TITfEfrffTq I\n589\nfadtqs.aat*\n"
            "aflunftqr<r{\n?6{ler\nqfilqfa llqqll\nqr aqrcti qt( |\ng\nei\n"
            "€ai TTi q{Fft Eemrrt'lni\nIf Venus be lord of the mantra"
        )
        conn = MagicMock()
        rows = self._row(conn, garbled)
        assert len(rows) == 1
        assert rows[0]["scaffold_status"] == "review", (
            "garbled OCR text with a single unique marker+planet must NOT "
            "auto-promote to 'live' -- this is the exact defect class F-144 fixes"
        )

    def test_legible_english_text_still_promoted_to_live(self):
        # Deliberately avoids any OTHER marker word (e.g. "recite" would itself
        # match the japa marker and force multi_marker=True/'review' regardless
        # of legibility -- that's correct pre-existing behavior, just not what
        # this test is isolating).
        legible = (
            "If Venus is the lord of the 7th house and well placed, the native "
            "benefits from the Venus mantra daily during the Venus dasha, "
            "reducing marital discord for lasting harmony in the home."
        )
        conn = MagicMock()
        rows = self._row(conn, legible)
        assert len(rows) == 1
        assert rows[0]["scaffold_status"] == "live", (
            "genuinely legible single-marker single-planet text should still "
            "earn 'live' -- this fix must not blanket-demote everything"
        )

    def test_multi_marker_still_forces_review_regardless_of_legibility(self):
        legible_but_ambiguous = (
            "For Venus afflictions, the native may wear a gemstone, recite a "
            "mantra, or worship at a temple depending on the dasha period."
        )
        conn = MagicMock()
        rows = self._row(conn, legible_but_ambiguous)
        assert len(rows) == 1
        assert rows[0]["scaffold_status"] == "review", (
            "multi-marker ambiguity must still force review even when the "
            "text itself is perfectly legible -- pre-existing behavior preserved"
        )
