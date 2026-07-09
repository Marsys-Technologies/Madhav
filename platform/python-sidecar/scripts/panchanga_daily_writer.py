#!/usr/bin/env python3
"""
panchanga_daily_writer.py — Deterministic forward-panchanga writer (R5.1 C3).

Re-provisions `public.panchanga_daily` (platform/migrations/366_panchanga_daily_reprovision.sql)
with REAL, deterministically-computed rows for a rolling +12-month window, at the
native's location default (Bhubaneswar — lat 20.2700, lon 85.8400, tz_offset +330min IST;
see panchang_engine/panchang_daily_reader.py BHUBANESWAR_LAT/LON).

This is a date-keyed reference-data writer, NOT a chart-build writer. It does NOT
conform to the orchestrator's WriterBase/@register contract (that contract is for
per-chart ga_*/bo_*/ka_*/ph_*/mi_* assets — see ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
§2). panchanga_daily is explicitly the ONE sanctioned new serving-plane data surface
per CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md §C3 — it is never touched by, and never
touches, the orchestrator or any ga_*/bo_*/ka_*/ph_*/mi_* build writer.

Computation source: panchang_engine.compute_panchang() (Swiss Ephemeris / pyswisseph),
the same deterministic engine already used by ka_muhurta_seva / muhurat.finder for
engine-direct scoring. No LLM call anywhere in this module (deterministic-first, B.10).

Usage:
    python scripts/panchanga_daily_writer.py                  # today .. today+365d
    python scripts/panchanga_daily_writer.py --days 400
    python scripts/panchanga_daily_writer.py --from 2026-07-09 --to 2027-07-09
    python scripts/panchanga_daily_writer.py --dry-run         # compute only, no DB write

Idempotency: per-date UPSERT (ON CONFLICT (date) DO UPDATE). Safe to re-run monthly
(the scheduled refresh job) or ad hoc — re-running never accretes duplicate rows and
always reflects the latest computation_version/ephemeris_version if the engine changes.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, timedelta

logger = logging.getLogger("panchanga_daily_writer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Native's location default (Bhubaneswar) — single-observer table.
# Mirrors panchang_engine/panchang_daily_reader.py BHUBANESWAR_LAT/LON exactly.
NATIVE_LAT: float = 20.2700
NATIVE_LON: float = 85.8400
NATIVE_TZ_OFFSET_MINUTES: int = 330  # IST = UTC+5:30

DEFAULT_WINDOW_DAYS = 365  # rolling +12 months


def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key)
        if val:
            return val
    raise RuntimeError(
        "panchanga_daily_writer: no DB URL in environment. "
        "Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


def _row_from_panchang(p) -> dict:
    """
    Build one panchanga_daily row dict from a computed Panchang object.
    Populates BOTH consumer column families (name-based for outlook.py,
    id-based for panchang_daily_reader.py) from the SAME single computation —
    never two independent derivations of the same fact (B.3 / B.10 / N.5).
    """
    from panchang_engine.serialize import panchang_to_dict

    d = panchang_to_dict(p)

    return {
        "date": p.date,
        "lat": p.lat,
        "lon": p.lon,
        "tz_offset_minutes": p.tz_offset_minutes,
        "sunrise_utc": p.sunrise_utc,
        "sunset_utc": p.sunset_utc,
        "moonrise_utc": p.moonrise_utc,
        "moonset_utc": p.moonset_utc,
        # Tithi
        "tithi": p.tithi.id,
        "tithi_id": p.tithi.id,
        "tithi_name": p.tithi.name,
        "tithi_end_utc": p.tithi.end_utc,
        "paksha": p.paksha,
        # Vara
        "vara": p.vara.name,
        "vara_id": p.vara.id,
        "vara_lord": _VARA_LORDS.get(p.vara.id),
        # Nakshatra (Moon, sidereal Lahiri, at sunrise)
        "moon_nakshatra": p.nakshatra.name,
        "nakshatra_id": p.nakshatra.id,
        "moon_nakshatra_pada": None,  # not separately exposed on Anga; omitted rather than fabricated
        "moon_longitude_deg": next(
            (pl.longitude_sidereal for pl in p.planets if pl.name == "Moon"), None
        ),
        "sun_longitude_deg": next(
            (pl.longitude_sidereal for pl in p.planets if pl.name == "Sun"), None
        ),
        "nakshatra_end_utc": p.nakshatra.end_utc,
        # Yoga
        "yoga": p.yoga.name,
        "yoga_id": p.yoga.id,
        "yoga_end_utc": p.yoga.end_utc,
        # Karana
        "karana": p.karana_first.name,
        "karana_id": p.karana_first.id,
        "karana_second_id": p.karana_second.id,
        "karana_end_utc": p.karana_first.end_utc,
        # Moon phase (illumination %, [0,100]) — from the engine's rich sun_moon topic,
        # not the base serializer (panchang_to_dict does not carry sun_moon in its
        # output dict; the dataclass field on Panchang itself does).
        "moon_phase": (p.sun_moon.moon_illumination_pct if p.sun_moon is not None else None),
        # Enrichment JSONB — reuse the canonical serializer so cache reads are
        # byte-identical to engine-direct compute output (serialize.py docstring contract).
        "special_yogas": d["special_yogas"],
        "choghadiya": d["choghadiya"],
        "hora": d["hora"],
        "inauspicious": d["inauspicious"],
        "auspicious": d["auspicious"],
        "planets": d["planets"],
        # Provenance
        "ayanamsha_id": "lahiri",
        "computation_version": p.computation_version,
        "ephemeris_version": p.ephemeris_version,
    }


_VARA_LORDS = {
    1: "Sun", 2: "Moon", 3: "Mars", 4: "Mercury",
    5: "Jupiter", 6: "Venus", 7: "Saturn",
}

_UPSERT_SQL = """
    INSERT INTO panchanga_daily (
        date, lat, lon, tz_offset_minutes,
        sunrise_utc, sunset_utc, moonrise_utc, moonset_utc,
        tithi, tithi_id, tithi_name, tithi_end_utc, paksha,
        vara, vara_id, vara_lord,
        moon_nakshatra, nakshatra_id, moon_nakshatra_pada,
        moon_longitude_deg, sun_longitude_deg, nakshatra_end_utc,
        yoga, yoga_id, yoga_end_utc,
        karana, karana_id, karana_second_id, karana_end_utc,
        moon_phase,
        special_yogas, choghadiya, hora, inauspicious, auspicious, planets,
        ayanamsha_id, computation_version, ephemeris_version, computed_at
    ) VALUES (
        %(date)s, %(lat)s, %(lon)s, %(tz_offset_minutes)s,
        %(sunrise_utc)s, %(sunset_utc)s, %(moonrise_utc)s, %(moonset_utc)s,
        %(tithi)s, %(tithi_id)s, %(tithi_name)s, %(tithi_end_utc)s, %(paksha)s,
        %(vara)s, %(vara_id)s, %(vara_lord)s,
        %(moon_nakshatra)s, %(nakshatra_id)s, %(moon_nakshatra_pada)s,
        %(moon_longitude_deg)s, %(sun_longitude_deg)s, %(nakshatra_end_utc)s,
        %(yoga)s, %(yoga_id)s, %(yoga_end_utc)s,
        %(karana)s, %(karana_id)s, %(karana_second_id)s, %(karana_end_utc)s,
        %(moon_phase)s,
        %(special_yogas)s, %(choghadiya)s, %(hora)s, %(inauspicious)s, %(auspicious)s, %(planets)s,
        %(ayanamsha_id)s, %(computation_version)s, %(ephemeris_version)s, NOW()
    )
    ON CONFLICT (date) DO UPDATE SET
        lat = EXCLUDED.lat, lon = EXCLUDED.lon, tz_offset_minutes = EXCLUDED.tz_offset_minutes,
        sunrise_utc = EXCLUDED.sunrise_utc, sunset_utc = EXCLUDED.sunset_utc,
        moonrise_utc = EXCLUDED.moonrise_utc, moonset_utc = EXCLUDED.moonset_utc,
        tithi = EXCLUDED.tithi, tithi_id = EXCLUDED.tithi_id,
        tithi_name = EXCLUDED.tithi_name, tithi_end_utc = EXCLUDED.tithi_end_utc, paksha = EXCLUDED.paksha,
        vara = EXCLUDED.vara, vara_id = EXCLUDED.vara_id, vara_lord = EXCLUDED.vara_lord,
        moon_nakshatra = EXCLUDED.moon_nakshatra, nakshatra_id = EXCLUDED.nakshatra_id,
        moon_nakshatra_pada = EXCLUDED.moon_nakshatra_pada,
        moon_longitude_deg = EXCLUDED.moon_longitude_deg, sun_longitude_deg = EXCLUDED.sun_longitude_deg,
        nakshatra_end_utc = EXCLUDED.nakshatra_end_utc,
        yoga = EXCLUDED.yoga, yoga_id = EXCLUDED.yoga_id, yoga_end_utc = EXCLUDED.yoga_end_utc,
        karana = EXCLUDED.karana, karana_id = EXCLUDED.karana_id,
        karana_second_id = EXCLUDED.karana_second_id, karana_end_utc = EXCLUDED.karana_end_utc,
        moon_phase = EXCLUDED.moon_phase,
        special_yogas = EXCLUDED.special_yogas, choghadiya = EXCLUDED.choghadiya, hora = EXCLUDED.hora,
        inauspicious = EXCLUDED.inauspicious, auspicious = EXCLUDED.auspicious, planets = EXCLUDED.planets,
        ayanamsha_id = EXCLUDED.ayanamsha_id,
        computation_version = EXCLUDED.computation_version, ephemeris_version = EXCLUDED.ephemeris_version,
        computed_at = NOW()
"""


def write_window(date_from: date, date_to: date, dry_run: bool = False) -> int:
    """
    Compute + upsert panchanga_daily rows for [date_from, date_to] inclusive.
    Returns the number of rows written (or that would be written, if dry_run).
    """
    import json
    from panchang_engine import compute_panchang

    n = 0
    conn = None
    cur = None
    if not dry_run:
        import psycopg

        conn = psycopg.connect(_get_db_url())
        cur = conn.cursor()

    current = date_from
    try:
        while current <= date_to:
            p = compute_panchang(current, NATIVE_LAT, NATIVE_LON, NATIVE_TZ_OFFSET_MINUTES)
            row = _row_from_panchang(p)
            if dry_run:
                logger.info(
                    "DRY-RUN %s: tithi=%s vara=%s nakshatra=%s yoga=%s karana=%s",
                    row["date"], row["tithi_name"], row["vara"], row["moon_nakshatra"],
                    row["yoga"], row["karana"],
                )
            else:
                params = dict(row)
                for jsonb_key in ("special_yogas", "choghadiya", "hora", "inauspicious", "auspicious", "planets"):
                    params[jsonb_key] = json.dumps(params[jsonb_key])
                cur.execute(_UPSERT_SQL, params)
            n += 1
            current += timedelta(days=1)

        if not dry_run:
            conn.commit()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="date_from", type=str, default=None,
                         help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--to", dest="date_to", type=str, default=None,
                         help="End date YYYY-MM-DD (default: --from + --days)")
    parser.add_argument("--days", type=int, default=DEFAULT_WINDOW_DAYS,
                         help=f"Window length in days if --to omitted (default: {DEFAULT_WINDOW_DAYS})")
    parser.add_argument("--dry-run", action="store_true",
                         help="Compute panchanga but do not write to the DB")
    args = parser.parse_args()

    date_from = date.fromisoformat(args.date_from) if args.date_from else date.today()
    date_to = date.fromisoformat(args.date_to) if args.date_to else date_from + timedelta(days=args.days)

    logger.info(
        "panchanga_daily_writer: window=%s..%s (%d days) location=(%.4f,%.4f) tz=%+d dry_run=%s",
        date_from, date_to, (date_to - date_from).days + 1,
        NATIVE_LAT, NATIVE_LON, NATIVE_TZ_OFFSET_MINUTES, args.dry_run,
    )

    n = write_window(date_from, date_to, dry_run=args.dry_run)
    logger.info("panchanga_daily_writer: %d rows %s", n, "computed (dry-run)" if args.dry_run else "upserted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
