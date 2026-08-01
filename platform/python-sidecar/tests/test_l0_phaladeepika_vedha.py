"""Tests for brahmagyan.l0_phaladeepika_vedha — the two cited L0 vedha
reference tables ADJUDICATION-11 Part 4 mandates for R-19 closure
(Phaladeepika PG353 malefic-count scale + PG338-339 Lattā rule).

Pure-data assertions only (no DB) — the seed functions themselves are
exercised indirectly via test_ka_vedha_gochara_writer.py's fetch-function
tests (which use fixture data, not this module's real rows) and via a real
throwaway-Postgres run (not part of this CI-facing suite).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brahmagyan.l0_phaladeepika_vedha import (
    AFFLICTION_CONDITION,
    LATTA_ROWS,
    MALEFIC_SCALE_ROWS,
    TABLE_VERSION,
)


class TestMaleficScaleRows:
    def test_exactly_five_rows(self):
        assert len(MALEFIC_SCALE_ROWS) == 5

    def test_counts_are_1_through_5(self):
        assert {r[0] for r in MALEFIC_SCALE_ROWS} == {1, 2, 3, 4, 5}

    def test_grades_match_pg353_verbatim_order(self):
        # "fear, failure, killing (blood-shed), death and ignominy respectively"
        grades_by_count = {r[0]: r[1] for r in MALEFIC_SCALE_ROWS}
        assert grades_by_count[1] == "fear"
        assert grades_by_count[2] == "failure"
        assert grades_by_count[3] == "killing"
        assert grades_by_count[4] == "death"
        assert grades_by_count[5] == "ignominy"


class TestLattaRows:
    def test_exactly_eight_grahas(self):
        assert len(LATTA_ROWS) == 8

    def test_ketu_deliberately_absent(self):
        grahas = {r[0] for r in LATTA_ROWS}
        assert "Ketu" not in grahas
        assert grahas == {"Sun", "Mars", "Jupiter", "Saturn", "Venus", "Mercury", "Rahu", "Moon"}

    def test_forward_grahas_match_pg338_sloka_42_44(self):
        by_graha = {r[0]: (r[1], r[2]) for r in LATTA_ROWS}
        assert by_graha["Sun"] == (12, "forward")
        assert by_graha["Mars"] == (3, "forward")
        assert by_graha["Jupiter"] == (6, "forward")
        assert by_graha["Saturn"] == (8, "forward")

    def test_backward_grahas_match_pg338_339_sloka_42_44(self):
        by_graha = {r[0]: (r[1], r[2]) for r in LATTA_ROWS}
        assert by_graha["Venus"] == (5, "backward")
        assert by_graha["Mercury"] == (7, "backward")
        assert by_graha["Rahu"] == (9, "backward")
        assert by_graha["Moon"] == (22, "backward")

    def test_mars_and_saturn_have_no_stated_effect_disclosed_gap(self):
        by_graha = {r[0]: r[3] for r in LATTA_ROWS}
        assert by_graha["Mars"] is None
        assert by_graha["Saturn"] is None

    def test_other_six_grahas_have_a_stated_effect(self):
        by_graha = {r[0]: r[3] for r in LATTA_ROWS}
        for graha in ("Sun", "Jupiter", "Venus", "Mercury", "Rahu", "Moon"):
            assert by_graha[graha] is not None and len(by_graha[graha]) > 0


class TestVersioning:
    def test_table_version_zero_padded(self):
        assert TABLE_VERSION == "phaladeepika_vedha_v01"


class TestAfflictionCondition:
    def test_condition_text_present_and_nonempty(self):
        assert "Janma-nakshatra" in AFFLICTION_CONDITION
        assert "Latta star" in AFFLICTION_CONDITION
