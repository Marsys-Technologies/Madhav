"""
jaimini_chara.py — Jaimini Chara Dasha engine for MARSYS-JIS.

Implements standard Jaimini Chara Dasha computation:
  - 12 rashis serve as dasha lords.
  - Period for each rashi determined by its sign lord's longitude within the sign.
  - Odd rashis (Aries=1, Gemini=3, Leo=5, Libra=7, Sagittarius=9, Aquarius=11):
      years = 30 - floor(lord's longitude in sign)
  - Even rashis (Taurus=2, Cancer=4, Virgo=6, Scorpio=8, Capricorn=10, Pisces=12):
      years = floor(lord's longitude in sign) + 1
  - Years capped at 12 per rashi.
  - Total cycle = 120 years.
  - Start rashi determined by Lagna (ascendant sign at birth).
  - Sub-periods (antar dasha) subdivide each rashi's period proportionally.

References: Jaimini Sutram, Upadesa Sutras §Chara Dasha computation.
Session: TR-P7-S2
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

# ── Constants ──────────────────────────────────────────────────────────────────

DAYS_PER_YEAR = 365.25

# 12 rashis in zodiac order (1-indexed).
RASHIS = [
    "Aries",       # 1  (odd)
    "Taurus",      # 2  (even)
    "Gemini",      # 3  (odd)
    "Cancer",      # 4  (even)
    "Leo",         # 5  (odd)
    "Virgo",       # 6  (even)
    "Libra",       # 7  (odd)
    "Scorpio",     # 8  (even)
    "Sagittarius", # 9  (odd)
    "Capricorn",   # 10 (even)
    "Aquarius",    # 11 (odd)
    "Pisces",      # 12 (even)
]

# 0-indexed: True = odd rashi, False = even rashi
RASHI_ODD = [i % 2 == 0 for i in range(12)]  # index 0 = Aries (odd), 1 = Taurus (even)...

# Sign lords for each rashi (Parasara rulership; Rahu/Ketu as co-lords of Scorpio/Aquarius
# are not used for primary Chara Dasha computation — use Mars for Scorpio, Saturn for Aquarius).
SIGN_LORDS = {
    "Aries":       "Mars",
    "Taurus":      "Venus",
    "Gemini":      "Mercury",
    "Cancer":      "Moon",
    "Leo":         "Sun",
    "Virgo":       "Mercury",
    "Libra":       "Venus",
    "Scorpio":     "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn":   "Saturn",
    "Aquarius":    "Saturn",
    "Pisces":      "Jupiter",
}

# Canonical planet longitudes for native Abhisek Mohanty (FORENSIC_ASTROLOGICAL_DATA_v8_0.md).
# Used as fallback when ephemeris is not available.
# All values are sidereal (Lahiri ayanamsha), degrees 0–360.
NATIVE_FALLBACK_LONGITUDES: Dict[str, float] = {
    "Sun":     322.61,   # Aquarius 22°37'
    "Moon":    326.73,   # Aquarius 26°44'  (Purva Bhadrapada)
    "Mars":    201.98,   # Scorpio 21°59'
    "Mercury": 305.05,   # Aquarius 5°3'
    "Jupiter": 233.28,   # Scorpio 23°17'
    "Venus":   343.52,   # Pisces 13°31'
    "Saturn":  199.28,   # Scorpio 19°17'
    "Rahu":    66.47,    # Gemini 6°28'
    "Ketu":    246.47,   # Sagittarius 6°28'
    "Lagna":   51.28,    # Taurus 21°17'  (ascendant)
}

# Native's ascendant sign index (0-based) — Taurus = index 1.
NATIVE_LAGNA_RASHI_INDEX = 1  # Taurus


# ── Core algorithm ─────────────────────────────────────────────────────────────

def _longitude_in_sign(planet_lon: float) -> float:
    """Return the planet's longitude within its sign (0–30 degrees)."""
    return planet_lon % 30.0


def _rashi_index_from_longitude(longitude: float) -> int:
    """Return 0-based rashi index (0=Aries, 11=Pisces) from ecliptic longitude."""
    return int(longitude / 30.0) % 12


def compute_chara_dasha_years(planet_longitudes: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    """
    Compute Chara Dasha period lengths for all 12 rashis.

    Args:
        planet_longitudes: dict of planet_name → sidereal longitude (0–360).
                           If None, uses NATIVE_FALLBACK_LONGITUDES.

    Returns:
        List of 12 dicts: [{rashi, years, sign_lord, lord_longitude_in_sign}, ...]
        in zodiac order (Aries through Pisces). Total years must sum to 120.
    """
    lons = planet_longitudes if planet_longitudes is not None else NATIVE_FALLBACK_LONGITUDES

    periods: List[Dict[str, Any]] = []
    total_years = 0

    for idx, rashi in enumerate(RASHIS):
        lord = SIGN_LORDS[rashi]
        lord_lon = lons.get(lord, 0.0)
        lon_in_sign = _longitude_in_sign(lord_lon)
        is_odd = RASHI_ODD[idx]

        if is_odd:
            years = 30 - int(math.floor(lon_in_sign))
        else:
            years = int(math.floor(lon_in_sign)) + 1

        # Cap at 12 (rashi cannot give more than 12 years in Chara Dasha).
        years = min(years, 12)

        # Enforce minimum of 1 year to avoid degenerate periods.
        years = max(years, 1)

        total_years += years
        periods.append({
            "rashi": rashi,
            "rashi_index": idx,
            "years": years,
            "sign_lord": lord,
            "lord_longitude_in_sign": round(lon_in_sign, 4),
            "is_odd_rashi": is_odd,
        })

    # Normalise: if sum != 120, distribute residual proportionally to largest periods.
    # (In practice, native data will sum close to 120; this handles edge cases.)
    if total_years != 120:
        diff = 120 - total_years
        # Add/subtract from the rashi with the most slack.
        if diff > 0:
            for _ in range(diff):
                candidates = [p for p in periods if p["years"] < 12]
                if not candidates:
                    break
                candidates.sort(key=lambda p: p["years"])
                candidates[0]["years"] += 1
        elif diff < 0:
            for _ in range(-diff):
                candidates = [p for p in periods if p["years"] > 1]
                if not candidates:
                    break
                candidates.sort(key=lambda p: p["years"], reverse=True)
                candidates[0]["years"] -= 1

    return periods


def compute_lagna_rashi_index(lagna_longitude: Optional[float] = None) -> int:
    """
    Return the 0-based rashi index of the native's ascendant.
    Defaults to NATIVE_LAGNA_RASHI_INDEX if lagna_longitude is None.
    """
    if lagna_longitude is None:
        return NATIVE_LAGNA_RASHI_INDEX
    return _rashi_index_from_longitude(lagna_longitude)


def build_full_chara_dasha(
    birth_date: date,
    planet_longitudes: Optional[Dict[str, float]] = None,
    lagna_longitude: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Build the complete Chara Dasha timeline anchored to birth_date.

    Args:
        birth_date: The native's birth date.
        planet_longitudes: dict of sidereal longitudes. None → native fallback.
        lagna_longitude: sidereal longitude of ascendant. None → native fallback.

    Returns:
        List of 12 dicts with rashi, years, start_date, end_date, and
        sub_periods (list of 12 antar dasha entries).
    """
    rashi_periods = compute_chara_dasha_years(planet_longitudes)
    lagna_idx = compute_lagna_rashi_index(lagna_longitude)

    # Reorder: start from lagna rashi, proceed in zodiac order.
    ordered = rashi_periods[lagna_idx:] + rashi_periods[:lagna_idx]

    result: List[Dict[str, Any]] = []
    current_start = birth_date

    for period in ordered:
        years = period["years"]
        days = int(round(years * DAYS_PER_YEAR))
        current_end = current_start + timedelta(days=days - 1)

        # Build antar dasha (sub-periods): 12 rashis subdivide the main period
        # in the same forward order starting from the main dasha rashi.
        antar_periods = _build_antar_dasha(current_start, current_end, years, period["rashi_index"], rashi_periods)

        result.append({
            "rashi": period["rashi"],
            "sign_lord": period["sign_lord"],
            "years": years,
            "start_date": current_start.isoformat(),
            "end_date": current_end.isoformat(),
            "is_odd_rashi": period["is_odd_rashi"],
            "antar_dasha": antar_periods,
        })

        current_start = current_end + timedelta(days=1)

    return result


def _build_antar_dasha(
    md_start: date,
    md_end: date,
    md_years: float,
    md_rashi_index: int,
    rashi_periods: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build 12 antar dasha periods within a given maha dasha period.

    Each antar dasha (AD) is proportional: AD_days = (AD_years / 120) * MD_days.
    The 12 rashis cycle starting from the MD rashi in zodiac forward order.
    """
    md_total_days = (md_end - md_start).days + 1
    # Reorder rashi_periods starting from MD rashi
    ordered = rashi_periods[md_rashi_index:] + rashi_periods[:md_rashi_index]

    result: List[Dict[str, Any]] = []
    current_start = md_start

    for i, antar in enumerate(ordered):
        ad_years = antar["years"]
        # Proportional allocation
        if i < len(ordered) - 1:
            ad_days = int(round((ad_years / 120.0) * md_total_days))
        else:
            # Last AD absorbs any rounding residual
            ad_days = (md_end - current_start).days + 1

        ad_end = current_start + timedelta(days=max(ad_days - 1, 0))
        # Clamp to MD boundary
        if ad_end > md_end:
            ad_end = md_end

        result.append({
            "rashi": antar["rashi"],
            "sign_lord": antar["sign_lord"],
            "years_proportion": round(ad_years / 120.0, 4),
            "start_date": current_start.isoformat(),
            "end_date": ad_end.isoformat(),
        })

        current_start = ad_end + timedelta(days=1)
        if current_start > md_end:
            break

    return result


def get_active_dasha(
    full_periods: List[Dict[str, Any]],
    query_date: date,
) -> Dict[str, Any]:
    """
    Return the active maha dasha and antar dasha for a given query date.

    Args:
        full_periods: output of build_full_chara_dasha()
        query_date: the date to look up.

    Returns:
        dict with keys: active_rashi_dasha, active_antar_dasha.
        If query_date is outside the 120-year cycle, returns the last/first period.
    """
    active_md = None
    for period in full_periods:
        start = date.fromisoformat(period["start_date"])
        end = date.fromisoformat(period["end_date"])
        if start <= query_date <= end:
            active_md = period
            break

    # Fallback: before birth → first; after cycle → last
    if active_md is None:
        if full_periods:
            active_md = full_periods[-1]
        else:
            return {"active_rashi_dasha": None, "active_antar_dasha": None}

    # Find active antar dasha
    active_ad = None
    for ad in active_md.get("antar_dasha", []):
        ad_start = date.fromisoformat(ad["start_date"])
        ad_end = date.fromisoformat(ad["end_date"])
        if ad_start <= query_date <= ad_end:
            active_ad = ad
            break

    if active_ad is None and active_md.get("antar_dasha"):
        active_ad = active_md["antar_dasha"][-1]

    return {
        "active_rashi_dasha": {
            "rashi": active_md["rashi"],
            "sign_lord": active_md["sign_lord"],
            "start_date": active_md["start_date"],
            "end_date": active_md["end_date"],
        },
        "active_antar_dasha": {
            "rashi": active_ad["rashi"] if active_ad else None,
            "sign_lord": active_ad["sign_lord"] if active_ad else None,
            "start_date": active_ad["start_date"] if active_ad else None,
            "end_date": active_ad["end_date"] if active_ad else None,
        } if active_ad else None,
    }
