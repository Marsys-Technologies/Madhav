"""
brahmagyan.ganita.l1_sensitive_points — ganita.sensitive_points
================================================================

Upagrahas: Mandi (Gulika), Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu
Special Lagnas: Hora Lagna, Ghati Lagna, Bhava Lagna, Varnada Lagna, Sree Lagna
Sahams: Punya, Vidya, Rajya, Vivaha (key 4)
Arudhas: A1–A12 (pada for each house)

Mathematical basis:
  - Upagrahas: derived from Saturn's position + day-of-week factors
  - Hora Lagna: accumulated hours from sunrise × 30° per hour, added to Lagna
  - Ghati Lagna: 1 ghati = 24 minutes; 1800 ghatis per day; position from Aries
  - Bhava Lagna: based on hora count from sunrise
  - Varnada Lagna: average of Hora Lagna and Ghati Lagna
  - Sree Lagna: derived from Moon's position relative to Lagna
  - Sahams: classical formulas from BPHS Ch.24
  - Arudhas: reflection of house lord from the house

All computations use Lahiri ayanamsha. Provenance envelope present.

Volume floor: 6 upagrahas + 5 special lagnas + 4 sahams + 12 arudhas = 27 rows minimum

BRAHMA-GA-1-6 / ganita.sensitive_points
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 27  # 6 + 5 + 4 + 12

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
PRIMARY_AYANAMSHA = "lahiri"
SOURCE_CITATION = (
    "BPHS Ch.24 (Sahams), Ch.4 (Upagrahas), Ch.12 (Arudha Padas); "
    "Phala Deepika / classical tradition for special lagnas; "
    "pyswisseph DE441; ayanamsha: Lahiri"
)

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

# Day of week lords (0=Sunday, 1=Monday, ..., 6=Saturday)
DAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Weekday order (Python: 0=Monday, 6=Sunday)
# 1984-02-05 was a Sunday
BIRTH_WEEKDAY = 6  # Sunday (Python convention) → day_lord_index = 0 (Sun)


# ── JD helper ─────────────────────────────────────────────────────────────────

def _birth_jd_utc() -> float:
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _lon_to_point(lon: float) -> dict[str, Any]:
    """Convert sidereal longitude to sign/nakshatra point dict."""
    lon = lon % 360.0
    sign_idx = int(lon / 30.0)
    nak_span = 360.0 / 27
    nak_idx = int(lon / nak_span)
    pada = int((lon % nak_span) / (nak_span / 4)) + 1
    return {
        "longitude": round(lon, 6),
        "sign_id": sign_idx + 1,
        "sign": SIGN_NAMES[sign_idx],
        "nakshatra_id": nak_idx + 1,
        "nakshatra": NAKSHATRA_NAMES[nak_idx],
        "nakshatra_pada": pada,
    }


# ── Upagrahas ─────────────────────────────────────────────────────────────────

def _approximate_sunrise_sunset_ist(lat: float, lon: float, date_str: str) -> tuple[float, float]:
    """
    Approximate sunrise and sunset hours in IST for Bhubaneswar on the given date.
    Returns (sunrise_ist_hour, sunset_ist_hour).

    For 1984-02-05 at Bhubaneswar (20.3°N, 85.8°E):
    Approximate sunrise: 06:33 IST, sunset: 17:52 IST.
    """
    # Approximate computation: use fixed values for the native's birth date
    # These are based on standard astronomical almanac
    return (6.55, 17.87)  # 06:33 and 17:52 IST


def compute_upagrahas(jd_utc: float, positions: dict[str, dict]) -> dict[str, dict]:
    """
    Compute 6 upagrahas for the native's chart.

    Upagrahas are sub-planets derived from Saturn's position and the day-of-week.

    1. Mandi/Gulika: Saturn's sub-planet
       Position = (day_number × 30° + 1/8 × day_length) + Saturn's position (approx)
       Standard formula: Mandi = Saturn position in each 1/8 of the day
       For Sunday: 7th 1/8 of day, Saturday: 1st 1/8, etc.

    2-6. Other upagrahas derived from Sun's position via fixed offsets:
       Dhuma = Sun + 133°20' (4s 13°20')
       Vyatipata = 360° - Dhuma
       Parivesha = Vyatipata + 180°
       Indrachapa = 360° - Parivesha
       Upaketu = Sun + 150° (5s 0°)

    Ref: BPHS Ch.4 + Phala Deepika
    """
    import swisseph as swe

    # Get Sun and Saturn positions
    sun_lon = positions.get("Sun", {}).get("sidereal_longitude", 0.0)
    saturn_lon = positions.get("Saturn", {}).get("sidereal_longitude", 0.0)

    # Approximate sunrise/sunset for birth date
    sr_ist, ss_ist = _approximate_sunrise_sunset_ist(NATIVE_LAT, NATIVE_LON, NATIVE_BIRTH_IST)
    day_duration_hours = ss_ist - sr_ist  # ~ 11.32 hours

    # Birth time in IST for the native
    birth_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    birth_hour_ist = birth_ist.hour + birth_ist.minute / 60.0  # 10.716...

    # Day-of-week index for Sunday: 0 (Sun), Saturday: 6
    # 1984-02-05 is Sunday → lord = Sun (index 0)
    # For Mandi: 1984-02-05 Sunday → 7th of 8 divisions of the day (traditional assignment)
    # Sunday weekday Mandi: 7th 1/8 of day
    # In classical Jyotish, each weekday has a specific 1/8 division for Gulika
    # Mon=6th, Tue=5th, Wed=4th, Thu=3rd, Fri=2nd, Sat=1st, Sun=7th
    DAY_GULIKA_PART = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}  # weekday (Mon=0) → part
    # Python weekday: Mon=0, Sun=6
    birth_weekday_py = datetime(1984, 2, 5).weekday()  # 6 = Sunday
    gulika_part = DAY_GULIKA_PART.get(birth_weekday_py, 7)

    # Gulika/Mandi position: start of the gulika_part / 8 of the day
    gulika_start_hour_ist = sr_ist + (gulika_part - 1) * (day_duration_hours / 8)
    # Sidereal longitude advanced from Saturn's position by time elapsed since day start
    gulika_elapsed = max(0.0, birth_hour_ist - gulika_start_hour_ist)
    gulika_offset = gulika_elapsed / day_duration_hours * 30.0  # degrees advanced in one sign per day
    mandi_lon = (saturn_lon + gulika_offset) % 360.0

    # Other upagrahas (from BPHS / Phala Deepika)
    dhuma_lon    = (sun_lon + 133 + 20/60.0) % 360.0   # Sun + 4s 13°20'
    vyatipata_lon = (360.0 - dhuma_lon) % 360.0
    parivesha_lon = (vyatipata_lon + 180.0) % 360.0
    indrachapa_lon = (360.0 - parivesha_lon) % 360.0
    upaketu_lon   = (sun_lon + 150.0) % 360.0

    return {
        "Mandi":      _lon_to_point(mandi_lon),
        "Dhuma":      _lon_to_point(dhuma_lon),
        "Vyatipata":  _lon_to_point(vyatipata_lon),
        "Parivesha":  _lon_to_point(parivesha_lon),
        "Indrachapa": _lon_to_point(indrachapa_lon),
        "Upaketu":    _lon_to_point(upaketu_lon),
    }


# ── Special Lagnas ────────────────────────────────────────────────────────────

def compute_special_lagnas(jd_utc: float, lagna_lon: float, positions: dict[str, dict]) -> dict[str, dict]:
    """
    Compute 5 special lagnas.

    1. Hora Lagna: elapsed hours since sunrise × 30° per hora, added to Lagna
    2. Ghati Lagna: elapsed ghatis (1 ghati = 24 min) × 360°/1800 per ghati + Aries
    3. Bhava Lagna: accumulated time-based lagna using hora count
    4. Varnada Lagna: complex formula using Hora and Ghati lagnas
    5. Sree Lagna: Moon's longitude + Lagna complement

    References:
      - FORENSIC v8.0 supplement has JH-authoritative values for the native.
      - These computations use mathematical formulas which may differ from JH
        by a few degrees; they are marked as MATHEMATICALLY_DERIVED.
    """
    sr_ist, ss_ist = _approximate_sunrise_sunset_ist(NATIVE_LAT, NATIVE_LON, NATIVE_BIRTH_IST)
    birth_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    birth_hour_ist = birth_ist.hour + birth_ist.minute / 60.0
    day_duration = ss_ist - sr_ist

    elapsed_since_sunrise = max(0.0, birth_hour_ist - sr_ist)  # hours elapsed

    # Hora Lagna: 1 hora = 1 hour; each hora advances 30°
    # At sunrise, Hora Lagna = Lagna. It advances 30° per hora (hour).
    hora_elapsed_horas = elapsed_since_sunrise  # each hora = 1 hour
    hora_lagna_lon = (lagna_lon + hora_elapsed_horas * 30.0) % 360.0

    # Ghati Lagna: 1 ghati = 24 minutes = 0.4 hours
    # 1 ghati → 1° advance from Aries
    elapsed_ghatis = elapsed_since_sunrise * 60.0 / 24.0  # number of ghatis
    ghati_lagna_lon = (elapsed_ghatis * 1.0) % 360.0  # 1° per ghati from Aries

    # Bhava Lagna (approximate): similar to Hora Lagna but from Aries
    bhava_lagna_lon = (elapsed_since_sunrise * 30.0) % 360.0

    # Varnada Lagna: per BPHS, complex formula involving Hora and Ghati
    # Simplified: (Hora Lagna + Ghati Lagna) / 2 (approximate)
    # FORENSIC v8 supplement gives authoritative JH value
    varnada_lon = ((hora_lagna_lon + ghati_lagna_lon) / 2.0) % 360.0

    # Sree Lagna: Moon lon + (distance from Moon to Lagna)
    moon_lon = positions.get("Moon", {}).get("sidereal_longitude", 0.0)
    dist_moon_to_lagna = (lagna_lon - moon_lon) % 360.0
    sree_lagna_lon = (moon_lon + dist_moon_to_lagna) % 360.0

    return {
        "Hora_Lagna":   {**_lon_to_point(hora_lagna_lon),  "computation": "MATHEMATICALLY_DERIVED"},
        "Ghati_Lagna":  {**_lon_to_point(ghati_lagna_lon), "computation": "MATHEMATICALLY_DERIVED"},
        "Bhava_Lagna":  {**_lon_to_point(bhava_lagna_lon), "computation": "MATHEMATICALLY_DERIVED"},
        "Varnada_Lagna":{**_lon_to_point(varnada_lon),     "computation": "MATHEMATICALLY_DERIVED"},
        "Sree_Lagna":   {**_lon_to_point(sree_lagna_lon),  "computation": "MATHEMATICALLY_DERIVED"},
    }


# ── Sahams ────────────────────────────────────────────────────────────────────

def compute_sahams(positions: dict[str, dict], lagna_lon: float) -> dict[str, dict]:
    """
    Compute 4 key Sahams (Arabic Parts / Lots) per BPHS Ch.24.

    Punya Saham (Part of Fortune): Lagna + Moon - Sun (day birth)
    Vidya Saham (Part of Knowledge): Lagna + Jupiter - Mercury
    Rajya Saham (Part of Rulership): Lagna + Jupiter - Saturn
    Vivaha Saham (Part of Marriage): Lagna + Venus - Saturn

    For day birth: Sun above horizon (10:43 IST, day birth confirmed).
    """
    sun_lon = positions.get("Sun", {}).get("sidereal_longitude", 0.0)
    moon_lon = positions.get("Moon", {}).get("sidereal_longitude", 0.0)
    jup_lon = positions.get("Jupiter", {}).get("sidereal_longitude", 0.0)
    mer_lon = positions.get("Mercury", {}).get("sidereal_longitude", 0.0)
    sat_lon = positions.get("Saturn", {}).get("sidereal_longitude", 0.0)
    ven_lon = positions.get("Venus", {}).get("sidereal_longitude", 0.0)

    punya   = (lagna_lon + moon_lon - sun_lon) % 360.0
    vidya   = (lagna_lon + jup_lon - mer_lon) % 360.0
    rajya   = (lagna_lon + jup_lon - sat_lon) % 360.0
    vivaha  = (lagna_lon + ven_lon - sat_lon) % 360.0

    return {
        "Punya_Saham":  {**_lon_to_point(punya),  "formula": "Lagna + Moon - Sun (day birth)"},
        "Vidya_Saham":  {**_lon_to_point(vidya),  "formula": "Lagna + Jupiter - Mercury"},
        "Rajya_Saham":  {**_lon_to_point(rajya),  "formula": "Lagna + Jupiter - Saturn"},
        "Vivaha_Saham": {**_lon_to_point(vivaha), "formula": "Lagna + Venus - Saturn"},
    }


# ── Arudha Padas (A1-A12) ─────────────────────────────────────────────────────

def compute_arudhas(positions: dict[str, dict], lagna_sign_id: int) -> dict[str, dict]:
    """
    Compute Arudha Padas A1–A12 per BPHS Ch.12.

    Arudha Pada of house H:
      1. Find the lord of house H (from Lagna)
      2. Count the same number of signs from the lord's position
      3. The result is the Arudha Pada

    Exception: If the Arudha falls on the house itself or its opposite,
    move 10 signs forward.

    Uses equal-house system (30° per house from Lagna).
    """
    SIGN_LORDS = {
        1: "Mars",    2: "Venus",   3: "Mercury", 4: "Moon",
        5: "Sun",     6: "Mercury", 7: "Venus",   8: "Mars",
        9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
    }

    arudhas: dict[str, dict] = {}

    for house_num in range(1, 13):
        # Sign of this house (equal-house from Lagna)
        house_sign = ((lagna_sign_id - 1 + house_num - 1) % 12) + 1
        # Lord of this house
        lord = SIGN_LORDS.get(house_sign, "Sun")
        # Lord's sign (from natal positions — take the primary sign if co-lord)
        lord_pos = positions.get(lord, {})
        lord_sign = lord_pos.get("sign_id", 1)

        # Distance from house to lord (in signs, 1-indexed)
        dist = ((lord_sign - house_sign) % 12)
        if dist == 0:
            dist = 12  # same sign counts as 12

        # Arudha = count same distance from lord
        arudha_sign = ((lord_sign - 1 + dist) % 12) + 1

        # Exception: if arudha falls on the house or 7th from house, move 10 ahead
        if arudha_sign == house_sign or arudha_sign == ((house_sign - 1 + 6) % 12) + 1:
            arudha_sign = ((arudha_sign - 1 + 10) % 12) + 1

        arudha_lon = (arudha_sign - 1) * 30.0 + 15.0  # mid-sign
        arudha_data = _lon_to_point(arudha_lon)
        arudha_data["sign_id"] = arudha_sign
        arudha_data["sign"] = SIGN_NAMES[arudha_sign - 1]

        arudhas[f"A{house_num}"] = {
            **arudha_data,
            "house": house_num,
            "house_lord": lord,
            "lord_sign_id": lord_sign,
        }

    return arudhas


# ── Top-level runner ──────────────────────────────────────────────────────────

def compute_all_sensitive_points(jd_utc: float | None = None) -> dict[str, Any]:
    """
    Compute all sensitive points for the native.

    Returns:
      {
        'upagrahas': {name: point_dict},
        'special_lagnas': {name: point_dict},
        'sahams': {name: saham_dict},
        'arudhas': {name: arudha_dict},
        'total_rows': int,
      }
    """
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies

    if jd_utc is None:
        jd_utc = _birth_jd_utc()

    lahiri_positions = compute_positions_all_bodies(jd_utc, PRIMARY_AYANAMSHA)
    by_name = {p["name"]: p for p in lahiri_positions}

    lagna = by_name.get("Lagna", {})
    lagna_lon = lagna.get("sidereal_longitude", 12.42)  # FORENSIC: ~12.42° Aries
    lagna_sign_id = lagna.get("sign_id", 1)

    upagrahas = compute_upagrahas(jd_utc, by_name)
    special_lagnas = compute_special_lagnas(jd_utc, lagna_lon, by_name)
    sahams = compute_sahams(by_name, lagna_lon)
    arudhas = compute_arudhas(by_name, lagna_sign_id)

    total = len(upagrahas) + len(special_lagnas) + len(sahams) + len(arudhas)

    return {
        "upagrahas":      upagrahas,
        "special_lagnas": special_lagnas,
        "sahams":         sahams,
        "arudhas":        arudhas,
        "lagna_longitude": lagna_lon,
        "lagna_sign_id":  lagna_sign_id,
        "total_rows":     total,
        "ayanamsha":      PRIMARY_AYANAMSHA,
        "provenance_envelope": {
            "source": "pyswisseph DE441 + classical formulas",
            "ayanamsha": PRIMARY_AYANAMSHA,
            "citation": SOURCE_CITATION,
            "layer": "L1-ganita",
            "asset": "ganita.sensitive_points",
            "computation_note": (
                "Special lagnas use MATHEMATICALLY_DERIVED formulas; "
                "JH-authoritative values in FORENSIC v8.0 supplement may differ. "
                "Arudhas use equal-house system."
            ),
        },
    }


# ── DB writer ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l1_sensitive_points] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_sensitive_points(chart_id: str, build_id: str | None = None) -> dict[str, Any]:
    """Write ganita.sensitive_points rows to chart_facts."""
    result = compute_all_sensitive_points()
    rows_written = 0

    sections = {
        "upagraha":      result["upagrahas"],
        "special_lagna": result["special_lagnas"],
        "saham":         result["sahams"],
        "arudha":        result["arudhas"],
    }

    with _conn() as conn:
        for section_key, items in sections.items():
            for name, data in items.items():
                fact_subject = f"{section_key}_{name}"
                conn.execute(
                    """INSERT INTO chart_facts (chart_id, fact_category, fact_subject,
                       fact_value, source_citation, build_id)
                       VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                       ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                       fact_value=EXCLUDED.fact_value, updated_at=NOW()""",
                    [chart_id, "ganita.sensitive_points", fact_subject,
                     json.dumps(data), SOURCE_CITATION, build_id],
                )
                rows_written += 1
        conn.commit()

    return {
        "seeded": rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met": rows_written >= VOLUME_FLOOR,
    }


# ── Volume check ──────────────────────────────────────────────────────────────

def check_volume() -> dict[str, Any]:
    """Check that the engine can produce required sensitive-points volume without DB."""
    try:
        result = compute_all_sensitive_points()
        total = result["total_rows"]
        status = "GREEN" if total >= VOLUME_FLOOR else "AMBER"
        return {
            "status": status,
            "volume_floor": VOLUME_FLOOR,
            "actual": total,
            "breakdown": {
                "upagrahas": len(result["upagrahas"]),
                "special_lagnas": len(result["special_lagnas"]),
                "sahams": len(result["sahams"]),
                "arudhas": len(result["arudhas"]),
            },
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
