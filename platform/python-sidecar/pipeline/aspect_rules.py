"""
aspect_rules.py — G17 Aspect Rule Library
==========================================
Covers three classical aspect systems used in Jyotish:
  1. Parashari graha-drishti (planetary aspects)
  2. Jaimini rasi-drishti (sign aspects)
  3. Tajik aspects (Varshaphala / annual chart aspects)

References:
  - Brihat Parashara Hora Shastra (BPHS), Drishti chapters
  - Jaimini Sutras, Adhyaya 1, Pada 1
  - Tajika Neelakanthi, Drishti chapter

canonical_id: G17
stream: A
session: A-06 [BUILD-ORCH-A-06]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. PARASHARI GRAHA-DRISHTI
# ---------------------------------------------------------------------------
# All grahas aspect the 7th house from themselves (opposition).
# Special additional aspects per BPHS:
#   Mars   : 4th and 8th
#   Jupiter: 5th and 9th
#   Saturn : 3rd and 10th
#   Rahu   : 5th and 9th (per Parashari tradition)
#   Ketu   : 5th and 9th (per Parashari tradition)
#
# Values are 1-based house-distances from the graha's own house
# (1 = same house, 7 = opposite house).

PARASHARI_GRAHA_DRISHTI: dict[str, list[int]] = {
    "sun":     [7],
    "moon":    [7],
    "mercury": [7],
    "venus":   [7],
    "mars":    [4, 7, 8],
    "jupiter": [5, 7, 9],
    "saturn":  [3, 7, 10],
    "rahu":    [5, 7, 9],
    "ketu":    [5, 7, 9],
}

# ---------------------------------------------------------------------------
# 2. JAIMINI RASI-DRISHTI
# ---------------------------------------------------------------------------
# Signs aspect other signs in a fixed pattern based on modality:
#
#   Movable  (Aries, Cancer, Libra, Capricorn)  →  aspect Fixed signs except adjacent
#   Fixed    (Taurus, Leo, Scorpio, Aquarius)   →  aspect Movable signs except adjacent
#   Dual     (Gemini, Virgo, Sagittarius, Pisces) → aspect all other Dual signs
#
# "Adjacent" means the sign immediately before or after in the zodiac that shares
# a modality category boundary. For the Movable→Fixed rule the excluded Fixed sign
# is the one directly adjacent (next or prior sign); similarly for Fixed→Movable.
#
# Classical mapping (Jaimini Sutras 1.1.25–27 tradition):

JAIMINI_RASI_DRISHTI: dict[str, list[str]] = {
    # Movable signs aspect fixed signs except the adjacent fixed sign
    "aries":       ["leo", "scorpio", "aquarius"],       # excludes taurus (adjacent)
    "cancer":      ["scorpio", "aquarius", "taurus"],    # excludes leo (adjacent)
    "libra":       ["aquarius", "taurus", "leo"],        # excludes scorpio (adjacent)
    "capricorn":   ["taurus", "leo", "scorpio"],         # excludes aquarius (adjacent)

    # Fixed signs aspect movable signs except the adjacent movable sign
    "taurus":      ["cancer", "libra", "capricorn"],     # excludes aries (adjacent)
    "leo":         ["libra", "capricorn", "aries"],      # excludes cancer (adjacent)
    "scorpio":     ["capricorn", "aries", "cancer"],     # excludes libra (adjacent)
    "aquarius":    ["aries", "cancer", "libra"],         # excludes capricorn (adjacent)

    # Dual signs aspect all other dual signs
    "gemini":      ["virgo", "sagittarius", "pisces"],
    "virgo":       ["gemini", "sagittarius", "pisces"],
    "sagittarius": ["gemini", "virgo", "pisces"],
    "pisces":      ["gemini", "virgo", "sagittarius"],
}

# ---------------------------------------------------------------------------
# 3. TAJIK ASPECTS
# ---------------------------------------------------------------------------
# Five recognised Tajik aspects used in Varshaphala (annual charts).
# Orbs distinguish applying (stronger) from separating (weaker) aspects.
# Nature: friendly aspects strengthen; inimical weaken; neutral is mixed.
#
# Source: Tajika Neelakanthi, standard orb tradition.

TAJIK_ASPECTS: dict[str, dict] = {
    "conjunction": {
        "degrees": 0,
        "orb_applying": 8,
        "orb_separating": 8,
        "nature": "neutral",
    },
    "sextile": {
        "degrees": 60,
        "orb_applying": 5,
        "orb_separating": 3,
        "nature": "friendly",
    },
    "square": {
        "degrees": 90,
        "orb_applying": 5,
        "orb_separating": 3,
        "nature": "inimical",
    },
    "trine": {
        "degrees": 120,
        "orb_applying": 8,
        "orb_separating": 6,
        "nature": "friendly",
    },
    "opposition": {
        "degrees": 180,
        "orb_applying": 8,
        "orb_separating": 8,
        "nature": "inimical",
    },
}

# ---------------------------------------------------------------------------
# 4. FUNCTIONS
# ---------------------------------------------------------------------------


def get_parashari_aspects(graha: str) -> list[int]:
    """Return list of house positions this graha aspects (1-based, from its own house).

    Args:
        graha: Graha name (case-insensitive), e.g. 'mars', 'Jupiter'.

    Returns:
        List of house distances (e.g. [4, 7, 8] for Mars).

    Raises:
        KeyError: if graha is not recognised.
    """
    return PARASHARI_GRAHA_DRISHTI[graha.lower()]


def get_jaimini_aspected_signs(sign: str) -> list[str]:
    """Return list of signs this sign aspects via Jaimini rasi-drishti.

    Args:
        sign: Sign name (case-insensitive), e.g. 'aries', 'Gemini'.

    Returns:
        List of aspected sign names (lowercase).

    Raises:
        KeyError: if sign is not recognised.
    """
    return JAIMINI_RASI_DRISHTI[sign.lower()]


def does_sign_aspect_sign_jaimini(from_sign: str, to_sign: str) -> bool:
    """Return True if from_sign aspects to_sign per Jaimini rasi-drishti.

    Note: Jaimini aspects are mutual — if A aspects B then B aspects A —
    but this function checks the explicit JAIMINI_RASI_DRISHTI mapping only.

    Args:
        from_sign: Aspecting sign name (case-insensitive).
        to_sign:   Aspected sign name (case-insensitive).

    Returns:
        True if to_sign appears in from_sign's aspect list.
    """
    return to_sign.lower() in JAIMINI_RASI_DRISHTI.get(from_sign.lower(), [])


def get_tajik_aspect(degree_diff: float) -> dict | None:
    """Given angular difference (0–180°), return matching Tajik aspect dict or None.

    Matching uses the applying orb (the wider of the two orbs) as the tolerance
    window around each aspect's exact degree.

    Args:
        degree_diff: Absolute angular separation in degrees, in range [0, 180].

    Returns:
        Tajik aspect dict (with keys: degrees, orb_applying, orb_separating, nature)
        for the first matching aspect, or None if no aspect matches.
    """
    # Normalise to [0, 180]
    diff = abs(degree_diff) % 360
    if diff > 180:
        diff = 360 - diff

    for aspect_name, aspect in TAJIK_ASPECTS.items():
        exact = aspect["degrees"]
        orb = aspect["orb_applying"]  # use applying orb as tolerance
        if abs(diff - exact) <= orb:
            return {"name": aspect_name, **aspect}
    return None


def parashari_aspect_houses_from_house(house: int, graha: str) -> list[int]:
    """Return list of houses aspected by graha placed in the given house (1–12).

    Uses modular arithmetic: (house - 1 + offset - 1) % 12 + 1

    Args:
        house: House number where graha is placed (1–12).
        graha: Graha name (case-insensitive).

    Returns:
        Sorted list of aspected house numbers (1–12, no duplicates).

    Raises:
        ValueError: if house is not in range 1–12.
        KeyError:   if graha is not recognised.
    """
    if not 1 <= house <= 12:
        raise ValueError(f"house must be 1–12, got {house}")

    offsets = get_parashari_aspects(graha)
    aspected = []
    for offset in offsets:
        # offset is 1-based distance; offset=7 means 7th from house
        target = (house - 1 + offset - 1) % 12 + 1
        aspected.append(target)

    return sorted(set(aspected))
