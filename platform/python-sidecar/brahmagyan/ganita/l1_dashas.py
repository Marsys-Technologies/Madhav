"""
brahmagyan.ganita.l1_dashas — ganita.dashas: Vimshottari to Sukshma + 3 additional systems
============================================================================================

Dasha timeline to Sukshma (4th level) depth for Vimshottari system, plus:
  - Yogini dasha (8-lord system, MD only — Sukshma depth would be ~4096 rows)
  - Kalachakra dasha (27-nakshatra navamsha-based, MD only)
  - Ashtottari dasha (108-year cycle, MD only)

Volume computation:
  Vimshottari to Sukshma (4 levels):
    MD: 9 mahadashas (covering lifetime)
    AD: 9 antardashas per MD → 81
    PD: 9 pratyantardashas per AD → 729
    Sukshma: 9 sukshmadasha per PD → 6,561
    Total Vimshottari: 9 + 81 + 729 + 6,561 = 7,380 rows

  Additional systems (MD only, one level):
    Yogini MD: 8 lords × 3 cycles ≈ 24 rows
    Kalachakra MD: nakshatra-based, ~12-20 rows per lifetime
    Ashtottari MD: 8 lords, ~8 rows per lifetime
    Total additional: ~50-60 rows

Volume floor: 6,561 (Vimshottari Sukshma minimum — the primary depth target)

BRAHMA-GA-1-4 / ganita.dashas
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 6500  # Vimshottari Sukshma depth: ~9 MD × 9 AD × 9 PD × 9 SK per cycle
# Note: actual count is ~7,380 for a full 120-year cycle from birth;
# floor is set at 6500 to allow for the partial first MD and any rounding.

NATIVE_BIRTH_IST = "1984-02-05T10:43:00"
PRIMARY_AYANAMSHA = "lahiri"
SOURCE_CITATION = "pyswisseph DE441; Vimshottari mathematical + Yogini + Kalachakra + Ashtottari"

# ── Vimshottari constants ─────────────────────────────────────────────────────

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_TOTAL_YEARS = sum(DASHA_YEARS.values())  # 120

NAKSHATRA_LORDS = (
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury "
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury "
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury"
).split()

# ── Yogini dasha constants ────────────────────────────────────────────────────
# 8-lord Yogini dasha with 1–8 year periods (total 36 years per cycle)
YOGINI_SEQUENCE = [
    ("Mangala",   "Moon",    1),
    ("Pingala",   "Sun",     2),
    ("Dhanya",    "Jupiter", 3),
    ("Bhramari",  "Mars",    4),
    ("Bhadrika",  "Mercury", 5),
    ("Ulka",      "Saturn",  6),
    ("Siddha",    "Venus",   7),
    ("Sankata",   "Rahu",    8),
]
YOGINI_TOTAL_YEARS = sum(y for _, _, y in YOGINI_SEQUENCE)  # 36

# ── Ashtottari constants ──────────────────────────────────────────────────────
# 108-year cycle, 8 lords
ASHTOTTARI_SEQUENCE = [
    ("Sun",     6),
    ("Moon",    15),
    ("Mars",    8),
    ("Mercury", 17),
    ("Saturn",  10),
    ("Jupiter", 19),
    ("Rahu",    12),
    ("Venus",   21),
]
ASHTOTTARI_TOTAL_YEARS = sum(y for _, y in ASHTOTTARI_SEQUENCE)  # 108


# ── JD helpers ────────────────────────────────────────────────────────────────

def _birth_jd_utc() -> float:
    import swisseph as swe
    dt_ist = datetime.fromisoformat(NATIVE_BIRTH_IST)
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _jd_to_date(jd: float) -> date:
    import swisseph as swe
    y, m, d, _ = swe.revjul(jd)
    return date(int(y), int(m), int(d))


def _years_to_days(years: float) -> float:
    return years * 365.25


# ── Vimshottari Sukshma (4 levels) ───────────────────────────────────────────

def compute_vimshottari_sukshma(
    moon_sidereal_lon: float,
    birth_jd: float,
    birth_date_obj: date | None = None,
    max_age_years: float = 90.0,
) -> list[dict[str, Any]]:
    """
    Compute Vimshottari dasha to Sukshma (4th level) depth.

    Returns a flat list of dasha rows, each with:
      level (1=MD, 2=AD, 3=PD, 4=Sukshma), lord, parent_lord,
      start_date, end_date, years.

    Limits to native's lifetime (birth to birth + max_age_years).
    """
    nak_span = 360.0 / 27
    nak_idx = int(moon_sidereal_lon / nak_span)
    nak_lord = NAKSHATRA_LORDS[nak_idx]
    nak_start = nak_idx * nak_span
    nak_progress = (moon_sidereal_lon - nak_start) / nak_span
    balance_years = DASHA_YEARS[nak_lord] * (1.0 - nak_progress)

    max_jd = birth_jd + _years_to_days(max_age_years)
    seq_start = DASHA_SEQUENCE.index(nak_lord)

    rows: list[dict] = []
    current_jd = birth_jd

    for cycle in range(4):  # 4 cycles × 120 years = 480 years, more than enough
        for i in range(9):
            seq_i = (seq_start + i) % 9
            md_lord = DASHA_SEQUENCE[seq_i]
            if cycle == 0 and i == 0:
                md_years = balance_years
            else:
                md_years = DASHA_YEARS[md_lord]

            md_days = _years_to_days(md_years)
            md_start_jd = current_jd
            md_end_jd = current_jd + md_days

            if md_start_jd >= max_jd:
                break

            md_row = {
                "level": 1,
                "dasha_system": "vimshottari",
                "lord": md_lord,
                "parent_lord": None,
                "grandparent_lord": None,
                "great_grandparent_lord": None,
                "start_date": _jd_to_date(md_start_jd).isoformat(),
                "end_date": _jd_to_date(md_end_jd).isoformat(),
                "years": round(md_years, 6),
            }
            rows.append(md_row)

            # AD within MD
            ad_seq_start = DASHA_SEQUENCE.index(md_lord)
            ad_start_jd = md_start_jd
            for j in range(9):
                ad_lord = DASHA_SEQUENCE[(ad_seq_start + j) % 9]
                ad_years = (DASHA_YEARS[ad_lord] / DASHA_TOTAL_YEARS) * md_years
                ad_days = _years_to_days(ad_years)
                ad_end_jd = ad_start_jd + ad_days

                ad_row = {
                    "level": 2,
                    "dasha_system": "vimshottari",
                    "lord": ad_lord,
                    "parent_lord": md_lord,
                    "grandparent_lord": None,
                    "great_grandparent_lord": None,
                    "start_date": _jd_to_date(ad_start_jd).isoformat(),
                    "end_date": _jd_to_date(ad_end_jd).isoformat(),
                    "years": round(ad_years, 6),
                }
                rows.append(ad_row)

                # PD within AD
                pd_seq_start = DASHA_SEQUENCE.index(ad_lord)
                pd_start_jd = ad_start_jd
                for k in range(9):
                    pd_lord = DASHA_SEQUENCE[(pd_seq_start + k) % 9]
                    pd_years = (DASHA_YEARS[pd_lord] / DASHA_TOTAL_YEARS) * ad_years
                    pd_days = _years_to_days(pd_years)
                    pd_end_jd = pd_start_jd + pd_days

                    pd_row = {
                        "level": 3,
                        "dasha_system": "vimshottari",
                        "lord": pd_lord,
                        "parent_lord": ad_lord,
                        "grandparent_lord": md_lord,
                        "great_grandparent_lord": None,
                        "start_date": _jd_to_date(pd_start_jd).isoformat(),
                        "end_date": _jd_to_date(pd_end_jd).isoformat(),
                        "years": round(pd_years, 6),
                    }
                    rows.append(pd_row)

                    # Sukshma within PD
                    sk_seq_start = DASHA_SEQUENCE.index(pd_lord)
                    sk_start_jd = pd_start_jd
                    for m in range(9):
                        sk_lord = DASHA_SEQUENCE[(sk_seq_start + m) % 9]
                        sk_years = (DASHA_YEARS[sk_lord] / DASHA_TOTAL_YEARS) * pd_years
                        sk_days = _years_to_days(sk_years)
                        sk_end_jd = sk_start_jd + sk_days
                        rows.append({
                            "level": 4,
                            "dasha_system": "vimshottari",
                            "lord": sk_lord,
                            "parent_lord": pd_lord,
                            "grandparent_lord": ad_lord,
                            "great_grandparent_lord": md_lord,
                            "start_date": _jd_to_date(sk_start_jd).isoformat(),
                            "end_date": _jd_to_date(sk_end_jd).isoformat(),
                            "years": round(sk_years, 6),
                        })
                        sk_start_jd = sk_end_jd

                    pd_start_jd = pd_end_jd

                ad_start_jd = ad_end_jd

            current_jd = md_end_jd
            if current_jd >= max_jd:
                break

        if current_jd >= max_jd:
            break

    return rows


# ── Yogini dasha (MD only) ────────────────────────────────────────────────────

def compute_yogini(moon_sidereal_lon: float, birth_jd: float,
                   max_age_years: float = 90.0) -> list[dict[str, Any]]:
    """
    Compute Yogini dasha (MD level only).

    Starting lord: based on Moon's nakshatra index.
    Formula: nak_idx % 8 → yogini index.
    """
    nak_span = 360.0 / 27
    nak_idx = int(moon_sidereal_lon / nak_span)
    yogini_start = nak_idx % 8

    nak_progress = (moon_sidereal_lon % nak_span) / nak_span
    starting_yogini = YOGINI_SEQUENCE[yogini_start]
    balance_years = starting_yogini[2] * (1.0 - nak_progress)

    max_jd = birth_jd + _years_to_days(max_age_years)
    current_jd = birth_jd
    rows: list[dict] = []

    for cycle in range(5):
        for i in range(8):
            idx = (yogini_start + i) % 8
            name, planet, years = YOGINI_SEQUENCE[idx]
            if cycle == 0 and i == 0:
                actual_years = balance_years
            else:
                actual_years = float(years)

            if current_jd >= max_jd:
                break

            rows.append({
                "level": 1,
                "dasha_system": "yogini",
                "lord": name,
                "planet_lord": planet,
                "parent_lord": None,
                "grandparent_lord": None,
                "great_grandparent_lord": None,
                "start_date": _jd_to_date(current_jd).isoformat(),
                "end_date": _jd_to_date(current_jd + _years_to_days(actual_years)).isoformat(),
                "years": round(actual_years, 6),
            })
            current_jd += _years_to_days(actual_years)

        if current_jd >= max_jd:
            break

    return rows


# ── Kalachakra dasha (MD only, simplified) ────────────────────────────────────

def compute_kalachakra(moon_sidereal_lon: float, birth_jd: float,
                       max_age_years: float = 90.0) -> list[dict[str, Any]]:
    """
    Compute Kalachakra dasha (MD level only, simplified).

    The Kalachakra dasha is based on the Moon's navamsha position.
    Full Kalachakra requires the 3 × 3 navamsha grid (deha/jeeva cycles).
    Simplified version: 9 navamshas per sign × 12 signs = 108 navamshas,
    each corresponding to a dasha period.

    Navamsha order determines dasha sequence:
    Savya (forward) navamshas: Aries-Gemini, Cancer-Virgo, Libra-Sag, Capricorn-Pisces alternating.
    Apasvya (reverse) navamshas: Taurus, Leo, Scorpio, Aquarius.

    Simplified Kalachakra periods (years) by navamsha group:
    Uses the standard 9-lord assignment with varying year counts.
    """
    # Simplified Kalachakra: compute Moon's navamsha (D9 position)
    nak_span = 360.0 / 27
    nak_idx = int(moon_sidereal_lon / nak_span)

    # Kalachakra period assignment based on nakshatra grouping
    # Nakshatras 1-9: 1st krama; 10-18: 2nd; 19-27: 3rd
    krama = nak_idx % 9

    # Kalachakra years for each nakshatra in order (simplified)
    KALACHAKRA_YEARS = [7, 16, 9, 21, 5, 9, 14, 7, 12]  # Ketu,Ve,Su,Mo,Ma,Ra,Ju,Sa,Me adapted
    KALACHAKRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

    max_jd = birth_jd + _years_to_days(max_age_years)
    current_jd = birth_jd
    rows: list[dict] = []

    # Balance of first period
    nak_progress = (moon_sidereal_lon % nak_span) / nak_span
    balance_years = KALACHAKRA_YEARS[krama] * (1.0 - nak_progress)

    for cycle in range(5):
        for i in range(9):
            idx = (krama + i) % 9
            lord = KALACHAKRA_LORDS[idx]
            if cycle == 0 and i == 0:
                years = balance_years
            else:
                years = float(KALACHAKRA_YEARS[idx])

            if current_jd >= max_jd:
                break

            rows.append({
                "level": 1,
                "dasha_system": "kalachakra",
                "lord": lord,
                "parent_lord": None,
                "grandparent_lord": None,
                "great_grandparent_lord": None,
                "start_date": _jd_to_date(current_jd).isoformat(),
                "end_date": _jd_to_date(current_jd + _years_to_days(years)).isoformat(),
                "years": round(years, 6),
            })
            current_jd += _years_to_days(years)

        if current_jd >= max_jd:
            break

    return rows


# ── Ashtottari dasha (MD only) ────────────────────────────────────────────────

def compute_ashtottari(moon_sidereal_lon: float, birth_jd: float,
                       max_age_years: float = 90.0) -> list[dict[str, Any]]:
    """
    Compute Ashtottari dasha (MD level only, 108-year cycle).

    Applicable when: Rahu is in 1, 3, 4, 5, 7, 9 from Lagna OR
    the native has a Rahu in angles. Computed unconditionally here
    (provenance marks it as conditional).

    Starting lord based on Moon's nakshatra.
    """
    nak_span = 360.0 / 27
    nak_idx = int(moon_sidereal_lon / nak_span)

    # Ashtottari nakshatra-to-lord mapping (repeating cycle of 8 lords)
    ASHTO_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"]
    start_idx = nak_idx % 8

    nak_progress = (moon_sidereal_lon % nak_span) / nak_span
    start_lord, start_years = ASHTO_LORDS[start_idx], ASHTOTTARI_SEQUENCE[start_idx][1]
    balance_years = start_years * (1.0 - nak_progress)

    max_jd = birth_jd + _years_to_days(max_age_years)
    current_jd = birth_jd
    rows: list[dict] = []

    for cycle in range(5):
        for i in range(8):
            idx = (start_idx + i) % 8
            lord = ASHTO_LORDS[idx]
            years = ASHTOTTARI_SEQUENCE[idx][1]
            if cycle == 0 and i == 0:
                actual_years = balance_years
            else:
                actual_years = float(years)

            if current_jd >= max_jd:
                break

            rows.append({
                "level": 1,
                "dasha_system": "ashtottari",
                "lord": lord,
                "parent_lord": None,
                "grandparent_lord": None,
                "great_grandparent_lord": None,
                "start_date": _jd_to_date(current_jd).isoformat(),
                "end_date": _jd_to_date(current_jd + _years_to_days(actual_years)).isoformat(),
                "years": round(actual_years, 6),
            })
            current_jd += _years_to_days(actual_years)

        if current_jd >= max_jd:
            break

    return rows


# ── Top-level dashas runner ───────────────────────────────────────────────────

def compute_all_dashas(jd_utc: float | None = None) -> dict[str, Any]:
    """
    Compute all 4 dasha systems for the native.

    Returns:
      {
        'vimshottari': list[row_dict],
        'yogini': list[row_dict],
        'kalachakra': list[row_dict],
        'ashtottari': list[row_dict],
        'moon_nakshatra': str,
        'moon_nakshatra_lord': str,
        'total_rows': int,
      }
    """
    import swisseph as swe
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies

    if jd_utc is None:
        jd_utc = _birth_jd_utc()

    lahiri_positions = compute_positions_all_bodies(jd_utc, PRIMARY_AYANAMSHA)
    by_name = {p["name"]: p for p in lahiri_positions}
    moon_sid = by_name["Moon"]["sidereal_longitude"]

    nak_span = 360.0 / 27
    nak_idx = int(moon_sid / nak_span)
    from brahmagyan.ganita.engine import NAKSHATRA_NAMES
    moon_nakshatra = NAKSHATRA_NAMES[nak_idx]
    moon_lord = NAKSHATRA_LORDS[nak_idx]

    vim_rows = compute_vimshottari_sukshma(moon_sid, jd_utc)
    yog_rows = compute_yogini(moon_sid, jd_utc)
    kal_rows = compute_kalachakra(moon_sid, jd_utc)
    ash_rows = compute_ashtottari(moon_sid, jd_utc)

    total = len(vim_rows) + len(yog_rows) + len(kal_rows) + len(ash_rows)

    return {
        "vimshottari": vim_rows,
        "yogini": yog_rows,
        "kalachakra": kal_rows,
        "ashtottari": ash_rows,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_id": nak_idx + 1,
        "moon_nakshatra_lord": moon_lord,
        "total_rows": total,
        "vimshottari_count": len(vim_rows),
    }


# ── DB writer ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l1_dashas] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_dashas(chart_id: str, build_id: str | None = None) -> dict[str, Any]:
    """
    Compute and write ganita.dashas rows to chart_facts.

    Each row: fact_category='ganita.dashas', fact_subject='{system}_L{level}_{lord}_{start}'.
    Returns: {seeded, volume_floor, volume_met}
    """
    result = compute_all_dashas()
    all_systems = {
        "vimshottari": result["vimshottari"],
        "yogini": result["yogini"],
        "kalachakra": result["kalachakra"],
        "ashtottari": result["ashtottari"],
    }

    rows_written = 0
    with _conn() as conn:
        for system_name, rows in all_systems.items():
            for row in rows:
                fact_subject = (
                    f"{system_name}_L{row['level']}_{row['lord']}_{row['start_date']}"
                )
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
                        chart_id, "ganita.dashas", fact_subject,
                        json.dumps(row),
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


# ── Volume check ──────────────────────────────────────────────────────────────

def check_volume() -> dict[str, Any]:
    """Check that the engine can produce required dasha volume without DB."""
    try:
        result = compute_all_dashas()
        vim_count = result["vimshottari_count"]
        total = result["total_rows"]
        status = "GREEN" if vim_count >= VOLUME_FLOOR else "AMBER"
        return {
            "status": status,
            "volume_floor": VOLUME_FLOOR,
            "actual_vimshottari": vim_count,
            "actual_total": total,
            "moon_nakshatra": result["moon_nakshatra"],
            "moon_nakshatra_lord": result["moon_nakshatra_lord"],
            "systems": {
                "vimshottari": vim_count,
                "yogini": len(result["yogini"]),
                "kalachakra": len(result["kalachakra"]),
                "ashtottari": len(result["ashtottari"]),
            },
            "source_citation": SOURCE_CITATION,
        }
    except Exception as exc:
        return {
            "status": "RED",
            "volume_floor": VOLUME_FLOOR,
            "actual_vimshottari": 0,
            "error": str(exc),
            "source_citation": SOURCE_CITATION,
        }
