"""
transits.py — current transit (gochara) positions.

Delegates to the canonical ka_graha_sancara service engine.
jd_ut is converted to a datetime via swisseph, then get_ephemeris() is called
with PATH-B (live swisseph, no db_conn) since the caller supplies a Julian Day
rather than a calendar date.

Public API (unchanged signature):
    compute_transits(jd_ut, ayanamsha_id='lahiri', *, lat=0., lon=0., tz=0.)
        -> dict[graha_name -> GrahaState-like dict]

The returned dict mirrors the GrahaState dataclass fields:
    sidereal_lon_deg, sign, sign_idx, nakshatra, nakshatra_idx,
    degrees_in_sign, degrees_in_nakshatra, speed_dps, is_retrograde, source
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Empty sentinel — returned on error so callers get a consistent type
_EMPTY_RESULT: dict[str, Any] = {}


def _jd_to_datetime(jd_ut: float) -> datetime:
    """Convert Julian Day (UT) to a timezone-aware UTC datetime."""
    try:
        import swisseph as swe
        year, month, day, hour_frac = swe.jdut1_to_utc(jd_ut, 1)  # gregflag=1
        hour = int(hour_frac)
        minute_frac = (hour_frac - hour) * 60
        minute = int(minute_frac)
        second = int((minute_frac - minute) * 60)
        return datetime(int(year), int(month), int(day), hour, minute, second,
                        tzinfo=timezone.utc)
    except Exception:
        # Fallback: rough Julian Day → Gregorian conversion
        # JD 2440588 = 1970-01-01 00:00 UTC
        unix_seconds = (jd_ut - 2440587.5) * 86400.0
        return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


def compute_transits(
    jd_ut: float,
    ayanamsha_id: str = "lahiri",
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """
    Compute transit (gochara) positions for all 9 grahas at Julian Day jd_ut.

    Parameters
    ----------
    jd_ut : float
        Julian Day Number (Universal Time).
    ayanamsha_id : str
        Ayanamsha; default 'lahiri'.
    lat, lon, tz : float
        Observer coordinates (unused by planetary longitude calculation;
        retained for API compatibility).

    Returns
    -------
    dict mapping graha name -> dict of position data (GrahaState fields).
    Returns an empty dict on error (logged).
    """
    try:
        from services.ka_graha_sancara.engine import get_ephemeris
    except ImportError as imp_err:
        logger.error("ka_graha_sancara service not available: %s", imp_err)
        return _EMPTY_RESULT

    dt = _jd_to_datetime(jd_ut)

    try:
        result = get_ephemeris(
            dt=dt,
            ayanamsha=ayanamsha_id,
            db_conn=None,       # no DB available from this call path; use PATH-B
            force_live=True,    # jd_ut callers want precise live computation
        )
    except Exception as exc:
        logger.error("compute_transits failed for jd_ut=%s: %s", jd_ut, exc)
        return _EMPTY_RESULT

    # Return dict of dicts (serialisable) rather than dataclasses
    out: dict[str, Any] = {}
    for name, gs in result.grahas.items():
        out[name] = {
            "sidereal_lon_deg": gs.sidereal_lon_deg,
            "sign": gs.sign,
            "sign_idx": gs.sign_idx,
            "nakshatra": gs.nakshatra,
            "nakshatra_idx": gs.nakshatra_idx,
            "degrees_in_sign": gs.degrees_in_sign,
            "degrees_in_nakshatra": gs.degrees_in_nakshatra,
            "speed_dps": gs.speed_dps,
            "is_retrograde": gs.is_retrograde,
            "source": gs.source,
        }
    return out
