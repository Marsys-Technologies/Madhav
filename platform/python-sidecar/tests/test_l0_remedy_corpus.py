"""
test_l0_remedy_corpus.py — Unit tests for brahmagyan.l0_remedy_corpus (BRAHMA-BG-0-9)

Tests (all pass without live DB):
  1. VOLUME_FLOOR is >= 50
  2. REMEDIES has >= 50 entries
  3. All REMEDIES have source_citation non-null
  4. All REMEDIES have source_canonical_id in ('BPHS','Phaladeepika','Tajaka')
  5. All REMEDIES have planet in the 9 classical grahas
  6. Saturn career remedies >= 3 in REMEDIES
  7. check_volume: dry_run returns GREEN (in-memory count >= floor)
  8. check_volume: dry_run saturn_career_check passes
  9. check_volume: dry_run source_citation_check passes
  10. check_volume: EMPTY when DB table has 0 rows
  11. check_volume: AMBER when 0 < rows < floor
  12. check_volume: GREEN when rows >= floor
  13. check_volume: saturn_career_check passes when >= 1 row
  14. check_volume: saturn_career_check fails when 0 rows
  15. query_remedy: returns in_memory when DB unavailable
  16. query_remedy: Saturn career returns >= 1 in_memory remedy
  17. query_remedy: provenance_envelope present
  18. query_remedy: count matches remedies length
  19. query_remedy: planet filter works on in_memory
  20. query_remedy: domain filter works on in_memory
  21. query_remedy: remedy_type filter works on in_memory
  22. _in_memory_query: planet+domain filter combined
  23. _in_memory_query: returns all if no filters
  24. query_remedy: 'Sun debilitated' equivalent — Sun domain='general' returns >= 1 result
  25. All planets covered in REMEDIES (9 grahas)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest


def _get_mod():
    from brahmagyan import l0_remedy_corpus as mod
    return mod


PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
# `classical_tradition` added for PARIŚEṢA-V4 owner ruling R-2 (F-23 / F-182):
# the navagraha bīja class is not BPHS material and must not carry a BPHS
# source_canonical_id. It is the value PR #1429 and migration 581 already
# established for the 9 bīja matrix rows; F-182 extends it to the 11 bīja
# domain-scaffold rows. See tests/l0/test_f182_mantra_corpus_sweep.py.
VALID_SOURCES = {"BPHS", "Phaladeepika", "Tajaka", "classical_tradition"}


# ── Constants and data ────────────────────────────────────────────────────────

class TestRemedyData:
    def test_volume_floor_gte_50(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 50

    def test_remedies_list_gte_floor(self):
        mod = _get_mod()
        assert len(mod.REMEDIES) >= mod.VOLUME_FLOOR

    def test_all_remedies_have_source_citation(self):
        mod = _get_mod()
        for r in mod.REMEDIES:
            assert r.get("source_citation"), f"Missing source_citation: {r['remedy_id']}"

    def test_all_remedies_have_valid_source_canonical_id(self):
        mod = _get_mod()
        for r in mod.REMEDIES:
            assert r.get("source_canonical_id") in VALID_SOURCES, (
                f"{r['remedy_id']}: source_canonical_id={r.get('source_canonical_id')}"
            )

    def test_all_remedies_have_valid_planet(self):
        mod = _get_mod()
        for r in mod.REMEDIES:
            assert r["planet"] in PLANETS, (
                f"{r['remedy_id']}: planet={r['planet']}"
            )

    def test_saturn_career_remedies_gte_3(self):
        mod = _get_mod()
        saturn_career = [
            r for r in mod.REMEDIES
            if r["planet"] == "Saturn" and r["domain"] == "career"
        ]
        assert len(saturn_career) >= 3, (
            f"Expected >= 3 Saturn/career remedies, got {len(saturn_career)}"
        )

    def test_all_planets_covered(self):
        mod = _get_mod()
        covered = {r["planet"] for r in mod.REMEDIES}
        assert covered == PLANETS, f"Missing planets: {PLANETS - covered}"

    def test_all_remedy_ids_unique(self):
        mod = _get_mod()
        ids = [r["remedy_id"] for r in mod.REMEDIES]
        assert len(ids) == len(set(ids)), "Duplicate remedy_ids found"

    def test_all_remedies_have_prescription_text(self):
        mod = _get_mod()
        for r in mod.REMEDIES:
            assert r.get("prescription_text"), f"Missing prescription_text: {r['remedy_id']}"

    def test_all_confidences_in_range(self):
        mod = _get_mod()
        for r in mod.REMEDIES:
            conf = r.get("confidence", 0)
            assert 0.0 <= conf <= 1.0, (
                f"{r['remedy_id']}: confidence={conf} out of [0,1]"
            )


# ── check_volume ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    def test_dry_run_returns_green(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        assert result["status"] == "GREEN"
        assert result["asset"] == "brahmagyan.remedy_corpus"

    def test_dry_run_saturn_career_check_passes(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        assert result["saturn_career_check"]["status"] == "PASS"
        assert result["saturn_career_check"]["count"] >= 3

    def test_dry_run_citation_check_passes(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        assert result["source_citation_check"]["status"] == "PASS"

    def test_dry_run_actual_rows_matches_data(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        assert result["actual_rows"] == len(mod.REMEDIES)

    def _make_mock_conn(
        self,
        total_count: int,
        saturn_career_count: int,
        null_citation: int = 0,
    ):
        cursor = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.side_effect = [
            (total_count,),
            (saturn_career_count,),
            (null_citation,),
        ]
        return conn

    def test_empty_when_zero_rows(self):
        mod = _get_mod()
        conn = self._make_mock_conn(0, 0)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "EMPTY"

    def test_amber_when_below_floor(self):
        mod = _get_mod()
        conn = self._make_mock_conn(10, 2)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "AMBER"

    def test_green_when_at_floor(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 3)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "GREEN"

    def test_saturn_career_check_pass(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 3)
        result = mod.check_volume(conn=conn)
        assert result["saturn_career_check"]["status"] == "PASS"

    def test_saturn_career_check_fail(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 0)
        result = mod.check_volume(conn=conn)
        assert result["saturn_career_check"]["status"] == "FAIL"


# ── query_remedy ──────────────────────────────────────────────────────────────

class TestQueryRemedy:
    def test_in_memory_when_db_unavailable(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(planet="Saturn", domain="career")
        assert result["ok"] is True
        assert result["source"] == "in_memory"

    def test_saturn_career_returns_results(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(planet="Saturn", domain="career")
        assert result["count"] >= 1
        # All results should be Saturn career
        for r in result["remedies"]:
            assert r["planet"] == "Saturn"
            assert r["domain"] == "career"

    def test_provenance_envelope_present(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy()
        assert "provenance_envelope" in result
        env = result["provenance_envelope"]
        assert env["source"] == "brahmagyan.remedy_corpus"
        assert env["asset"] == "BRAHMA-BG-0-9"

    def test_count_matches_remedies_length(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(planet="Saturn")
        assert result["count"] == len(result["remedies"])

    def test_planet_filter_in_memory(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(planet="Jupiter")
        assert all(r["planet"] == "Jupiter" for r in result["remedies"])

    def test_domain_filter_in_memory(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(domain="health")
        assert all(r["domain"] == "health" for r in result["remedies"])

    def test_remedy_type_filter_in_memory(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(remedy_type="mantra")
        assert all(r["remedy_type"] == "mantra" for r in result["remedies"])

    def test_sun_debilitated_returns_results(self):
        """Sun domain='general' returns >= 1 result (covers debilitated Sun queries)."""
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(planet="Sun", domain="general")
        assert result["count"] >= 1

    def test_no_filter_returns_all_up_to_limit(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_remedy(limit=100)
        assert result["count"] == min(100, len(mod.REMEDIES))


# ── _in_memory_query ──────────────────────────────────────────────────────────

class TestInMemoryQuery:
    def test_combined_filter_planet_domain(self):
        mod = _get_mod()
        result = mod._in_memory_query("Saturn", "career", None, 100)
        assert all(
            r["planet"] == "Saturn" and r["domain"] == "career"
            for r in result["remedies"]
        )

    def test_no_filters_returns_all(self):
        mod = _get_mod()
        result = mod._in_memory_query(None, None, None, 1000)
        assert result["count"] == len(mod.REMEDIES)

    def test_limit_respected(self):
        mod = _get_mod()
        result = mod._in_memory_query(None, None, None, 5)
        assert result["count"] == 5
        assert len(result["remedies"]) == 5

    def test_source_is_in_memory(self):
        mod = _get_mod()
        result = mod._in_memory_query("Sun", None, None, 10)
        assert result["source"] == "in_memory"


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
