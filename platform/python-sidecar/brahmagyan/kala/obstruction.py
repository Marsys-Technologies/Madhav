"""
brahmagyan.kala.obstruction — BRAHMA-KA-3-3: kala.obstruction + kala.snapshot
===============================================================================

Scans the temporal spine for dates where ≥2 adverse indicators overlap and
materialises them into `kala_obstruction`. Provides `period_snapshot(chart_id,
date)` — a point-in-time snapshot of the active dasha, transit positions,
active MSR signal count, convergence score, obstructions, and provenance
envelope.

Contract (KA-3-3):
  - Table: kala_obstruction
      chart_id         UUID
      date             DATE
      obstruction_type TEXT CHECK IN ('malefic_transit', 'adverse_dasha',
                                      'double_affliction')
      severity         FLOAT   [0.0, 1.0]
      factors          JSONB
      source_citation  TEXT NOT NULL
  - Algorithm:
      Scan kala_timeline (or the canonical Vimshottari schedule) for dates
      where ≥2 adverse indicators are present:
        (i)  Sani/Rahu/Ketu transit through 1st/4th/7th/8th/12th house
        (ii) Unfavourable MD lord (Sani, Rahu, Ketu, or a debilitated lord)
      When ≥2 indicators coincide → severity ≥ 0.5; ≥3 → severity ≥ 0.75.
  - Tool: period_snapshot(chart_id, date) →
        { active_dasha, active_antardasha, transit_positions,
          active_signals_count, convergence_score, obstructions,
          provenance_envelope }

FORENSIC grounding:
  Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar, Odisha.
  Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1 Vimshottari Dasha schedule.
  Saturn MD: 1991-08-21 → 2010-08-21 (sub-periods DSH.V.006 → DSH.V.014)
  Mercury MD: 2010-08-21 → 2027-08-21 (sub-periods DSH.V.015 → DSH.V.023)
  Adverse MDs (Sani, Rahu, Ketu lords): flagged as 'adverse_dasha'.
  Malefic transits: Sani/Rahu/Ketu through dusthana houses (1,4,7,8,12).

source_citation for all inserted rows:
  "PyJHora/SwissEph DE441 + Brahma-L1"

BRAHMA-KA-3-3
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0"
)

SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1"

# Adverse Mahadasha lords (Sani, Rahu, Ketu = inherently malefic/separative)
ADVERSE_MD_LORDS: frozenset[str] = frozenset({"Saturn", "Rahu", "Ketu"})

# Dusthana houses — malefic transit through these is adverse
DUSTHANA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 8, 12})

# Malefic planets for transit indicator
TRANSIT_MALEFICS: frozenset[str] = frozenset({"Saturn", "Rahu", "Ketu"})

# ── Canonical Vimshottari Dasha schedule (FORENSIC §5.1) ──────────────────────
# DSH.V.001 through DSH.V.023 — native's chart (birth 1984-02-05)
# Each row: (row_id, MD_lord, AD_lord, start_date, end_date)
# source_citation: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1 — all dates canonical

VIMSHOTTARI_SCHEDULE: list[tuple[str, str, str, str, str]] = [
    ("DSH.V.001", "Jupiter", "Venus",   "1984-02-05", "1986-03-03"),
    ("DSH.V.002", "Jupiter", "Sun",     "1986-03-03", "1986-12-21"),
    ("DSH.V.003", "Jupiter", "Moon",    "1986-12-21", "1988-04-21"),
    ("DSH.V.004", "Jupiter", "Mars",    "1988-04-21", "1989-03-27"),
    ("DSH.V.005", "Jupiter", "Rahu",    "1989-03-27", "1991-08-21"),
    ("DSH.V.006", "Saturn",  "Saturn",  "1991-08-21", "1994-08-24"),
    ("DSH.V.007", "Saturn",  "Mercury", "1994-08-24", "1997-05-03"),
    ("DSH.V.008", "Saturn",  "Ketu",    "1997-05-03", "1998-06-12"),
    ("DSH.V.009", "Saturn",  "Venus",   "1998-06-12", "2001-08-12"),
    ("DSH.V.010", "Saturn",  "Sun",     "2001-08-12", "2002-07-24"),
    ("DSH.V.011", "Saturn",  "Moon",    "2002-07-24", "2004-02-24"),
    ("DSH.V.012", "Saturn",  "Mars",    "2004-02-24", "2005-04-03"),
    ("DSH.V.013", "Saturn",  "Rahu",    "2005-04-03", "2008-02-09"),
    ("DSH.V.014", "Saturn",  "Jupiter", "2008-02-09", "2010-08-21"),
    ("DSH.V.015", "Mercury", "Mercury", "2010-08-21", "2013-01-18"),
    ("DSH.V.016", "Mercury", "Ketu",    "2013-01-18", "2014-01-15"),
    ("DSH.V.017", "Mercury", "Venus",   "2014-01-15", "2016-11-15"),
    ("DSH.V.018", "Mercury", "Sun",     "2016-11-15", "2017-09-21"),
    ("DSH.V.019", "Mercury", "Moon",    "2017-09-21", "2019-02-21"),
    ("DSH.V.020", "Mercury", "Mars",    "2019-02-21", "2020-02-18"),
    ("DSH.V.021", "Mercury", "Rahu",    "2020-02-18", "2022-09-06"),
    ("DSH.V.022", "Mercury", "Jupiter", "2022-09-06", "2024-12-12"),
    ("DSH.V.023", "Mercury", "Saturn",  "2024-12-12", "2027-08-21"),
    ("DSH.V.024", "Ketu",    "Ketu",    "2027-08-21", "2028-01-18"),
    ("DSH.V.025", "Ketu",    "Venus",   "2028-01-18", "2029-03-18"),
    ("DSH.V.026", "Ketu",    "Sun",     "2029-03-18", "2029-07-24"),
    ("DSH.V.027", "Ketu",    "Moon",    "2029-07-24", "2030-02-24"),
    ("DSH.V.028", "Ketu",    "Mars",    "2030-02-24", "2030-07-21"),
    ("DSH.V.029", "Ketu",    "Rahu",    "2030-07-21", "2031-08-09"),
    ("DSH.V.030", "Ketu",    "Jupiter", "2031-08-09", "2032-07-15"),
    ("DSH.V.031", "Ketu",    "Saturn",  "2032-07-15", "2033-08-24"),
    ("DSH.V.032", "Ketu",    "Mercury", "2033-08-24", "2034-08-21"),
    ("DSH.V.033", "Venus",   "Venus",   "2034-08-21", "2037-12-21"),
]


def get_dasha_for_date(target_date: date) -> dict[str, str] | None:
    """
    Return the active Vimshottari Mahadasha / Antardasha for a given date.

    Uses the canonical FORENSIC §5.1 schedule. Returns None if the date is
    outside the tabulated range.

    Returns:
        {
          "row_id": str,
          "md": str,          # Mahadasha lord
          "ad": str,          # Antardasha lord
          "start": str,       # YYYY-MM-DD
          "end": str,         # YYYY-MM-DD
        }
    """
    for row_id, md, ad, start_str, end_str in VIMSHOTTARI_SCHEDULE:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        if start <= target_date < end:
            return {
                "row_id": row_id,
                "md": md,
                "ad": ad,
                "start": start_str,
                "end": end_str,
            }
    return None


def _is_adverse_dasha(md: str, ad: str) -> bool:
    """
    Return True if the Mahadasha or Antardasha lord is a natural malefic
    (Saturn, Rahu, Ketu) per the obstruction algorithm.
    """
    return md in ADVERSE_MD_LORDS or ad in ADVERSE_MD_LORDS


# ── Transit indicator helpers (static house placement from FORENSIC) ───────────
# NOTE: Full ephemeris-based transit positions require PyJHora/SwissEph (external).
# This module computes the adverse-transit indicator from the kala_timeline DB
# table when available. When DB is absent (unit-test mode), it uses a
# deterministic stub based on the dasha schedule alone.
#
# The native's natal chart houses (D1, Lahiri; FORENSIC §2.1):
#   Lagna = Aries (H1), so:
#   H1=Aries, H2=Taurus, H3=Gemini, H4=Cancer, H5=Leo, H6=Virgo,
#   H7=Libra, H8=Scorpio, H9=Sag, H10=Cap, H11=Aquarius, H12=Pisces


def _compute_indicators(
    md: str,
    ad: str,
    transit_data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Return list of adverse indicator dicts for the given dasha state.

    Each indicator:
        { "type": str, "description": str, "severity_weight": float }

    Indicator types:
      adverse_dasha    — MD or AD lord is a natural malefic (Sani/Rahu/Ketu)
      malefic_transit  — Sani/Rahu/Ketu transiting dusthana house per transit_data
      double_affliction— BOTH adverse_dasha AND malefic_transit present
    """
    indicators: list[dict[str, Any]] = []

    # --- Indicator 1: adverse dasha lord ---
    if md in ADVERSE_MD_LORDS:
        indicators.append({
            "type": "adverse_dasha",
            "description": f"{md} Mahadasha (natural malefic lord)",
            "severity_weight": 0.5,
            "planet": md,
            "role": "MD",
        })
    if ad in ADVERSE_MD_LORDS:
        indicators.append({
            "type": "adverse_dasha",
            "description": f"{ad} Antardasha (natural malefic sub-lord)",
            "severity_weight": 0.35,
            "planet": ad,
            "role": "AD",
        })

    # --- Indicator 2: malefic transit through dusthana ---
    if transit_data:
        for planet, house in transit_data.items():
            if planet in TRANSIT_MALEFICS and house in DUSTHANA_HOUSES:
                indicators.append({
                    "type": "malefic_transit",
                    "description": (
                        f"{planet} transiting H{house} (dusthana)"
                    ),
                    "severity_weight": 0.4,
                    "planet": planet,
                    "house": house,
                })

    return indicators


def _classify_obstruction(
    indicators: list[dict[str, Any]],
) -> tuple[str, float] | None:
    """
    Given a list of indicators, return (obstruction_type, severity) when ≥2
    adverse indicators coincide; return None when count < 2.

    Severity:
      2 indicators → 0.50
      3 indicators → 0.75
      4+          → 0.90 (cap)

    Obstruction type:
      If both adverse_dasha + malefic_transit present → 'double_affliction'
      Only malefic_transit                            → 'malefic_transit'
      Only adverse_dasha                              → 'adverse_dasha'
    """
    if len(indicators) < 2:
        return None

    types_present = {ind["type"] for ind in indicators}
    has_transit = "malefic_transit" in types_present
    has_dasha = "adverse_dasha" in types_present

    if has_transit and has_dasha:
        obs_type = "double_affliction"
    elif has_transit:
        obs_type = "malefic_transit"
    else:
        obs_type = "adverse_dasha"

    count = len(indicators)
    if count == 2:
        severity = 0.50
    elif count == 3:
        severity = 0.75
    else:
        severity = 0.90

    return obs_type, min(severity, 1.0)


# ── DB helpers ─────────────────────────────────────────────────────────────────


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "[STOP] DATABASE_URL not set. "
            "Set DATABASE_URL=postgresql://... and ensure DB is reachable."
        )
    return url


def _get_conn():  # type: ignore[return]
    """Lazy psycopg import — avoids import-time DB dependency."""
    try:
        import psycopg  # type: ignore
        return psycopg.connect(_db_url())
    except ImportError as exc:
        raise ImportError(
            "psycopg (v3) is required for DB operations. "
            "Install with: pip install psycopg[binary]"
        ) from exc


# ── Core: query transit positions from kala_timeline ──────────────────────────


def _fetch_transit_positions(chart_id: str, target_date: date) -> dict[str, Any] | None:
    """
    Attempt to fetch transit_positions JSONB for target_date from kala_timeline.
    Returns None if the table doesn't exist or row is absent.
    """
    try:
        with _get_conn() as conn:
            row = conn.execute(
                """
                SELECT transit_positions
                FROM kala_timeline
                WHERE chart_id = %s AND date = %s
                LIMIT 1
                """,
                (chart_id, target_date),
            ).fetchone()
            if row and row[0]:
                return row[0] if isinstance(row[0], dict) else json.loads(row[0])
    except Exception:
        pass
    return None


def _fetch_active_signals_count(chart_id: str) -> int:
    """Return count of active MSR signals for chart_id from bodha_signals."""
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM bodha_signals WHERE chart_id = %s",
                (chart_id,),
            ).fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def _fetch_convergence_score(chart_id: str) -> float:
    """Return average confidence from bodha_signals as a proxy convergence score."""
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT AVG(confidence) FROM bodha_signals WHERE chart_id = %s",
                (chart_id,),
            ).fetchone()
            val = row[0] if row else None
            return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


# ── Core: period_snapshot ──────────────────────────────────────────────────────


def period_snapshot(
    chart_id: str,
    target_date: str | date,
    *,
    transit_positions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Return a point-in-time period snapshot for a chart at a given date.

    Args:
        chart_id:          UUID of the chart.
        target_date:       Date string (YYYY-MM-DD) or datetime.date object.
        transit_positions: Optional pre-computed transit dict {planet: house_int}.
                           If None, attempts to fetch from kala_timeline DB table;
                           falls back to None (no transit indicators computed).

    Returns:
        {
          "chart_id": str,
          "snapshot_date": str,          # YYYY-MM-DD
          "active_dasha": str | None,    # MD lord or None
          "active_antardasha": str | None,
          "dasha_row_id": str | None,
          "dasha_period": {"start": str, "end": str} | None,
          "transit_positions": dict | None,
          "active_signals_count": int,
          "convergence_score": float,
          "indicators": list[dict],
          "obstructions": list[dict],    # obstruction records (if ≥2 indicators)
          "provenance_envelope": {
              "source": str,
              "source_citation": str,
              "computed_at": str,
              "chart_id": str,
              "snapshot_date": str,
          }
        }
    """
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    snapshot_date_str = target_date.isoformat()

    # 1. Active dasha
    dasha_info = get_dasha_for_date(target_date)
    active_dasha = dasha_info["md"] if dasha_info else None
    active_antardasha = dasha_info["ad"] if dasha_info else None
    dasha_row_id = dasha_info["row_id"] if dasha_info else None
    dasha_period = (
        {"start": dasha_info["start"], "end": dasha_info["end"]}
        if dasha_info
        else None
    )

    # 2. Transit positions (from arg → kala_timeline → None)
    if transit_positions is None:
        transit_positions = _fetch_transit_positions(chart_id, target_date)

    # 3. Active signals count + convergence score
    active_signals_count = _fetch_active_signals_count(chart_id)
    convergence_score = _fetch_convergence_score(chart_id)

    # 4. Compute indicators
    indicators: list[dict[str, Any]] = []
    if active_dasha is not None:
        indicators = _compute_indicators(
            active_dasha,
            active_antardasha or "",
            transit_data=transit_positions,
        )

    # 5. Classify obstructions
    obstructions: list[dict[str, Any]] = []
    classification = _classify_obstruction(indicators)
    if classification is not None:
        obs_type, severity = classification
        obstructions.append({
            "obstruction_type": obs_type,
            "severity": severity,
            "factors": {
                "indicators": indicators,
                "md": active_dasha,
                "ad": active_antardasha,
                "transit_positions": transit_positions,
            },
            "source_citation": SOURCE_CITATION,
        })

    provenance = {
        "source": "brahma.kala.obstruction",
        "source_citation": SOURCE_CITATION,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "chart_id": chart_id,
        "snapshot_date": snapshot_date_str,
    }

    return {
        "chart_id": chart_id,
        "snapshot_date": snapshot_date_str,
        "active_dasha": active_dasha,
        "active_antardasha": active_antardasha,
        "dasha_row_id": dasha_row_id,
        "dasha_period": dasha_period,
        "transit_positions": transit_positions,
        "active_signals_count": active_signals_count,
        "convergence_score": convergence_score,
        "indicators": indicators,
        "obstructions": obstructions,
        "provenance_envelope": provenance,
    }


# ── Core: scan and seed kala_obstruction ──────────────────────────────────────


def scan_and_seed_obstructions(
    chart_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    dry_run: bool = False,
) -> int:
    """
    Scan the Vimshottari schedule for date ranges where ≥2 adverse indicators
    overlap and upsert rows into kala_obstruction.

    The algorithm walks each antardasha period, samples one date per period
    (the first day), evaluates indicators, and writes an obstruction row for
    the entire AD period when criteria are met.

    Args:
        chart_id:    Chart UUID.
        start_date:  Inclusive lower bound (default: first AD start in schedule).
        end_date:    Exclusive upper bound (default: last AD end in schedule).
        dry_run:     Log rows without writing to DB.

    Returns:
        Number of rows upserted.
    """
    rows_to_insert: list[dict[str, Any]] = []

    for row_id, md, ad, start_str, end_str in VIMSHOTTARI_SCHEDULE:
        period_start = date.fromisoformat(start_str)
        period_end = date.fromisoformat(end_str)

        # Filter by requested date range
        if start_date and period_end <= start_date:
            continue
        if end_date and period_start >= end_date:
            continue

        # Sample mid-period date for transit lookup
        sample_date = period_start + timedelta(
            days=(period_end - period_start).days // 2
        )

        transit_positions = _fetch_transit_positions(chart_id, sample_date)
        indicators = _compute_indicators(md, ad, transit_data=transit_positions)
        classification = _classify_obstruction(indicators)

        if classification is None:
            continue

        obs_type, severity = classification

        # One row per antardasha period — sample_date as representative date
        rows_to_insert.append({
            "chart_id": chart_id,
            "date": sample_date.isoformat(),
            "obstruction_type": obs_type,
            "severity": severity,
            "factors": {
                "row_id": row_id,
                "md": md,
                "ad": ad,
                "period_start": start_str,
                "period_end": end_str,
                "indicators": indicators,
                "transit_positions": transit_positions,
            },
            "source_citation": SOURCE_CITATION,
        })

    if dry_run:
        logger.info("[dry_run] Would upsert %d rows into kala_obstruction", len(rows_to_insert))
        for r in rows_to_insert:
            logger.info(
                "  %s | %s | severity=%.2f | %s",
                r["date"],
                r["obstruction_type"],
                r["severity"],
                r["source_citation"],
            )
        return len(rows_to_insert)

    if not rows_to_insert:
        logger.info("No obstruction rows to insert for chart_id=%s", chart_id)
        return 0

    with _get_conn() as conn:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO kala_obstruction
                    (chart_id, date, obstruction_type, severity, factors, source_citation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (chart_id, date, obstruction_type) DO UPDATE SET
                    severity        = EXCLUDED.severity,
                    factors         = EXCLUDED.factors,
                    source_citation = EXCLUDED.source_citation,
                    computed_at     = NOW()
            """
            for r in rows_to_insert:
                cur.execute(sql, (
                    r["chart_id"],
                    r["date"],
                    r["obstruction_type"],
                    r["severity"],
                    json.dumps(r["factors"]),
                    r["source_citation"],
                ))
        conn.commit()

    logger.info(
        "kala_obstruction: upserted %d rows for chart_id=%s",
        len(rows_to_insert),
        chart_id,
    )
    return len(rows_to_insert)


# ── Acceptance gate ────────────────────────────────────────────────────────────


def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    Run the KA-3-3 acceptance gate.

    Gates:
      AC1: period_snapshot("2010-01-01") returns non-null dasha (Saturn MD)
      AC2: period_snapshot("2002-01-01") returns Saturn MD
      AC3: period_snapshot for adverse Saturn period has ≥2 indicators
      AC4: kala_obstruction table has ≥1 row for chart_id
      AC5: All rows in kala_obstruction have non-null source_citation

    Returns dict with keys: passed (bool), checks (list of check results).
    """
    checks: list[dict[str, Any]] = []

    # AC1: 2010-01-01 should be Saturn MD (period ends 2010-08-21)
    try:
        snap = period_snapshot(chart_id, "2010-01-01")
        passed = snap["active_dasha"] is not None
        checks.append({
            "id": "AC1",
            "desc": "period_snapshot('2010-01-01') returns non-null dasha",
            "passed": passed,
            "value": snap.get("active_dasha"),
        })
    except Exception as exc:
        checks.append({"id": "AC1", "desc": "period_snapshot 2010-01-01", "passed": False, "error": str(exc)})

    # AC2: 2002-01-01 should be Saturn MD
    try:
        snap = period_snapshot(chart_id, "2002-01-01")
        md = snap.get("active_dasha")
        passed = md == "Saturn"
        checks.append({
            "id": "AC2",
            "desc": "period_snapshot('2002-01-01') returns Saturn MD",
            "passed": passed,
            "value": md,
        })
    except Exception as exc:
        checks.append({"id": "AC2", "desc": "period_snapshot 2002-01-01", "passed": False, "error": str(exc)})

    # AC3: Saturn/Rahu period (2005-04-03 to 2008-02-09) should have ≥2 indicators
    try:
        snap = period_snapshot(chart_id, "2006-06-01")
        indicator_count = len(snap.get("indicators", []))
        passed = indicator_count >= 2
        checks.append({
            "id": "AC3",
            "desc": "Saturn/Rahu AD period (2006-06-01) has ≥2 adverse indicators",
            "passed": passed,
            "value": indicator_count,
        })
    except Exception as exc:
        checks.append({"id": "AC3", "desc": "indicator count check", "passed": False, "error": str(exc)})

    # AC4: kala_obstruction has ≥1 row
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM kala_obstruction WHERE chart_id = %s",
                (chart_id,),
            ).fetchone()
            count = int(row[0]) if row else 0
        checks.append({
            "id": "AC4",
            "desc": "kala_obstruction has ≥1 row for chart_id",
            "passed": count >= 1,
            "value": count,
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "kala_obstruction row count", "passed": False, "error": str(exc)})

    # AC5: all rows have non-null source_citation
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM kala_obstruction "
                "WHERE chart_id = %s AND (source_citation IS NULL OR source_citation = '')",
                (chart_id,),
            ).fetchone()
            null_count = int(row[0]) if row else 0
        checks.append({
            "id": "AC5",
            "desc": "All kala_obstruction rows have non-null source_citation",
            "passed": null_count == 0,
            "value": null_count,
        })
    except Exception as exc:
        checks.append({"id": "AC5", "desc": "source_citation completeness", "passed": False, "error": str(exc)})

    passed = all(c["passed"] for c in checks)
    result = {"chart_id": chart_id, "gate_passed": passed, "checks": checks}

    if passed:
        logger.info("KA-3-3 acceptance gate PASSED for chart_id=%s", chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error("KA-3-3 acceptance gate FAILED for chart_id=%s — %s", chart_id, failed)

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────


def _cmd_snapshot(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    result = period_snapshot(chart_id, args.date)
    print(json.dumps(result, indent=2, default=str))


def _cmd_scan(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None
    count = scan_and_seed_obstructions(
        chart_id,
        start_date=start,
        end_date=end,
        dry_run=args.dry_run,
    )
    print(f"kala_obstruction: {count} rows {'would be ' if args.dry_run else ''}upserted")


def _cmd_gate(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    result = run_acceptance_gate(chart_id)
    print(json.dumps(result, indent=2, default=str))
    if not result["gate_passed"]:
        sys.exit(1)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="BRAHMA-KA-3-3: kala.obstruction + period_snapshot"
    )
    parser.add_argument(
        "--chart-id", default=None, help="Chart UUID (default: native FORENSIC chart)"
    )

    sub = parser.add_subparsers(dest="command")

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Emit period_snapshot for a date")
    p_snap.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")

    # scan
    p_scan = sub.add_parser("scan", help="Scan Vimshottari schedule and seed kala_obstruction")
    p_scan.add_argument("--start", default=None, help="Start date YYYY-MM-DD (inclusive)")
    p_scan.add_argument("--end", default=None, help="End date YYYY-MM-DD (exclusive)")
    p_scan.add_argument("--dry-run", action="store_true", help="Log rows without writing to DB")

    # gate
    sub.add_parser("gate", help="Run acceptance gate (exits 1 if FAIL)")

    args = parser.parse_args()
    if args.command == "snapshot":
        _cmd_snapshot(args)
    elif args.command == "scan":
        _cmd_scan(args)
    elif args.command == "gate":
        _cmd_gate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
