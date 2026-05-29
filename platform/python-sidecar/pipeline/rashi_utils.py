"""
rashi_utils.py — Pure lookup table for 12 rashis (zodiac signs) with classical metadata.

No DB interaction, no swisseph calls. Maps sidereal longitude (0–360°) to
rashi name, tattva, guna, ruler, and degrees into rashi.

Sign boundaries: 30° each, starting at Mesha (Aries) = 0°.
"""

RASHIS = [
    {"id": 1,  "name": "Mesha",     "english": "Aries",       "ruler": "Mars",    "tattva": "Fire",  "guna": "Rajas",  "start_deg": 0.0,   "end_deg": 30.0},
    {"id": 2,  "name": "Vrishabha", "english": "Taurus",      "ruler": "Venus",   "tattva": "Earth", "guna": "Tamas",  "start_deg": 30.0,  "end_deg": 60.0},
    {"id": 3,  "name": "Mithuna",   "english": "Gemini",      "ruler": "Mercury", "tattva": "Air",   "guna": "Rajas",  "start_deg": 60.0,  "end_deg": 90.0},
    {"id": 4,  "name": "Karka",     "english": "Cancer",      "ruler": "Moon",    "tattva": "Water", "guna": "Tamas",  "start_deg": 90.0,  "end_deg": 120.0},
    {"id": 5,  "name": "Simha",     "english": "Leo",         "ruler": "Sun",     "tattva": "Fire",  "guna": "Rajas",  "start_deg": 120.0, "end_deg": 150.0},
    {"id": 6,  "name": "Kanya",     "english": "Virgo",       "ruler": "Mercury", "tattva": "Earth", "guna": "Tamas",  "start_deg": 150.0, "end_deg": 180.0},
    {"id": 7,  "name": "Tula",      "english": "Libra",       "ruler": "Venus",   "tattva": "Air",   "guna": "Rajas",  "start_deg": 180.0, "end_deg": 210.0},
    {"id": 8,  "name": "Vrischika", "english": "Scorpio",     "ruler": "Mars",    "tattva": "Water", "guna": "Tamas",  "start_deg": 210.0, "end_deg": 240.0},
    {"id": 9,  "name": "Dhanus",    "english": "Sagittarius", "ruler": "Jupiter", "tattva": "Fire",  "guna": "Rajas",  "start_deg": 240.0, "end_deg": 270.0},
    {"id": 10, "name": "Makara",    "english": "Capricorn",   "ruler": "Saturn",  "tattva": "Earth", "guna": "Tamas",  "start_deg": 270.0, "end_deg": 300.0},
    {"id": 11, "name": "Kumbha",    "english": "Aquarius",    "ruler": "Saturn",  "tattva": "Air",   "guna": "Rajas",  "start_deg": 300.0, "end_deg": 330.0},
    {"id": 12, "name": "Meena",     "english": "Pisces",      "ruler": "Jupiter", "tattva": "Water", "guna": "Tamas",  "start_deg": 330.0, "end_deg": 360.0},
]

# Sanity checks at import
assert len(RASHIS) == 12, "RASHIS must have exactly 12 entries"
for _i, _r in enumerate(RASHIS):
    assert _r["id"] == _i + 1, f"Rashi id mismatch at index {_i}: expected {_i + 1}, got {_r['id']}"
    assert _r["start_deg"] == _i * 30.0, f"start_deg mismatch at index {_i}"
    assert _r["end_deg"] == (_i + 1) * 30.0, f"end_deg mismatch at index {_i}"


def rashi_for_longitude(sidereal_lon: float) -> dict:
    """
    Returns rashi dict + degrees_into for a sidereal longitude.

    Args:
        sidereal_lon: Sidereal longitude in degrees (any real number; wrapped mod 360).

    Returns:
        dict with all RASHIS fields plus:
            "degrees_into": float (degrees into the rashi, 6 decimal places)
    """
    lon = sidereal_lon % 360.0
    idx = int(lon / 30.0)
    # Guard against floating-point edge case at exactly 360.0 after mod
    if idx >= 12:
        idx = 11
    rashi = RASHIS[idx]
    deg_into = lon - rashi["start_deg"]
    # Clamp to avoid negative result from floating-point edge cases
    deg_into = max(0.0, deg_into)
    return {**rashi, "degrees_into": round(deg_into, 6)}


def rashi_for_all_ayanamshas(tropical_lon: float, ayanamsha_values: dict) -> dict:
    """
    Returns {ayanamsha_id: rashi_result} for each ayanamsha in ayanamsha_values.

    Args:
        tropical_lon: Tropical (Western) longitude in degrees.
        ayanamsha_values: dict mapping ayanamsha_id (str or int) → offset in degrees.
                          Sidereal longitude = tropical_lon - offset.

    Returns:
        dict mapping each ayanamsha_id to its rashi_for_longitude result.
    """
    return {
        ayanamsha_id: rashi_for_longitude(tropical_lon - offset)
        for ayanamsha_id, offset in ayanamsha_values.items()
    }
