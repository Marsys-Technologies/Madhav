"""
upagrahas.py — Upagraha (shadow body) positions + outer planet positions.

Upagrahas are computed via classical sphuta formulas from Sun's position
and sunrise-based timing (Gulika/Mandi). All positions are sidereal (Lahiri).
Outer planets (Uranus/Neptune/Pluto) computed directly via pyswisseph.
"""
from __future__ import annotations
from datetime import datetime, timedelta
import swisseph as swe
from .types import PlanetState
from .shastra_tables import GULIKA_INDEX, SIGN_NAMES, NAKSHATRA_NAMES


def _jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def _ayanamsha(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa_ut(jd)


def _sid_lon(trop_lon: float, ayan: float) -> float:
    return (trop_lon - ayan) % 360.0


def _sign(lon: float) -> tuple:
    idx = int(lon / 30) % 12
    return idx + 1, SIGN_NAMES[idx]


def _nak_pada(lon: float) -> tuple:
    nak_deg = 360.0 / 27.0
    nak_idx = int(lon / nak_deg) % 27
    pada = min(int((lon % nak_deg) / (nak_deg / 4)) + 1, 4)
    return nak_idx + 1, NAKSHATRA_NAMES[nak_idx], pada


def _make_planet(name: str, sid_lon: float) -> PlanetState:
    sid_lon = sid_lon % 360.0
    sign_id, sign_name = _sign(sid_lon)
    nak_id, nak_name, pada = _nak_pada(sid_lon)
    return PlanetState(
        name=name,
        longitude_sidereal=round(sid_lon, 4),
        sign_id=sign_id,
        sign_name=sign_name,
        nakshatra_id=nak_id,
        nakshatra_name=nak_name,
        nakshatra_pada=pada,
        retrograde=False,
        combust=False,
    )


def compute_upagrahas_from_sun_lon(sun_lon: float, vara_id: int) -> list:
    """
    Compute 7 upagrahas from Sun's sidereal longitude (pure formula, no JD).

    Classical sphuta formulas:
      Dhuma      = Sun + 133°20'
      Vyatipata  = 360° - Dhuma
      Parivesha  = Vyatipata + 180°
      Indrachapa = 360° - Parivesha
      Upaketu    = Indrachapa + 16°40'
      Mrityu     = Sun + 165°

    Args:
        sun_lon: Sun's sidereal longitude in degrees
        vara_id: 1..7 (weekday, 1=Sunday) — accepted for API symmetry

    Returns:
        list[PlanetState] of 6 upagrahas
    """
    dhuma      = (sun_lon + 133.333) % 360
    vyatipata  = (360.0 - dhuma) % 360
    parivesha  = (vyatipata + 180.0) % 360
    indrachapa = (360.0 - parivesha) % 360
    upaketu    = (indrachapa + 16.667) % 360
    mrityu     = (sun_lon + 165.0) % 360
    return [
        _make_planet("Dhuma",      dhuma),
        _make_planet("Vyatipata",  vyatipata),
        _make_planet("Parivesha",  parivesha),
        _make_planet("Indrachapa", indrachapa),
        _make_planet("Upaketu",    upaketu),
        _make_planet("Mrityu",     mrityu),
    ]


def compute_upagrahas(sunrise_utc: datetime, sunset_utc: datetime,
                      vara_id: int) -> list:
    """
    Compute all 8 upagrahas: Gulika + Mandi + 6 formula upagrahas.

    Gulika and Mandi are timed by dividing the day (sunrise→sunset) into 8
    equal parts. Each weekday assigns the Gulika slot via GULIKA_INDEX.
    Mandi occupies the slot immediately before Gulika (cyclically).

    The longitude for Gulika/Mandi is taken as the Sun's sidereal position
    at the midpoint of the respective slot + 90° (classical convention).

    Args:
        sunrise_utc: UTC sunrise datetime
        sunset_utc:  UTC sunset datetime
        vara_id:     1..7 (weekday of the day, 1=Sunday)

    Returns:
        list[PlanetState] of 8 upagrahas (Gulika, Mandi, + 6 formula bodies)
    """
    day_dur = (sunset_utc - sunrise_utc).total_seconds()
    part = day_dur / 8.0

    gulika_idx = GULIKA_INDEX[vara_id]  # 1-based slot index
    gulika_start = sunrise_utc + timedelta(seconds=part * (gulika_idx - 1))
    gulika_mid   = gulika_start + timedelta(seconds=part / 2)

    jd_g = _jd(gulika_mid)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun_res, _ = swe.calc_ut(jd_g, swe.SUN)
    ayan = _ayanamsha(jd_g)
    sun_sid = _sid_lon(sun_res[0], ayan)

    # Gulika: Sun position at Gulika midpoint + 90° (classical convention)
    gulika_lon = (sun_sid + 90.0) % 360

    # Mandi: slot just before Gulika (cyclically)
    mandi_idx = gulika_idx - 1 if gulika_idx > 1 else 8
    mandi_start = sunrise_utc + timedelta(seconds=part * (mandi_idx - 1))
    mandi_mid   = mandi_start + timedelta(seconds=part / 2)
    jd_m = _jd(mandi_mid)
    sun_m, _ = swe.calc_ut(jd_m, swe.SUN)
    ayan_m = _ayanamsha(jd_m)
    mandi_lon = (_sid_lon(sun_m[0], ayan_m) + 90.0) % 360

    formula_upagrahas = compute_upagrahas_from_sun_lon(sun_sid, vara_id)

    return [
        _make_planet("Gulika", gulika_lon),
        _make_planet("Mandi",  mandi_lon),
        *formula_upagrahas,
    ]


def compute_outer_planets(instant_utc: datetime) -> list:
    """
    Compute Uranus, Neptune, Pluto sidereal positions at the given UTC instant.

    Uses pyswisseph directly. Pluto is included if swe.PLUTO is available
    (swisseph >= 2.x). If Pluto calc raises an error, it is skipped gracefully.

    Args:
        instant_utc: UTC datetime for the computation

    Returns:
        list[PlanetState] of 2 or 3 planets (Uranus, Neptune, [Pluto])
    """
    jd = _jd(instant_utc)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayan = _ayanamsha(jd)
    results = []
    candidates = [("Uranus", swe.URANUS), ("Neptune", swe.NEPTUNE)]
    try:
        candidates.append(("Pluto", swe.PLUTO))
    except AttributeError:
        pass  # swe.PLUTO not defined in this build

    for name, body in candidates:
        try:
            res, _ = swe.calc_ut(jd, body)
            sid_lon = _sid_lon(res[0], ayan)
            sign_id, sign_name = _sign(sid_lon)
            nak_id, nak_name, pada = _nak_pada(sid_lon)
            results.append(PlanetState(
                name=name,
                longitude_sidereal=round(sid_lon, 4),
                sign_id=sign_id,
                sign_name=sign_name,
                nakshatra_id=nak_id,
                nakshatra_name=nak_name,
                nakshatra_pada=pada,
                retrograde=(res[3] < 0),
                combust=False,
            ))
        except Exception:
            pass  # skip bodies that fail (e.g. Pluto in older ephemeris builds)

    return results
