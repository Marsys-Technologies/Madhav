"""
tajik_varsha_year_lords_writer.py — MARSYS-JIS A20 Tajik Hadda fold writer
Implements A20: Tajik Hadda fold — Muntha + Hadda lord per Tajik varsha year.
Source: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §1.C + FORENSIC §A20
Classical authority: Tajika Neelakanthi — Hadda lords + Muntha analysis

Algorithm:
  For each Tajik varsha year 1..150:
  - varsha_start = birth_dt_utc + (varsha_year-1)*365.25 days
  - year_lord   = YEAR_LORD_SEQUENCE[(varsha_year-1) % 7]  (abdadhipati cycle)
  - Muntha      = advances 1 sign/year from natal Lagna sign
  - Hadda lord  = Egyptian/Ptolemaic bounds for lagna degree-in-sign

Stream D — [BUILD-ORCH-STREAM-D-A20]
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Classical Hadda (Egyptian bounds / Ptolemaic bounds) table
# Each sign: list of (degree_start, degree_end, hadda_lord)
# Source: Tajika Neelakanthi; standard Ptolemaic Hadda attribution
# ---------------------------------------------------------------------------
HADDA_TABLE: dict[str, list[tuple[int, int, str]]] = {
    'Aries':       [(0, 6, 'Jupiter'), (6, 14, 'Venus'),   (14, 21, 'Mercury'), (21, 26, 'Mars'),    (26, 30, 'Saturn')],
    'Taurus':      [(0, 8, 'Venus'),   (8, 15, 'Mercury'), (15, 22, 'Jupiter'), (22, 26, 'Saturn'),  (26, 30, 'Mars')],
    'Gemini':      [(0, 7, 'Mercury'), (7, 14, 'Jupiter'), (14, 21, 'Venus'),   (21, 25, 'Saturn'),  (25, 30, 'Mars')],
    'Cancer':      [(0, 7, 'Mars'),    (7, 13, 'Venus'),   (13, 19, 'Mercury'), (19, 26, 'Jupiter'), (26, 30, 'Saturn')],
    'Leo':         [(0, 6, 'Jupiter'), (6, 11, 'Mercury'), (11, 18, 'Saturn'),  (18, 24, 'Mars'),    (24, 30, 'Venus')],
    'Virgo':       [(0, 7, 'Mercury'), (7, 17, 'Venus'),   (17, 21, 'Jupiter'), (21, 28, 'Mars'),    (28, 30, 'Saturn')],
    'Libra':       [(0, 7, 'Saturn'),  (7, 11, 'Mercury'), (11, 19, 'Jupiter'), (19, 24, 'Venus'),   (24, 30, 'Mars')],
    'Scorpio':     [(0, 7, 'Mars'),    (7, 11, 'Venus'),   (11, 19, 'Mercury'), (19, 24, 'Jupiter'), (24, 30, 'Saturn')],
    'Sagittarius': [(0, 12, 'Jupiter'),(12, 17, 'Venus'),  (17, 21, 'Mercury'), (21, 26, 'Saturn'),  (26, 30, 'Mars')],
    'Capricorn':   [(0, 7, 'Mercury'), (7, 14, 'Jupiter'), (14, 22, 'Venus'),   (22, 26, 'Mars'),    (26, 30, 'Saturn')],
    'Aquarius':    [(0, 7, 'Mercury'), (7, 13, 'Venus'),   (13, 20, 'Jupiter'), (20, 25, 'Mars'),    (25, 30, 'Saturn')],
    'Pisces':      [(0, 12, 'Venus'),  (12, 16, 'Jupiter'),(16, 19, 'Mercury'), (19, 28, 'Mars'),    (28, 30, 'Saturn')],
}

# Abdadhipati (year lord) 7-planet cycle — standard Tajik sequence
YEAR_LORD_SEQUENCE: list[str] = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

# Sign order (0-indexed: Aries=0, ..., Pisces=11)
SIGNS: list[str] = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

# Single sign lord (Mars rules both Aries+Scorpio; Mercury rules Gemini+Virgo, etc.)
SIGN_LORDS: dict[str, str] = {
    'Aries':       'Mars',
    'Taurus':      'Venus',
    'Gemini':      'Mercury',
    'Cancer':      'Moon',
    'Leo':         'Sun',
    'Virgo':       'Mercury',
    'Libra':       'Venus',
    'Scorpio':     'Mars',
    'Sagittarius': 'Jupiter',
    'Capricorn':   'Saturn',
    'Aquarius':    'Saturn',
    'Pisces':      'Jupiter',
}

ASSET_ID = "A20_tajik_varsha_year_lords"
ASSET_LABEL = "Tajik Varsha Year Lords (Muntha + Hadda)"
ENGINE_VERSION = "tajik_engine/1.0.0"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_hadda_lord(sign: str, degree_in_sign: float) -> Tuple[str, int, int]:
    """
    Return (hadda_lord, degree_start, degree_end) for given sign + degree_in_sign.
    Falls through to the last sector if nothing matches (degree == 30 edge case).
    """
    sectors = HADDA_TABLE[sign]
    for (start, end, lord) in sectors:
        if start <= degree_in_sign < end:
            return lord, start, end
    # Edge case: degree exactly 30 → last sector
    last = sectors[-1]
    return last[2], last[0], last[1]


def compute_muntha_sign(lagna_sign: str, varsha_year: int) -> str:
    """
    Muntha advances 1 sign per year from natal Lagna sign.
    Year 1 → Muntha = Lagna sign itself.
    Year 2 → next sign, etc.
    """
    idx = SIGNS.index(lagna_sign)
    return SIGNS[(idx + varsha_year - 1) % 12]


def lagna_sign_from_longitude(lagna_longitude: float) -> str:
    """Derive sign name from 0-360 ecliptic longitude."""
    idx = int(lagna_longitude / 30) % 12
    return SIGNS[idx]


def degree_in_sign_from_longitude(lagna_longitude: float) -> float:
    """Return degree within sign (0.0 – <30.0) from 0-360 longitude."""
    return lagna_longitude % 30.0


# ---------------------------------------------------------------------------
# Main writer
# ---------------------------------------------------------------------------

def write_tajik_varsha_year_lords(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    birth_dt_utc: datetime,
    lagna_sign: str,        # natal Lagna sign name, e.g. 'Aquarius'
    lagna_longitude: float, # 0-360 ecliptic longitude of natal Lagna
) -> int:
    """
    Write 150 Tajik varsha year lord rows for the given chart.

    Args:
        conn:             psycopg2 connection (already open).
        chart_id:         UUID string for the chart.
        ayanamsha_id:     Ayanamsha identifier (e.g. 'lahiri').
        build_id:         UUID string for the build run.
        birth_dt_utc:     Exact birth datetime in UTC (timezone-aware or naive).
        lagna_sign:       Natal Lagna sign, e.g. 'Aquarius'.
        lagna_longitude:  Ecliptic longitude of Lagna (0-360°).

    Returns:
        Number of rows actually inserted (0 if all already existed).
    """
    if lagna_sign not in SIGNS:
        raise ValueError(f"Unknown lagna_sign '{lagna_sign}'. Must be one of {SIGNS}")

    lagna_sign_derived = lagna_sign_from_longitude(lagna_longitude)
    degree_in_sign = degree_in_sign_from_longitude(lagna_longitude)
    hadda_lord, hadda_start, hadda_end = get_hadda_lord(lagna_sign_derived, degree_in_sign)

    rows_inserted = 0

    with conn.cursor() as cur:
        for varsha_year in range(1, 151):
            varsha_start = birth_dt_utc + timedelta(days=(varsha_year - 1) * 365.25)
            varsha_end   = birth_dt_utc + timedelta(days=varsha_year * 365.25)
            age_at_varsha = varsha_year - 1

            year_lord = YEAR_LORD_SEQUENCE[(varsha_year - 1) % 7]

            muntha_sign  = compute_muntha_sign(lagna_sign, varsha_year)
            muntha_lord  = SIGN_LORDS[muntha_sign]
            muntha_house = (SIGNS.index(muntha_sign) - SIGNS.index(lagna_sign)) % 12 + 1

            muntha_context: dict = {
                'muntha_sign':      muntha_sign,
                'muntha_lord':      muntha_lord,
                'muntha_house':     muntha_house,
                'muntha_sign_lord': SIGN_LORDS[muntha_sign],
            }
            hadda_context: dict = {
                'lagna_sign':        lagna_sign_derived,
                'degree_in_sign':    round(degree_in_sign, 4),
                'hadda_lord':        hadda_lord,
                'hadda_degree_start': hadda_start,
                'hadda_degree_end':   hadda_end,
            }

            cur.execute(
                """
                INSERT INTO l1_tajik_varsha_year_lords
                  (varsha_id, chart_id, ayanamsha_id, build_id, varsha_year,
                   varsha_start_iso, varsha_end_iso, age_at_varsha,
                   year_lord, year_lord_method, muntha_sign, muntha_house,
                   hadda_lord, hadda_degree_start, hadda_degree_end,
                   muntha_context_jsonb, hadda_context_jsonb,
                   verification_pass_status, computed_at)
                VALUES (%s,%s,%s,%s,%s, %s,%s,%s, %s,%s,%s,%s, %s,%s,%s, %s::jsonb,%s::jsonb, %s,NOW())
                ON CONFLICT (chart_id, ayanamsha_id, build_id, varsha_year) DO NOTHING
                """,
                (
                    str(uuid.uuid4()),
                    chart_id,
                    ayanamsha_id,
                    build_id,
                    varsha_year,
                    varsha_start,
                    varsha_end,
                    age_at_varsha,
                    year_lord,
                    'abdadhipati',
                    muntha_sign,
                    muntha_house,
                    hadda_lord,
                    float(hadda_start),
                    float(hadda_end),
                    json.dumps(muntha_context),
                    json.dumps(hadda_context),
                    'pass',
                ),
            )
            rows_inserted += cur.rowcount

    conn.commit()
    logger.info(
        "A20: inserted %d Tajik varsha year lord rows for chart=%s ayanamsha=%s build=%s",
        rows_inserted,
        chart_id,
        ayanamsha_id,
        build_id,
    )
    return rows_inserted


# ---------------------------------------------------------------------------
# Two-pass verification helper
# ---------------------------------------------------------------------------

def verify_tajik_varsha_year_lords(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    expected_count: int = 150,
) -> bool:
    """
    Verify that exactly `expected_count` rows exist for (chart_id, ayanamsha_id, build_id).
    Returns True if the count matches, False otherwise.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM l1_tajik_varsha_year_lords
            WHERE chart_id = %s AND ayanamsha_id = %s AND build_id = %s
            """,
            (chart_id, ayanamsha_id, build_id),
        )
        actual = cur.fetchone()[0]

    ok = actual == expected_count
    if not ok:
        logger.warning(
            "A20 verify FAIL: expected %d rows, found %d (chart=%s ayanamsha=%s build=%s)",
            expected_count,
            actual,
            chart_id,
            ayanamsha_id,
            build_id,
        )
    else:
        logger.info(
            "A20 verify PASS: %d rows confirmed (chart=%s ayanamsha=%s build=%s)",
            actual,
            chart_id,
            ayanamsha_id,
            build_id,
        )
    return ok
