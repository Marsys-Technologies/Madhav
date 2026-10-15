"""
Varshaphala (Tajika) annual chart computation engine.

M3-W3-C2 deliverable. For each year of the native's life, computes the moment
the Sun returns to its exact natal sidereal longitude (the Solar Return moment
under Tajika reckoning) and casts the chart at that instant from the native's
birth location.

Per CLAUDE.md §I B.10: pyswisseph is required. The engine halts with
[EXTERNAL_COMPUTATION_REQUIRED] if pyswisseph is absent.

Per PROJECT_ARCHITECTURE §B.1: outputs are L1.5 substrate (computed from L1
chart inputs), not L2.5 interpretation.

Run (chart id, birth datetime and birth coordinates are all required):
    python3 platform/scripts/temporal/compute_varshaphala.py \\
        --chart-id <chart-uuid> \\
        --birth <ISO8601-birth-datetime-with-offset> \\
        --birth-lat <lat> --birth-lon <lon> \\
        [--year-start <birth year>] [--year-end <birth year + 77>] \\
        --output 05_TEMPORAL_ENGINES/varshaphala/VARSHAPHALA_RAW_v1_0.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import swisseph as swe
except ImportError:
    print(
        "[EXTERNAL_COMPUTATION_REQUIRED]: pyswisseph not installed. "
        "Install with `pip install pyswisseph` and re-run.",
        file=sys.stderr,
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

PLANETS_ORDER = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
SWE_PLANET_CODE = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class VarshaphalaRow:
    chart_id: str
    year: int
    solar_return_utc: str            # ISO8601 UTC
    ascendant_sidereal_lon: float
    ascendant_sign: str
    planets: dict[str, dict[str, Any]]
    computed_by: str = "pyswisseph"
    ayanamsha: str = "lahiri"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def setup_swe(*, ayanamsha: str, ephe_path: str | None) -> tuple[int, str]:
    if ayanamsha != "lahiri":
        raise NotImplementedError(f"Only 'lahiri' ayanamsha implemented; got {ayanamsha!r}")
    if ephe_path:
        swe.set_ephe_path(ephe_path)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        ephe_mode = "swisseph_files"
    else:
        flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
        ephe_mode = "moshier"
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return flags, ephe_mode


def jd_for_utc(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    utc = dt.astimezone(timezone.utc)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
    )


def utc_for_jd(jd: float) -> datetime:
    """Inverse of jd_for_utc: convert Julian Day to UTC datetime."""
    y, m, d, frac = swe.revjul(jd)
    h_total = frac
    h = int(h_total)
    m_total = (h_total - h) * 60.0
    mi = int(m_total)
    s_total = (m_total - mi) * 60.0
    sec = int(round(s_total))
    if sec == 60:
        sec = 0
        mi += 1
    if mi == 60:
        mi = 0
        h += 1
    return datetime(y, m, d, h, mi, sec, tzinfo=timezone.utc)


def compute_planet_sidereal_lon(jd_ut: float, planet: str, flags: int) -> float:
    if planet == "Ketu":
        rahu_pos, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)
        return (rahu_pos[0] + 180.0) % 360.0
    pos, _ = swe.calc_ut(jd_ut, SWE_PLANET_CODE[planet], flags)
    return pos[0] % 360.0


def sign_for(lon: float) -> str:
    return ZODIAC_SIGNS[int(lon // 30.0) % 12]


def nakshatra_for(lon: float) -> str:
    return NAKSHATRAS[int(lon // NAK_SIZE_DEG) % 27]


def signed_lon_delta(a: float, b: float) -> float:
    """Return (a - b) wrapped into [-180, 180)."""
    d = (a - b + 540.0) % 360.0 - 180.0
    return d


# ---------------------------------------------------------------------------
# Solar Return search
# ---------------------------------------------------------------------------

def _coarse_bracket_for_year(
    year: int, natal_sun_lon: float, flags: int,
) -> tuple[float, float]:
    """
    Find a 1-day bracket in [year-Jan-1 UTC, (year+1)-Jan-1 UTC] where the
    signed Sun-longitude delta crosses from negative to positive.

    Returns (jd_low, jd_high) such that f(jd_low) <= 0 < f(jd_high), where
    f(jd) = signed_lon_delta(sun_lon(jd), natal_sun_lon).
    """
    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year + 1, 1, 1, 0.0)
    step = 1.0  # 1-day coarse step
    jd_prev = jd_start
    f_prev = signed_lon_delta(
        compute_planet_sidereal_lon(jd_prev, "Sun", flags), natal_sun_lon,
    )
    jd_curr = jd_start + step
    while jd_curr <= jd_end + 1e-9:
        f_curr = signed_lon_delta(
            compute_planet_sidereal_lon(jd_curr, "Sun", flags), natal_sun_lon,
        )
        # Looking for: f_prev < 0 and f_curr >= 0 — but careful at wrap.
        # The Sun increases ~1 deg/day. A negative-to-positive crossing within
        # 1 day means we found the return bracket.
        if f_prev <= 0.0 < f_curr and (f_curr - f_prev) < 5.0:
            return jd_prev, jd_curr
        jd_prev = jd_curr
        f_prev = f_curr
        jd_curr += step
    raise RuntimeError(
        f"No solar return bracket found for year {year} "
        f"(natal_sun_lon={natal_sun_lon:.6f})"
    )


def find_solar_return(
    year: int, natal_sun_lon: float, flags: int,
    *, precision_minutes: float = 0.5,
) -> float:
    """
    Return the Julian Day (UT) of the Solar Return for the given year, to
    `precision_minutes` precision. Uses coarse 1-day bracket then bisection.
    """
    jd_lo, jd_hi = _coarse_bracket_for_year(year, natal_sun_lon, flags)
    f_lo = signed_lon_delta(
        compute_planet_sidereal_lon(jd_lo, "Sun", flags), natal_sun_lon,
    )
    f_hi = signed_lon_delta(
        compute_planet_sidereal_lon(jd_hi, "Sun", flags), natal_sun_lon,
    )
    target_jd_precision = precision_minutes / (24.0 * 60.0)
    while (jd_hi - jd_lo) > target_jd_precision:
        jd_mid = 0.5 * (jd_lo + jd_hi)
        f_mid = signed_lon_delta(
            compute_planet_sidereal_lon(jd_mid, "Sun", flags), natal_sun_lon,
        )
        if f_mid <= 0.0:
            jd_lo, f_lo = jd_mid, f_mid
        else:
            jd_hi, f_hi = jd_mid, f_mid
    return 0.5 * (jd_lo + jd_hi)


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------

def compute_varshaphala(
    *,
    chart_id: str,
    birth_dt: datetime,
    birth_lat: float,
    birth_lon: float,
    year_start: int,
    year_end: int,
    ayanamsha: str = "lahiri",
    ephe_path: str | None = None,
) -> tuple[list[VarshaphalaRow], dict]:
    flags, ephe_mode = setup_swe(ayanamsha=ayanamsha, ephe_path=ephe_path)

    # Natal Sun sidereal longitude.
    natal_jd = jd_for_utc(birth_dt)
    natal_sun_lon = compute_planet_sidereal_lon(natal_jd, "Sun", flags)

    diagnostics = {
        "ephe_mode": ephe_mode,
        "ayanamsha": ayanamsha,
        "computed_by": "pyswisseph",
        "birth_iso": birth_dt.isoformat(),
        "natal_jd_ut": natal_jd,
        "natal_sun_sidereal_lon_deg": natal_sun_lon,
        "birth_lat": birth_lat,
        "birth_lon": birth_lon,
        "year_start": year_start,
        "year_end": year_end,
        "search_precision_minutes": 0.5,
    }

    rows: list[VarshaphalaRow] = []
    for year in range(year_start, year_end + 1):
        sr_jd = find_solar_return(year, natal_sun_lon, flags)
        sr_dt = utc_for_jd(sr_jd)

        # Recompute planets at the Solar Return moment.
        planets_data: dict[str, dict[str, Any]] = {}
        for planet in PLANETS_ORDER:
            lon = compute_planet_sidereal_lon(sr_jd, planet, flags)
            planets_data[planet] = {
                "sidereal_lon": lon,
                "sign": sign_for(lon),
                "nakshatra": nakshatra_for(lon),
            }

        # Ascendant via houses_ex (sidereal flag).
        # houses_ex returns (house_cusps[12], ascmc[8]); ascmc[0] = Asc, ascmc[1] = MC.
        cusps, ascmc = swe.houses_ex(
            sr_jd, birth_lat, birth_lon, b"P", swe.FLG_SIDEREAL,
        )
        asc_lon = ascmc[0] % 360.0

        rows.append(VarshaphalaRow(
            chart_id=chart_id,
            year=year,
            solar_return_utc=sr_dt.isoformat(),
            ascendant_sidereal_lon=asc_lon,
            ascendant_sign=sign_for(asc_lon),
            planets=planets_data,
            computed_by="pyswisseph",
            ayanamsha=ayanamsha,
        ))

    return rows, diagnostics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--chart-id", required=True,
                        help="Chart UUID (the charts.chart_id of the chart under test). REQUIRED.")
    parser.add_argument(
        "--birth", required=True,
        help="ISO8601 birth datetime of the chart under test (timezone-aware), from its `charts` row. REQUIRED: no birth datetime is embedded in this script.",
    )
    parser.add_argument("--birth-lat", type=float, required=True,
                        help="Birth latitude in decimal degrees (N positive). REQUIRED (from the charts row).")
    parser.add_argument("--birth-lon", type=float, required=True,
                        help="Birth longitude in decimal degrees (E positive). REQUIRED (from the charts row).")
    parser.add_argument("--year-start", type=int, default=None,
                        help="First solar-return year (default: the birth year).")
    parser.add_argument("--year-end", type=int, default=None,
                        help="Last solar-return year (default: year-start + 77).")
    parser.add_argument("--ayanamsha", default="lahiri")
    parser.add_argument(
        "--ephe-path", default=os.environ.get("SE_EPHE_PATH"),
        help="Optional Swiss Ephemeris .se1 file directory.",
    )
    parser.add_argument(
        "--output",
        default="05_TEMPORAL_ENGINES/varshaphala/VARSHAPHALA_RAW_v1_0.json",
    )
    args = parser.parse_args()

    birth_dt = parse_iso8601(args.birth)
    year_start = args.year_start if args.year_start is not None else birth_dt.year
    year_end = args.year_end if args.year_end is not None else year_start + 77

    rows, diag = compute_varshaphala(
        chart_id=args.chart_id,
        birth_dt=birth_dt,
        birth_lat=args.birth_lat,
        birth_lon=args.birth_lon,
        year_start=year_start,
        year_end=year_end,
        ayanamsha=args.ayanamsha,
        ephe_path=args.ephe_path,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "computed_at": datetime.now(tz=timezone.utc).isoformat(),
        "chart_id": args.chart_id,
        "ayanamsha": args.ayanamsha,
        "computed_by": "pyswisseph",
        "diagnostics": diag,
        "row_count": len(rows),
        "rows": [asdict(r) for r in rows],
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(rows)} Varshaphala rows to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
