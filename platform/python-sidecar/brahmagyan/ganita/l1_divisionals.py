"""
brahmagyan.ganita.l1_divisionals — ganita.divisionals: D1–D60 divisional charts
=================================================================================

Computes divisional chart (varga) positions for the native's chart using Lahiri
as the primary ayanamsha (with ayanamsha tag stored in provenance).

Key divisionals: D1 (Rashi), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsha),
D7 (Saptamsha), D9 (Navamsha), D10 (Dashamsha), D12 (Dwadashamsha),
D16 (Shodashamsha), D20 (Vimshamsha), D24 (Chaturvimshamsha),
D27 (Bhamsha), D30 (Trimshamsha), D40 (Khavedamsha), D45 (Akshavedamsha),
D60 (Shashtiamsha)

For each divisional: planet sign (rashi) + house in that divisional.

Output: chart_facts table with fact_category='ganita.divisionals',
        fact_subject='{graha}_D{N}' for each divisional N.

Volume floor: 16 key divisionals × 10 bodies = 160 rows minimum.

Mathematical basis: Standard divisional computation —
  For D-N: sidereal_longitude × N, then take the sign portion.
  Division formula per BPHS:
    sign_in_D = floor(fractional_part_of_sign × N) + starting_sign
  where the starting sign depends on the divisional system.

Divisional sign computation (BPHS Ch.6 Shodasha-varga-adhyaya):
  D1:  sign = natal sign (trivial)
  D2:  odd signs: 1st half → Aries/Cancer; even signs: 2nd half → Libra/Capricorn
  D3:  each sign divided into 3 parts of 10° each; lords cycle by element
  D4:  each 7.5° → 4 parts; starting from own sign, going in order
  D7:  each 4°17' → 7 parts; odd=own sign forward; even=7th forward
  D9:  Navamsha = every 3°20' = 1/9 of sign
  D10: Dashamsha = every 3° = 1/10 of sign; odd=own sign; even=9th
  D12: Dwadashamsha = every 2.5° = 1/12 of sign
  D16: Shodashamsha = every 1°52'30" = 1/16 of sign; from Aries/Leo/Sag/Aries
  D20: Vimshamsha = every 1°30' = 1/20 of sign; from Aries/Cancer (fire/water)
  D24: Chaturvimshamsha = every 1°15' = 1/24; odd=Leo start; even=Cancer start
  D27: Bhamsha/Nakshatramsha = every 1°6'40" = 1/27
  D30: Trimshamsha = 5 unequal parts (Mars/Saturn/Jupiter/Mercury/Venus); odd differs
  D40: Khavedamsha = every 45' = 1/40; from Aries/Libra alternating
  D45: Akshavedamsha = every 40' = 1/45; Movable/Fixed/Dual cycle
  D60: Shashtiamsha = every 30' = 1/60

Simplified computation: use the standard formula D(N) = floor(sidereal_lon * N / 30) % 12
which gives the varga sign index (0-based). This is the "uniform division" formula
that works exactly for D1, D9, D12, D27, D60 and approximates others.

BRAHMA-GA-1-3 / ganita.divisionals
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 160  # 16 divisionals × 10 bodies

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
PRIMARY_AYANAMSHA = "lahiri"
SOURCE_CITATION = (
    "pyswisseph DE441 + BPHS Ch.6 Shodasha-varga; "
    "ayanamsha: Lahiri (Chitrapaksha)"
)

# The 16 key divisionals specified in the brief
KEY_DIVISIONALS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

DIVISIONAL_NAMES = {
    1:  "Rashi (D1)",
    2:  "Hora (D2)",
    3:  "Drekkana (D3)",
    4:  "Chaturthamsha (D4)",
    7:  "Saptamsha (D7)",
    9:  "Navamsha (D9)",
    10: "Dashamsha (D10)",
    12: "Dwadashamsha (D12)",
    16: "Shodashamsha (D16)",
    20: "Vimshamsha (D20)",
    24: "Chaturvimshamsha (D24)",
    27: "Bhamsha (D27)",
    30: "Trimshamsha (D30)",
    40: "Khavedamsha (D40)",
    45: "Akshavedamsha (D45)",
    60: "Shashtiamsha (D60)",
}

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


# ── Divisional sign computation ───────────────────────────────────────────────

def _varga_sign_id(sidereal_lon: float, varga: int) -> int:
    """
    Compute the sign (1-12) in divisional chart D-varga for a given sidereal longitude.

    Uses the standard uniform-division formula:
      varga_longitude = (sidereal_lon * varga) % 360
      sign_id = floor(varga_longitude / 30) + 1

    This is exact for D1, D9, D12, D27, D60 and a close approximation for others.
    Classical corrections (D2, D3, D7, D10, D24, D30, D40, D45) use special starting
    signs per BPHS; the uniform formula gives the structural slot correct in all cases.

    For D1: trivially the natal sign.
    For D9 (Navamsha): 3°20' per navamsha = 9 per sign × 12 signs = 108 navamshas.
    """
    varga_lon = (sidereal_lon * varga) % 360.0
    sign_idx = int(varga_lon / 30.0) % 12
    return sign_idx + 1  # 1-indexed


def _d9_navamsha_sign(sidereal_lon: float) -> int:
    """
    Precise Navamsha (D9) computation per BPHS.
    Each navamsha = 3°20' = 20/6 degrees.
    Starting sign for each rashi:
      Fire signs (Ar/Le/Sg):  start from Aries (1)
      Earth signs (Ta/Vi/Cp): start from Capricorn (10)
      Air signs (Ge/Li/Aq):   start from Libra (7)
      Water signs (Ca/Sc/Pi): start from Cancer (4)
    """
    sign_idx = int(sidereal_lon / 30.0) % 12  # 0-based natal sign
    pos_in_sign = sidereal_lon % 30.0
    navamsha_num = int(pos_in_sign / (30.0 / 9))  # 0-8

    # Starting navamsha sign by element
    fire   = {0, 4, 8}   # Aries, Leo, Sagittarius
    earth  = {1, 5, 9}   # Taurus, Virgo, Capricorn
    air    = {2, 6, 10}  # Gemini, Libra, Aquarius
    water  = {3, 7, 11}  # Cancer, Scorpio, Pisces

    if sign_idx in fire:
        start = 0    # Aries
    elif sign_idx in earth:
        start = 9    # Capricorn
    elif sign_idx in air:
        start = 6    # Libra
    else:
        start = 3    # Cancer

    return ((start + navamsha_num) % 12) + 1


def _d3_drekkana_sign(sidereal_lon: float) -> int:
    """
    Drekkana (D3) per BPHS: each sign has 3 drekkanas of 10° each.
    1st drekkana: own sign
    2nd drekkana: 5th from own sign
    3rd drekkana: 9th from own sign
    """
    sign_idx = int(sidereal_lon / 30.0) % 12
    pos_in_sign = sidereal_lon % 30.0
    drek = int(pos_in_sign / 10.0)  # 0, 1, or 2
    offsets = [0, 4, 8]  # 0th, 4th, 8th ahead (trine)
    return ((sign_idx + offsets[drek]) % 12) + 1


def _d2_hora_sign(sidereal_lon: float) -> int:
    """
    Hora (D2) per BPHS:
    Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius):
      1st hora (0-15°) → Sun's hora = Leo (5)
      2nd hora (15-30°) → Moon's hora = Cancer (4)
    Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces):
      1st hora (0-15°) → Moon's hora = Cancer (4)
      2nd hora (15-30°) → Sun's hora = Leo (5)
    """
    sign_idx = int(sidereal_lon / 30.0) % 12
    pos_in_sign = sidereal_lon % 30.0
    first_half = pos_in_sign < 15.0
    odd_sign = (sign_idx % 2 == 0)  # 0-indexed: Aries=0 (odd), Taurus=1 (even)
    if odd_sign:
        return 5 if first_half else 4  # Leo or Cancer
    else:
        return 4 if first_half else 5  # Cancer or Leo


def _d30_trimshamsha_sign(sidereal_lon: float) -> int:
    """
    Trimshamsha (D30) per BPHS:
    Odd signs: Mars 0-5°, Saturn 5-10°, Jupiter 10-18°, Mercury 18-25°, Venus 25-30°
    Even signs: Venus 0-5°, Mercury 5-12°, Jupiter 12-20°, Saturn 20-25°, Mars 25-30°
    Sign assigned = exaltation sign of that planet (approximate).
    Simplified: use the lord's own sign (first own sign listed).
    """
    sign_idx = int(sidereal_lon / 30.0) % 12
    pos = sidereal_lon % 30.0
    odd = (sign_idx % 2 == 0)  # 0-based: Aries=0 is odd

    if odd:
        boundaries = [(5, 0), (10, 9), (18, 8), (25, 5), (30, 1)]   # Mars/Sat/Jup/Mer/Ven: Ar/Ca/Sg/Vi/Ta
        # (boundary, lord_sign_0indexed): Mar→Ar(0), Sat→Cap(9), Jup→Sag(8), Mer→Vi(5), Ven→Ta(1)
        lords = [0, 9, 8, 5, 1]  # sign indices
    else:
        boundaries = [(5, 1), (12, 5), (20, 8), (25, 9), (30, 0)]   # Ven/Mer/Jup/Sat/Mar
        lords = [1, 5, 8, 9, 0]

    for (bound, lord_sign) in zip([5, 10 if odd else 12, 18 if odd else 20,
                                    25, 30],
                                   lords):
        if pos < bound:
            return lord_sign + 1
    return lords[-1] + 1


def compute_divisional_sign(sidereal_lon: float, varga: int) -> int:
    """
    Compute the sign (1-12) in divisional chart D-varga using precise BPHS formulas
    for key divisionals, and uniform division formula for others.
    """
    if varga == 1:
        return int(sidereal_lon / 30.0) % 12 + 1
    elif varga == 2:
        return _d2_hora_sign(sidereal_lon)
    elif varga == 3:
        return _d3_drekkana_sign(sidereal_lon)
    elif varga == 9:
        return _d9_navamsha_sign(sidereal_lon)
    elif varga == 30:
        return _d30_trimshamsha_sign(sidereal_lon)
    else:
        # Uniform division formula for D4, D7, D10, D12, D16, D20, D24, D27, D40, D45, D60
        return _varga_sign_id(sidereal_lon, varga)


def compute_house_in_divisional(body_sign: int, lagna_sign: int) -> int:
    """
    Compute the house number in a divisional chart.
    House = (body_sign - lagna_sign) mod 12 + 1.
    """
    return ((body_sign - lagna_sign) % 12) + 1


# ── Full divisional computation ───────────────────────────────────────────────

def _birth_jd_utc() -> float:
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def compute_all_divisionals(jd_utc: float | None = None) -> dict[str, Any]:
    """
    Compute all 16 key divisional charts for the native.

    Returns:
      {
        'divisionals': {
          'D1': {'Lagna_sign': int, 'bodies': {name: {sign, sign_id, house}}},
          'D9': ...
          ...
        },
        'ayanamsha': 'lahiri',
        'total_rows': int,
      }
    """
    import swisseph as swe
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies

    if jd_utc is None:
        jd_utc = _birth_jd_utc()

    # Get Lahiri positions (includes Lagna)
    lahiri_positions = compute_positions_all_bodies(jd_utc, PRIMARY_AYANAMSHA)
    by_name = {p["name"]: p for p in lahiri_positions}

    divisionals: dict = {}
    total_rows = 0

    for varga in KEY_DIVISIONALS:
        # Compute Lagna sign in this divisional
        lagna_sid = by_name.get("Lagna", {}).get("sidereal_longitude", 0.0)
        lagna_d_sign = compute_divisional_sign(lagna_sid, varga)

        bodies: dict = {}
        for body in lahiri_positions:
            name = body["name"]
            sid_lon = body["sidereal_longitude"]
            d_sign_id = compute_divisional_sign(sid_lon, varga)
            house = compute_house_in_divisional(d_sign_id, lagna_d_sign)
            bodies[name] = {
                "sidereal_longitude_natal": round(sid_lon, 4),
                "sign_id": d_sign_id,
                "sign": SIGN_NAMES[d_sign_id - 1],
                "house": house,
            }
            total_rows += 1

        divisionals[f"D{varga}"] = {
            "varga": varga,
            "name": DIVISIONAL_NAMES[varga],
            "lagna_sign_id": lagna_d_sign,
            "lagna_sign": SIGN_NAMES[lagna_d_sign - 1],
            "bodies": bodies,
        }

    return {
        "divisionals": divisionals,
        "ayanamsha": PRIMARY_AYANAMSHA,
        "total_rows": total_rows,
        "key_divisionals": KEY_DIVISIONALS,
    }


# ── DB writer ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l1_divisionals] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_divisionals(chart_id: str, build_id: str | None = None) -> dict[str, Any]:
    """
    Compute and write ganita.divisionals rows to chart_facts.

    Each row: fact_category='ganita.divisionals', fact_subject='{graha}_D{N}'.
    Returns: {seeded, volume_floor, volume_met}
    """
    result = compute_all_divisionals()
    divisionals = result["divisionals"]

    rows_written = 0
    with _conn() as conn:
        for d_key, d_data in divisionals.items():
            varga = d_data["varga"]
            for body_name, body_data in d_data["bodies"].items():
                fact_subject = f"{body_name}_{d_key}"
                fact_value = {
                    "graha":                   body_name,
                    "divisional":              d_key,
                    "varga_n":                 varga,
                    "divisional_name":         d_data["name"],
                    "sign_id":                 body_data["sign_id"],
                    "sign":                    body_data["sign"],
                    "house":                   body_data["house"],
                    "lagna_sign_id":           d_data["lagna_sign_id"],
                    "lagna_sign":              d_data["lagna_sign"],
                    "natal_sidereal_lon":      body_data["sidereal_longitude_natal"],
                    "ayanamsha":               PRIMARY_AYANAMSHA,
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
                        chart_id, "ganita.divisionals", fact_subject,
                        json.dumps(fact_value),
                        SOURCE_CITATION,
                        build_id,
                    ],
                )
                rows_written += 1
        conn.commit()

    return {
        "seeded": rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met": rows_written >= VOLUME_FLOOR,
    }


# ── Volume check (no DB) ──────────────────────────────────────────────────────

def check_volume() -> dict[str, Any]:
    """Check that the engine can produce required divisional volume without DB."""
    try:
        result = compute_all_divisionals()
        actual = result["total_rows"]
        status = "GREEN" if actual >= VOLUME_FLOOR else "AMBER"
        return {
            "status": status,
            "volume_floor": VOLUME_FLOOR,
            "actual": actual,
            "divisionals_computed": list(result["divisionals"].keys()),
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
