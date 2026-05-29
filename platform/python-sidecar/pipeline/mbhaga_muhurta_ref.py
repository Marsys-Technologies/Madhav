"""
mbhaga_muhurta_ref.py — G25 + G26 global reference data
G25: Mrityubhaga critical degrees, Gandanta junction zones, Pushkara navamsas
G26: Muhurta auspiciousness tables (tithi, vara, nakshatra, Abhijit)

Sources: BPHS classical tradition; Muhurta-Chintamani; Hora Shastra.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# G25 — Sensitive degree points
# ---------------------------------------------------------------------------

# Mrityubhaga degrees per graha per sign.
# Format: graha -> list of (sign_index, degree) where sign_index 0=Aries…11=Pisces
# Source: BPHS / classical tradition (degrees are approximate; tradition varies).
MRITYUBHAGA_DEGREES: dict[str, list[tuple[int, float]]] = {
    "sun":     [(0, 20), (1, 9),  (2, 12), (3, 6),  (4, 8),  (5, 24),
                (6, 16), (7, 17), (8, 22), (9, 2),  (10, 3), (11, 23)],
    "moon":    [(0, 26), (1, 12), (2, 13), (3, 25), (4, 24), (5, 11),
                (6, 26), (7, 14), (8, 13), (9, 25), (10, 5), (11, 12)],
    "mars":    [(0, 20), (1, 28), (2, 20), (3, 20), (4, 20), (5, 20),
                (6, 20), (7, 28), (8, 20), (9, 20), (10, 20), (11, 20)],
    "mercury": [(0, 15), (1, 14), (2, 8),  (3, 19), (4, 1),  (5, 14),
                (6, 15), (7, 14), (8, 8),  (9, 19), (10, 1), (11, 14)],
    "jupiter": [(0, 18), (1, 28), (2, 23), (3, 18), (4, 23), (5, 27),
                (6, 18), (7, 28), (8, 23), (9, 18), (10, 23), (11, 27)],
    "venus":   [(0, 27), (1, 11), (2, 28), (3, 4),  (4, 25), (5, 19),
                (6, 27), (7, 11), (8, 28), (9, 4),  (10, 25), (11, 19)],
    "saturn":  [(0, 21), (1, 11), (2, 21), (3, 20), (4, 13), (5, 15),
                (6, 21), (7, 11), (8, 21), (9, 20), (10, 13), (11, 15)],
}

# Gandanta zones — junctions between water-sign tail and fire-sign head.
# Each zone spans last 3°20' of the water sign (deg 26°40'=26.666…) and
# first 3°20' of the following fire sign (deg 0°–3°20'=3.333…).
GANDANTA_ZONES: list[dict] = [
    {
        "from_sign": "pisces",    "from_sign_index": 11,
        "to_sign":   "aries",     "to_sign_index":   0,
        "gandanta_start_deg": 26.666,   # last 3°20' of Pisces
        "gandanta_end_deg":    3.333,   # first 3°20' of Aries
    },
    {
        "from_sign": "cancer",    "from_sign_index": 3,
        "to_sign":   "leo",       "to_sign_index":   4,
        "gandanta_start_deg": 26.666,
        "gandanta_end_deg":    3.333,
    },
    {
        "from_sign": "scorpio",   "from_sign_index": 7,
        "to_sign":   "sagittarius", "to_sign_index": 8,
        "gandanta_start_deg": 26.666,
        "gandanta_end_deg":    3.333,
    },
]

# Pushkara navamsas — auspicious navamsa positions.
# Classical rule: 4th navamsa (10°–13°20') and 8th navamsa (23°20'–26°40')
# of every sign are Pushkara navamsas.
# navamsa width = 30/9 = 3.333…°
_SIGN_NAMES = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

PUSHKARA_NAVAMSAS: list[dict] = []
for _si, _sn in enumerate(_SIGN_NAMES):
    # 4th navamsa: spans 10°–13°20'
    PUSHKARA_NAVAMSAS.append({
        "sign": _sn, "sign_index": _si,
        "navamsa": 4, "start_deg": 10.0, "end_deg": 13.333,
    })
    # 8th navamsa: spans 23°20'–26°40'
    PUSHKARA_NAVAMSAS.append({
        "sign": _sn, "sign_index": _si,
        "navamsa": 8, "start_deg": 23.333, "end_deg": 26.667,
    })


# ---------------------------------------------------------------------------
# G26 — Muhurta auspiciousness tables
# ---------------------------------------------------------------------------

# Tithi quality — tithis 1–30.
# 1–15: bright fortnight (Shukla Paksha). 16–30: dark fortnight (Krishna Paksha).
# 30 = Amavasya (new moon).
TITHI_QUALITY: dict[int, dict] = {
    1:  {"name": "Pratipada (S)",    "quality": "mixed"},
    2:  {"name": "Dwitiya (S)",      "quality": "good"},
    3:  {"name": "Tritiya (S)",      "quality": "good"},
    4:  {"name": "Chaturthi (S)",    "quality": "mixed"},
    5:  {"name": "Panchami (S)",     "quality": "good"},
    6:  {"name": "Shashthi (S)",     "quality": "mixed"},
    7:  {"name": "Saptami (S)",      "quality": "good"},
    8:  {"name": "Ashtami (S)",      "quality": "mixed"},
    9:  {"name": "Navami (S)",       "quality": "mixed"},
    10: {"name": "Dashami (S)",      "quality": "good"},
    11: {"name": "Ekadashi (S)",     "quality": "good"},
    12: {"name": "Dwadashi (S)",     "quality": "good"},
    13: {"name": "Trayodashi (S)",   "quality": "good"},
    14: {"name": "Chaturdashi (S)",  "quality": "mixed"},
    15: {"name": "Purnima",          "quality": "good"},
    16: {"name": "Pratipada (K)",    "quality": "inauspicious"},
    17: {"name": "Dwitiya (K)",      "quality": "inauspicious"},
    18: {"name": "Tritiya (K)",      "quality": "inauspicious"},
    19: {"name": "Chaturthi (K)",    "quality": "inauspicious"},
    20: {"name": "Panchami (K)",     "quality": "inauspicious"},
    21: {"name": "Shashthi (K)",     "quality": "inauspicious"},
    22: {"name": "Saptami (K)",      "quality": "inauspicious"},
    23: {"name": "Ashtami (K)",      "quality": "inauspicious"},
    24: {"name": "Navami (K)",       "quality": "inauspicious"},
    25: {"name": "Dashami (K)",      "quality": "inauspicious"},
    26: {"name": "Ekadashi (K)",     "quality": "inauspicious"},
    27: {"name": "Dwadashi (K)",     "quality": "inauspicious"},
    28: {"name": "Trayodashi (K)",   "quality": "inauspicious"},
    29: {"name": "Chaturdashi (K)",  "quality": "inauspicious"},
    30: {"name": "Amavasya",         "quality": "inauspicious"},
}

# Vara (weekday) quality.
VARA_QUALITY: dict[str, dict] = {
    "sunday":    {"lord": "sun",     "quality": "mixed"},
    "monday":    {"lord": "moon",    "quality": "good"},
    "tuesday":   {"lord": "mars",    "quality": "inauspicious"},
    "wednesday": {"lord": "mercury", "quality": "good"},
    "thursday":  {"lord": "jupiter", "quality": "good"},
    "friday":    {"lord": "venus",   "quality": "good"},
    "saturday":  {"lord": "saturn",  "quality": "mixed"},
}

# Nakshatra muhurta classification — all 27 nakshatras.
# Classes: dhruva (fixed), chara (movable), mridu (soft), ugra (fierce),
#          tikshna (sharp), sadharana (common/mixed).
NAKSHATRA_MUHURTA_CLASS: dict[int, dict] = {
    1:  {"name": "Ashwini",          "class": "chara",      "lord": "ketu"},
    2:  {"name": "Bharani",          "class": "ugra",       "lord": "venus"},
    3:  {"name": "Krittika",         "class": "tikshna",    "lord": "sun"},
    4:  {"name": "Rohini",           "class": "dhruva",     "lord": "moon"},
    5:  {"name": "Mrigashira",       "class": "mridu",      "lord": "mars"},
    6:  {"name": "Ardra",            "class": "tikshna",    "lord": "rahu"},
    7:  {"name": "Punarvasu",        "class": "chara",      "lord": "jupiter"},
    8:  {"name": "Pushya",           "class": "mridu",      "lord": "saturn"},
    9:  {"name": "Ashlesha",         "class": "tikshna",    "lord": "mercury"},
    10: {"name": "Magha",            "class": "ugra",       "lord": "ketu"},
    11: {"name": "Purva Phalguni",   "class": "ugra",       "lord": "venus"},
    12: {"name": "Uttara Phalguni",  "class": "dhruva",     "lord": "sun"},
    13: {"name": "Hasta",            "class": "dhruva",     "lord": "moon"},
    14: {"name": "Chitra",           "class": "mridu",      "lord": "mars"},
    15: {"name": "Swati",            "class": "chara",      "lord": "rahu"},
    16: {"name": "Vishakha",         "class": "sadharana",  "lord": "jupiter"},
    17: {"name": "Anuradha",         "class": "mridu",      "lord": "saturn"},
    18: {"name": "Jyeshtha",         "class": "tikshna",    "lord": "mercury"},
    19: {"name": "Mula",             "class": "tikshna",    "lord": "ketu"},
    20: {"name": "Purva Ashadha",    "class": "ugra",       "lord": "venus"},
    21: {"name": "Uttara Ashadha",   "class": "dhruva",     "lord": "sun"},
    22: {"name": "Shravana",         "class": "chara",      "lord": "moon"},
    23: {"name": "Dhanishtha",       "class": "chara",      "lord": "mars"},
    24: {"name": "Shatabhisha",      "class": "sadharana",  "lord": "rahu"},
    25: {"name": "Purva Bhadrapada", "class": "ugra",       "lord": "jupiter"},
    26: {"name": "Uttara Bhadrapada","class": "dhruva",     "lord": "saturn"},
    27: {"name": "Revati",           "class": "mridu",      "lord": "mercury"},
}

# Abhijit Muhurta — the midday auspicious window (~48 min centred on solar noon).
ABHIJIT_MUHURTA: dict = {
    "description":    "Abhijit Muhurta",
    "duration_mins":  48,
    "center":         "solar_noon",
    "quality":        "highly_auspicious",
    "notes":          "Abhijit is the 8th muhurta of the day (of 15); "
                      "equivalent to the Abhijit nakshatra (0°–6°40' Capricorn). "
                      "Generally auspicious for all works; supersedes most dosha.",
}


# ---------------------------------------------------------------------------
# G25 helper functions
# ---------------------------------------------------------------------------

_GANDANTA_WATER_SIGNS = {z["from_sign_index"] for z in GANDANTA_ZONES}   # {11, 3, 7}
_GANDANTA_FIRE_SIGNS  = {z["to_sign_index"]   for z in GANDANTA_ZONES}   # {0, 4, 8}


def is_gandanta(sign_index: int, degree: float) -> bool:
    """Return True if (sign_index, degree) falls within a Gandanta zone.

    Args:
        sign_index: 0=Aries … 11=Pisces
        degree:     0.0–29.999… within the sign

    Returns:
        True if the position is in the last 3°20' of a water sign OR
        the first 3°20' of the following fire sign.
    """
    if sign_index in _GANDANTA_WATER_SIGNS and degree >= 26.666:
        return True
    if sign_index in _GANDANTA_FIRE_SIGNS and degree <= 3.333:
        return True
    return False


def is_pushkara(sign_index: int, degree: float) -> bool:
    """Return True if (sign_index, degree) falls in a Pushkara navamsa.

    Pushkara navamsas are the 4th (10°–13°20') and 8th (23°20'–26°40')
    navamsas of every sign.
    """
    # 4th navamsa: 10.0 – 13.333
    if 10.0 <= degree <= 13.333:
        return True
    # 8th navamsa: 23.333 – 26.667
    if 23.333 <= degree <= 26.667:
        return True
    return False


# Build a fast lookup: (graha, sign_index) -> set of critical degrees
_MBHAGA_LOOKUP: dict[tuple[str, int], set[float]] = {}
for _graha, _entries in MRITYUBHAGA_DEGREES.items():
    for _si, _deg in _entries:
        _MBHAGA_LOOKUP.setdefault((_graha, _si), set()).add(float(_deg))


def is_mrityubhaga(graha: str, sign_index: int, degree: float,
                   orb: float = 1.0) -> bool:
    """Return True if the graha is within `orb` degrees of its mrityubhaga point.

    Args:
        graha:      one of sun/moon/mars/mercury/jupiter/venus/saturn (lowercase)
        sign_index: 0=Aries … 11=Pisces
        degree:     0.0–29.999… within the sign
        orb:        tolerance in degrees (default 1.0°)

    Returns:
        True if abs(degree - critical_degree) <= orb for any critical degree
        of this graha in this sign.
    """
    key = (graha.lower(), sign_index)
    critical_degrees = _MBHAGA_LOOKUP.get(key, set())
    return any(abs(degree - cd) <= orb for cd in critical_degrees)


# ---------------------------------------------------------------------------
# G26 helper functions
# ---------------------------------------------------------------------------

def get_tithi_quality(tithi: int) -> str:
    """Return quality string ('good', 'mixed', 'inauspicious') for tithi 1–30."""
    if tithi not in TITHI_QUALITY:
        raise ValueError(f"tithi must be 1–30, got {tithi}")
    return TITHI_QUALITY[tithi]["quality"]


def get_vara_quality(weekday: str) -> str:
    """Return quality string for a weekday (lowercase english name)."""
    key = weekday.lower()
    if key not in VARA_QUALITY:
        raise ValueError(f"Unknown weekday '{weekday}'. Use sunday…saturday.")
    return VARA_QUALITY[key]["quality"]


def get_nakshatra_muhurta_class(nakshatra: int) -> str:
    """Return the muhurta class (dhruva/chara/mridu/ugra/tikshna/sadharana)
    for nakshatra 1–27."""
    if nakshatra not in NAKSHATRA_MUHURTA_CLASS:
        raise ValueError(f"nakshatra must be 1–27, got {nakshatra}")
    return NAKSHATRA_MUHURTA_CLASS[nakshatra]["class"]
