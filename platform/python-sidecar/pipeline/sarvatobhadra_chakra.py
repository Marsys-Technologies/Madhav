"""
sarvatobhadra_chakra.py — Sarvatobhadra Chakra global reference data.

Sarvatobhadra Chakra: 9×9 grid containing 28 nakshatras (27 standard + Abhijit)
used for muhurta analysis and transit obstruction (vedha) determination.

The grid is indexed (row, col) from 0–8, where:
  - row 0 = north side
  - row 8 = south side
  - col 0 = west side
  - col 8 = east side
  - corners (0,0), (0,8), (8,0), (8,8) are empty
  - center (4,4) is the sarvata (all-auspicious) center

Vedha pairs are nakshatras diametrically opposite across the center of the grid.
A transiting planet in vedha with a natal nakshatra causes obstruction.

Source: Muhurta Chintamani (classical), Jyotish Sara Sangraha.
Stream C global — A17 [BUILD-ORCH-STREAM-C-A17-S1]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# SBC_POSITIONS — 28 nakshatra positions in the 9×9 grid
# ---------------------------------------------------------------------------
# Keys: nakshatra_id, nakshatra_name, grid_row, grid_col, side,
#       ruling_vowel, ruling_consonant
# ruling_vowel / ruling_consonant: empty string where tradition varies by source.

SBC_POSITIONS: list[dict] = [
    # id=1  Ashwini — west side
    {
        "nakshatra_id": 1,
        "nakshatra_name": "ashwini",
        "grid_row": 5,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=2  Bharani — west side
    {
        "nakshatra_id": 2,
        "nakshatra_name": "bharani",
        "grid_row": 4,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=3  Krittika — west side
    {
        "nakshatra_id": 3,
        "nakshatra_name": "krittika",
        "grid_row": 3,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=4  Rohini — north side
    {
        "nakshatra_id": 4,
        "nakshatra_name": "rohini",
        "grid_row": 0,
        "grid_col": 1,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=5  Mrigashira — west side
    {
        "nakshatra_id": 5,
        "nakshatra_name": "mrigashira",
        "grid_row": 2,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=6  Ardra — north side
    {
        "nakshatra_id": 6,
        "nakshatra_name": "ardra",
        "grid_row": 0,
        "grid_col": 2,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=7  Punarvasu — north side
    {
        "nakshatra_id": 7,
        "nakshatra_name": "punarvasu",
        "grid_row": 0,
        "grid_col": 3,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=8  Pushya — north side
    {
        "nakshatra_id": 8,
        "nakshatra_name": "pushya",
        "grid_row": 0,
        "grid_col": 4,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=9  Aslesha — north side
    {
        "nakshatra_id": 9,
        "nakshatra_name": "aslesha",
        "grid_row": 0,
        "grid_col": 5,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=10 Magha — north side
    {
        "nakshatra_id": 10,
        "nakshatra_name": "magha",
        "grid_row": 0,
        "grid_col": 6,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=11 Purva Phalguni — west side
    {
        "nakshatra_id": 11,
        "nakshatra_name": "purva_phalguni",
        "grid_row": 1,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=12 Uttara Phalguni — north side
    {
        "nakshatra_id": 12,
        "nakshatra_name": "uttara_phalguni",
        "grid_row": 0,
        "grid_col": 7,
        "side": "north",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=13 Hasta — east side
    {
        "nakshatra_id": 13,
        "nakshatra_name": "hasta",
        "grid_row": 1,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=14 Chitra — east side
    {
        "nakshatra_id": 14,
        "nakshatra_name": "chitra",
        "grid_row": 2,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=15 Swati — east side
    {
        "nakshatra_id": 15,
        "nakshatra_name": "swati",
        "grid_row": 3,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=16 Vishakha — east side
    {
        "nakshatra_id": 16,
        "nakshatra_name": "vishakha",
        "grid_row": 4,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=17 Anuradha — east side
    {
        "nakshatra_id": 17,
        "nakshatra_name": "anuradha",
        "grid_row": 5,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=18 Jyeshtha — east side
    {
        "nakshatra_id": 18,
        "nakshatra_name": "jyeshtha",
        "grid_row": 6,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=19 Mula — east side
    {
        "nakshatra_id": 19,
        "nakshatra_name": "mula",
        "grid_row": 7,
        "grid_col": 8,
        "side": "east",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=20 Purva Ashadha — south side
    {
        "nakshatra_id": 20,
        "nakshatra_name": "purva_ashadha",
        "grid_row": 8,
        "grid_col": 7,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=21 Uttara Ashadha — south side
    {
        "nakshatra_id": 21,
        "nakshatra_name": "uttara_ashadha",
        "grid_row": 8,
        "grid_col": 6,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=22 Abhijit — south side (the 28th nakshatra, between U.Ashadha and Shravana)
    {
        "nakshatra_id": 22,
        "nakshatra_name": "abhijit",
        "grid_row": 8,
        "grid_col": 5,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=23 Shravana — south side
    {
        "nakshatra_id": 23,
        "nakshatra_name": "shravana",
        "grid_row": 8,
        "grid_col": 4,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=24 Dhanishtha — south side
    {
        "nakshatra_id": 24,
        "nakshatra_name": "dhanishtha",
        "grid_row": 8,
        "grid_col": 3,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=25 Shatabhisha — south side
    {
        "nakshatra_id": 25,
        "nakshatra_name": "shatabhisha",
        "grid_row": 8,
        "grid_col": 2,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=26 Purva Bhadrapada — south side
    {
        "nakshatra_id": 26,
        "nakshatra_name": "purva_bhadrapada",
        "grid_row": 8,
        "grid_col": 1,
        "side": "south",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=27 Uttara Bhadrapada — west side
    {
        "nakshatra_id": 27,
        "nakshatra_name": "uttara_bhadrapada",
        "grid_row": 7,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
    # id=28 Revati — west side
    {
        "nakshatra_id": 28,
        "nakshatra_name": "revati",
        "grid_row": 6,
        "grid_col": 0,
        "side": "west",
        "ruling_vowel": "",
        "ruling_consonant": "",
    },
]

# ---------------------------------------------------------------------------
# SBC_VEDHA_PAIRS — 14 vedha (obstruction) pairs
# ---------------------------------------------------------------------------
# Vedha occurs between nakshatras diametrically opposite across the center (4,4).
# A nakshatra at (r, c) is vedha with the nakshatra at (8-r, 8-c).
#
# Axis classification:
#   north-south: both on row 0 / row 8 (same column, opposite rows)
#   east-west:   both on col 0 / col 8 (same row, opposite cols)
#   diagonal:    one on corner-adjacent position
#
# Source: Muhurta Chintamani ch. Sarvatobhadra Chakra.

SBC_VEDHA_PAIRS: list[dict] = [
    # rohini (4) at (0,1) ↔ shravana (23) at (8,7) — north-south (col 1 ↔ col 7 across center)
    {
        "nakshatra_1_id": 4,
        "nakshatra_1_name": "rohini",
        "nakshatra_2_id": 23,
        "nakshatra_2_name": "shravana",
        "vedha_axis": "north-south",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # ardra (6) at (0,2) ↔ shatabhisha (25) at (8,6) — north-south
    {
        "nakshatra_1_id": 6,
        "nakshatra_1_name": "ardra",
        "nakshatra_2_id": 25,
        "nakshatra_2_name": "shatabhisha",
        "vedha_axis": "north-south",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # punarvasu (7) at (0,3) ↔ purva_bhadrapada (26) at (8,5) — north-south
    {
        "nakshatra_1_id": 7,
        "nakshatra_1_name": "punarvasu",
        "nakshatra_2_id": 26,
        "nakshatra_2_name": "purva_bhadrapada",
        "vedha_axis": "north-south",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # pushya (8) at (0,4) ↔ uttara_bhadrapada (27) at (8,4) — north-south (same col)
    {
        "nakshatra_1_id": 8,
        "nakshatra_1_name": "pushya",
        "nakshatra_2_id": 27,
        "nakshatra_2_name": "uttara_bhadrapada",
        "vedha_axis": "north-south",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # aslesha (9) at (0,5) ↔ revati (28) at (6,0) — diagonal
    {
        "nakshatra_1_id": 9,
        "nakshatra_1_name": "aslesha",
        "nakshatra_2_id": 28,
        "nakshatra_2_name": "revati",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # magha (10) at (0,6) ↔ ashwini (1) at (5,0) — diagonal
    {
        "nakshatra_1_id": 10,
        "nakshatra_1_name": "magha",
        "nakshatra_2_id": 1,
        "nakshatra_2_name": "ashwini",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # uttara_phalguni (12) at (0,7) ↔ bharani (2) at (4,0) — diagonal
    {
        "nakshatra_1_id": 12,
        "nakshatra_1_name": "uttara_phalguni",
        "nakshatra_2_id": 2,
        "nakshatra_2_name": "bharani",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # hasta (13) at (1,8) ↔ krittika (3) at (3,0) — east-west
    {
        "nakshatra_1_id": 13,
        "nakshatra_1_name": "hasta",
        "nakshatra_2_id": 3,
        "nakshatra_2_name": "krittika",
        "vedha_axis": "east-west",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # chitra (14) at (2,8) ↔ mrigashira (5) at (2,0) — east-west (same row)
    {
        "nakshatra_1_id": 14,
        "nakshatra_1_name": "chitra",
        "nakshatra_2_id": 5,
        "nakshatra_2_name": "mrigashira",
        "vedha_axis": "east-west",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # swati (15) at (3,8) ↔ purva_phalguni (11) at (1,0) — east-west
    {
        "nakshatra_1_id": 15,
        "nakshatra_1_name": "swati",
        "nakshatra_2_id": 11,
        "nakshatra_2_name": "purva_phalguni",
        "vedha_axis": "east-west",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # vishakha (16) at (4,8) ↔ uttara_ashadha (21) at (8,6) — diagonal
    {
        "nakshatra_1_id": 16,
        "nakshatra_1_name": "vishakha",
        "nakshatra_2_id": 21,
        "nakshatra_2_name": "uttara_ashadha",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # anuradha (17) at (5,8) ↔ purva_ashadha (20) at (8,7) — diagonal
    {
        "nakshatra_1_id": 17,
        "nakshatra_1_name": "anuradha",
        "nakshatra_2_id": 20,
        "nakshatra_2_name": "purva_ashadha",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # jyeshtha (18) at (6,8) ↔ abhijit (22) at (8,5) — diagonal
    {
        "nakshatra_1_id": 18,
        "nakshatra_1_name": "jyeshtha",
        "nakshatra_2_id": 22,
        "nakshatra_2_name": "abhijit",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
    # mula (19) at (7,8) ↔ dhanishtha (24) at (8,3) — diagonal
    {
        "nakshatra_1_id": 19,
        "nakshatra_1_name": "mula",
        "nakshatra_2_id": 24,
        "nakshatra_2_name": "dhanishtha",
        "vedha_axis": "diagonal",
        "classical_citation": "Muhurta Chintamani, Sarvatobhadra Chakra vedha pairs",
    },
]

# ---------------------------------------------------------------------------
# seed_sarvatobhadra — idempotent DB seeder
# ---------------------------------------------------------------------------

def seed_sarvatobhadra(conn) -> tuple[int, int]:
    """
    Seed l1_sarvatobhadra_positions and l1_sarvatobhadra_vedha tables.

    Idempotent: uses INSERT ... ON CONFLICT DO NOTHING.
    Returns (positions_inserted, vedha_inserted).
    """
    positions_inserted = 0
    vedha_inserted = 0

    with conn.cursor() as cur:
        # Seed positions
        for pos in SBC_POSITIONS:
            cur.execute(
                """
                INSERT INTO l1_sarvatobhadra_positions
                    (nakshatra_id, nakshatra_name, grid_row, grid_col, side,
                     ruling_vowel, ruling_consonant)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (nakshatra_id) DO NOTHING
                """,
                (
                    pos["nakshatra_id"],
                    pos["nakshatra_name"],
                    pos["grid_row"],
                    pos["grid_col"],
                    pos["side"],
                    pos.get("ruling_vowel", ""),
                    pos.get("ruling_consonant", ""),
                ),
            )
            positions_inserted += cur.rowcount

        # Seed vedha pairs
        for pair in SBC_VEDHA_PAIRS:
            cur.execute(
                """
                INSERT INTO l1_sarvatobhadra_vedha
                    (nakshatra_1_id, nakshatra_1_name, nakshatra_2_id, nakshatra_2_name,
                     vedha_axis, classical_citation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (
                    LEAST(nakshatra_1_id, nakshatra_2_id),
                    GREATEST(nakshatra_1_id, nakshatra_2_id)
                ) DO NOTHING
                """,
                (
                    pair["nakshatra_1_id"],
                    pair["nakshatra_1_name"],
                    pair["nakshatra_2_id"],
                    pair["nakshatra_2_name"],
                    pair["vedha_axis"],
                    pair.get("classical_citation", ""),
                ),
            )
            vedha_inserted += cur.rowcount

        conn.commit()

    return positions_inserted, vedha_inserted
