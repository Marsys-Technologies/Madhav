"""
lagna.py — Lagna (Ascendant) + 12 house cusps + MC computation.

P0 topic — most time-sensitive; present only for PanchangaInstant (not Day).
Uses swe.houses_ex() with Placidus house system. Sidereal (Lahiri ayanamsha).
"""
from __future__ import annotations
from datetime import datetime, timedelta
import swisseph as swe
from .types import LagnaState


def _datetime_to_jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def _get_ayanamsha(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa_ut(jd)


def _sidereal_lon(tropical_lon: float, ayanamsha: float) -> float:
    return (tropical_lon - ayanamsha) % 360.0


def _sign_from_lon(lon: float) -> tuple:
    from .shastra_tables import SIGN_NAMES
    sign_idx = int(lon / 30) % 12
    return sign_idx + 1, SIGN_NAMES[sign_idx]


def _nak_pada_from_lon(lon: float) -> tuple:
    from .shastra_tables import NAKSHATRA_NAMES
    nak_deg = 360.0 / 27.0
    pada_deg = nak_deg / 4.0
    nak_idx = int(lon / nak_deg) % 27
    pada = min(int((lon % nak_deg) / pada_deg) + 1, 4)
    return nak_idx + 1, NAKSHATRA_NAMES[nak_idx], pada


def compute_lagna(instant_local: datetime, lat: float, lon: float,
                  tz_offset_minutes: int,
                  house_system: str = "P") -> LagnaState:
    """
    Compute Lagna (Ascendant), 12 sidereal house cusps, and MC at exact instant.

    Args:
        instant_local:      naive local datetime
        lat, lon:           decimal degrees (positive N/E)
        tz_offset_minutes:  UTC offset in minutes (e.g. 330 for IST +05:30)
        house_system:       swisseph house system char (default "P" = Placidus)

    Returns: LagnaState with sidereal ascendant + cusps + MC.
    """
    instant_utc = instant_local - timedelta(minutes=tz_offset_minutes)
    jd = _datetime_to_jd(instant_utc)

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayan = swe.get_ayanamsa_ut(jd)

    # swe.houses_ex returns (cusps_12, ascmc_8)
    # In this swisseph binding: cusps[0..11] = H1..H12 tropical (0-based, 12 elements)
    # ascmc[0] = ASC tropical; ascmc[1] = MC tropical
    cusps_trop, ascmc_trop = swe.houses_ex(jd, lat, lon, house_system.encode())

    asc_sid = _sidereal_lon(ascmc_trop[0], ayan)
    mc_sid  = _sidereal_lon(ascmc_trop[1], ayan)
    cusps_sid = [_sidereal_lon(cusps_trop[i], ayan) for i in range(0, 12)]

    asc_sign_id, asc_sign_name = _sign_from_lon(asc_sid)
    asc_nak_id, asc_nak_name, asc_pada = _nak_pada_from_lon(asc_sid)
    mc_sign_id, mc_sign_name = _sign_from_lon(mc_sid)

    return LagnaState(
        ascendant_deg=round(asc_sid, 4),
        ascendant_sign_id=asc_sign_id,
        ascendant_sign_name=asc_sign_name,
        ascendant_nak_id=asc_nak_id,
        ascendant_nak_name=asc_nak_name,
        ascendant_pada=asc_pada,
        mc_deg=round(mc_sid, 4),
        mc_sign_id=mc_sign_id,
        mc_sign_name=mc_sign_name,
        house_cusps=cusps_sid,
        house_system=house_system,
    )
