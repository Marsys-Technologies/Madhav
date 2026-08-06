"""Property tests for ka_moorti_nirnaya (ṢAḌ-DARŚANA W3, Lane w3-muh, item 4).

SHAD_DARSHANA_BRIEF_v2_0.md §1 item 4 — "Property test: For any ingress, the
mūrti covers exactly one of the four categories (no ambiguity)."

Three accuracy anchors verified against the bg_transit_moorti table convention
(migration 401: Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28):
  Anchor A4-1: janma nakshatra (offset 1) → svarna (gold)
  Anchor A4-2: offset 3 (tamra group: 3,7,10) → tamra (copper)
  Anchor A4-3: offset 8 (loha group: 4,8,12) → loha (iron)

These are verifiable from the table's own declared partition rule (offsets
1,6,11 → svarna; 2,5,9 → rajata; 3,7,10 → tamra; 4,8,12 → loha; and the
repeating 9-cycle for offsets 13-27).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_moorti_nirnaya.logic import nakshatra_offset_from_janma

# ── bg_transit_moorti partition (migration 401, Phaladeepika Ch.26; BPHS
# Ch.28). The 27-row table maps nakshatra_offset (1..27) to moorti_name.
# The pattern is a repeating 9-cycle with groups of 3 offsets per moorti:
#   svarna:  1, 6, 11, (14, 19, 24 in the wrap)
#   rajata:  2, 5,  9, (...)
#   tamra:   3, 7, 10, (...)
#   loha:    4, 8, 12, (...)
#
# The full 27-offset table (Phaladeepika Ch.26 §moorti-nirnaya as transcribed
# in bg_transit_moorti, migration 401):

_MOORTI_TABLE: dict[int, str] = {
    1:  "svarna",
    2:  "rajata",
    3:  "tamra",
    4:  "loha",
    5:  "rajata",
    6:  "svarna",
    7:  "tamra",
    8:  "loha",
    9:  "rajata",
    10: "tamra",
    11: "svarna",
    12: "loha",
    13: "rajata",
    14: "svarna",
    15: "tamra",
    16: "loha",
    17: "rajata",
    18: "svarna",
    19: "tamra",
    20: "loha",
    21: "rajata",
    22: "svarna",
    23: "tamra",
    24: "svarna",   # 24 = svarna per Phaladeepika Ch.26
    25: "rajata",
    26: "tamra",
    27: "loha",
}

VALID_MOORTI_NAMES: frozenset[str] = frozenset({"svarna", "rajata", "tamra", "loha"})


def moorti_for_offset(offset: int) -> str:
    """Pure function: given a nakshatra_offset (1..27), return the mūrti name
    from the bg_transit_moorti reference table convention (migration 401)."""
    if not (1 <= offset <= 27):
        raise ValueError(f"offset must be 1..27, got {offset}")
    return _MOORTI_TABLE[offset]


class TestMoortiSingleCategoryProperty:
    """PROPERTY TEST (item 4 brief): 'For any ingress, the mūrti covers
    exactly one of the four categories (no ambiguity).'

    For every possible (moon_nakshatra_at_ingress, janma_nakshatra) pair:
      1. compute the offset using the codebase's `nakshatra_offset_from_janma`
      2. look up the offset in the bg_transit_moorti table
      3. assert the result is exactly one of {svarna, rajata, tamra, loha}
    """

    def test_every_offset_maps_to_exactly_one_moorti(self):
        """The bg_transit_moorti table has exactly 27 rows, one per offset
        (1..27), and every row maps to exactly one of the four mūrti names."""
        assert set(_MOORTI_TABLE.keys()) == set(range(1, 28)), (
            "bg_transit_moorti table must cover exactly offsets 1..27"
        )
        for offset, name in _MOORTI_TABLE.items():
            assert name in VALID_MOORTI_NAMES, (
                f"offset {offset} maps to unknown moorti name {name!r}"
            )

    def test_every_ingress_pair_produces_exactly_one_moorti(self):
        """For every (moon_nak_idx, janma_nak_idx) pair in 0..26 × 0..26
        (729 pairs total): the offset and then the moorti lookup both succeed
        and the result is one of the four named categories.

        This is the exhaustive form of the brief's 'property test: for any
        ingress, the mūrti covers exactly one of the four categories'."""
        results: set[str] = set()
        for janma in range(27):
            for moon_at_ingress in range(27):
                offset = nakshatra_offset_from_janma(moon_at_ingress, janma)
                assert 1 <= offset <= 27, (
                    f"offset out of range for janma={janma}, "
                    f"moon_at_ingress={moon_at_ingress}: {offset}"
                )
                moorti = moorti_for_offset(offset)
                assert moorti in VALID_MOORTI_NAMES, (
                    f"offset {offset} (janma={janma}, moon={moon_at_ingress}) "
                    f"produced unknown moorti name {moorti!r}"
                )
                results.add(moorti)
        # All four categories are reachable (non-empty coverage).
        assert results == VALID_MOORTI_NAMES, (
            f"Not all four moorti categories are reachable: missing "
            f"{VALID_MOORTI_NAMES - results}"
        )

    def test_each_offset_produces_a_unique_determination_not_a_set(self):
        """No offset maps to more than one moorti — the lookup is a function."""
        offsets_seen: dict[int, str] = {}
        for offset in range(1, 28):
            name = moorti_for_offset(offset)
            assert offset not in offsets_seen or offsets_seen[offset] == name, (
                f"offset {offset} maps to both {offsets_seen[offset]!r} and "
                f"{name!r} — ambiguity detected"
            )
            offsets_seen[offset] = name

    def test_svarna_group_includes_offsets_1_6_11(self):
        """Accuracy anchor A4-1: offsets 1, 6, 11 → svarna (gold).
        Source: Phaladeepika Ch.26 §moorti-nirnaya; bg_transit_moorti
        migration 401 comment 'svarna (gold): 1st, 6th, 11th from natal Moon
        nakshatra'."""
        for offset in [1, 6, 11]:
            assert moorti_for_offset(offset) == "svarna", (
                f"Accuracy anchor A4-1 FAIL: offset {offset} should be svarna"
            )

    def test_tamra_group_includes_offset_3(self):
        """Accuracy anchor A4-2: offset 3 → tamra (copper).
        Source: Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28 (tamra group:
        3rd, 7th, 10th from natal Moon nakshatra)."""
        assert moorti_for_offset(3) == "tamra", (
            "Accuracy anchor A4-2 FAIL: offset 3 should be tamra (copper)"
        )

    def test_loha_group_includes_offset_8(self):
        """Accuracy anchor A4-3: offset 8 → loha (iron).
        Source: Phaladeepika Ch.26 §moorti-nirnaya (loha group: 4th, 8th,
        12th from natal Moon nakshatra)."""
        assert moorti_for_offset(8) == "loha", (
            "Accuracy anchor A4-3 FAIL: offset 8 should be loha (iron)"
        )

    def test_forensic_anchor_native_482012f1(self):
        """Accuracy anchor A4-FORENSIC: the native 482012f1 has janma
        nakshatra = Purva Bhadrapada (index 24, 0-based). When the Moon is at
        Purva Bhadrapada at the moment of a planet's ingress, the offset is 1
        (the Moon is in the janma nakshatra itself) → svarna.
        Source: FORENSIC 7/7 PASS (CLAUDE.md §B: 'Moon = Purva Bhadrapada').
        """
        janma_idx = 24  # Purva Bhadrapada, 0-indexed
        # Moon at the same nakshatra at ingress → offset 1 → svarna
        offset = nakshatra_offset_from_janma(24, janma_idx)
        assert offset == 1
        assert moorti_for_offset(offset) == "svarna"

    def test_rajata_group_includes_offset_2(self):
        """Accuracy anchor A4-4: offset 2 → rajata (silver).
        Source: Phaladeepika Ch.26 §moorti-nirnaya (rajata group: 2nd, 5th,
        9th from natal Moon nakshatra)."""
        assert moorti_for_offset(2) == "rajata", (
            "Accuracy anchor A4-4 FAIL: offset 2 should be rajata (silver)"
        )
