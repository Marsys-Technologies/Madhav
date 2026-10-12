#!/usr/bin/env python3
"""
compute_narayana.py — Jaimini Narayana Dasha engine (M3-W3-C1 deliverable 2).

Computes Lagna and Narayana Dasha (rashi-based, Mahadasha + Antardasha) until a
horizon year using pyswisseph (Lahiri ayanamsha by default).

The session brief specifies hardcoded sign durations (Ar=1yr, Ta=2yr, ... Pi=12yr,
i.e. years = sign-number-in-natural-order). This is NOT the standard BPHS
Narayana rule, which counts from each sign to the sign of its lord (with the
movable/fixed/dual directional convention). Per CLAUDE.md §I B.10 we cannot
silently fabricate a tradition, so this engine emits BOTH variants:

  brief — hardcoded sign-number durations from the session brief.
  bphs  — standard sign-to-lord count rule (count - 1; 0 → 12 years).

Sequence rule (per the brief):
  - Mahadasha begins from the Lagna sign.
  - Movable / dual signs: count forward in zodiacal order.
  - Fixed signs: reverse order.
  - 12 rashis total per cycle.

Antardashas: 12 sub-rashis per Mahadasha.

Usage:
  python3 compute_narayana.py \\
      --chart-id <chart-uuid> \\
      --birth <ISO8601-birth-datetime-with-offset> \\
      --lat <lat> --lon <lon> \\
      --output 05_TEMPORAL_ENGINES/dasha/jaimini/NARAYANA_RAW_v1_0.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass
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

SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

MOVABLE = {"Aries", "Cancer", "Libra", "Capricorn"}
FIXED = {"Taurus", "Leo", "Scorpio", "Aquarius"}
DUAL = {"Gemini", "Virgo", "Sagittarius", "Pisces"}

# Brief-specified durations: sign-number in natural order
BRIEF_DURATIONS = {sign: i + 1 for i, sign in enumerate(SIGNS)}

PLANET_IDS = [
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
]


@dataclass
class Position:
    planet: str
    sidereal_lon: float
    sign: str
    deg_in_sign: float


def parse_iso(iso: str) -> dt.datetime:
    s = iso.replace("Z", "+00:00")
    return dt.datetime.fromisoformat(s)


def julian_day_ut(birth: dt.datetime) -> float:
    utc = birth.astimezone(dt.timezone.utc)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
    )


def lon_to_sign(lon: float) -> tuple[str, float]:
    idx = int(lon // 30) % 12
    return SIGNS[idx], lon - 30.0 * idx


def sidereal_position(jd: float, planet_id: int) -> float:
    flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    pos, _ = swe.calc_ut(jd, planet_id, flag)
    return pos[0] % 360.0


def compute_planet_positions(jd: float) -> list[Position]:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    out = []
    for name, pid in PLANET_IDS:
        lon = sidereal_position(jd, pid)
        sign, deg = lon_to_sign(lon)
        out.append(Position(planet=name, sidereal_lon=lon, sign=sign, deg_in_sign=deg))
    return out


def compute_lagna(jd: float, lat: float, lon: float) -> tuple[str, float, float]:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)
    asc_lon = ascmc[0] % 360.0
    sign, deg = lon_to_sign(asc_lon)
    return sign, deg, asc_lon


def narayana_sequence(start_sign: str) -> list[str]:
    """
    Narayana MD sequence:
      - Movable / dual sign: forward zodiacal from start
      - Fixed sign: reverse zodiacal from start
    """
    idx = SIGNS.index(start_sign)
    if start_sign in FIXED:
        return [SIGNS[(idx - i) % 12] for i in range(12)]
    return [SIGNS[(idx + i) % 12] for i in range(12)]


def narayana_duration_bphs(sign: str, lord_in_sign: str | None) -> tuple[int, str]:
    """
    BPHS sign-to-lord count rule (count - 1; 0 → 12 years).
    Movable/dual: count forward; Fixed: count backward.
    """
    if lord_in_sign is None:
        return 0, "lord position unknown"
    a = SIGNS.index(sign)
    b = SIGNS.index(lord_in_sign)
    if sign in MOVABLE or sign in DUAL:
        count = ((b - a) % 12) + 1
    else:
        count = ((a - b) % 12) + 1
    years = count - 1
    if years == 0:
        years = 12
    return years, f"sign={sign} lord_in={lord_in_sign} count={count}"


def antardasha_sequence(maha_sign: str) -> list[str]:
    idx = SIGNS.index(maha_sign)
    if maha_sign in FIXED:
        return [SIGNS[(idx - i) % 12] for i in range(12)]
    return [SIGNS[(idx + i) % 12] for i in range(12)]


def build_narayana(
    chart_id: str,
    birth_iso: str,
    lagna_sign: str,
    positions: list[Position],
    horizon_year: int,
    variant: str,
) -> list[dict[str, Any]]:
    planet_sign = {p.planet: p.sign for p in positions}
    lord_in_sign = {sign: planet_sign.get(SIGN_LORD[sign]) for sign in SIGNS}

    sequence = narayana_sequence(lagna_sign)
    birth_date = parse_iso(birth_iso).date()
    horizon_date = dt.date(horizon_year, 12, 31)

    rows: list[dict[str, Any]] = []
    cursor = birth_date
    cycles = 0
    while cursor < horizon_date and cycles < 5:  # safety
        cycles += 1
        for md_sign in sequence:
            if variant == "brief":
                md_years = BRIEF_DURATIONS[md_sign]
                md_note = "variant=brief (sign-number-in-natural-order)"
                verification_note = (
                    "[EXTERNAL_COMPUTATION_REQUIRED] Brief-specified Narayana "
                    "constants do not match BPHS sign-to-lord rule. Native verdict "
                    "required."
                )
            elif variant == "bphs":
                md_years, md_note = narayana_duration_bphs(md_sign, lord_in_sign[md_sign])
                verification_note = (
                    "[EXTERNAL_COMPUTATION_REQUIRED] BPHS sign-to-lord rule. "
                    "FORENSIC has no Narayana table to cross-check against; "
                    "external acharya/JH verification needed."
                )
            else:
                raise ValueError(f"unknown variant {variant!r}")

            md_start = cursor
            md_end = md_start + dt.timedelta(days=md_years * 365.25)
            duration_days_md = (md_end - md_start).days

            rows.append({
                "chart_id": chart_id,
                "system": "narayana",
                "variant": variant,
                "rashi": md_sign,
                "antardasha_rashi": None,
                "level": "M",
                "start_date": md_start.isoformat(),
                "end_date": md_end.isoformat(),
                "duration_days": duration_days_md,
                "duration_years_specified": md_years,
                "lagna_sign": lagna_sign,
                "computed_by": "pyswisseph",
                "ayanamsha": "lahiri",
                "needs_verification": True,
                "verification_note": verification_note,
                "computation_note": md_note,
            })

            ad_seq = antardasha_sequence(md_sign)
            ad_cursor = md_start
            for ad_sign in ad_seq:
                ad_start = ad_cursor
                ad_end = ad_start + dt.timedelta(days=md_years * 365.25 / 12.0)
                duration_days_ad = (ad_end - ad_start).days
                rows.append({
                    "chart_id": chart_id,
                    "system": "narayana",
                    "variant": variant,
                    "rashi": md_sign,
                    "antardasha_rashi": ad_sign,
                    "level": "A",
                    "start_date": ad_start.isoformat(),
                    "end_date": ad_end.isoformat(),
                    "duration_days": duration_days_ad,
                    "duration_years_specified": md_years / 12.0,
                    "lagna_sign": lagna_sign,
                    "computed_by": "pyswisseph",
                    "ayanamsha": "lahiri",
                    "needs_verification": True,
                    "verification_note": verification_note,
                    "computation_note": md_note,
                })
                ad_cursor = ad_end

            cursor = md_end
            if cursor >= horizon_date:
                break

    return rows


def main() -> int:
    p = argparse.ArgumentParser(description="Jaimini Narayana Dasha engine")
    p.add_argument("--chart-id", required=True)
    p.add_argument("--birth", required=True)
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--ayanamsha", default="lahiri")
    p.add_argument("--horizon-year", type=int, default=2050)
    p.add_argument("--output", required=True)
    p.add_argument("--variants", default="brief,bphs")
    args = p.parse_args()

    if args.ayanamsha != "lahiri":
        sys.stderr.write(f"ERROR: only 'lahiri' supported; got {args.ayanamsha}\n")
        return 2

    birth_dt = parse_iso(args.birth)
    jd = julian_day_ut(birth_dt)
    positions = compute_planet_positions(jd)
    lagna_sign, lagna_deg, lagna_lon = compute_lagna(jd, args.lat, args.lon)

    sys.stderr.write(f"[narayana] Lagna={lagna_sign} {lagna_deg:.4f}°\n")

    all_rows: list[dict[str, Any]] = []
    for variant in [v.strip() for v in args.variants.split(",") if v.strip()]:
        rows = build_narayana(
            chart_id=args.chart_id,
            birth_iso=args.birth,
            lagna_sign=lagna_sign,
            positions=positions,
            horizon_year=args.horizon_year,
            variant=variant,
        )
        sys.stderr.write(f"[narayana] variant={variant}: {len(rows)} rows\n")
        all_rows.extend(rows)

    payload = {
        "schema": "narayana_dasha.v1",
        "chart_id": args.chart_id,
        "birth_datetime": args.birth,
        "ayanamsha": args.ayanamsha,
        "computed_by": "pyswisseph",
        "engine_version": "compute_narayana.py v1.0",
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
    sys.stderr.write(f"[narayana] wrote {len(all_rows)} rows -> {out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
