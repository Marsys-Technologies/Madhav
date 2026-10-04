"""brahmagyan.natural_malefics: the ONE cited constant for which grahas are natural malefics (SS N-61 / AR-6).

A sibling L0 module, deliberately NOT imported by `l0_reference.py` (so no frozen L0 writer digest moves for a
constant), and importing nothing, so it adds no weight to any digest closure that reads it. Read by L1 (the
ga_structural argala score convention) and, when bo_karanajala is rebuilt, by L2 instead of any local set.

Source: BPHS (Santhanam trans.) Ch. 3 "Natural benefics and malefics": "Malefics are the Sun, Saturn and Mars".
The nodes are not in that sentence and are stated separately here. Moon and Mercury are conditional (neither
listed). Corpus chunks: bphs_pg0343_c01 (the sentence), bphs_pg0343_c02 (the note). Grade: sourced_ocr_unverified.

Not this module's job (a post-J1 L0 item, recorded in the design note, not built): a `natural_class` column on
`reference_planets`, and unifying the four classification definitions (this constant, the boolean column
`reference_planets.natural_benefic`, `valence_doctrine._NATURAL_NATURE`, L2's local set). Consistency with the
`natural_benefic` column is asserted by a test, not at import.
"""
from __future__ import annotations

# L0 `reference_planets.planet_id` values (lower case), the same identifiers l0_reference.PLANETS uses.
NATURAL_MALEFIC_PLANET_IDS: tuple[str, ...] = ("sun", "mars", "saturn")
NODE_PLANET_IDS: tuple[str, ...] = ("rahu", "ketu")

NATURAL_MALEFIC_CITATION = (
    "BPHS (Santhanam trans.) Ch. 3 'Natural benefics and malefics', bphs_pg0343_c01, bphs_pg0343_c02: "
    "malefics are the Sun, Saturn and Mars; the nodes are stated separately. sourced_ocr_unverified."
)
