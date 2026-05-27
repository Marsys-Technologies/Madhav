"""
panchanga.py — Birth-moment panchanga.

Scaffold derives the five angas from the Sun + Moon longitudes directly
rather than reaching into the existing `panchang_engine/` module — keeping
natal_engine self-contained for now. Unit 1.2 may wrap panchang_engine.angas
once we confirm the conventions match JH exactly.
"""

from __future__ import annotations

from .positions import NAKSHATRA_NAMES
from .schema import GrahaState

_TITHI_NAMES_SHUKLA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima",
]
_TITHI_NAMES_KRISHNA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Amavasya",
]

_VARA_NAMES = [
    # ISO weekday: 0=Monday..6=Sunday; convert to Vedic week (Sunday=Ravivara index 0)
    "Somavara", "Mangalavara", "Budhavara", "Guruvara",
    "Shukravara", "Shanivara", "Ravivara",
]

_YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

_KARANA_FIXED = ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]
_KARANA_CYCLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]


def _tithi(sun_lon: float, moon_lon: float) -> str:
    diff = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(diff // 12.0)  # 0..29
    if tithi_idx < 15:
        return f"Shukla {_TITHI_NAMES_SHUKLA[tithi_idx]}"
    return f"Krishna {_TITHI_NAMES_KRISHNA[tithi_idx - 15]}"


def _vara_from_weekday(weekday_iso: int) -> str:
    # Python weekday(): Monday=0..Sunday=6; our table starts Monday.
    return _VARA_NAMES[weekday_iso % 7]


def _yoga(sun_lon: float, moon_lon: float) -> str:
    s = (sun_lon + moon_lon) % 360.0
    yoga_idx = int(s // (360.0 / 27.0)) % 27
    return _YOGA_NAMES[yoga_idx]


def _karana(sun_lon: float, moon_lon: float) -> str:
    diff = (moon_lon - sun_lon) % 360.0
    half_tithi_idx = int(diff // 6.0)  # 0..59
    if half_tithi_idx == 0:
        return _KARANA_FIXED[0]
    if half_tithi_idx >= 57:
        return _KARANA_FIXED[(half_tithi_idx - 57) + 1]
    return _KARANA_CYCLE[(half_tithi_idx - 1) % 7]


def compute_panchanga(
    sun: GrahaState, moon: GrahaState, weekday_iso: int
) -> dict[str, str]:
    return {
        "tithi": _tithi(sun.longitude_deg, moon.longitude_deg),
        "vara": _vara_from_weekday(weekday_iso),
        "nakshatra": NAKSHATRA_NAMES[moon.nakshatra_id - 1],
        "yoga": _yoga(sun.longitude_deg, moon.longitude_deg),
        "karana": _karana(sun.longitude_deg, moon.longitude_deg),
    }
