"""
nakshatra_utils.py — Pure lookup table for 27 nakshatras with pada boundaries.

No DB interaction, no swisseph calls. Maps sidereal longitude (0–360°) to
nakshatra name, pada (1–4), and degrees into nakshatra.

Ruler cycle (repeats × 3): Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
"""

NAKSHATRA_SPAN = 360.0 / 27  # 13.333333...°
PADA_SIZE = NAKSHATRA_SPAN / 4  # 3.333333...°

NAKSHATRAS = [
    {
        "id": 1,
        "name": "Ashwini",
        "deity": "Ashwini Kumaras",
        "ruler": "Ketu",
        "start_deg": 0.0,
        "end_deg": NAKSHATRA_SPAN * 1,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 2,
        "name": "Bharani",
        "deity": "Yama",
        "ruler": "Venus",
        "start_deg": NAKSHATRA_SPAN * 1,
        "end_deg": NAKSHATRA_SPAN * 2,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 3,
        "name": "Krittika",
        "deity": "Agni",
        "ruler": "Sun",
        "start_deg": NAKSHATRA_SPAN * 2,
        "end_deg": NAKSHATRA_SPAN * 3,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 4,
        "name": "Rohini",
        "deity": "Brahma",
        "ruler": "Moon",
        "start_deg": NAKSHATRA_SPAN * 3,
        "end_deg": NAKSHATRA_SPAN * 4,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 5,
        "name": "Mrigashira",
        "deity": "Soma",
        "ruler": "Mars",
        "start_deg": NAKSHATRA_SPAN * 4,
        "end_deg": NAKSHATRA_SPAN * 5,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 6,
        "name": "Ardra",
        "deity": "Rudra",
        "ruler": "Rahu",
        "start_deg": NAKSHATRA_SPAN * 5,
        "end_deg": NAKSHATRA_SPAN * 6,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 7,
        "name": "Punarvasu",
        "deity": "Aditi",
        "ruler": "Jupiter",
        "start_deg": NAKSHATRA_SPAN * 6,
        "end_deg": NAKSHATRA_SPAN * 7,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 8,
        "name": "Pushya",
        "deity": "Brihaspati",
        "ruler": "Saturn",
        "start_deg": NAKSHATRA_SPAN * 7,
        "end_deg": NAKSHATRA_SPAN * 8,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 9,
        "name": "Ashlesha",
        "deity": "Nagas",
        "ruler": "Mercury",
        "start_deg": NAKSHATRA_SPAN * 8,
        "end_deg": NAKSHATRA_SPAN * 9,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 10,
        "name": "Magha",
        "deity": "Pitrs",
        "ruler": "Ketu",
        "start_deg": NAKSHATRA_SPAN * 9,
        "end_deg": NAKSHATRA_SPAN * 10,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 11,
        "name": "PurvaPhalguni",
        "deity": "Bhaga",
        "ruler": "Venus",
        "start_deg": NAKSHATRA_SPAN * 10,
        "end_deg": NAKSHATRA_SPAN * 11,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 12,
        "name": "UttaraPhalguni",
        "deity": "Aryaman",
        "ruler": "Sun",
        "start_deg": NAKSHATRA_SPAN * 11,
        "end_deg": NAKSHATRA_SPAN * 12,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 13,
        "name": "Hasta",
        "deity": "Savitri",
        "ruler": "Moon",
        "start_deg": NAKSHATRA_SPAN * 12,
        "end_deg": NAKSHATRA_SPAN * 13,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 14,
        "name": "Chitra",
        "deity": "Tvashtr",
        "ruler": "Mars",
        "start_deg": NAKSHATRA_SPAN * 13,
        "end_deg": NAKSHATRA_SPAN * 14,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 15,
        "name": "Swati",
        "deity": "Vayu",
        "ruler": "Rahu",
        "start_deg": NAKSHATRA_SPAN * 14,
        "end_deg": NAKSHATRA_SPAN * 15,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 16,
        "name": "Vishakha",
        "deity": "Indra-Agni",
        "ruler": "Jupiter",
        "start_deg": NAKSHATRA_SPAN * 15,
        "end_deg": NAKSHATRA_SPAN * 16,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 17,
        "name": "Anuradha",
        "deity": "Mitra",
        "ruler": "Saturn",
        "start_deg": NAKSHATRA_SPAN * 16,
        "end_deg": NAKSHATRA_SPAN * 17,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 18,
        "name": "Jyeshtha",
        "deity": "Indra",
        "ruler": "Mercury",
        "start_deg": NAKSHATRA_SPAN * 17,
        "end_deg": NAKSHATRA_SPAN * 18,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 19,
        "name": "Mula",
        "deity": "Nirriti",
        "ruler": "Ketu",
        "start_deg": NAKSHATRA_SPAN * 18,
        "end_deg": NAKSHATRA_SPAN * 19,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 20,
        "name": "PurvaAshadha",
        "deity": "Apas",
        "ruler": "Venus",
        "start_deg": NAKSHATRA_SPAN * 19,
        "end_deg": NAKSHATRA_SPAN * 20,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 21,
        "name": "UttaraAshadha",
        "deity": "Vishvadevas",
        "ruler": "Sun",
        "start_deg": NAKSHATRA_SPAN * 20,
        "end_deg": NAKSHATRA_SPAN * 21,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 22,
        "name": "Shravana",
        "deity": "Vishnu",
        "ruler": "Moon",
        "start_deg": NAKSHATRA_SPAN * 21,
        "end_deg": NAKSHATRA_SPAN * 22,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 23,
        "name": "Dhanishtha",
        "deity": "Ashta Vasus",
        "ruler": "Mars",
        "start_deg": NAKSHATRA_SPAN * 22,
        "end_deg": NAKSHATRA_SPAN * 23,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 24,
        "name": "Shatabhisha",
        "deity": "Varuna",
        "ruler": "Rahu",
        "start_deg": NAKSHATRA_SPAN * 23,
        "end_deg": NAKSHATRA_SPAN * 24,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 25,
        "name": "PurvaBhadrapada",
        "deity": "Aja Ekapad",
        "ruler": "Jupiter",
        "start_deg": NAKSHATRA_SPAN * 24,
        "end_deg": NAKSHATRA_SPAN * 25,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 26,
        "name": "UttaraBhadrapada",
        "deity": "Ahir Budhnya",
        "ruler": "Saturn",
        "start_deg": NAKSHATRA_SPAN * 25,
        "end_deg": NAKSHATRA_SPAN * 26,
        "pada_size": PADA_SIZE,
    },
    {
        "id": 27,
        "name": "Revati",
        "deity": "Pushan",
        "ruler": "Mercury",
        "start_deg": NAKSHATRA_SPAN * 26,
        "end_deg": 360.0,
        "pada_size": PADA_SIZE,
    },
]

# Sanity check at import: ensure exactly 27 entries and ruler cycle is correct.
assert len(NAKSHATRAS) == 27, "NAKSHATRAS must have exactly 27 entries"
_RULER_CYCLE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
for _i, _nak in enumerate(NAKSHATRAS):
    assert _nak["ruler"] == _RULER_CYCLE[_i % 9], (
        f"Ruler mismatch at index {_i}: expected {_RULER_CYCLE[_i % 9]}, got {_nak['ruler']}"
    )


def nakshatra_for_longitude(sidereal_lon: float) -> dict:
    """
    Returns nakshatra dict + pada (1–4) + degrees_into_nakshatra for a sidereal longitude.

    Args:
        sidereal_lon: Sidereal longitude in degrees (any real number; wrapped mod 360).

    Returns:
        dict with all NAKSHATRAS fields plus:
            "pada": int (1–4)
            "degrees_into": float (degrees into the nakshatra, 6 decimal places)
    """
    lon = sidereal_lon % 360.0
    idx = int(lon / NAKSHATRA_SPAN)
    # Guard against floating-point edge case at exactly 360.0 after mod
    if idx >= 27:
        idx = 26
    nak = NAKSHATRAS[idx]
    deg_into = lon - nak["start_deg"]
    # Clamp to avoid negative due to floating-point
    deg_into = max(0.0, deg_into)
    pada = int(deg_into / PADA_SIZE) + 1
    return {**nak, "pada": min(pada, 4), "degrees_into": round(deg_into, 6)}


def nakshatra_for_all_ayanamshas(tropical_lon: float, ayanamsha_values: dict) -> dict:
    """
    Returns {ayanamsha_id: nakshatra_result} for each ayanamsha in ayanamsha_values.

    Args:
        tropical_lon: Tropical (Western) longitude in degrees.
        ayanamsha_values: dict mapping ayanamsha_id (str or int) → offset in degrees.
                          Sidereal longitude = tropical_lon - offset.

    Returns:
        dict mapping each ayanamsha_id to its nakshatra_for_longitude result.
    """
    return {
        ayanamsha_id: nakshatra_for_longitude(tropical_lon - offset)
        for ayanamsha_id, offset in ayanamsha_values.items()
    }
