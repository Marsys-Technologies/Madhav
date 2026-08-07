"""Accuracy-anchor tests for ka_kota_chakra (Item 16, ṢAḌ-DARŚANA W3).

MANDATORY ACCURACY STANDARD (from the subagent task brief):
  Verify Kota assignments for at least 3 nakshatras against classical text.

CLASSICAL SOURCE (tier-(iii), as documented in brahmagyan/l0_kota_chakra_rings.py):
  The Kota-Chakra fort-chakra ring partition is taken from a secondary published
  description — it is honestly disclosed as tier-(iii) evidence (ADJUDICATION-9,
  2026-08-01; see l0_kota_chakra_rings.py). The corpus-ingestion gap for the
  primary classical source (Muhūrta Chintāmaṇi / Nārada-Saṃhitā class texts)
  is filed.

WHAT THE CLASSICAL RULE SAYS:
  The Kota Chakra is a 4×4 fortress grid built around the janma nakshatra
  (birth nakshatra) as its centre. Nakshatras are counted cyclically from the
  janma nakshatra (counting the janma nakshatra itself as 1). The four rings:
    • Stambha (pillar / innermost):         4th, 11th, 18th, 25th
    • Durgantara / Madhya (inner ward):     3rd, 5th, 10th, 12th, 17th, 19th, 24th, 26th
    • Prakara (outer wall / rampart):       2nd, 6th, 9th, 13th, 16th, 20th, 23rd, 27th
    • Bahya (exterior / outside the fort):  all others (1st = janma itself,
                                             7th, 8th, 14th, 15th, 21st, 22nd)

  This is the universal counting from the janma nakshatra — independent of which
  specific nakshatra the planet occupies. So a planet 4 nakshatras away from the
  janma nakshatra is always in Stambha, regardless of whether the janma is
  Ashwini or Revati or any other.

ANCHOR NAKSHATRAS — three independent count-from-janma checks:
  (The tests use `count_from_janma` and `ring_for_count` from the serving layer,
  verifying the classical rule is correctly implemented by asserting each count
  maps to the ring the classical text assigns it to.)

  ANCHOR 1: count = 4 → Stambha (the innermost pillar, 4th nakshatra from janma)
    "The 4th, 11th, 18th, 25th from janma are the Stambhas (pillars)."
    Source: tier-(iii) secondary description; ADJUDICATION-9.

  ANCHOR 2: count = 3 → Durgantara (inner ward / middle ring)
    "The 3rd, 5th, 10th... from janma are the Durgantara (inner ward)."
    Source: tier-(iii) secondary description; ADJUDICATION-9.

  ANCHOR 3: count = 2 → Prakara (outer wall)
    "The 2nd, 6th, 9th, 13th... from janma are the Prakara (outer wall)."
    Source: tier-(iii) secondary description; ADJUDICATION-9.

  ANCHOR 4 (bonus): count = 1 → Bahya (exterior, the janma nakshatra itself)
    The janma nakshatra itself is not listed in the three fort rings,
    so it falls to the Bahya (exterior) by the partition.
    Source: tier-(iii) secondary description; ADJUDICATION-9.

NATIVE CHART VERIFICATION:
  The native (Abhisek Mohanty, CLAUDE.md §B) has Moon in Purva Bhadrapada
  (nakshatra index 24 in 0-based, 25th nakshatra = Purva Bhadrapada in the
  standard 27-nakshatra scheme).

  With janma = Purva Bhadrapada (index 24), the 4th nakshatra from janma
  (count=4) is Purva Bhadrapada + 3 = index 27 mod 27 = index 0 = Ashwini.
  Ashwini should be in Stambha for this native.

  The 3rd nakshatra (count=3) is index 26 = Revati → Durgantara.
  The 2nd nakshatra (count=2) is index 25 = Uttara Bhadrapada → Prakara.
  The janma itself (count=1) → Bahya.

These native-chart spot checks verify the full pipeline: janma nakshatra
from FORENSIC chart → count arithmetic → ring assignment.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brahmagyan.l0_kota_chakra_rings import (
    STAMBHA_COUNTS,
    DURGANTARA_COUNTS,
    PRAKARA_COUNTS,
    BAHYA_COUNTS,
    ring_sets_by_name,
)
from services.ka_kota_chakra.logic import (
    count_from_janma,
    ring_for_count,
)

_RING_SETS = ring_sets_by_name()

# ── ANCHOR 1: 4th from janma → Stambha ───────────────────────────────────────

class TestAnchor1StambhaIsFourthFromJanma:
    """Classical rule: Stambha (pillar / innermost ring) = 4th, 11th, 18th, 25th
    from the janma nakshatra. This anchor verifies all four Stambha positions.

    Source: tier-(iii) secondary description; ADJUDICATION-9 (2026-08-01).
    """

    def test_4th_from_janma_is_stambha(self):
        assert ring_for_count(4, _RING_SETS) == "stambha", \
            "Classical rule: 4th nakshatra from janma = Stambha (pillar)"

    def test_11th_from_janma_is_stambha(self):
        assert ring_for_count(11, _RING_SETS) == "stambha", \
            "Classical rule: 11th nakshatra from janma = Stambha (pillar)"

    def test_18th_from_janma_is_stambha(self):
        assert ring_for_count(18, _RING_SETS) == "stambha", \
            "Classical rule: 18th nakshatra from janma = Stambha (pillar)"

    def test_25th_from_janma_is_stambha(self):
        assert ring_for_count(25, _RING_SETS) == "stambha", \
            "Classical rule: 25th nakshatra from janma = Stambha (pillar)"

    def test_stambha_set_contains_exactly_four_pillar_positions(self):
        assert STAMBHA_COUNTS == frozenset({4, 11, 18, 25}), \
            "Stambha must be exactly the 4 classical pillar positions: 4, 11, 18, 25"


# ── ANCHOR 2: 3rd from janma → Durgantara ────────────────────────────────────

class TestAnchor2DurgantaraIsThirdFromJanma:
    """Classical rule: Durgantara/Madhya (inner ward) = 3rd, 5th, 10th, 12th,
    17th, 19th, 24th, 26th from janma.

    Source: tier-(iii) secondary description; ADJUDICATION-9 (2026-08-01).
    """

    def test_3rd_from_janma_is_durgantara(self):
        assert ring_for_count(3, _RING_SETS) == "durgantara", \
            "Classical rule: 3rd nakshatra from janma = Durgantara (inner ward)"

    def test_5th_from_janma_is_durgantara(self):
        assert ring_for_count(5, _RING_SETS) == "durgantara", \
            "Classical rule: 5th nakshatra from janma = Durgantara (inner ward)"

    def test_10th_from_janma_is_durgantara(self):
        assert ring_for_count(10, _RING_SETS) == "durgantara", \
            "Classical rule: 10th nakshatra from janma = Durgantara (inner ward)"

    def test_26th_from_janma_is_durgantara(self):
        assert ring_for_count(26, _RING_SETS) == "durgantara", \
            "Classical rule: 26th nakshatra from janma = Durgantara (inner ward)"


# ── ANCHOR 3: 2nd from janma → Prakara ───────────────────────────────────────

class TestAnchor3PrakaraIsSecondFromJanma:
    """Classical rule: Prakara (outer wall / rampart) = 2nd, 6th, 9th, 13th,
    16th, 20th, 23rd, 27th from janma.

    Source: tier-(iii) secondary description; ADJUDICATION-9 (2026-08-01).
    """

    def test_2nd_from_janma_is_prakara(self):
        assert ring_for_count(2, _RING_SETS) == "prakara", \
            "Classical rule: 2nd nakshatra from janma = Prakara (outer wall)"

    def test_6th_from_janma_is_prakara(self):
        assert ring_for_count(6, _RING_SETS) == "prakara", \
            "Classical rule: 6th nakshatra from janma = Prakara (outer wall)"

    def test_27th_from_janma_is_prakara(self):
        assert ring_for_count(27, _RING_SETS) == "prakara", \
            "Classical rule: 27th nakshatra from janma = Prakara (outer wall)"

    def test_prakara_set_size_is_eight(self):
        assert len(PRAKARA_COUNTS) == 8, \
            "Prakara must have exactly 8 positions per the classical rule"


# ── ANCHOR 4: 1st = janma itself → Bahya ─────────────────────────────────────

class TestAnchor4JanmaNakshatraIsBahya:
    """The janma nakshatra itself (count=1) is not assigned to any of the
    three named rings in the classical description, so it falls to Bahya
    (exterior). This is disclosed explicitly in ADJUDICATION-9.

    This is a key classical interpretation: a planet at the birth nakshatra
    is OUTSIDE the fort's formal structure — it is in the Bahya (exterior).

    Source: tier-(iii) secondary description; ADJUDICATION-9 (2026-08-01).
    """

    def test_1st_from_janma_ie_janma_itself_is_bahya(self):
        assert ring_for_count(1, _RING_SETS) == "bahya", \
            "The janma nakshatra itself (count=1) must be Bahya (exterior)"

    def test_7th_from_janma_is_bahya(self):
        assert ring_for_count(7, _RING_SETS) == "bahya", \
            "7th nakshatra from janma must be Bahya (exterior)"

    def test_8th_from_janma_is_bahya(self):
        assert ring_for_count(8, _RING_SETS) == "bahya", \
            "8th nakshatra from janma must be Bahya (exterior)"

    def test_bahya_has_seven_positions(self):
        # {1,7,8,14,15,21,22} = 7 positions as described in the classical partition
        assert len(BAHYA_COUNTS) == 7, \
            f"Bahya must have exactly 7 positions, got {len(BAHYA_COUNTS)}: {sorted(BAHYA_COUNTS)}"


# ── Native-chart spot checks (Abhisek Mohanty, CLAUDE.md §B) ─────────────────

class TestNativeChartKotaSpotChecks:
    """FORENSIC-anchored checks: native Moon = Purva Bhadrapada (nakshatra idx 24,
    0-based). Count arithmetic from janma → ring assignment.

    FORENSIC anchor: CLAUDE.md §B "Moon = Purva Bhadrapada" — this is the 7/7
    FORENSIC-PASS canonical birth fact. Purva Bhadrapada is index 24 (0-based)
    in the 27-nakshatra sequence (0=Ashwini, 1=Bharani, ..., 24=PurvaBhadrapada,
    25=UttaraBhadrapada, 26=Revati).
    """

    # janma_nak_idx = 24 (Purva Bhadrapada, 0-based)
    JANMA_IDX = 24

    def test_native_4th_nakshatra_from_janma_is_index_0_ashwini_in_stambha(self):
        # count=4, janma=24 → nak_idx_0based = (24 + 3) % 27 = 0 = Ashwini
        nak_idx = (self.JANMA_IDX + 3) % 27
        assert nak_idx == 0, f"Expected Ashwini (idx 0), got idx {nak_idx}"
        count = count_from_janma(nak_idx_0based=nak_idx, janma_nak_idx_0based=self.JANMA_IDX)
        assert count == 4
        ring = ring_for_count(count, _RING_SETS)
        assert ring == "stambha", \
            f"Ashwini is 4th from native janma (PurvaBhadrapada) → must be Stambha, got {ring}"

    def test_native_3rd_nakshatra_from_janma_is_index_26_revati_in_durgantara(self):
        # count=3, janma=24 → nak_idx_0based = (24 + 2) % 27 = 26 = Revati
        nak_idx = (self.JANMA_IDX + 2) % 27
        assert nak_idx == 26, f"Expected Revati (idx 26), got idx {nak_idx}"
        count = count_from_janma(nak_idx_0based=nak_idx, janma_nak_idx_0based=self.JANMA_IDX)
        assert count == 3
        ring = ring_for_count(count, _RING_SETS)
        assert ring == "durgantara", \
            f"Revati is 3rd from native janma → must be Durgantara, got {ring}"

    def test_native_2nd_nakshatra_from_janma_is_index_25_uttarabhadrapada_in_prakara(self):
        # count=2, janma=24 → nak_idx_0based = (24 + 1) % 27 = 25 = UttaraBhadrapada
        nak_idx = (self.JANMA_IDX + 1) % 27
        assert nak_idx == 25, f"Expected UttaraBhadrapada (idx 25), got idx {nak_idx}"
        count = count_from_janma(nak_idx_0based=nak_idx, janma_nak_idx_0based=self.JANMA_IDX)
        assert count == 2
        ring = ring_for_count(count, _RING_SETS)
        assert ring == "prakara", \
            f"UttaraBhadrapada is 2nd from native janma → must be Prakara, got {ring}"

    def test_native_janma_nakshatra_itself_is_bahya(self):
        # count=1 (the janma nakshatra itself)
        count = count_from_janma(nak_idx_0based=self.JANMA_IDX, janma_nak_idx_0based=self.JANMA_IDX)
        assert count == 1
        ring = ring_for_count(count, _RING_SETS)
        assert ring == "bahya", \
            f"The janma nakshatra itself (count=1) must be Bahya, got {ring}"
