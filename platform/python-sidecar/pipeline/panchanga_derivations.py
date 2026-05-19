"""
panchanga_derivations — Vedic 5-limb time-quality computation for any date.

All derivations are pure functions of (sun_longitude_at_sunrise, moon_longitude_at_sunrise,
sunrise_datetime). Constants are canonical Vedic panchanga.

Imports SIGNS + SIGN_TO_IDX from pipeline.ephemeris_derivations to maintain
single-source-of-truth for sign-name canonicalization (per §4.B executor note).
"""
from __future__ import annotations
from datetime import datetime
from .ephemeris_derivations import SIGNS, SIGN_TO_IDX  # imported, not re-declared

# ── Nakshatra names (27) ──────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# ── Tithi names (1..30) ───────────────────────────────────────────────────────
TITHI_NAMES = [
    # 1..15 Shukla paksha (waxing)
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Shukla Purnima",
    # 16..30 Krishna paksha (waning)
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Krishna Amavasya",
]

# ── Vara (sunrise-anchored day-of-week) ───────────────────────────────────────
# Index 0..6 keyed to Sunday=0 (Vedic convention).
# Python weekday(): Mon=0, Sun=6. Vedic: Sun=0..Sat=6. Map: (weekday + 1) % 7.
VARA_NAMES = ["Ravivara", "Somavara", "Mangalavara", "Budhavara", "Guruvara", "Shukravara", "Shanivara"]
VARA_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# ── Yoga names (27) ───────────────────────────────────────────────────────────
YOGAS = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

# ── Karana names ──────────────────────────────────────────────────────────────
MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
# Fixed karanas keyed by their exact position in the 60-slot lunar month.
FIXED_KARANA_POSITIONS = {
    0: "Kintughna",   # First half of Shukla Pratipada
    57: "Shakuni",    # Second half of Krishna Chaturdashi
    58: "Catushpada", # First half of Krishna Amavasya
    59: "Naga",       # Second half of Krishna Amavasya
}

NAK_SPAN = 360.0 / 27           # 13.333...° per nakshatra
PADA_SPAN = NAK_SPAN / 4        # 3.333...° per pada
TITHI_ARC_DEG = 12.0            # Each tithi spans 12° of (Moon - Sun) elongation
YOGA_ARC_DEG = NAK_SPAN         # Each yoga spans 13.333° (= 1 nakshatra span)


def compute_tithi(sun_lon: float, moon_lon: float) -> tuple[int, str, str, float]:
    """
    Compute tithi from sidereal Lahiri Sun + Moon longitudes.
    Returns (tithi_index_1_to_30, tithi_name, paksha, tithi_fraction).
    tithi_fraction ∈ [0, 30) — useful for karana boundary computation.
    """
    diff = (moon_lon - sun_lon) % 360.0
    tithi_fraction = diff / TITHI_ARC_DEG          # [0, 30)
    tithi_index = int(tithi_fraction) + 1           # [1, 30]
    tithi_index = max(1, min(30, tithi_index))
    name = TITHI_NAMES[tithi_index - 1]
    paksha = "shukla" if tithi_index <= 15 else "krishna"
    return tithi_index, name, paksha, round(tithi_fraction, 5)


def compute_vara(sunrise_dt: datetime) -> tuple[int, str, str]:
    """
    Returns (vara_index_0_to_6, vara_name, vara_lord) for the given sunrise datetime.
    Weekday of sunrise_dt determines the vara. Pass sunrise_dt in IST (not UTC).
    """
    vara_index = (sunrise_dt.weekday() + 1) % 7
    return vara_index, VARA_NAMES[vara_index], VARA_LORDS[vara_index]


def compute_moon_nakshatra(moon_lon: float) -> tuple[str, int, int]:
    """
    Returns (nakshatra_name, nakshatra_index_0_to_26, pada_1_to_4) for Moon longitude.
    """
    nak_idx = int((moon_lon % 360.0) / NAK_SPAN)
    nak_idx = max(0, min(26, nak_idx))
    pada = int((moon_lon % NAK_SPAN) / PADA_SPAN) + 1
    return NAKSHATRAS[nak_idx], nak_idx, pada


def compute_yoga(sun_lon: float, moon_lon: float) -> tuple[int, str]:
    """
    Returns (yoga_index_1_to_27, yoga_name).
    Yoga = floor((sun_lon + moon_lon) % 360 / 13.333°) + 1.
    """
    combined = (sun_lon + moon_lon) % 360.0
    yoga_idx = int(combined / YOGA_ARC_DEG)         # [0, 26]
    yoga_idx = max(0, min(26, yoga_idx))
    return yoga_idx + 1, YOGAS[yoga_idx]


def compute_karana(tithi_fraction: float) -> tuple[int, str]:
    """
    Returns (karana_position_in_month_0_to_59, karana_name).
    Each tithi has 2 karanas (first half + second half) → 60 positions per lunar month.
    Positions 0, 57, 58, 59 are fixed; all others cycle through the 7 movable karanas.
    """
    position = int(tithi_fraction * 2)              # [0, 59]
    position = max(0, min(59, position))
    if position in FIXED_KARANA_POSITIONS:
        return position, FIXED_KARANA_POSITIONS[position]
    # Movable karanas: position 1 = Bava (first movable), cycling every 7.
    movable_index = (position - 1) % 7
    return position, MOVABLE_KARANAS[movable_index]
