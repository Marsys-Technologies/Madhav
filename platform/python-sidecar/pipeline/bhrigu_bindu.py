"""
bhrigu_bindu.py — G49 Bhrigu Bindu Reference Module
====================================================
Classical source: Bhrigu Nadi tradition; Bhrigu Samhita interpretation.

Bhrigu Bindu is a sensitive natal point defined as the midpoint between the
Moon and True Rahu (North Node) in a chart. It is a karmic receptive point
that activates dramatically when outer planets transit over it, indicating
significant life events.

Key principle: The midpoint must be computed using the shorter arc of the
zodiac circle (i.e., the arc ≤ 180°) to find the true midpoint.

canonical_id: G49
stream: A
session: G48-G49-G50-S1 [BUILD-ORCH-A-15]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. BHRIGU BINDU RULES
# ---------------------------------------------------------------------------

BHRIGU_BINDU_RULES: dict = {
    "computation": {
        "formula": "Midpoint of Moon longitude and True Rahu longitude",
        "formula_alt": "(moon_longitude + rahu_longitude) / 2",
        "note": "If difference > 180°, add 180° to shorter arc midpoint (use wrap-around midpoint)",
        "tropical_vs_sidereal": "Compute in sidereal (ayanamsha-corrected) longitude",
    },
    "activation_window_deg": 3.0,    # transit within 3° activates BB
    "activation_window_alt_deg": 1.0,  # tight orb for precise timing
    "transiting_planets_ranked": [
        "saturn", "jupiter", "rahu", "ketu", "mars",
        "sun", "moon", "mercury", "venus",
    ],
    "activation_significance": {
        "saturn": (
            "Major life events, karmic turning points, career/structure shifts; "
            "delays and discipline; tests of commitment"
        ),
        "jupiter": (
            "Expansion, wisdom, marriage, children, fortune; "
            "blessings and opportunity; teacher or guide appears"
        ),
        "rahu": (
            "Sudden changes, new directions, foreigners, unconventional events; "
            "worldly ambition triggers; obsession themes activated"
        ),
        "ketu": (
            "Spiritual events, losses, separation, liberation experiences; "
            "past-life karma surfaces; introspection and withdrawal"
        ),
        "mars": (
            "Conflicts, energy surge, accidents, initiatives; "
            "courage or aggression themes; physical vitality events"
        ),
        "sun": (
            "Authority figures, ego events, father-related, recognition; "
            "government/leadership encounters; identity assertion"
        ),
        "moon": (
            "Emotional surges, mother, home, short-term events (monthly trigger); "
            "mood intensification; nurturing themes"
        ),
        "mercury": (
            "Communication, contracts, siblings, short travels; "
            "intellectual activity, commerce, paperwork events"
        ),
        "venus": (
            "Relationships, arts, luxury, marriage, finance; "
            "pleasure and desire themes; beauty and harmony events"
        ),
    },
    "transit_duration": {
        "saturn": "~2.5 months through 3° orb",
        "jupiter": "~1 month through 3° orb",
        "rahu_ketu": "~2 months through 3° orb",
        "mars": "~2 weeks through 3° orb",
        "sun": "~6 days through 3° orb",
        "moon": "~2 days through 3° orb",
        "mercury": "~3 weeks through 3° orb",
        "venus": "~2-3 weeks through 3° orb",
    },
    "natal_sign_amplification": {
        "description": "Sign occupied by Bhrigu Bindu colors its results",
        "example": "BB in Scorpio amplifies transformation and secrecy themes",
    },
    "house_position_significance": {
        "description": "House of BB from ASC determines primary life domain of activation",
        1: "Self, body, personality",
        2: "Wealth, family, speech",
        3: "Siblings, courage, short journeys",
        4: "Mother, home, property, emotions",
        5: "Children, intelligence, romance, past-life merit",
        6: "Enemies, disease, debts, service",
        7: "Marriage, partnerships, public",
        8: "Longevity, occult, sudden events, inheritance",
        9: "Father, dharma, fortune, spirituality",
        10: "Career, authority, reputation",
        11: "Gains, friends, desires fulfilled",
        12: "Losses, expenses, liberation, foreign lands",
    },
}

# ---------------------------------------------------------------------------
# 2. COMPUTATION AND UTILITY FUNCTIONS
# ---------------------------------------------------------------------------


def compute_bhrigu_bindu(moon_longitude: float, rahu_longitude: float) -> float:
    """Compute Bhrigu Bindu as midpoint of Moon and Rahu longitudes (0-360).

    Both inputs must be in the same coordinate system (sidereal or tropical).
    Returns longitude in 0-360 range.

    The midpoint is taken over the shorter arc to ensure the result is the
    true midpoint between the two points, not the antipodal midpoint.

    Examples:
        >>> compute_bhrigu_bindu(30.0, 150.0)
        90.0
        >>> compute_bhrigu_bindu(350.0, 10.0)  # wrap-around: arc = 20°, midpoint = 0°
        0.0
    """
    # Normalise inputs to [0, 360)
    moon = moon_longitude % 360
    rahu = rahu_longitude % 360

    diff = abs(moon - rahu)

    if diff > 180:
        # The shorter arc crosses 0°/360° boundary — use the wrap-around midpoint
        mid = (moon + rahu + 360) / 2 % 360
    else:
        mid = (moon + rahu) / 2

    return mid % 360


def is_planet_activating_bb(
    planet_longitude: float, bb_longitude: float, orb: float = 3.0
) -> bool:
    """Return True if planet is within *orb* degrees of Bhrigu Bindu.

    Uses circular distance (accounts for 0°/360° wrap-around).

    Args:
        planet_longitude: Current longitude of the transiting planet (0-360).
        bb_longitude: Natal Bhrigu Bindu longitude (0-360).
        orb: Maximum allowable separation in degrees (default 3.0).

    Returns:
        True if the planet is within orb degrees of BB, False otherwise.
    """
    diff = abs(planet_longitude - bb_longitude) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= orb


def get_activation_significance(transiting_planet: str) -> str:
    """Return the significance of a given planet transiting Bhrigu Bindu.

    Args:
        transiting_planet: Name of the planet (case-insensitive).
            Accepted: sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu.

    Returns:
        Descriptive string. Returns "Unknown planet" if not found.
    """
    planet = transiting_planet.lower()
    return BHRIGU_BINDU_RULES["activation_significance"].get(
        planet, "Unknown planet"
    )


# ---------------------------------------------------------------------------
# 3. MODULE ASSERTIONS
# ---------------------------------------------------------------------------

assert "computation" in BHRIGU_BINDU_RULES
assert "activation_window_deg" in BHRIGU_BINDU_RULES
assert abs(compute_bhrigu_bindu(30.0, 150.0) - 90.0) < 0.001
assert abs(compute_bhrigu_bindu(350.0, 10.0) - 0.0) < 0.001   # wrap-around case
assert is_planet_activating_bb(90.0, 91.0, 3.0) is True
assert is_planet_activating_bb(90.0, 95.0, 3.0) is False
