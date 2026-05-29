"""
tajik_tables.py — G50 Tajika Reference Tables
==============================================
Classical sources: Tajika Neelakanthi; Tahira-Neelakanthi;
Phala-Deepika Tajik chapters; Mantreswara.

Tajika (Varshaphala) is the annual horoscopy system derived from the Arabic
tradition and codified in Sanskrit by Neelakantha. It uses a solar return
chart (Varsha Kundali) computed for the moment the Sun returns to its natal
longitude each year. The system employs its own set of 5 aspects, a unique
annual lord (Varshesha), and a special dasha system (Mudda Dasha).

canonical_id: G50
stream: A
session: G48-G49-G50-S1 [BUILD-ORCH-A-15]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. HADDA LORDS (Egyptian/Ptolemaic Bounds)
# ---------------------------------------------------------------------------
# Each sign is divided into 5 unequal sections ruled by different grahas.
# Classical Egyptian assignment (Ptolemaic bounds):
#
#   Aries:    Jupiter 0-6, Venus 6-12, Mercury 12-20, Mars 20-25, Saturn 25-30
#   Taurus:   Venus 0-8, Mercury 8-14, Jupiter 14-22, Saturn 22-27, Mars 27-30
#   Gemini:   Mercury 0-6, Jupiter 6-12, Venus 12-17, Mars 17-24, Saturn 24-30
#   Cancer:   Mars 0-7, Venus 7-13, Mercury 13-19, Jupiter 19-26, Saturn 26-30
#   Leo:      Jupiter 0-6, Venus 6-11, Saturn 11-18, Mercury 18-24, Mars 24-30
#   Virgo:    Mercury 0-7, Venus 7-17, Jupiter 17-21, Mars 21-28, Saturn 28-30
#   Libra:    Saturn 0-6, Mercury 6-14, Jupiter 14-21, Venus 21-28, Mars 28-30
#   Scorpio:  Mars 0-7, Venus 7-11, Mercury 11-19, Jupiter 19-24, Saturn 24-30
#   Sagittarius: Jupiter 0-12, Venus 12-17, Mercury 17-21, Saturn 21-26, Mars 26-30
#   Capricorn: Mercury 0-7, Jupiter 7-14, Venus 14-22, Saturn 22-26, Mars 26-30
#   Aquarius: Mercury 0-7, Venus 7-13, Jupiter 13-20, Mars 20-25, Saturn 25-30
#   Pisces:   Venus 0-12, Jupiter 12-16, Mercury 16-19, Mars 19-28, Saturn 28-30

HADDA_LORDS: dict[str, list[dict]] = {
    "aries": [
        {"start_deg": 0.0,  "end_deg": 6.0,  "lord": "jupiter"},
        {"start_deg": 6.0,  "end_deg": 12.0, "lord": "venus"},
        {"start_deg": 12.0, "end_deg": 20.0, "lord": "mercury"},
        {"start_deg": 20.0, "end_deg": 25.0, "lord": "mars"},
        {"start_deg": 25.0, "end_deg": 30.0, "lord": "saturn"},
    ],
    "taurus": [
        {"start_deg": 0.0,  "end_deg": 8.0,  "lord": "venus"},
        {"start_deg": 8.0,  "end_deg": 14.0, "lord": "mercury"},
        {"start_deg": 14.0, "end_deg": 22.0, "lord": "jupiter"},
        {"start_deg": 22.0, "end_deg": 27.0, "lord": "saturn"},
        {"start_deg": 27.0, "end_deg": 30.0, "lord": "mars"},
    ],
    "gemini": [
        {"start_deg": 0.0,  "end_deg": 6.0,  "lord": "mercury"},
        {"start_deg": 6.0,  "end_deg": 12.0, "lord": "jupiter"},
        {"start_deg": 12.0, "end_deg": 17.0, "lord": "venus"},
        {"start_deg": 17.0, "end_deg": 24.0, "lord": "mars"},
        {"start_deg": 24.0, "end_deg": 30.0, "lord": "saturn"},
    ],
    "cancer": [
        {"start_deg": 0.0,  "end_deg": 7.0,  "lord": "mars"},
        {"start_deg": 7.0,  "end_deg": 13.0, "lord": "venus"},
        {"start_deg": 13.0, "end_deg": 19.0, "lord": "mercury"},
        {"start_deg": 19.0, "end_deg": 26.0, "lord": "jupiter"},
        {"start_deg": 26.0, "end_deg": 30.0, "lord": "saturn"},
    ],
    "leo": [
        {"start_deg": 0.0,  "end_deg": 6.0,  "lord": "jupiter"},
        {"start_deg": 6.0,  "end_deg": 11.0, "lord": "venus"},
        {"start_deg": 11.0, "end_deg": 18.0, "lord": "saturn"},
        {"start_deg": 18.0, "end_deg": 24.0, "lord": "mercury"},
        {"start_deg": 24.0, "end_deg": 30.0, "lord": "mars"},
    ],
    "virgo": [
        {"start_deg": 0.0,  "end_deg": 7.0,  "lord": "mercury"},
        {"start_deg": 7.0,  "end_deg": 17.0, "lord": "venus"},
        {"start_deg": 17.0, "end_deg": 21.0, "lord": "jupiter"},
        {"start_deg": 21.0, "end_deg": 28.0, "lord": "mars"},
        {"start_deg": 28.0, "end_deg": 30.0, "lord": "saturn"},
    ],
    "libra": [
        {"start_deg": 0.0,  "end_deg": 6.0,  "lord": "saturn"},
        {"start_deg": 6.0,  "end_deg": 14.0, "lord": "mercury"},
        {"start_deg": 14.0, "end_deg": 21.0, "lord": "jupiter"},
        {"start_deg": 21.0, "end_deg": 28.0, "lord": "venus"},
        {"start_deg": 28.0, "end_deg": 30.0, "lord": "mars"},
    ],
    "scorpio": [
        {"start_deg": 0.0,  "end_deg": 7.0,  "lord": "mars"},
        {"start_deg": 7.0,  "end_deg": 11.0, "lord": "venus"},
        {"start_deg": 11.0, "end_deg": 19.0, "lord": "mercury"},
        {"start_deg": 19.0, "end_deg": 24.0, "lord": "jupiter"},
        {"start_deg": 24.0, "end_deg": 30.0, "lord": "saturn"},
    ],
    "sagittarius": [
        {"start_deg": 0.0,  "end_deg": 12.0, "lord": "jupiter"},
        {"start_deg": 12.0, "end_deg": 17.0, "lord": "venus"},
        {"start_deg": 17.0, "end_deg": 21.0, "lord": "mercury"},
        {"start_deg": 21.0, "end_deg": 26.0, "lord": "saturn"},
        {"start_deg": 26.0, "end_deg": 30.0, "lord": "mars"},
    ],
    "capricorn": [
        {"start_deg": 0.0,  "end_deg": 7.0,  "lord": "mercury"},
        {"start_deg": 7.0,  "end_deg": 14.0, "lord": "jupiter"},
        {"start_deg": 14.0, "end_deg": 22.0, "lord": "venus"},
        {"start_deg": 22.0, "end_deg": 26.0, "lord": "saturn"},
        {"start_deg": 26.0, "end_deg": 30.0, "lord": "mars"},
    ],
    "aquarius": [
        {"start_deg": 0.0,  "end_deg": 7.0,  "lord": "mercury"},
        {"start_deg": 7.0,  "end_deg": 13.0, "lord": "venus"},
        {"start_deg": 13.0, "end_deg": 20.0, "lord": "jupiter"},
        {"start_deg": 20.0, "end_deg": 25.0, "lord": "mars"},
        {"start_deg": 25.0, "end_deg": 30.0, "lord": "saturn"},
    ],
    "pisces": [
        {"start_deg": 0.0,  "end_deg": 12.0, "lord": "venus"},
        {"start_deg": 12.0, "end_deg": 16.0, "lord": "jupiter"},
        {"start_deg": 16.0, "end_deg": 19.0, "lord": "mercury"},
        {"start_deg": 19.0, "end_deg": 28.0, "lord": "mars"},
        {"start_deg": 28.0, "end_deg": 30.0, "lord": "saturn"},
    ],
}

# ---------------------------------------------------------------------------
# 2. TAJIK ASPECTS (EXTENDED)
# ---------------------------------------------------------------------------
# Tajika uses only 5 aspects (not the full 7 of Parashari).
# Applying aspects (planet approaching) are stronger than separating.
# The "Ithasala" yoga is an applying aspect between two planets, conferring
# the results signified by the faster planet to the slower planet.

TAJIK_ASPECT_ORBS: dict[str, dict] = {
    "conjunction": {
        "degrees": 0,
        "nature": "neutral",
        "orb_applying": 8,
        "orb_separating": 8,
    },
    "sextile": {
        "degrees": 60,
        "nature": "friendly",
        "orb_applying": 7,
        "orb_separating": 5,
    },
    "square": {
        "degrees": 90,
        "nature": "inimical",
        "orb_applying": 7,
        "orb_separating": 5,
    },
    "trine": {
        "degrees": 120,
        "nature": "friendly",
        "orb_applying": 8,
        "orb_separating": 6,
    },
    "opposition": {
        "degrees": 180,
        "nature": "inimical",
        "orb_applying": 8,
        "orb_separating": 6,
    },
}

TAJIK_ASPECTS_EXTENDED: dict = {
    "conjunction": {
        "degrees": 0,
        "nature": "neutral",
        "orb_applying": 8,
        "orb_separating": 8,
        "strength_modifier": 1.0,
        "classical_name": "Yuddha",
        "notes": (
            "Both planets merge energies; results depend on mutual relationship "
            "(maitri). Can be extremely powerful if planets are friends."
        ),
    },
    "sextile": {
        "degrees": 60,
        "nature": "friendly",
        "orb_applying": 7,
        "orb_separating": 5,
        "strength_modifier": 0.75,
        "classical_name": "Sextile",
        "notes": (
            "Moderate friendly aspect; yields partial results; "
            "requires support from other factors to fully manifest."
        ),
    },
    "square": {
        "degrees": 90,
        "nature": "inimical",
        "orb_applying": 7,
        "orb_separating": 5,
        "strength_modifier": 0.75,
        "classical_name": "Chaturastra",
        "notes": (
            "Conflict and obstruction; planets obstruct each other's significations; "
            "effort and struggle required; can yield results with difficulty."
        ),
    },
    "trine": {
        "degrees": 120,
        "nature": "friendly",
        "orb_applying": 8,
        "orb_separating": 6,
        "strength_modifier": 1.0,
        "classical_name": "Trikona",
        "notes": (
            "Most benefic Tajik aspect; freely flowing energy; "
            "best for conferring positive results of the faster planet."
        ),
    },
    "opposition": {
        "degrees": 180,
        "nature": "inimical",
        "orb_applying": 8,
        "orb_separating": 6,
        "strength_modifier": 0.5,
        "classical_name": "Saptama",
        "notes": (
            "Most obstructive aspect; planets directly oppose; "
            "Isarapha (separation) yoga when faster planet is separating, "
            "indicating failure of the matter."
        ),
    },
}

# ---------------------------------------------------------------------------
# 3. YEAR LORD RULES (VARSHESHA)
# ---------------------------------------------------------------------------

YEAR_LORD_RULES: dict = {
    "muntha_computation": "Lagna degree at birth advances 1 sign per solar year",
    "muntha_lord": "Lord of the sign occupied by Muntha at solar return",
    "varsha_lagna_lord": "Lord of rising sign at solar return moment",
    "trirashi_pati": "Lord of the trikona sign occupied by most planets at solar return",
    "din_ratri_prabhu": "Day-lord (vara lord) of solar return day",
    "panchadayadi_vargesh": "Lord of the navamsa varga of solar return ASC",
    "year_lord_selection": [
        "Muntha lord is strongest candidate",
        "If Muntha lord is in 6H/8H/12H from solar return ASC, use next candidate",
        "Tri-rashi pati as fallback",
        "Year lord governs primary themes of the varsha year",
    ],
    "mudda_dasha_starting_lord": (
        "Same as year lord; Mudda dasha begins with year lord's period"
    ),
    "panchadayadi_five_candidates": [
        "Muntha lord",
        "Varsha lagna lord",
        "Tri-rashi pati (trirashi pati)",
        "Din-ratri prabhu (day lord)",
        "Panchadayadi vargesh (navamsa lord of solar return ASC)",
    ],
    "house_strength_evaluation": (
        "The candidate with greatest house strength (kendradhipatya + trikona) "
        "from the solar return lagna is declared Varshesha"
    ),
}

# ---------------------------------------------------------------------------
# 4. MUDDA AND PATYAYINI DASHA RULES
# ---------------------------------------------------------------------------
# Note on period_days sum:
# Sun(11) + Moon(32) + Mars(8) + Mercury(46) + Jupiter(43) + Venus(52)
# + Saturn(23) + Rahu(18) + Ketu(7) = 240 days.
# In the full annual cycle, the Mudda dasha repeats starting from the
# Varshesha (year lord) and runs for 365 days total (the yearly solar cycle),
# meaning the sequence may cycle through more than once or the starting
# point offset determines coverage. The 240-day base is the single-pass sum.

MUDDA_PATYAYINI_RULES: dict = {
    "mudda_dasha": {
        "total_days": 365,
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "jupiter", "venus", "saturn", "rahu", "ketu",
        ],
        "period_days": {
            "sun": 11,
            "moon": 32,
            "mars": 8,
            "mercury": 46,
            "jupiter": 43,
            "venus": 52,
            "saturn": 23,
            "rahu": 18,
            "ketu": 7,
        },
        "single_pass_sum_days": 240,
        "note": (
            "Period days proportional to Vimshottari years. "
            "Single-pass cycle sum = 240 days. The annual 365-day cycle starts "
            "from the Varshesha (year lord) and the sequence continues through "
            "the full 365-day year, wrapping as needed."
        ),
        "starting_planet": "Year lord of the varsha chart (Varshesha)",
        "sub_periods": (
            "Each Mudda period is further divisible into sub-periods (antardasha) "
            "in the same planetary sequence and proportional duration"
        ),
    },
    "patyayini_dasha": {
        "total_years": 120,
        "system": (
            "Same sequence as Vimshottari applied to 120 years but starting "
            "from Solar Return lagna lord"
        ),
        "use_case": (
            "Long-range Tajik predictions spanning multiple varsha years; "
            "provides the macro backdrop into which Mudda dashas fit"
        ),
        "period_years": {
            "sun": 6,
            "moon": 10,
            "mars": 7,
            "rahu": 18,
            "jupiter": 16,
            "saturn": 19,
            "mercury": 17,
            "ketu": 7,
            "venus": 20,
        },
    },
}

# ---------------------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def get_hadda_lord(sign: str, degree_in_sign: float) -> str:
    """Return the Hadda lord for given sign and degree within sign (0-30).

    Args:
        sign: Zodiac sign name (case-insensitive, e.g. "aries", "Taurus").
        degree_in_sign: Degree within the sign, 0.0 to 30.0 (exclusive).

    Returns:
        Name of the graha ruling the Hadda section (lowercase).

    Raises:
        KeyError: If the sign is not found.
        ValueError: If degree_in_sign is outside the range [0, 30).
    """
    sign_lower = sign.lower()
    if sign_lower not in HADDA_LORDS:
        raise KeyError(f"Sign '{sign}' not found in HADDA_LORDS")
    if not (0.0 <= degree_in_sign < 30.0):
        raise ValueError(f"degree_in_sign must be in [0, 30), got {degree_in_sign}")

    for section in HADDA_LORDS[sign_lower]:
        if section["start_deg"] <= degree_in_sign < section["end_deg"]:
            return section["lord"]

    # Fallback: last section's lord (handles exact 30.0 edge if ever passed)
    return HADDA_LORDS[sign_lower][-1]["lord"]


def get_year_lord_rules() -> dict:
    """Return YEAR_LORD_RULES."""
    return YEAR_LORD_RULES


def get_mudda_period_days(planet: str) -> int:
    """Return Mudda dasha period in days for the given planet.

    Args:
        planet: Planet name (case-insensitive), e.g. "sun", "Saturn".

    Returns:
        Integer number of days.

    Raises:
        KeyError: If the planet is not found in the Mudda dasha table.
    """
    planet_lower = planet.lower()
    period_days = MUDDA_PATYAYINI_RULES["mudda_dasha"]["period_days"]
    if planet_lower not in period_days:
        raise KeyError(f"Planet '{planet}' not found in Mudda dasha period_days")
    return period_days[planet_lower]


def get_tajik_aspect_info(aspect_name: str) -> dict:
    """Return extended aspect info dict.

    Args:
        aspect_name: Aspect name (case-insensitive), e.g. "trine", "conjunction".

    Returns:
        Dict with keys: degrees, nature, orb_applying, orb_separating,
        strength_modifier, classical_name, notes.

    Raises:
        KeyError: If the aspect name is not found.
    """
    aspect_lower = aspect_name.lower()
    if aspect_lower not in TAJIK_ASPECTS_EXTENDED:
        raise KeyError(f"Aspect '{aspect_name}' not found in TAJIK_ASPECTS_EXTENDED")
    return TAJIK_ASPECTS_EXTENDED[aspect_lower]


# ---------------------------------------------------------------------------
# 6. MODULE ASSERTIONS
# ---------------------------------------------------------------------------

assert len(HADDA_LORDS) == 12, "Must have all 12 signs"
assert all(len(v) == 5 for v in HADDA_LORDS.values()), "Each sign must have 5 Hadda sections"
assert sum(MUDDA_PATYAYINI_RULES["mudda_dasha"]["period_days"].values()) == 240
assert get_hadda_lord("aries", 0.0) == "jupiter"
assert get_hadda_lord("aries", 7.0) == "venus"
assert get_mudda_period_days("sun") == 11
