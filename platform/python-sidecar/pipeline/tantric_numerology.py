"""
tantric_numerology.py — G46 Tantric Correspondences + G47 Numerology Overlays
MARSYS-JIS global reference data module.

G46: Sri Vidya chakra-graha map + Sri Yantra correspondences
G47: Pythagorean, Chaldean, and Vedic Ank Jyotish numerology systems

Note: Different traditions assign chakras differently.
The CHAKRA_GRAHA_MAP below follows the most common Vedic Tantric assignment.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# G46 — TANTRIC_CORRESPONDENCES
# ---------------------------------------------------------------------------

CHAKRA_GRAHA_MAP: dict[str, dict] = {
    "sun": {
        "chakra": "manipura",
        "chakra_number": 3,
        "chakra_sanskrit": "Maṇipūra",
        "element": "fire",
        "bija_mantra": "RAM",
        "body_location": "solar plexus",
    },
    "moon": {
        "chakra": "svadhisthana",
        "chakra_number": 2,
        "chakra_sanskrit": "Svādhiṣṭhāna",
        "element": "water",
        "bija_mantra": "VAM",
        "body_location": "sacral",
    },
    "mars": {
        "chakra": "muladhara",
        "chakra_number": 1,
        "chakra_sanskrit": "Mūlādhāra",
        "element": "earth",
        "bija_mantra": "LAM",
        "body_location": "root/base",
    },
    "mercury": {
        "chakra": "vishuddha",
        "chakra_number": 5,
        "chakra_sanskrit": "Viśuddha",
        "element": "ether/akasha",
        "bija_mantra": "HAM",
        "body_location": "throat",
    },
    "jupiter": {
        "chakra": "ajna",
        "chakra_number": 6,
        "chakra_sanskrit": "Ājñā",
        "element": "mind",
        "bija_mantra": "OM/AUM",
        "body_location": "third eye",
    },
    "venus": {
        "chakra": "anahata",
        "chakra_number": 4,
        "chakra_sanskrit": "Anāhata",
        "element": "air",
        "bija_mantra": "YAM",
        "body_location": "heart",
    },
    "saturn": {
        "chakra": "sahasrara",
        "chakra_number": 7,
        "chakra_sanskrit": "Sahasrāra",
        "element": "cosmic consciousness",
        "bija_mantra": "AH",
        "body_location": "crown",
    },
    "rahu": {
        "chakra": "ajna",
        "chakra_number": 6,
        "chakra_sanskrit": "Ājñā",
        "notes": "shadow planet associated with Ajna (illusion aspect)",
    },
    "ketu": {
        "chakra": "sahasrara",
        "chakra_number": 7,
        "chakra_sanskrit": "Sahasrāra",
        "notes": "moksha/liberation aspect at crown",
    },
}

# Sri Yantra / Sri Vidya geometry correspondences
SRIVIDYA_TRIANGLE: dict[str, object] = {
    "triangle_count": 9,
    "central_bindu": "param_shiva",
    "outer_triangles": "shakti",
    "inner_triangles": "shiva",
    "bija": "SHREEM",
    "kamakala": "Ka-Aa-La",
}


def get_chakra(graha: str) -> dict:
    """Return chakra correspondence dict for the given graha.

    Args:
        graha: Planet name in lowercase (e.g. 'sun', 'moon', 'rahu').

    Returns:
        Dict of chakra data for the graha.

    Raises:
        KeyError: If graha is not found in CHAKRA_GRAHA_MAP.
    """
    key = graha.lower().strip()
    if key not in CHAKRA_GRAHA_MAP:
        raise KeyError(f"Graha '{graha}' not found in CHAKRA_GRAHA_MAP.")
    return CHAKRA_GRAHA_MAP[key]


# ---------------------------------------------------------------------------
# G47 — NUMEROLOGY_OVERLAYS
# ---------------------------------------------------------------------------

# Pythagorean letter-to-number mapping (A=1 … Z=8, I=9 wraps at 9)
PYTHAGOREAN_NUMEROLOGY: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

# Chaldean letter-to-number mapping (no 9 assigned; max value is 8)
CHALDEAN_NUMEROLOGY: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 5, "Y": 1, "Z": 7,
}

# Vedic Ank Jyotish — nakshatra (1-27) to number (1-9 repeating cycle)
VEDIC_ANKJYOTISH: dict[int, int] = {
    n: ((n - 1) % 9) + 1 for n in range(1, 28)
}

# Classical Vedic numerology graha-number assignments
GRAHA_NUMBER: dict[str, int] = {
    "sun": 1,
    "moon": 2,
    "jupiter": 3,
    "rahu": 4,
    "mercury": 5,
    "venus": 6,
    "ketu": 7,
    "saturn": 8,
    "mars": 9,
}

# Master numbers that are NOT reduced further
_MASTER_NUMBERS = frozenset({11, 22, 33})


def reduce_to_single_digit(n: int) -> int:
    """Reduce an integer to a single digit (1-9).

    Master numbers 11, 22, and 33 are preserved **only when the original
    input is itself a master number**.  Intermediate sums that happen to
    equal 11/22/33 during reduction are NOT treated as master numbers and
    continue to be reduced.  For example:
        29  → 2+9 = 11  → 1+1 = 2   (29 is not a master number → keep going)
        11  → 11                      (original input is a master number → stop)

    Args:
        n: Positive integer to reduce.

    Returns:
        Single digit 1-9, or a master number (11, 22, 33) if ``n`` is one.
    """
    # If the original value is itself a master number, preserve it.
    if n in _MASTER_NUMBERS:
        return n
    # Otherwise reduce unconditionally until a single digit is reached.
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def compute_pythagorean_name_number(name: str) -> int:
    """Compute Pythagorean numerology number for a name string.

    Only alphabetic characters are counted; spaces and non-alpha characters
    are ignored. Master numbers 11, 22, 33 are preserved without further
    reduction.

    Args:
        name: Name string (any case).

    Returns:
        Single-digit (1-9) or master number (11, 22, 33) value.
    """
    total = sum(
        PYTHAGOREAN_NUMEROLOGY[ch.upper()]
        for ch in name
        if ch.upper() in PYTHAGOREAN_NUMEROLOGY
    )
    return reduce_to_single_digit(total)


def compute_chaldean_name_number(name: str) -> int:
    """Compute Chaldean numerology number for a name string.

    Only alphabetic characters are counted. Master numbers 11, 22, 33
    are preserved without further reduction.

    Args:
        name: Name string (any case).

    Returns:
        Single-digit (1-9) or master number (11, 22, 33) value.
    """
    total = sum(
        CHALDEAN_NUMEROLOGY[ch.upper()]
        for ch in name
        if ch.upper() in CHALDEAN_NUMEROLOGY
    )
    return reduce_to_single_digit(total)


def get_graha_number(graha: str) -> int:
    """Return the classical Vedic numerology number for a graha.

    Args:
        graha: Planet name in lowercase (e.g. 'sun', 'saturn').

    Returns:
        Integer number (1-9) assigned to the graha.

    Raises:
        KeyError: If graha is not found in GRAHA_NUMBER.
    """
    key = graha.lower().strip()
    if key not in GRAHA_NUMBER:
        raise KeyError(f"Graha '{graha}' not found in GRAHA_NUMBER.")
    return GRAHA_NUMBER[key]


def get_nakshatra_number(nakshatra: int) -> int:
    """Return the Vedic Ank Jyotish number for a nakshatra index.

    Args:
        nakshatra: Nakshatra number (1-27).

    Returns:
        Numerology number in the range 1-9.

    Raises:
        KeyError: If nakshatra index is outside 1-27.
    """
    if nakshatra not in VEDIC_ANKJYOTISH:
        raise KeyError(f"Nakshatra index {nakshatra} out of range (1-27).")
    return VEDIC_ANKJYOTISH[nakshatra]
