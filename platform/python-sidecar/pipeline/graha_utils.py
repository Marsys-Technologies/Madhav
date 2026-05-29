"""
graha_utils.py — Pure lookup table for 9 grahas (planets) + Rahu/Ketu nodes with classical attributes.

No DB interaction, no swisseph calls. Provides exaltation, debilitation, moolatrikona,
rulership, nature, tattva, and gender for each graha.

Notes:
  - Rahu and Ketu both use swisseph_id=11 (mean node); True node is id=10 and handled separately.
  - exalted_deg is the exact degree of peak exaltation within the rashi (0-based within sign).
  - moolatrikona_range is [start_deg, end_deg] (0-based within the moolatrikona rashi).
  - Rahu/Ketu have no tattva, no moolatrikona, and empty ruler_of lists.
"""

from __future__ import annotations

GRAHAS: dict[str, dict] = {
    "sun": {
        "id": "sun",
        "name": "Surya",
        "index": 0,
        "swisseph_id": 0,
        "nature": "malefic",
        "tattva": "Fire",
        "gender": "male",
        "ruler_of": ["simha"],
        "exalted_in": "mesha",
        "exalted_deg": 10.0,
        "debilitated_in": "tula",
        "moolatrikona": "simha",
        "moolatrikona_range": [0, 20],
    },
    "moon": {
        "id": "moon",
        "name": "Chandra",
        "index": 1,
        "swisseph_id": 1,
        "nature": "benefic",
        "tattva": "Water",
        "gender": "female",
        "ruler_of": ["karka"],
        "exalted_in": "vrishabha",
        "exalted_deg": 3.0,
        "debilitated_in": "vrischika",
        "moolatrikona": "karka",
        "moolatrikona_range": [4, 30],
    },
    "mars": {
        "id": "mars",
        "name": "Mangala",
        "index": 2,
        "swisseph_id": 4,
        "nature": "malefic",
        "tattva": "Fire",
        "gender": "male",
        "ruler_of": ["mesha", "vrischika"],
        "exalted_in": "makara",
        "exalted_deg": 28.0,
        "debilitated_in": "karka",
        "moolatrikona": "mesha",
        "moolatrikona_range": [0, 12],
    },
    "mercury": {
        "id": "mercury",
        "name": "Budha",
        "index": 3,
        "swisseph_id": 2,
        "nature": "neutral",
        "tattva": "Earth",
        "gender": "neuter",
        "ruler_of": ["mithuna", "kanya"],
        "exalted_in": "kanya",
        "exalted_deg": 15.0,
        "debilitated_in": "meena",
        "moolatrikona": "kanya",
        "moolatrikona_range": [16, 20],
    },
    "jupiter": {
        "id": "jupiter",
        "name": "Guru",
        "index": 4,
        "swisseph_id": 5,
        "nature": "benefic",
        "tattva": "Ether",
        "gender": "male",
        "ruler_of": ["dhanus", "meena"],
        "exalted_in": "karka",
        "exalted_deg": 5.0,
        "debilitated_in": "makara",
        "moolatrikona": "dhanus",
        "moolatrikona_range": [0, 10],
    },
    "venus": {
        "id": "venus",
        "name": "Shukra",
        "index": 5,
        "swisseph_id": 3,
        "nature": "benefic",
        "tattva": "Water",
        "gender": "female",
        "ruler_of": ["vrishabha", "tula"],
        "exalted_in": "meena",
        "exalted_deg": 27.0,
        "debilitated_in": "kanya",
        "moolatrikona": "tula",
        "moolatrikona_range": [0, 15],
    },
    "saturn": {
        "id": "saturn",
        "name": "Shani",
        "index": 6,
        "swisseph_id": 6,
        "nature": "malefic",
        "tattva": "Air",
        "gender": "neuter",
        "ruler_of": ["makara", "kumbha"],
        "exalted_in": "tula",
        "exalted_deg": 20.0,
        "debilitated_in": "mesha",
        "moolatrikona": "kumbha",
        "moolatrikona_range": [0, 20],
    },
    "rahu": {
        "id": "rahu",
        "name": "Rahu",
        "index": 7,
        "swisseph_id": 11,
        "nature": "malefic",
        "tattva": None,
        "gender": "neuter",
        "ruler_of": [],
        "exalted_in": "mithuna",
        "exalted_deg": None,
        "debilitated_in": "dhanus",
        "moolatrikona": None,
        "moolatrikona_range": None,
    },
    "ketu": {
        "id": "ketu",
        "name": "Ketu",
        "index": 8,
        "swisseph_id": 11,
        "nature": "malefic",
        "tattva": None,
        "gender": "neuter",
        "ruler_of": [],
        "exalted_in": "dhanus",
        "exalted_deg": None,
        "debilitated_in": "mithuna",
        "moolatrikona": None,
        "moolatrikona_range": None,
    },
}

# Required keys that every graha entry must carry
REQUIRED_KEYS = frozenset({
    "id", "name", "index", "swisseph_id", "nature", "tattva", "gender",
    "ruler_of", "exalted_in", "exalted_deg", "debilitated_in",
    "moolatrikona", "moolatrikona_range",
})


def get_graha(graha_id: str) -> dict:
    """Return graha dict for the given id.

    Raises KeyError if the id is not found.
    """
    return GRAHAS[graha_id]


def grahas_ruling_rashi(rashi_name: str) -> list[str]:
    """Return list of graha_ids that rule the given rashi (lowercase)."""
    return [gid for gid, g in GRAHAS.items() if rashi_name in g["ruler_of"]]


def is_exalted(graha_id: str, rashi_name: str) -> bool:
    """Return True if the graha is in its sign of exaltation."""
    return GRAHAS[graha_id]["exalted_in"] == rashi_name


def is_debilitated(graha_id: str, rashi_name: str) -> bool:
    """Return True if the graha is in its sign of debilitation."""
    return GRAHAS[graha_id]["debilitated_in"] == rashi_name
