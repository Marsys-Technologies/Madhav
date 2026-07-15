"""bodha_writers.bhavat_bhavam_registry — the Bhavat Bhavam 12-cell doctrinal map.

Lane B-4 (D-1.5b, CR-97). Pure registry DATA — deliberately not expressed as
scattered if/else logic anywhere else in the codebase (brief BRIEF_D1_5B.md
§Lane B-4: "The 12-cell doctrinal map ... as registry data").

DOCTRINE (hard rule, not an oversight): only the six ODD houses receive a
"house of the house" (bhavat bhavam) derivation. EVEN houses receive NOTHING
— no derived house is ever computed for an even primary house. This module
is the single source of truth for that rule; every consumer (the shastra-map
extension in register_d9_judgment.ts, and the bo_laksana bhavat_bhavam_amplifier
MSR emitter) reads this table rather than re-deriving it.

Map (verbatim from the brief):
  1  -> {1, 7}
  3  -> {2, 8}
  5  -> {3, 9}
  7  -> {4, 10}
  9  -> {5, 11}
  11 -> {6, 12}
  2, 4, 6, 8, 10, 12 -> {}  (even houses: no derivation, by design)
"""
from __future__ import annotations

MAP_VERSION = "1.0"

# The 12-cell map as pure data. Every house 1..12 is present as a key so
# callers never need a fallback branch to distinguish "odd, no entry yet"
# from "even, deliberately empty" — both read as an empty tuple.
BHAVAT_BHAVAM_MAP: dict[int, tuple[int, ...]] = {
    1: (1, 7),
    2: (),
    3: (2, 8),
    4: (),
    5: (3, 9),
    6: (),
    7: (4, 10),
    8: (),
    9: (5, 11),
    10: (),
    11: (6, 12),
    12: (),
}

ODD_HOUSES: tuple[int, ...] = (1, 3, 5, 7, 9, 11)
EVEN_HOUSES: tuple[int, ...] = (2, 4, 6, 8, 10, 12)


def derived_houses(primary_house: int) -> tuple[int, ...]:
    """Return the derived ("house of the house") bhāvas for `primary_house`.

    Even houses ALWAYS return an empty tuple — this is the hard doctrinal
    rule (brief: "even houses receive NOTHING"), enforced here as code so no
    caller can accidentally synthesize a derived house for an even primary.
    """
    if primary_house not in BHAVAT_BHAVAM_MAP:
        raise ValueError(f"bhavat_bhavam: house {primary_house} is not a valid bhava (1-12)")
    return BHAVAT_BHAVAM_MAP[primary_house]


def is_odd_house(house: int) -> bool:
    return house in ODD_HOUSES
