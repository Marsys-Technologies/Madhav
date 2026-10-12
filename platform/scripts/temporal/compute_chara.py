#!/usr/bin/env python3
"""
compute_chara.py — Jaimini Chara Dasha engine (M3-W3-C1 deliverable 1).

Computes Atmakaraka and Chara Dasha (Mahadasha + Antardasha) for a native chart
using pyswisseph (Lahiri ayanamsha by default). Two duration variants are
emitted side-by-side because the M3-W3-C1 brief specifies hardcoded sign
durations (Ar=7..Pi=12) that do NOT match the canonical K.N. Rao Padakrama
durations encoded in FORENSIC §5.3, and per CLAUDE.md §I B.10 we cannot
silently pick one. The cross-check artifact reports both vs FORENSIC; native
verdict gates the golden fixture.

Variants:
  brief  — hardcoded constants from the session brief (Ar=7, Ta=6, Ge=5,
           Cn=4, Le=3, Vi=8, Li=9, Sc=10, Sg=9, Cp=10, Aq=11, Pi=12).
  bphs   — count from sign to its lord, applying the standard rule:
             count forward in odd (movable+dual rules vary by sub-tradition)
             and backward in even signs; subtract 1 from the count;
             0 → 12 years. This is the BPHS-Parashari-Jaimini synthesis
             named in the brief and in Sanjay Rath's tradition.

Usage:
  python3 compute_chara.py \\
      --chart-id <chart-uuid> \\
      --birth <ISO8601-birth-datetime-with-offset> \\
      --lat <lat> --lon <lon> \\
      --output 05_TEMPORAL_ENGINES/dasha/jaimini/CHARA_RAW_v1_0.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import swisseph as swe
except ImportError:
    sys.stderr.write("ERROR: pyswisseph not installed. pip install pyswisseph\n")
    sys.exit(2)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Sign lord mapping (classical seven-sign-lord scheme; Rahu/Ketu not used as lords here)
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Sign category for Jaimini directional rule
MOVABLE = {"Aries", "Cancer", "Libra", "Capricorn"}
FIXED = {"Taurus", "Leo", "Scorpio", "Aquarius"}
DUAL = {"Gemini", "Virgo", "Sagittarius", "Pisces"}

# Brief-specified hardcoded durations (variant=brief)
BRIEF_DURATIONS = {
    "Aries": 7, "Taurus": 6, "Gemini": 5, "Cancer": 4,
    "Leo": 3, "Virgo": 8, "Libra": 9, "Scorpio": 10,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12,
}

# Planets considered for Atmakaraka per 7-karaka system (Sun..Saturn; nodes excluded)
AK_PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
]


@dataclass
class Position:
    planet: str
    sidereal_lon: float       # 0..360 degrees
    sign: str
    deg_in_sign: float        # 0..30 degrees


def parse_iso(iso: str) -> dt.datetime:
    s = iso.replace("Z", "+00:00")
    return dt.datetime.fromisoformat(s)


def julian_day_ut(birth: dt.datetime) -> float:
    """Convert birth datetime (timezone-aware) to Julian Day UT."""
    utc = birth.astimezone(dt.timezone.utc)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
    )


def sidereal_position(jd_ut: float, planet_id: int) -> float:
    """Sidereal longitude (Lahiri) in 0..360."""
    flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    pos, _ = swe.calc_ut(jd_ut, planet_id, flag)
    return pos[0] % 360.0


def lon_to_sign(lon: float) -> tuple[str, float]:
    idx = int(lon // 30) % 12
    deg_in_sign = lon - 30.0 * idx
    return SIGNS[idx], deg_in_sign


def compute_atmakaraka(jd_ut: float) -> tuple[Position, list[Position]]:
    """Atmakaraka = planet with highest degree-in-sign (7-karaka system)."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    positions: list[Position] = []
    for name, pid in AK_PLANETS:
        lon = sidereal_position(jd_ut, pid)
        sign, deg = lon_to_sign(lon)
        positions.append(Position(planet=name, sidereal_lon=lon, sign=sign, deg_in_sign=deg))
    ak = max(positions, key=lambda p: p.deg_in_sign)
    return ak, positions


def compute_lagna(jd_ut: float, lat: float, lon: float) -> tuple[str, float, float]:
    """Sidereal Lagna (Ascendant) using Placidus houses + Lahiri."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)
    asc_lon = ascmc[0] % 360.0
    sign, deg = lon_to_sign(asc_lon)
    return sign, deg, asc_lon


# ---------------------------------------------------------------------------
# Chara dasha sequence + duration logic
# ---------------------------------------------------------------------------

def chara_sequence_from_ak(ak_sign: str, ak_position_planets: dict[str, str]) -> list[str]:
    """
    Determine the 12-rashi Chara Mahadasha sequence.

    Standard rule (Sanjay Rath / BPHS-Jaimini synthesis):
      - Mahadasha begins from the sign occupied by the Atmakaraka.
      - Successive signs follow zodiacal order (Aries → Taurus → ...).
        (The Padakrama-vs-direct-order distinction is a known fork; this
        engine emits the direct-order sequence and flags the alternate path.)
    """
    start_idx = SIGNS.index(ak_sign)
    return [SIGNS[(start_idx + i) % 12] for i in range(12)]


def chara_duration_bphs(sign: str, lord_position_sign: str | None) -> tuple[int, str]:
    """
    BPHS sign-to-lord count rule:
      - Count from `sign` to the sign occupied by its lord.
      - Direction depends on movable/fixed/dual:
          movable → forward
          fixed   → backward (12 - forward + 2 = ...) — implemented via reverse count
          dual    → forward (per Sanjay Rath; some traditions use 'forward but ending at sign before lord')
      - Subtract 1 from the count; 0 → 12 years.

    Returns (years, note). If lord_position_sign is None (data missing), returns (0, reason).
    """
    if lord_position_sign is None:
        return 0, "lord position unknown — cannot compute"
    a = SIGNS.index(sign)
    b = SIGNS.index(lord_position_sign)
    if sign in MOVABLE or sign in DUAL:
        # forward count (inclusive of start; per BPHS, count from sign to lord)
        count = ((b - a) % 12) + 1
    else:
        # fixed → backward count
        count = ((a - b) % 12) + 1
    years = count - 1
    if years == 0:
        years = 12
    return years, f"sign={sign} lord_in={lord_position_sign} count={count}"


def antardasha_sequence(maha_sign: str) -> list[str]:
    """
    Antardasha sequence within a Chara Mahadasha:
      - Odd-counted signs from MD (movable/dual): zodiacal order starting from MD+1
      - Even-counted signs (fixed): reverse zodiacal starting from MD-1
      - 12 antardashas total; sub-period proportional to sub-rashi duration relative
        to total over the 12 sub-rashis.
    For deterministic output we use the simple traditional rule:
      - MD sign in movable/dual: forward order from MD itself (Aries → Taurus → ...)
      - MD sign in fixed: reverse order from MD (Aries → Pisces → Aquarius → ...)
    """
    start_idx = SIGNS.index(maha_sign)
    if maha_sign in FIXED:
        return [SIGNS[(start_idx - i) % 12] for i in range(12)]
    return [SIGNS[(start_idx + i) % 12] for i in range(12)]


def add_years_proportional(start: dt.date, years_total: float, fraction: float) -> dt.date:
    """Advance a date by `years_total * fraction` years (calendar-day approximation)."""
    days = years_total * fraction * 365.25
    return start + dt.timedelta(days=days)


def build_chara(
    chart_id: str,
    birth_iso: str,
    ak: Position,
    all_positions: list[Position],
    lagna_sign: str,
    horizon_year: int,
    variant: str,
) -> list[dict[str, Any]]:
    """
    Build full Chara dasha entries (MD + AD) until horizon_year.

    variant: 'brief' or 'bphs' — selects sign-duration source.
    """
    # Sign occupancy for each lord (used by bphs variant)
    planet_sign = {p.planet: p.sign for p in all_positions}
    lord_in_sign = {sign: planet_sign.get(SIGN_LORD[sign]) for sign in SIGNS}

    sequence = chara_sequence_from_ak(ak.sign, planet_sign)
    birth_dt = parse_iso(birth_iso)
    birth_date = birth_dt.date()
    horizon_date = dt.date(horizon_year, 12, 31)

    rows: list[dict[str, Any]] = []
    cursor = birth_date
    md_idx = 0

    # We loop through MD cycles until we pass the horizon
    cycles = 0
    while cursor < horizon_date and cycles < 8:  # safety: max 8 cycles (~96+ years)
        cycles += 1
        for md_sign in sequence:
            if variant == "brief":
                md_years = BRIEF_DURATIONS[md_sign]
                md_note = f"variant=brief (hardcoded constant Ar=7..Pi=12)"
                needs_verification = True
                verification_note = (
                    "[EXTERNAL_COMPUTATION_REQUIRED] Brief-specified constant; "
                    "does not match standard BPHS sign-to-lord rule nor FORENSIC §5.3 "
                    "K.N. Rao Padakrama durations. Native verdict required."
                )
            elif variant == "bphs":
                md_years, md_note = chara_duration_bphs(md_sign, lord_in_sign[md_sign])
                needs_verification = True  # BPHS variant differs from Padakrama (FORENSIC §5.3)
                verification_note = (
                    "[EXTERNAL_COMPUTATION_REQUIRED] BPHS sign-to-lord rule; "
                    "FORENSIC §5.3 uses K.N. Rao Padakrama scheme which yields "
                    "different durations. Cross-check artifact reports both."
                )
            else:
                raise ValueError(f"unknown variant {variant!r}")

            md_start = cursor
            md_end = md_start + dt.timedelta(days=md_years * 365.25)
            duration_days_md = (md_end - md_start).days

            rows.append({
                "chart_id": chart_id,
                "system": "chara",
                "variant": variant,
                "rashi": md_sign,
                "antardasha_rashi": None,
                "level": "M",
                "start_date": md_start.isoformat(),
                "end_date": md_end.isoformat(),
                "duration_days": duration_days_md,
                "duration_years_specified": md_years,
                "atmakaraka": ak.planet,
                "atmakaraka_degree_in_sign": round(ak.deg_in_sign, 4),
                "atmakaraka_sign": ak.sign,
                "lagna_sign": lagna_sign,
                "computed_by": "pyswisseph",
                "ayanamsha": "lahiri",
                "needs_verification": needs_verification,
                "verification_note": verification_note,
                "computation_note": md_note,
            })

            # Antardashas: 12 sub-rashis, each a 1/12 fraction of MD
            ad_seq = antardasha_sequence(md_sign)
            ad_cursor = md_start
            for ad_sign in ad_seq:
                ad_start = ad_cursor
                ad_end = ad_start + dt.timedelta(days=md_years * 365.25 / 12.0)
                duration_days_ad = (ad_end - ad_start).days
                rows.append({
                    "chart_id": chart_id,
                    "system": "chara",
                    "variant": variant,
                    "rashi": md_sign,
                    "antardasha_rashi": ad_sign,
                    "level": "A",
                    "start_date": ad_start.isoformat(),
                    "end_date": ad_end.isoformat(),
                    "duration_days": duration_days_ad,
                    "duration_years_specified": md_years / 12.0,
                    "atmakaraka": ak.planet,
                    "atmakaraka_degree_in_sign": round(ak.deg_in_sign, 4),
                    "atmakaraka_sign": ak.sign,
                    "lagna_sign": lagna_sign,
                    "computed_by": "pyswisseph",
                    "ayanamsha": "lahiri",
                    "needs_verification": needs_verification,
                    "verification_note": verification_note,
                    "computation_note": md_note,
                })
                ad_cursor = ad_end

            cursor = md_end
            if cursor >= horizon_date:
                break

    return rows


def main() -> int:
    p = argparse.ArgumentParser(description="Jaimini Chara Dasha engine")
    p.add_argument("--chart-id", required=True)
    p.add_argument("--birth", required=True, help="ISO8601 birth datetime, tz-aware")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--ayanamsha", default="lahiri")
    p.add_argument("--horizon-year", type=int, default=2050)
    p.add_argument("--output", required=True)
    p.add_argument("--variants", default="brief,bphs", help="comma-separated variants")
    args = p.parse_args()

    if args.ayanamsha != "lahiri":
        sys.stderr.write(f"ERROR: only 'lahiri' supported in v1.0; got {args.ayanamsha}\n")
        return 2

    birth_dt = parse_iso(args.birth)
    jd = julian_day_ut(birth_dt)

    ak, positions = compute_atmakaraka(jd)
    lagna_sign, lagna_deg, lagna_lon = compute_lagna(jd, args.lat, args.lon)

    sys.stderr.write(
        f"[chara] AK={ak.planet} {ak.sign} {ak.deg_in_sign:.4f}°  "
        f"Lagna={lagna_sign} {lagna_deg:.4f}°\n"
    )

    all_rows: list[dict[str, Any]] = []
    for variant in [v.strip() for v in args.variants.split(",") if v.strip()]:
        rows = build_chara(
            chart_id=args.chart_id,
            birth_iso=args.birth,
            ak=ak,
            all_positions=positions,
            lagna_sign=lagna_sign,
            horizon_year=args.horizon_year,
            variant=variant,
        )
        sys.stderr.write(f"[chara] variant={variant}: {len(rows)} rows\n")
        all_rows.extend(rows)

    payload = {
        "schema": "chara_dasha.v1",
        "chart_id": args.chart_id,
        "birth_datetime": args.birth,
        "ayanamsha": args.ayanamsha,
        "computed_by": "pyswisseph",
        "engine_version": "compute_chara.py v1.0",
        "atmakaraka": {
            "planet": ak.planet,
            "sign": ak.sign,
            "degree_in_sign": round(ak.deg_in_sign, 4),
            "sidereal_longitude": round(ak.sidereal_lon, 4),
        },
        "lagna": {
            "sign": lagna_sign,
            "degree_in_sign": round(lagna_deg, 4),
            "sidereal_longitude": round(lagna_lon, 4),
        },
        "all_positions": [
            {
                "planet": p.planet,
                "sign": p.sign,
                "degree_in_sign": round(p.deg_in_sign, 4),
                "sidereal_longitude": round(p.sidereal_lon, 4),
            }
            for p in positions
        ],
        "horizon_year": args.horizon_year,
        "rows": all_rows,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
    sys.stderr.write(f"[chara] wrote {len(all_rows)} rows -> {out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
