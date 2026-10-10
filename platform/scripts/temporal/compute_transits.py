"""
Transit engine v1 — date-indexed sidereal positions of all 9 planets plus
Sade Sati state and eclipse-point proximity.

M3-W2-B2 deliverable. Same Lahiri sidereal + Moshier ephemeris discipline as
compute_vimshottari.py / compute_yogini.py.

Per CLAUDE.md §I B.10 (no fabricated computation): pyswisseph is mandatory.

Public API:
    get_transit_states(birth_dt, query_date, ayanamsha='lahiri') -> dict

CLI:
    python3 platform/scripts/temporal/compute_transits.py \\
        --birth <ISO8601 birth datetime of the chart, e.g. 2000-01-01T06:00:00+05:30> \\
        --date 2026-05-01 \\
        --output 05_TEMPORAL_ENGINES/transit/sample_2026_05_01.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import swisseph as swe
except ImportError:
    print(
        "[EXTERNAL_COMPUTATION_REQUIRED]: pyswisseph not installed. "
        "Install with `pip install pyswisseph` and re-run.",
        file=sys.stderr,
    )
    sys.exit(2)


SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "PurvaPhalguni", "UttaraPhalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "PurvaAshadha", "UttaraAshadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "PurvaBhadrapada", "UttaraBhadrapada", "Revati",
)
NAK_SIZE_DEG = 360.0 / 27.0
SIGN_SIZE_DEG = 30.0

# pyswisseph planet codes. Rahu uses TRUE_NODE; Ketu derived as Rahu + 180.
PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.TRUE_NODE,   # Ketu computed as +180 from this
}


def parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _sidereal_jd_ut(d: date) -> float:
    """Julian day for 00:00 UTC on the given date."""
    return swe.julday(d.year, d.month, d.day, 0.0)


def _set_lahiri():
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def _planet_lon_speed(jd_ut: float, planet_code: int, *, moshier: bool = True) -> tuple[float, float]:
    flags = swe.FLG_SIDEREAL | (swe.FLG_MOSEPH if moshier else swe.FLG_SWIEPH) | swe.FLG_SPEED
    pos, _ = swe.calc_ut(jd_ut, planet_code, flags)
    return pos[0] % 360.0, pos[3]   # longitude (deg), speed (deg/day)


def _decompose(lon_deg: float) -> dict:
    sign_idx = int(lon_deg // SIGN_SIZE_DEG)
    nak_idx = int(lon_deg // NAK_SIZE_DEG)
    return {
        "sidereal_lon_deg": lon_deg,
        "sign": SIGNS[sign_idx],
        "sign_idx_0_based": sign_idx,
        "degrees_in_sign": lon_deg - sign_idx * SIGN_SIZE_DEG,
        "nakshatra": NAKSHATRAS[nak_idx],
        "nakshatra_idx_0_based": nak_idx,
        "degrees_in_nakshatra": lon_deg - nak_idx * NAK_SIZE_DEG,
    }


def _natal_moon_sign(birth_dt: datetime) -> str:
    """Compute the natal Moon sign from birth_dt (the chart's own birth datetime)."""
    _set_lahiri()
    if birth_dt.tzinfo is None:
        raise ValueError("birth_dt must be timezone-aware")
    utc_dt = birth_dt.astimezone(timezone.utc)
    jd_ut = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )
    lon, _ = _planet_lon_speed(jd_ut, swe.MOON)
    return SIGNS[int(lon // SIGN_SIZE_DEG)]


def _sade_sati_state(saturn_sign: str, natal_moon_sign: str) -> dict:
    """
    Sade Sati: Saturn in 12th, 1st, or 2nd from natal Moon.
    Worked example (illustrative, not a chart value): for natal Moon = Aquarius
    (idx 10 0-based): 12th = Capricorn (9), 1st = Aquarius (10), 2nd = Pisces (11).
    """
    moon_idx = SIGNS.index(natal_moon_sign)
    sat_idx = SIGNS.index(saturn_sign)
    rel = (sat_idx - moon_idx) % 12  # 0=natal moon sign, 11=12th, 1=2nd
    if rel == 11:
        return {"active": True, "phase": "first_dhaiya_12th", "saturn_sign": saturn_sign}
    if rel == 0:
        return {"active": True, "phase": "second_dhaiya_1st_natal_moon", "saturn_sign": saturn_sign}
    if rel == 1:
        return {"active": True, "phase": "third_dhaiya_2nd", "saturn_sign": saturn_sign}
    return {"active": False, "phase": None, "saturn_sign": saturn_sign}


def _eclipse_proximity(planet_states: dict, threshold_deg: float = 15.0) -> list[dict]:
    """For Sun and Moon: distance to Rahu/Ketu axis. <= threshold => near eclipse point."""
    rahu_lon = planet_states["Rahu"]["sidereal_lon_deg"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    out = []
    for pname in ("Sun", "Moon"):
        plon = planet_states[pname]["sidereal_lon_deg"]
        d_rahu = min((plon - rahu_lon) % 360.0, (rahu_lon - plon) % 360.0)
        d_ketu = min((plon - ketu_lon) % 360.0, (ketu_lon - plon) % 360.0)
        nearest_node = "Rahu" if d_rahu < d_ketu else "Ketu"
        nearest_dist = min(d_rahu, d_ketu)
        out.append({
            "planet": pname,
            "nearest_node": nearest_node,
            "distance_deg": nearest_dist,
            "near_eclipse_point": nearest_dist <= threshold_deg,
        })
    return out


def get_transit_states(
    birth_dt: datetime,
    query_date: date,
    ayanamsha: str = "lahiri",
    *,
    natal_moon_sign: str | None = None,
) -> dict:
    """
    Compute sidereal transit positions for the 9 planets on query_date.

    Returns:
        {
          "query_date": "YYYY-MM-DD",
          "ayanamsha": "lahiri",
          "computed_by": "pyswisseph",
          "natal_moon_sign": "<sign of the natal Moon, or null when unavailable>",
          "planets": { "Sun": {...}, "Moon": {...}, ..., "Rahu": {...}, "Ketu": {...} },
          "sade_sati": { "active": bool, "phase": str|None, "saturn_sign": str },
          "eclipse_proximity": [ {"planet":..., "nearest_node":..., ...}, ... ],
        }
    """
    if ayanamsha != "lahiri":
        raise NotImplementedError(f"Only 'lahiri' implemented; got {ayanamsha!r}")

    _set_lahiri()
    jd = _sidereal_jd_ut(query_date)

    planet_states: dict[str, dict] = {}
    for name, code in PLANETS.items():
        lon, speed = _planet_lon_speed(jd, code)
        d = _decompose(lon)
        d["speed_deg_per_day"] = speed
        d["is_retrograde"] = speed < 0 and name not in ("Sun", "Moon", "Rahu", "Ketu")
        planet_states[name] = d

    # Ketu = Rahu + 180.
    rahu_lon = planet_states["Rahu"]["sidereal_lon_deg"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_d = _decompose(ketu_lon)
    # Nodes are always retrograde mean-direction; mark accordingly. True nodes
    # do oscillate, so leave is_retrograde=False and surface speed instead.
    ketu_d["speed_deg_per_day"] = -planet_states["Rahu"]["speed_deg_per_day"]
    ketu_d["is_retrograde"] = False
    planet_states["Ketu"] = ketu_d

    if natal_moon_sign is None:
        try:
            natal_moon_sign = _natal_moon_sign(birth_dt)
        except Exception:
            # No chart-specific default is ever substituted (CLAUDE.md B.10 / N.7.6): when the
            # natal Moon sign cannot be computed from birth_dt, Sade Sati is reported as null.
            natal_moon_sign = None

    saturn_sign = planet_states["Saturn"]["sign"]
    if natal_moon_sign is None:
        sade = {
            "active": None,
            "phase": None,
            "saturn_sign": saturn_sign,
            "reason": "natal_moon_sign_unavailable",
        }
    else:
        sade = _sade_sati_state(saturn_sign, natal_moon_sign)
    eclipse_prox = _eclipse_proximity(planet_states)

    return {
        "query_date": query_date.isoformat(),
        "ayanamsha": ayanamsha,
        "computed_by": "pyswisseph",
        "ephe_mode": "moshier",
        "natal_moon_sign": natal_moon_sign,
        "planets": planet_states,
        "sade_sati": sade,
        "eclipse_proximity": eclipse_prox,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--birth", required=True,
        help="ISO8601 birth datetime of the chart under test (timezone-aware), taken from "
             "its `charts` row. REQUIRED: no birth datetime is embedded in this script.",
    )
    parser.add_argument(
        "--date", default=date.today().isoformat(),
        help="Query date YYYY-MM-DD (default: today).",
    )
    parser.add_argument(
        "--output", default=None,
        help="Optional output path; default: print to stdout.",
    )
    parser.add_argument("--ayanamsha", default="lahiri")
    args = parser.parse_args()

    birth_dt = parse_iso8601(args.birth)
    query_date = date.fromisoformat(args.date)

    state = get_transit_states(birth_dt, query_date, ayanamsha=args.ayanamsha)

    payload = json.dumps(state, indent=2, default=str)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload)
        print(f"Wrote transit state for {args.date} to {out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
