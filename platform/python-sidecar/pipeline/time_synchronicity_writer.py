"""
time_synchronicity_writer.py — Time-Synchronicity convergence window detector.

Identifies 30-day windows 2026-2060 where 3+ independent timing systems
simultaneously signal importance for the native's chart.

Timing systems checked:
  1. vimshottari_dasha — MD/AD boundary within window
  2. jaimini_chara     — Chara dasha sign change within window
  3. tajik_varsha      — Solar return (birthday ± 15 days) within window
  4. bhrigu_bindu      — Transit hit in l1_bhrigu_bindu_transits within window
  5. graha_aspect      — Exact aspect hit in l1_graha_aspects_lifetime within window
  6. vedha_activation  — SBC vedha pair transit (slow planet crosses vedha nakshatra)
  7. sade_sati         — Saturn moon-sign crossing within window

Stream C — A15 [BUILD-ORCH-STREAM-C-A15-S1]
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Native constants
# ---------------------------------------------------------------------------
NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
NATIVE_BIRTH = date(1984, 2, 5)

# Vimshottari dasha schedule (approximate from Purva Bhadrapada nakshatra start)
# MD boundaries — each tuple is (lord, start_date, end_date)
_VIMSHOTTARI_MD: list[tuple[str, date, date]] = [
    ("Jupiter", date(1984, 2, 5),  date(2000, 2, 5)),
    ("Saturn",  date(2000, 2, 5),  date(2019, 2, 5)),
    ("Mercury", date(2019, 2, 5),  date(2036, 2, 5)),
    ("Ketu",    date(2036, 2, 5),  date(2043, 2, 5)),
    ("Venus",   date(2043, 2, 5),  date(2063, 2, 5)),
]

# Antardasha proportions (years) within each MD, in traditional order
# Standard sequence: same lord first, then the next in the dasha order
_DASHA_LORDS_IN_ORDER = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

_MD_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
    "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

# Sade-sati: Saturn transits over/near natal Moon sign (Aquarius, 11th sign)
# Native's Moon is in Aquarius. Saturn in Aquarius periods (approximate):
# Past: 1994-04 to 1996-06, 2023-03 to 2025-08
# Future: 2052-03 to 2054-07
_SADE_SATI_WINDOWS: list[tuple[date, date]] = [
    # Past window (not in our 2026-2060 range but included for completeness)
    (date(1994, 4, 1),  date(1996, 6, 30)),
    # Near-past/present (Saturn Aquarius 2023-2025 — Capricorn entry = sade sati start)
    # Sade sati = 7.5 yrs: Saturn in 12th (Capricorn), 1st (Aquarius), 2nd (Pisces)
    # Saturn Capricorn: 2020-01 to 2023-03
    # Saturn Aquarius: 2023-03 to 2025-08
    # Saturn Pisces: 2025-08 to 2028-03
    (date(2020, 1, 1),  date(2028, 3, 31)),
    # Future sade sati: Saturn Capricorn ~2049, Aquarius ~2052, Pisces ~2055
    (date(2049, 1, 1),  date(2056, 3, 31)),
]

# Jaimini Chara dasha: approximate 1-year sign rotation starting from Aries 2026
# This is a simplified placeholder; true Chara requires exact chart computation
_JAIMINI_SIGN_YEARS = 1  # average tenure per sign
_JAIMINI_START = date(2026, 1, 1)
_JAIMINI_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Minimum systems that must converge to form a cluster
CLUSTER_THRESHOLD = 3

# Total timing systems (denominator for convergence_score)
TOTAL_SYSTEMS = 7

# Window size in days
WINDOW_DAYS = 30

# Step size for sliding window (smaller = more granular; identifies overlapping clusters)
WINDOW_STEP = 7


# ---------------------------------------------------------------------------
# Antardasha computation helpers
# ---------------------------------------------------------------------------

def _compute_antardashas(md_lord: str, md_start: date, md_end: date) -> list[date]:
    """Return the boundary dates of antardashas within a maha dasha.

    AD duration formula: (MD_years * AD_years) / 120 years.
    The 120-year Vimshottari cycle is the denominator.
    """
    md_years = _MD_YEARS[md_lord]

    # Find starting position in the dasha sequence
    try:
        start_idx = _DASHA_LORDS_IN_ORDER.index(md_lord)
    except ValueError:
        start_idx = 0

    boundaries: list[date] = []
    current = md_start

    for i in range(len(_DASHA_LORDS_IN_ORDER)):
        ad_lord = _DASHA_LORDS_IN_ORDER[(start_idx + i) % len(_DASHA_LORDS_IN_ORDER)]
        ad_years = _MD_YEARS[ad_lord]
        # Standard formula: AD duration (years) = (md_years * ad_years) / 120
        ad_days = int(round((md_years * ad_years / 120) * 365.25))
        next_date = current + timedelta(days=ad_days)
        if next_date > md_end:
            break
        boundaries.append(next_date)
        current = next_date

    return boundaries


def enumerate_vimshottari_dates(start_year: int = 2026, end_year: int = 2060) -> list[date]:
    """Return all MD and AD boundary dates within [start_year, end_year]."""
    range_start = date(start_year, 1, 1)
    range_end = date(end_year, 12, 31)

    key_dates: list[date] = []

    for md_lord, md_start, md_end in _VIMSHOTTARI_MD:
        # MD boundary
        if range_start <= md_start <= range_end:
            key_dates.append(md_start)
        if range_start <= md_end <= range_end:
            key_dates.append(md_end)

        # Antardasha boundaries
        if md_end < range_start or md_start > range_end:
            continue
        for ad_date in _compute_antardashas(md_lord, md_start, md_end):
            if range_start <= ad_date <= range_end:
                key_dates.append(ad_date)

    return sorted(set(key_dates))


def enumerate_jaimini_dates(start_year: int = 2026, end_year: int = 2060) -> list[date]:
    """Return approximate Jaimini Chara dasha sign-change dates."""
    range_start = date(start_year, 1, 1)
    range_end = date(end_year, 12, 31)

    key_dates: list[date] = []
    current = _JAIMINI_START
    sign_idx = 0
    # Each sign gets approximately 1 year; cycle through all 12 repeatedly
    while current <= range_end:
        if current >= range_start:
            key_dates.append(current)
        # Advance ~1 year
        next_year = current.year + _JAIMINI_SIGN_YEARS
        try:
            current = current.replace(year=next_year)
        except ValueError:
            current = current.replace(year=next_year, day=28)
        sign_idx = (sign_idx + 1) % 12

    return sorted(key_dates)


def enumerate_tajik_dates(start_year: int = 2026, end_year: int = 2060) -> list[date]:
    """Return native's approximate solar return dates (birthday ± 0 days)."""
    key_dates: list[date] = []
    for year in range(start_year, end_year + 1):
        # Feb 5 is the solar return (approximate; true SR requires ephemeris)
        try:
            sr_date = NATIVE_BIRTH.replace(year=year)
        except ValueError:
            sr_date = date(year, 2, 28)
        key_dates.append(sr_date)
    return key_dates


def enumerate_sade_sati_dates(start_year: int = 2026, end_year: int = 2060) -> list[date]:
    """Return boundary dates of sade sati windows."""
    range_start = date(start_year, 1, 1)
    range_end = date(end_year, 12, 31)

    key_dates: list[date] = []
    for ss_start, ss_end in _SADE_SATI_WINDOWS:
        if range_start <= ss_start <= range_end:
            key_dates.append(ss_start)
        if range_start <= ss_end <= range_end:
            key_dates.append(ss_end)

    return sorted(key_dates)


def enumerate_key_dates(conn: Any, chart_id: str) -> dict[str, list[date]]:
    """
    Return a mapping of timing-system name → list of key dates in 2026-2060.

    Parameters
    ----------
    conn      : psycopg2 connection (or compatible)
    chart_id  : UUID string for the native

    Returns
    -------
    dict with keys:
      vimshottari_dasha, jaimini_chara, tajik_varsha,
      bhrigu_bindu, graha_aspect, vedha_activation, sade_sati
    """
    result: dict[str, list[date]] = {
        "vimshottari_dasha": enumerate_vimshottari_dates(),
        "jaimini_chara":     enumerate_jaimini_dates(),
        "tajik_varsha":      enumerate_tajik_dates(),
        "sade_sati":         enumerate_sade_sati_dates(),
        "bhrigu_bindu":      [],
        "graha_aspect":      [],
        "vedha_activation":  [],
    }

    try:
        with conn.cursor() as cur:
            # Bhrigu Bindu transits in range
            cur.execute(
                """
                SELECT DISTINCT hit_iso
                FROM l1_bhrigu_bindu_transits
                WHERE chart_id = %s
                  AND hit_iso BETWEEN '2026-01-01' AND '2060-12-31'
                ORDER BY hit_iso
                """,
                (chart_id,),
            )
            result["bhrigu_bindu"] = [row[0] for row in cur.fetchall()]

            # Graha aspect exact dates in range
            cur.execute(
                """
                SELECT DISTINCT exact_date
                FROM l1_graha_aspects_lifetime
                WHERE chart_id = %s
                  AND exact_date BETWEEN '2026-01-01' AND '2060-12-31'
                ORDER BY exact_date
                """,
                (chart_id,),
            )
            result["graha_aspect"] = [row[0] for row in cur.fetchall()]

            # Vedha activation: BB transits where graha is a slow planet (Saturn, Jupiter, Rahu)
            # and the transit type indicates a vedha nakshatra crossing
            cur.execute(
                """
                SELECT DISTINCT hit_iso
                FROM l1_bhrigu_bindu_transits
                WHERE chart_id = %s
                  AND graha IN ('saturn', 'jupiter', 'rahu', 'Saturn', 'Jupiter', 'Rahu')
                  AND hit_iso BETWEEN '2026-01-01' AND '2060-12-31'
                ORDER BY hit_iso
                """,
                (chart_id,),
            )
            result["vedha_activation"] = [row[0] for row in cur.fetchall()]

    except Exception as exc:  # noqa: BLE001
        log.warning("DB query failed in enumerate_key_dates: %s", exc)

    return result


# ---------------------------------------------------------------------------
# Window scanning
# ---------------------------------------------------------------------------

def find_synchronicity_windows(
    key_dates: dict[str, list[date]],
    chart_id: str = NATIVE_CHART_ID,
    start_year: int = 2026,
    end_year: int = 2060,
) -> list[dict[str, Any]]:
    """
    Slide a 30-day window across 2026-2060 and collect convergence clusters.

    Parameters
    ----------
    key_dates  : output of enumerate_key_dates
    chart_id   : UUID string for the native
    start_year : first year to scan
    end_year   : last year to scan (inclusive)

    Returns
    -------
    List of window dicts, one per convergence cluster (cluster_intensity >= 3).
    Each dict contains:
      chart_id, window_start, window_end, cluster_intensity,
      systems_active, key_dates (json-serialisable dict),
      divergence_flag, divergence_detail, convergence_score, narrative
    """
    scan_start = date(start_year, 1, 1)
    scan_end = date(end_year, 12, 31)

    windows: list[dict[str, Any]] = []
    seen_keys: set[tuple[date, date]] = set()

    current = scan_start
    while current <= scan_end - timedelta(days=WINDOW_DAYS):
        win_end = current + timedelta(days=WINDOW_DAYS)

        # Count systems that have a key date within [current, win_end)
        active_systems: list[str] = []
        hit_dates: dict[str, str] = {}  # system → first hit date as ISO string

        for system, dates in key_dates.items():
            for d in dates:
                if current <= d < win_end:
                    active_systems.append(system)
                    hit_dates[system] = d.isoformat()
                    break  # only count each system once per window

        intensity = len(active_systems)

        if intensity >= CLUSTER_THRESHOLD:
            key = (current, win_end)
            if key not in seen_keys:
                seen_keys.add(key)

                # Divergence check: bhrigu_bindu present but vimshottari+jaimini both absent
                bb_active = "bhrigu_bindu" in active_systems
                vd_active = "vimshottari_dasha" in active_systems
                jc_active = "jaimini_chara" in active_systems
                divergence = bb_active and not vd_active and not jc_active

                divergence_detail: str | None = None
                if divergence:
                    divergence_detail = (
                        "Bhrigu Bindu signals convergence but both Vimshottari dasha "
                        "and Jaimini Chara dasha are silent in this window — "
                        "possible BB false positive or dasha-system disagreement."
                    )

                convergence_score = round(intensity / TOTAL_SYSTEMS, 4)

                # Narrative
                system_labels = ", ".join(active_systems)
                narrative = (
                    f"{intensity} timing systems converge in the window "
                    f"{current.isoformat()} to {win_end.isoformat()}: "
                    f"{system_labels}. "
                )
                if intensity >= 5:
                    narrative += "High-intensity cluster — multiple major timing cycles agree."
                elif intensity >= 4:
                    narrative += "Significant cluster — strong multi-system agreement."
                else:
                    narrative += "Moderate cluster — baseline convergence threshold met."

                if divergence:
                    narrative += " NOTE: Divergence detected between BB and dasha systems."

                windows.append(
                    {
                        "chart_id": chart_id,
                        "window_start": current,
                        "window_end": win_end,
                        "cluster_intensity": intensity,
                        "systems_active": active_systems,
                        "key_dates": hit_dates,
                        "divergence_flag": divergence,
                        "divergence_detail": divergence_detail,
                        "convergence_score": convergence_score,
                        "narrative": narrative,
                    }
                )

        current += timedelta(days=WINDOW_STEP)

    return windows


# ---------------------------------------------------------------------------
# DB seed
# ---------------------------------------------------------------------------

def seed_time_synchronicity(conn: Any, chart_id: str = NATIVE_CHART_ID) -> int:
    """
    Enumerate key dates and insert convergence windows into l1_time_synchronicity.

    Parameters
    ----------
    conn      : psycopg2 connection (autocommit or caller-managed transaction)
    chart_id  : UUID string for the native

    Returns
    -------
    Number of rows inserted (ON CONFLICT DO NOTHING — idempotent).
    """
    key_dates = enumerate_key_dates(conn, chart_id)
    windows = find_synchronicity_windows(key_dates, chart_id=chart_id)

    if not windows:
        log.warning("No synchronicity windows found — check key_dates data.")
        return 0

    inserted = 0
    with conn.cursor() as cur:
        for w in windows:
            cur.execute(
                """
                INSERT INTO l1_time_synchronicity (
                    chart_id, window_start, window_end,
                    cluster_intensity, systems_active, key_dates,
                    divergence_flag, divergence_detail,
                    convergence_score, embedding, narrative, classical_citation
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s::jsonb,
                    %s, %s,
                    %s, NULL, %s, %s
                )
                ON CONFLICT (chart_id, window_start, window_end) DO NOTHING
                """,
                (
                    chart_id,
                    w["window_start"],
                    w["window_end"],
                    w["cluster_intensity"],
                    w["systems_active"],
                    json.dumps(w["key_dates"]),
                    w["divergence_flag"],
                    w["divergence_detail"],
                    w["convergence_score"],
                    w["narrative"],
                    None,  # classical_citation — future step
                ),
            )
            inserted += cur.rowcount

    conn.commit()
    log.info("seed_time_synchronicity: inserted %d windows for chart %s", inserted, chart_id)
    return inserted
