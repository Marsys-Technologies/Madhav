"""
friendship_karaka_ref.py — G18: Natural graha friendship 9×9 table + G19: Karaka assignment reference.

Source: BPHS (Brihat Parashara Hora Shastra) classical canon.

Notes:
  - Natural friendship (naisargika maitri) is one-directional: Sun's view of Saturn != Saturn's view of Sun.
  - Composite (tatkalika + naisargika) friendship calculation requires temporary friendship overlay;
    get_composite_friendship() is a stub that returns natural friendship until temporary data is available.
  - House karakas: natural significators (karaka) per house per BPHS.
  - Domain karakas: planets that signify a life domain.
  - Rahu and Ketu are treated as shadow planets; their friendships follow tantric/BPHS convention.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# G18 — Natural Friendship Table (naisargika maitri)
# ---------------------------------------------------------------------------
# Relationship values: 'mitra' (friend), 'sama' (neutral), 'shatru' (enemy)
# Each graha's perspective is independent.
# ---------------------------------------------------------------------------

NATURAL_FRIENDSHIP: dict[str, dict[str, str]] = {
    "sun": {
        "moon": "mitra",
        "mars": "mitra",
        "jupiter": "mitra",
        "mercury": "sama",
        "venus": "shatru",
        "saturn": "shatru",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "moon": {
        "sun": "mitra",
        "mercury": "mitra",
        "mars": "sama",
        "jupiter": "sama",
        "venus": "sama",
        "saturn": "sama",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "mars": {
        "sun": "mitra",
        "moon": "mitra",
        "jupiter": "mitra",
        "venus": "sama",
        "saturn": "sama",
        "mercury": "shatru",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "mercury": {
        "sun": "mitra",
        "venus": "mitra",
        "mars": "sama",
        "jupiter": "sama",
        "saturn": "sama",
        "moon": "shatru",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "jupiter": {
        "sun": "mitra",
        "moon": "mitra",
        "mars": "mitra",
        "saturn": "sama",
        "mercury": "shatru",
        "venus": "shatru",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "venus": {
        "mercury": "mitra",
        "saturn": "mitra",
        "mars": "sama",
        "jupiter": "sama",
        "sun": "shatru",
        "moon": "shatru",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "saturn": {
        "mercury": "mitra",
        "venus": "mitra",
        "jupiter": "sama",
        "sun": "shatru",
        "moon": "shatru",
        "mars": "shatru",
        "rahu": "shatru",
        "ketu": "shatru",
    },
    "rahu": {
        "mercury": "mitra",
        "venus": "mitra",
        "saturn": "mitra",
        "mars": "sama",
        "jupiter": "sama",
        "sun": "shatru",
        "moon": "shatru",
        "ketu": "shatru",
    },
    "ketu": {
        "mercury": "mitra",
        "venus": "mitra",
        "saturn": "mitra",
        "mars": "sama",
        "jupiter": "sama",
        "sun": "shatru",
        "moon": "shatru",
        "rahu": "shatru",
    },
}

# ---------------------------------------------------------------------------
# G19a — House Karakas (natural significators per bhava 1–12)
# ---------------------------------------------------------------------------
# Source: BPHS Chapter on Bhava Karakas.
# Multiple karakas per house listed in order of primary to secondary significance.
# ---------------------------------------------------------------------------

HOUSE_KARAKAS: dict[int, list[str]] = {
    1: ["sun"],
    2: ["jupiter"],
    3: ["mars", "mercury"],
    4: ["moon", "mercury", "venus", "mars"],
    5: ["jupiter", "sun"],
    6: ["saturn", "mars"],
    7: ["venus", "mercury", "jupiter"],
    8: ["saturn"],
    9: ["sun", "jupiter"],
    10: ["sun", "mercury", "jupiter", "saturn"],
    11: ["jupiter", "mercury"],
    12: ["saturn", "ketu"],
}

# ---------------------------------------------------------------------------
# G19b — Domain Karakas (significators per life domain)
# ---------------------------------------------------------------------------
# Classical correspondences; first item is the primary karaka.
# ---------------------------------------------------------------------------

DOMAIN_KARAKAS: dict[str, list[str]] = {
    "career": ["sun", "saturn", "mercury", "jupiter", "mars"],
    "marriage": ["venus", "jupiter"],
    "children": ["jupiter", "moon", "sun"],
    "wealth": ["jupiter", "venus", "mercury"],
    "health": ["sun", "moon", "mars"],
    "education": ["mercury", "jupiter", "venus"],
    "spirituality": ["ketu", "jupiter", "saturn", "moon"],
    "longevity": ["saturn", "mars", "sun"],
    "siblings": ["mars", "mercury"],
    "mother": ["moon", "venus", "mercury"],
    "father": ["sun", "jupiter", "saturn"],
    "enemies": ["mars", "saturn", "sun"],
}

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

_VALID_GRAHAS = frozenset(NATURAL_FRIENDSHIP.keys())
_VALID_RELATIONSHIPS = frozenset({"mitra", "sama", "shatru"})


def get_natural_friendship(graha1: str, graha2: str) -> str:
    """Return 'mitra', 'sama', or 'shatru' from graha1's perspective towards graha2.

    Args:
        graha1: The observer graha (lowercase, e.g. 'sun').
        graha2: The target graha (lowercase, e.g. 'saturn').

    Returns:
        Relationship string: 'mitra', 'sama', or 'shatru'.

    Raises:
        ValueError: If either graha name is invalid or graha1 == graha2.
    """
    graha1 = graha1.lower().strip()
    graha2 = graha2.lower().strip()
    if graha1 not in _VALID_GRAHAS:
        raise ValueError(f"Unknown graha: '{graha1}'. Valid: {sorted(_VALID_GRAHAS)}")
    if graha2 not in _VALID_GRAHAS:
        raise ValueError(f"Unknown graha: '{graha2}'. Valid: {sorted(_VALID_GRAHAS)}")
    if graha1 == graha2:
        raise ValueError(f"graha1 and graha2 must differ; got '{graha1}' for both.")
    return NATURAL_FRIENDSHIP[graha1][graha2]


def get_house_karaka(house: int) -> list[str]:
    """Return list of natural karakas for a house (1–12).

    Args:
        house: House number, 1-based integer.

    Returns:
        List of graha names (primary first).

    Raises:
        ValueError: If house is not in range 1–12.
    """
    if house not in HOUSE_KARAKAS:
        raise ValueError(f"House must be 1–12; got {house}.")
    return list(HOUSE_KARAKAS[house])


def get_domain_karaka(domain: str) -> list[str]:
    """Return list of karakas for a significance domain.

    Args:
        domain: Domain name (lowercase), e.g. 'marriage', 'career'.

    Returns:
        List of graha names (primary first).

    Raises:
        KeyError: If domain is not in DOMAIN_KARAKAS.
    """
    domain = domain.lower().strip()
    if domain not in DOMAIN_KARAKAS:
        raise KeyError(
            f"Unknown domain: '{domain}'. Valid: {sorted(DOMAIN_KARAKAS.keys())}"
        )
    return list(DOMAIN_KARAKAS[domain])


def get_composite_friendship(graha1: str, graha2: str) -> str:
    """Return composite (temporary + natural averaged) friendship relationship.

    Stub: returns natural friendship until temporary (tatkalika) friendship
    overlay data is available. The composite rule is:
      - mitra + mitra  => adhimitra (treated as mitra here)
      - mitra + sama   => mitra
      - mitra + shatru => sama
      - sama  + sama   => sama
      - sama  + shatru => shatru
      - shatru+ shatru => adhi-shatru (treated as shatru here)

    Args:
        graha1: Observer graha.
        graha2: Target graha.

    Returns:
        Relationship string: 'mitra', 'sama', or 'shatru'.
    """
    return get_natural_friendship(graha1, graha2)
