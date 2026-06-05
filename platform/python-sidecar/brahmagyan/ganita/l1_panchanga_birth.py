"""
brahmagyan.ganita.l1_panchanga_birth — ganita.panchanga: birth-moment panchang
=================================================================================

Birth-moment Panchanga for the native (1984-02-05, 10:43 IST, Bhubaneswar):
  - Tithi (lunar day): Shukla / Krishna + number + lord
  - Vara (weekday): day of week + ruling planet
  - Nakshatra: Moon's nakshatra at birth + lord + pada
  - Yoga: one of 27 yogas (Sun lon + Moon lon computed)
  - Karana: one of 11 karanas (half-tithi)
  - Lagna at birth (Ascendant sign)

Also provides:
  - facts_store health check: verifies chart_facts is the primary store
  - forensic_render: reconstruct FORENSIC v8.0 view from chart_facts positions

FORENSIC v8.0 grounding checks (from FORENSIC_ASTROLOGICAL_DATA_v8_0.md):
  - Tithi: expected Shukla Tritiya (3rd lunar day, waxing)
  - Vara: Ravivara (Sunday) ✓ (1984-02-05 confirmed Sunday)
  - Nakshatra: Purva Bhadrapada (Moon) ✓ (structural anchor)
  - Yoga: Shiva yoga (computed from Sun+Moon longitude)
  - Karana: Garaja (half of Shukla Tritiya)
  - Lagna: Aries (Mesha) ✓ (structural anchor)

BRAHMA-GA-1-7 / ganita.panchanga
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
PRIMARY_AYANAMSHA = "lahiri"
SOURCE_CITATION = (
    "BPHS Ch.2 Panchanga + Jyotish tradition; pyswisseph DE441; "
    "ayanamsha: Lahiri; FORENSIC grounding: FORENSIC_ASTROLOGICAL_DATA_v8_0.md"
)

# Tithi names (1-30)
TITHI_NAMES = [
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

TITHI_LORDS = [
    "Moon", "Sun", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Moon", "Sun", "Mars",
    "Mercury", "Jupiter", "Venus", "Saturn", "Moon",  # Full Moon
    "Moon", "Sun", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Moon", "Sun", "Mars",
    "Mercury", "Jupiter", "Venus", "Saturn", "Sun",  # Amavasya
]

# Yoga names (27 yogas)
YOGA_NAMES = [
    "Vishkambha", "Preeti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

# Karana names (11 karanas: 4 fixed + 7 movable)
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja",
    "Vanija", "Vishti",  # 7 movable (repeating)
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",  # 4 fixed
]

# Weekday names (0=Sunday per Jyotish tradition)
VARA_NAMES = ["Ravivara", "Somavara", "Mangalavara", "Budhavara",
               "Guruvara", "Shukravara", "Shanivara"]
VARA_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_LORDS = (
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury "
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury "
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury"
).split()

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# FORENSIC v8.0 expected values for acceptance check
FORENSIC_PANCHANGA = {
    "tithi_name": "Tritiya",    # Shukla Tritiya
    "tithi_paksha": "Shukla",
    "vara": "Ravivara",
    "nakshatra": "Purva Bhadrapada",
    "yoga": "Shiva",
    "karana": "Garaja",
    "lagna_sign": "Aries",
}


# ── JD helper ─────────────────────────────────────────────────────────────────

def _birth_jd_utc() -> float:
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


# ── Panchanga computation ─────────────────────────────────────────────────────

def compute_birth_panchanga(jd_utc: float | None = None) -> dict[str, Any]:
    """
    Compute the 5 limbs of the Panchanga for the native's birth moment.

    Returns dict with: tithi, vara, nakshatra, yoga, karana, lagna.
    """
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies
    import swisseph as swe

    if jd_utc is None:
        jd_utc = _birth_jd_utc()

    lahiri_positions = compute_positions_all_bodies(jd_utc, PRIMARY_AYANAMSHA)
    by_name = {p["name"]: p for p in lahiri_positions}

    sun_lon = by_name["Sun"]["sidereal_longitude"]
    moon_lon = by_name["Moon"]["sidereal_longitude"]
    lagna = by_name.get("Lagna", {})

    # ── Tithi ─────────────────────────────────────────────────────────────────
    # Tithi = (Moon - Sun) / 12° → integer [0, 29]
    tithi_lon = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(tithi_lon / 12.0)  # 0-29
    tithi_num = tithi_idx + 1  # 1-30
    tithi_name = TITHI_NAMES[tithi_idx]
    tithi_paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    tithi_lord = TITHI_LORDS[tithi_idx]

    # ── Vara ──────────────────────────────────────────────────────────────────
    # 1984-02-05 is Sunday → Ravivara (index 0)
    birth_dt = datetime.fromisoformat(NATIVE_BIRTH_IST)
    # Python weekday: Mon=0, Sun=6; Jyotish: Sun=0, Mon=1, ...
    py_weekday = birth_dt.weekday()  # 6 = Sunday
    jyotish_weekday = (py_weekday + 1) % 7  # Sun=0
    vara_name = VARA_NAMES[jyotish_weekday]
    vara_lord = VARA_LORDS[jyotish_weekday]

    # ── Nakshatra ─────────────────────────────────────────────────────────────
    nak_span = 360.0 / 27
    nak_idx = int(moon_lon / nak_span)
    nak_name = NAKSHATRA_NAMES[nak_idx]
    nak_lord = NAKSHATRA_LORDS[nak_idx]
    nak_pada = int((moon_lon % nak_span) / (nak_span / 4)) + 1

    # ── Yoga ──────────────────────────────────────────────────────────────────
    # Yoga = floor((Sun + Moon) / (360/27))
    yoga_lon = (sun_lon + moon_lon) % 360.0
    yoga_idx = int(yoga_lon / (360.0 / 27))
    yoga_name = YOGA_NAMES[yoga_idx]

    # ── Karana ────────────────────────────────────────────────────────────────
    # Karana = half-tithi = floor((Moon - Sun) / 6°)
    karana_n = int(tithi_lon / 6.0)  # 0-59
    # Fixed karanas:
    # 0 = Kimstughna (1st half of Prathama Shukla)
    # 58 = Chatushpada (1st half of Amavasya)
    # 59 = Naga (2nd half of Amavasya)
    # 57 = Shakuni (1st half of Chaturdashi Krishna? — actually 2nd half of Krishna Chaturdashi)
    if karana_n == 0:
        karana_name = "Kimstughna"
    elif 57 <= karana_n <= 59:
        fixed = {57: "Shakuni", 58: "Chatushpada", 59: "Naga"}
        karana_name = fixed[karana_n]
    else:
        movable_idx = (karana_n - 1) % 7
        karana_name = KARANA_NAMES[movable_idx]

    # ── Lagna ─────────────────────────────────────────────────────────────────
    lagna_sign_id = lagna.get("sign_id", 1)
    lagna_sign = lagna.get("sign", SIGN_NAMES[lagna_sign_id - 1])
    lagna_lon = lagna.get("sidereal_longitude", 0.0)

    panchanga = {
        "tithi": {
            "name": tithi_name,
            "number": tithi_num,
            "paksha": tithi_paksha,
            "lord": tithi_lord,
            "longitude_distance": round(tithi_lon, 4),
        },
        "vara": {
            "name": vara_name,
            "lord": vara_lord,
            "weekday_index": jyotish_weekday,
        },
        "nakshatra": {
            "name": nak_name,
            "lord": nak_lord,
            "pada": nak_pada,
            "moon_longitude": round(moon_lon, 4),
        },
        "yoga": {
            "name": yoga_name,
            "index": yoga_idx + 1,
            "sun_moon_sum": round(yoga_lon, 4),
        },
        "karana": {
            "name": karana_name,
            "number": karana_n,
        },
        "lagna": {
            "sign_id": lagna_sign_id,
            "sign": lagna_sign,
            "longitude": round(lagna_lon, 4),
        },
        "source_citation": SOURCE_CITATION,
        "ayanamsha": PRIMARY_AYANAMSHA,
        "birth_ist": NATIVE_BIRTH_IST,
        "provenance_envelope": {
            "source": "pyswisseph DE441",
            "ayanamsha": PRIMARY_AYANAMSHA,
            "layer": "L1-ganita",
            "asset": "ganita.panchanga",
        },
    }

    # ── FORENSIC acceptance check ─────────────────────────────────────────────
    checks = []
    checks.append({
        "id": "P1", "desc": "Tithi = Tritiya",
        "passed": tithi_name == FORENSIC_PANCHANGA["tithi_name"],
        "value": tithi_name,
    })
    checks.append({
        "id": "P2", "desc": "Paksha = Shukla",
        "passed": tithi_paksha == FORENSIC_PANCHANGA["tithi_paksha"],
        "value": tithi_paksha,
    })
    checks.append({
        "id": "P3", "desc": "Vara = Ravivara (Sunday)",
        "passed": vara_name == FORENSIC_PANCHANGA["vara"],
        "value": vara_name,
    })
    checks.append({
        "id": "P4", "desc": "Nakshatra = Purva Bhadrapada",
        "passed": nak_name == FORENSIC_PANCHANGA["nakshatra"],
        "value": nak_name,
    })
    checks.append({
        "id": "P5", "desc": "Yoga = Shiva",
        "passed": yoga_name == FORENSIC_PANCHANGA["yoga"],
        "value": yoga_name,
    })
    checks.append({
        "id": "P6", "desc": "Karana = Garaja",
        "passed": karana_name == FORENSIC_PANCHANGA["karana"],
        "value": karana_name,
    })
    checks.append({
        "id": "P7", "desc": "Lagna = Aries (Mesha)",
        "passed": lagna_sign == FORENSIC_PANCHANGA["lagna_sign"],
        "value": lagna_sign,
    })

    gate_passed = all(c["passed"] for c in checks)
    panchanga["forensic_checks"] = checks
    panchanga["forensic_gate_passed"] = gate_passed

    return panchanga


# ── facts_store health check ──────────────────────────────────────────────────

def check_facts_store_schema() -> dict[str, Any]:
    """
    Verify that chart_facts is the primary store and has the correct schema.
    Checks (without live DB): verifies the schema contract is documented.

    With DB: checks that the chart_facts table has the expected columns.
    """
    expected_columns = [
        "chart_id", "fact_category", "fact_subject", "fact_value",
        "source_citation", "build_id", "created_at", "updated_at",
    ]
    try:
        import psycopg
        db_url = next(
            (v for k in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL")
             if (v := os.environ.get(k, ""))),
            None,
        )
        if not db_url:
            return {
                "status": "AMBER",
                "note": "DATABASE_URL not set — schema contract documented only",
                "expected_columns": expected_columns,
                "primary_store": "chart_facts",
                "source_citation": SOURCE_CITATION,
            }
        with psycopg.connect(db_url) as conn:
            row = conn.execute(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_name = 'chart_facts' ORDER BY ordinal_position""",
            ).fetchall()
            actual_cols = [r[0] for r in row]
            missing = [c for c in expected_columns if c not in actual_cols]
            return {
                "status": "GREEN" if not missing else "AMBER",
                "actual_columns": actual_cols,
                "expected_columns": expected_columns,
                "missing": missing,
                "primary_store": "chart_facts",
                "source_citation": SOURCE_CITATION,
            }
    except Exception as exc:
        return {
            "status": "AMBER",
            "note": f"DB check failed: {exc} — schema documented only",
            "expected_columns": expected_columns,
            "primary_store": "chart_facts",
            "source_citation": SOURCE_CITATION,
        }


# ── forensic_render ───────────────────────────────────────────────────────────

def forensic_render() -> dict[str, Any]:
    """
    Reconstruct a FORENSIC v8.0 compatible view from computed chart data.

    Verifies key data points:
      - Sun in Capricorn (Shravana) under Lahiri
      - Moon in Purva Bhadrapada under Lahiri
      - Lagna in Aries (Mesha) under Lahiri
      - Birth Panchanga (Tithi, Vara, Nakshatra, Yoga, Karana)

    Returns a structured dict compatible with FORENSIC v8.0 format
    and an acceptance gate result.
    """
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies, _birth_jd_utc
    jd = _birth_jd_utc()
    lahiri_positions = compute_positions_all_bodies(jd, PRIMARY_AYANAMSHA)
    by_name = {p["name"]: p for p in lahiri_positions}

    panchanga = compute_birth_panchanga(jd)

    # Build FORENSIC-format planet table
    planet_table = []
    for body in lahiri_positions:
        planet_table.append({
            "graha":          body["name"],
            "sign_id":        body["sign_id"],
            "sign":           body["sign"],
            "longitude_deg":  body["sidereal_longitude"],
            "nakshatra":      body["nakshatra"],
            "nakshatra_id":   body["nakshatra_id"],
            "pada":           body["nakshatra_pada"],
            "house":          body.get("house", 0),
            "is_retrograde":  body.get("is_retrograde", False),
            "ayanamsha":      PRIMARY_AYANAMSHA,
        })

    # Acceptance gate
    checks = []
    sun = by_name.get("Sun", {})
    checks.append({
        "id": "FR1", "desc": "Sun in Capricorn (sign_id=10)",
        "passed": sun.get("sign_id") == 10,
        "value": sun.get("sign"),
    })
    moon = by_name.get("Moon", {})
    checks.append({
        "id": "FR2", "desc": "Moon in Purva Bhadrapada (nak_id=25)",
        "passed": moon.get("nakshatra_id") == 25,
        "value": moon.get("nakshatra"),
    })
    lagna = by_name.get("Lagna", {})
    checks.append({
        "id": "FR3", "desc": "Lagna in Aries (sign_id=1)",
        "passed": lagna.get("sign_id") == 1,
        "value": lagna.get("sign"),
    })
    checks.append({
        "id": "FR4", "desc": "Vara = Ravivara (Sunday)",
        "passed": panchanga["vara"]["name"] == "Ravivara",
        "value": panchanga["vara"]["name"],
    })
    checks.append({
        "id": "FR5", "desc": "Nakshatra = Purva Bhadrapada",
        "passed": panchanga["nakshatra"]["name"] == "Purva Bhadrapada",
        "value": panchanga["nakshatra"]["name"],
    })

    gate_passed = all(c["passed"] for c in checks)
    return {
        "forensic_render_version": "BRAHMA-L1-v1.0",
        "native": {
            "birth_ist": NATIVE_BIRTH_IST,
            "lat": NATIVE_LAT,
            "lon": NATIVE_LON,
            "name": "Abhisek Mohanty",
        },
        "planet_table": planet_table,
        "panchanga": panchanga,
        "acceptance_gate": {
            "passed": gate_passed,
            "checks": checks,
        },
        "source_citation": SOURCE_CITATION,
        "ayanamsha": PRIMARY_AYANAMSHA,
    }


# ── DB writer ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l1_panchanga] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_panchanga(chart_id: str, build_id: str | None = None) -> dict[str, Any]:
    """Write ganita.panchanga row to chart_facts."""
    panchanga = compute_birth_panchanga()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO chart_facts (chart_id, fact_category, fact_subject,
               fact_value, source_citation, build_id)
               VALUES (%s, %s, %s, %s::jsonb, %s, %s)
               ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
               fact_value=EXCLUDED.fact_value, updated_at=NOW()""",
            [chart_id, "ganita.panchanga", "birth_panchanga",
             json.dumps(panchanga), SOURCE_CITATION, build_id],
        )
        conn.commit()
    return {"seeded": 1, "forensic_gate_passed": panchanga["forensic_gate_passed"]}


# ── Volume / health check ────────────────────────────────────────────────────

def check_volume() -> dict[str, Any]:
    """Health check for panchanga + facts_store + forensic_render."""
    panchanga = compute_birth_panchanga()
    render = forensic_render()
    facts_store = check_facts_store_schema()

    gate_ok = panchanga["forensic_gate_passed"] and render["acceptance_gate"]["passed"]
    return {
        "status": "GREEN" if gate_ok else "AMBER",
        "panchanga_forensic_gate": panchanga["forensic_gate_passed"],
        "forensic_render_gate": render["acceptance_gate"]["passed"],
        "facts_store_status": facts_store["status"],
        "panchanga_checks": panchanga["forensic_checks"],
        "render_checks": render["acceptance_gate"]["checks"],
        "source_citation": SOURCE_CITATION,
    }
