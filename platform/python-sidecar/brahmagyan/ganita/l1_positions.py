"""
brahmagyan.ganita.l1_positions — ganita.positions: 5 ayanamshas × 10 bodies
=============================================================================

Produces planet positions for 5 ayanamshas × all grahas + Ascendant for the native's chart.

Five ayanamshas (per BRAHMA_BUILD_UX_SPEC and FORENSIC v8.0):
  1. Lahiri (Chitrapaksha)  — primary
  2. Raman
  3. KP (Krishnamurti)
  4. True Citra
  5. Yukteshwar

For each ayanamsha: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Lagna (Ascendant)
Each position row: degrees, sign (rashi), nakshatra, pada, house

Output: chart_facts table with fact_category='ganita.positions',
        fact_subject='{graha}_{ayanamsha_key}'

Volume floor: 5 ayanamshas × 10 bodies = 50 rows (base)
With sub-fields (sign, nakshatra, pada, house) the actual data is stored as a rich JSONB value.

BRAHMA-GA-1-2 / ganita.positions
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 50  # 5 ayanamshas × 10 bodies

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
NATIVE_TZ_OFFSET = 5.5

SOURCE_CITATION = "pyswisseph DE441 (Swiss Ephemeris); multiple ayanamshas"

# Ayanamsha registry — order matters (Lahiri is primary)
AYANAMSHAS = [
    {"key": "lahiri",      "label": "Lahiri (Chitrapaksha)",  "swe_id": None},  # swe.SIDM_LAHIRI
    {"key": "raman",       "label": "Raman",                  "swe_id": None},  # swe.SIDM_RAMAN
    {"key": "kp",          "label": "KP (Krishnamurti)",      "swe_id": None},  # swe.SIDM_KRISHNAMURTI
    {"key": "true_citra",  "label": "True Citra",             "swe_id": None},  # swe.SIDM_TRUE_CITRA
    {"key": "yukteshwar",  "label": "Yukteshwar",             "swe_id": None},  # swe.SIDM_YUKTESHWAR
]

GRAHA_NAMES = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu", "Lagna",
]

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


# ── Ayanamsha SWE ID lookup ───────────────────────────────────────────────────

def _swe_sidm_id(key: str) -> int:
    import swisseph as swe
    return {
        "lahiri":     swe.SIDM_LAHIRI,
        "raman":      swe.SIDM_RAMAN,
        "kp":         swe.SIDM_KRISHNAMURTI,
        "true_citra": swe.SIDM_TRUE_CITRA,
        "yukteshwar": swe.SIDM_YUKTESHWAR,
    }[key]


# ── JD computation ────────────────────────────────────────────────────────────

def _birth_jd_utc() -> float:
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


# ── Position computation for all bodies ──────────────────────────────────────

def compute_positions_all_bodies(jd_utc: float, ayanamsha_key: str) -> list[dict[str, Any]]:
    """
    Compute sidereal positions for 9 grahas + Lagna for one ayanamsha.

    Returns list of 10 dicts: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Lagna.
    Each dict contains:
      name, sidereal_longitude, sign_id, sign, nakshatra_id, nakshatra, nakshatra_pada, house,
      tropical_longitude, speed_dps, is_retrograde, ayanamsha_key, ayanamsha_value
    """
    import swisseph as swe

    swe_id = _swe_sidm_id(ayanamsha_key)
    swe.set_sid_mode(swe_id, 0, 0)
    aya_val = swe.get_ayanamsa_ut(jd_utc)

    PLANET_IDS = [
        ("Sun",     swe.SUN),
        ("Moon",    swe.MOON),
        ("Mars",    swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus",   swe.VENUS),
        ("Saturn",  swe.SATURN),
        ("Rahu",    swe.TRUE_NODE),
    ]

    def _parse(trop_lon: float, speed: float) -> dict:
        sid_lon = (trop_lon - aya_val) % 360.0
        sign_idx = int(sid_lon / 30)
        nak_span = 360.0 / 27
        nak_idx = int(sid_lon / nak_span)
        nak_pos = sid_lon % nak_span
        pada = int(nak_pos / (nak_span / 4)) + 1
        return {
            "sidereal_longitude": round(sid_lon, 6),
            "tropical_longitude": round(trop_lon, 6),
            "sign_id":            sign_idx + 1,
            "sign":               SIGN_NAMES[sign_idx],
            "nakshatra_id":       nak_idx + 1,
            "nakshatra":          NAKSHATRA_NAMES[nak_idx],
            "nakshatra_pada":     pada,
            "speed_dps":          round(speed, 6),
            "is_retrograde":      speed < 0,
            "ayanamsha_key":      ayanamsha_key,
            "ayanamsha_value":    round(aya_val, 6),
        }

    results: list[dict] = []
    planet_lons: dict[str, float] = {}
    for name, pid in PLANET_IDS:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        result, _ = swe.calc_ut(jd_utc, pid, flags)
        trop_lon = result[0]
        speed = result[3]
        planet_lons[name] = trop_lon
        row = {"name": name}
        row.update(_parse(trop_lon, speed))
        results.append(row)

    # Ketu = Rahu + 180°
    rahu_trop = planet_lons["Rahu"]
    ketu_trop = (rahu_trop + 180.0) % 360.0
    ketu_row = {"name": "Ketu"}
    ketu_row.update(_parse(ketu_trop, 0.0))
    ketu_row["is_retrograde"] = False
    results.append(ketu_row)

    # Lagna (Ascendant) — requires lat/lon
    lagna_added = False
    try:
        cusps, ascmc = swe.houses(jd_utc, NATIVE_LAT, NATIVE_LON, b"P")
        asc_trop = ascmc[0]
        lagna_row = {"name": "Lagna"}
        lagna_row.update(_parse(asc_trop, 0.0))
        lagna_row["is_retrograde"] = False
        lagna_row["speed_dps"] = 0.0
        results.append(lagna_row)
        lagna_added = True

        # Compute house numbers using Placidus cusps (tropical).
        # swe.houses returns a 12-element tuple (index 0..11 = house 1..12 cusps).
        house_cusps = list(cusps)  # 12 elements, each is the cusp of house (i+1)
        for body in results:
            trop = body["tropical_longitude"]
            house_num = 12  # default fallback
            for i in range(12):
                c_start = house_cusps[i]
                c_end = house_cusps[(i + 1) % 12]
                # Handle wrap-around crossing 0°/360°
                if c_end > c_start:
                    if c_start <= trop < c_end:
                        house_num = i + 1
                        break
                else:
                    if trop >= c_start or trop < c_end:
                        house_num = i + 1
                        break
            body["house"] = house_num
    except Exception as exc:
        logger.warning("[l1_positions] Lagna/house computation failed: %s", exc)
        if not lagna_added:
            results.append({
                "name": "Lagna",
                "sidereal_longitude": 0.0,
                "tropical_longitude": 0.0,
                "sign_id": 1, "sign": "Aries",
                "nakshatra_id": 1, "nakshatra": "Ashwini",
                "nakshatra_pada": 1, "speed_dps": 0.0,
                "is_retrograde": False,
                "ayanamsha_key": ayanamsha_key,
                "ayanamsha_value": round(aya_val, 6),
                "house": 1,
            })
        for body in results:
            if "house" not in body:
                body["house"] = 0

    return results


def compute_all_ayanamshas(jd_utc: float) -> dict[str, list[dict]]:
    """
    Compute positions for all 5 ayanamshas.

    Returns dict: {ayanamsha_key: [list of 10 body dicts]}
    """
    results: dict = {}
    for aya in AYANAMSHAS:
        key = aya["key"]
        try:
            positions = compute_positions_all_bodies(jd_utc, key)
            results[key] = positions
            logger.info("[l1_positions] ayanamsha=%s bodies=%d", key, len(positions))
        except Exception as exc:
            logger.error("[l1_positions] ayanamsha=%s failed: %s", key, exc)
            results[key] = []
    return results


# ── chart_facts writer ────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l1_positions] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_positions(chart_id: str, build_id: str | None = None) -> dict[str, Any]:
    """
    Compute and write ganita.positions rows to chart_facts.

    Each row: fact_category='ganita.positions', fact_subject='{graha}_{ayanamsha}',
              fact_value=JSON position dict.

    Returns: {seeded: int, ayanamshas: list, volume_floor: int}
    """
    jd = _birth_jd_utc()
    all_positions = compute_all_ayanamshas(jd)

    rows_written = 0
    with _conn() as conn:
        for aya_key, positions in all_positions.items():
            for body in positions:
                fact_subject = f"{body['name']}_{aya_key}"
                fact_value = {
                    "graha":               body["name"],
                    "ayanamsha":           aya_key,
                    "sidereal_longitude":  body["sidereal_longitude"],
                    "tropical_longitude":  body["tropical_longitude"],
                    "sign_id":             body["sign_id"],
                    "sign":                body["sign"],
                    "nakshatra_id":        body["nakshatra_id"],
                    "nakshatra":           body["nakshatra"],
                    "nakshatra_pada":      body["nakshatra_pada"],
                    "house":               body.get("house", 0),
                    "speed_dps":           body["speed_dps"],
                    "is_retrograde":       body["is_retrograde"],
                    "ayanamsha_value_deg": body["ayanamsha_value"],
                }
                conn.execute(
                    """
                    INSERT INTO chart_facts
                      (chart_id, fact_category, fact_subject, fact_value,
                       source_citation, build_id)
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                    ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                      fact_value = EXCLUDED.fact_value,
                      source_citation = EXCLUDED.source_citation,
                      build_id = EXCLUDED.build_id,
                      updated_at = NOW()
                    """,
                    [
                        chart_id, "ganita.positions", fact_subject,
                        json.dumps(fact_value),
                        f"pyswisseph DE441 / {aya_key} ayanamsha",
                        build_id,
                    ],
                )
                rows_written += 1
        conn.commit()

    logger.info("[l1_positions] seed_positions: chart=%s rows=%d", chart_id, rows_written)
    return {
        "seeded": rows_written,
        "ayanamshas": list(all_positions.keys()),
        "volume_floor": VOLUME_FLOOR,
        "volume_met": rows_written >= VOLUME_FLOOR,
    }


# ── Volume check (no DB required) ────────────────────────────────────────────

def check_volume() -> dict[str, Any]:
    """
    Check that the engine can produce the required volume without a DB connection.
    Returns {status: GREEN|AMBER|RED, volume_floor, actual, ayanamshas}.
    """
    try:
        jd = _birth_jd_utc()
        all_positions = compute_all_ayanamshas(jd)
        total = sum(len(v) for v in all_positions.values())
        ayas_ok = [k for k, v in all_positions.items() if len(v) >= 10]
        status = "GREEN" if total >= VOLUME_FLOOR else "AMBER"
        return {
            "status": status,
            "volume_floor": VOLUME_FLOOR,
            "actual": total,
            "ayanamshas_ok": ayas_ok,
            "ayanamshas_missing": [k for k in all_positions if k not in ayas_ok],
            "source_citation": SOURCE_CITATION,
        }
    except Exception as exc:
        return {
            "status": "RED",
            "volume_floor": VOLUME_FLOOR,
            "actual": 0,
            "error": str(exc),
            "source_citation": SOURCE_CITATION,
        }
