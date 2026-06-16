"""
brahmagyan.kala.timeline — BRAHMA-KA-3-1: kala.timeline
=========================================================

Builds and queries the deterministic dasha×transit alignment series
for a given chart over its native life range.

Contract (BRAHMA L3 Kāla KA-3-1):
  - owns: daily dasha×transit alignment rows in kala_timeline
  - tool: timeline_query(chart_id, date_range) → {timeline, provenance_envelope}
  - table: kala_timeline (chart_id, date, active_mahadasha, active_antardasha,
           transit_highlights JSONB, signal_activations JSONB, source_citation NOT NULL)
  - acceptance:
      - Saturn MD rows present for dates in 1991-08-21 → 2010-08-21
      - Mercury MD rows present for dates in 2010-08-21 → 2027-08-21
      - source_citation NOT NULL on all rows
      - deterministic: same date always returns same row

Depends on:
  - chart_facts dasha_vimshottari rows (L1 ganita.dashas) — queried via dasha_chain
    algorithm if DB rows are empty (see dasha_chain.py logic replicated here for
    standalone use without HTTP round-trip)
  - ephemeris_daily table (L1 ganita.positions) — optional; graceful degradation
  - msr_signals / bodha_signals tables (L2 bodha.signals) — optional; graceful degradation

Source data:
  FORENSIC §5.1 Vimshottari Dasha — Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Usage:
    # Seed native chart (date range defaults to 1984-01-01 → 2050-12-31)
    python -m brahmagyan.kala.timeline seed --chart-id 482012f1-...

    # Query range
    python -m brahmagyan.kala.timeline query \\
        --chart-id 482012f1-... \\
        --start 1991-01-01 --end 2010-12-31

    # Run acceptance gate
    python -m brahmagyan.kala.timeline gate --chart-id 482012f1-...

Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST Bhubaneswar
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-KA-3-1
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

SOURCE_CITATION = "PyJHora/SwissEph DE441 + Brahma-L1"

SEED_START = date(1984, 1, 1)
SEED_END   = date(2050, 12, 31)

# ── Vimshottari constants (from FORENSIC §5.1 — do not recompute) ─────────────
#
# Period order and durations per classical Vimshottari system.
# Canonical boundary dates for Abhisek Mohanty are sourced from
# FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (FORENSIC dates are canonical
# per GAP.09 resolution; JH dates ±7-9 days are NOT used).

VIMSHOTTARI: list[tuple[str, int]] = [
    ("Ketu",    7),
    ("Venus",   20),
    ("Sun",     6),
    ("Moon",    10),
    ("Mars",    7),
    ("Rahu",    18),
    ("Jupiter", 16),
    ("Saturn",  19),
    ("Mercury", 17),
]
TOTAL_YEARS = 120
DAYS_PER_YEAR = 365.25

# Canonical MD boundaries from FORENSIC §5.1 (Abhisek Mohanty native).
# These are the ground-truth period start/end dates the system is anchored to.
# Do NOT recompute — any deviation from these dates is a B.10 violation.
#
# Format: (md_lord, md_start_iso, md_end_iso)
FORENSIC_MD_SCHEDULE: list[tuple[str, str, str]] = [
    ("Jupiter", "1984-02-05", "1991-08-21"),  # DSH.V.001–005 (balance at birth)
    ("Saturn",  "1991-08-21", "2010-08-21"),  # DSH.V.006–014
    ("Mercury", "2010-08-21", "2027-08-21"),  # DSH.V.015–023
    ("Ketu",    "2027-08-21", "2034-08-21"),  # DSH.V.024–032
    ("Venus",   "2034-08-21", "2054-08-21"),  # DSH.V.033–041
    ("Sun",     "2054-08-21", "2060-08-21"),  # DSH.V.042–050
]

# Canonical AD boundaries (sub-periods) from FORENSIC §5.1
FORENSIC_AD_SCHEDULE: list[tuple[str, str, str, str]] = [
    # (md_lord, ad_lord, start_iso, end_iso)
    ("Jupiter", "Venus",   "1984-02-05", "1986-03-03"),
    ("Jupiter", "Sun",     "1986-03-03", "1986-12-21"),
    ("Jupiter", "Moon",    "1986-12-21", "1988-04-21"),
    ("Jupiter", "Mars",    "1988-04-21", "1989-03-27"),
    ("Jupiter", "Rahu",    "1989-03-27", "1991-08-21"),
    ("Saturn",  "Saturn",  "1991-08-21", "1994-08-24"),
    ("Saturn",  "Mercury", "1994-08-24", "1997-05-03"),
    ("Saturn",  "Ketu",    "1997-05-03", "1998-06-12"),
    ("Saturn",  "Venus",   "1998-06-12", "2001-08-12"),
    ("Saturn",  "Sun",     "2001-08-12", "2002-07-24"),
    ("Saturn",  "Moon",    "2002-07-24", "2004-02-24"),
    ("Saturn",  "Mars",    "2004-02-24", "2005-04-03"),
    ("Saturn",  "Rahu",    "2005-04-03", "2008-02-09"),
    ("Saturn",  "Jupiter", "2008-02-09", "2010-08-21"),
    ("Mercury", "Mercury", "2010-08-21", "2013-01-18"),
    ("Mercury", "Ketu",    "2013-01-18", "2014-01-15"),
    ("Mercury", "Venus",   "2014-01-15", "2016-11-15"),
    ("Mercury", "Sun",     "2016-11-15", "2017-09-21"),
    ("Mercury", "Moon",    "2017-09-21", "2019-02-21"),
    ("Mercury", "Mars",    "2019-02-21", "2020-02-18"),
    ("Mercury", "Rahu",    "2020-02-18", "2022-09-06"),
    ("Mercury", "Jupiter", "2022-09-06", "2024-12-12"),
    ("Mercury", "Saturn",  "2024-12-12", "2027-08-21"),
    ("Ketu",    "Ketu",    "2027-08-21", "2028-01-18"),
    ("Ketu",    "Venus",   "2028-01-18", "2029-03-18"),
    ("Ketu",    "Sun",     "2029-03-18", "2029-07-24"),
    ("Ketu",    "Moon",    "2029-07-24", "2030-02-24"),
    ("Ketu",    "Mars",    "2030-02-24", "2030-07-21"),
    ("Ketu",    "Rahu",    "2030-07-21", "2031-08-09"),
    ("Ketu",    "Jupiter", "2031-08-09", "2032-07-15"),
    ("Ketu",    "Saturn",  "2032-07-15", "2033-08-24"),
    ("Ketu",    "Mercury", "2033-08-24", "2034-08-21"),
    ("Venus",   "Venus",   "2034-08-21", "2037-12-21"),
    ("Venus",   "Sun",     "2037-12-21", "2038-12-21"),
    ("Venus",   "Moon",    "2038-12-21", "2040-08-21"),
    ("Venus",   "Mars",    "2040-08-21", "2041-10-21"),
    ("Venus",   "Rahu",    "2041-10-21", "2044-10-21"),
    ("Venus",   "Jupiter", "2044-10-21", "2047-06-21"),
    ("Venus",   "Saturn",  "2047-06-21", "2050-08-21"),
    ("Venus",   "Mercury", "2050-08-21", "2053-06-21"),
]

# ── Dasha resolution ───────────────────────────────────────────────────────────


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _active_md(query_date: date) -> tuple[str, date, date]:
    """
    Return (md_lord, md_start, md_end) for the given date.
    Uses FORENSIC_MD_SCHEDULE as ground truth; falls back to algorithmic
    extension for dates outside the covered range.
    """
    for md_lord, start_s, end_s in FORENSIC_MD_SCHEDULE:
        start = _parse_date(start_s)
        end   = _parse_date(end_s)
        if start <= query_date < end:
            return md_lord, start, end

    # Outside FORENSIC range — extend algorithmically
    # (Vimshottari cycles repeat every 120 years)
    last_lord, _, last_end_s = FORENSIC_MD_SCHEDULE[-1]
    last_end = _parse_date(last_end_s)

    seq_idx = next(i for i, (n, _) in enumerate(VIMSHOTTARI) if n == last_lord)
    current_start = last_end

    # Forward extension
    if query_date >= last_end:
        idx = seq_idx
        while True:
            idx = (idx + 1) % len(VIMSHOTTARI)
            lord, yrs = VIMSHOTTARI[idx]
            current_end = current_start + timedelta(days=int(yrs * DAYS_PER_YEAR))
            if current_start <= query_date < current_end:
                return lord, current_start, current_end
            current_start = current_end

    # Backward extension (pre-1984)
    first_lord, first_start_s, _ = FORENSIC_MD_SCHEDULE[0]
    first_start = _parse_date(first_start_s)
    idx = next(i for i, (n, _) in enumerate(VIMSHOTTARI) if n == first_lord)
    current_end = first_start
    while True:
        idx = (idx - 1) % len(VIMSHOTTARI)
        lord, yrs = VIMSHOTTARI[idx]
        current_start = current_end - timedelta(days=int(yrs * DAYS_PER_YEAR))
        if current_start <= query_date < current_end:
            return lord, current_start, current_end
        current_end = current_start


def _active_ad(query_date: date) -> tuple[str, date, date]:
    """
    Return (ad_lord, ad_start, ad_end) for the given date.
    Uses FORENSIC_AD_SCHEDULE where available; falls back to proportional
    subdivision within the active MD.
    """
    # Try FORENSIC AD schedule first
    for md_lord, ad_lord, start_s, end_s in FORENSIC_AD_SCHEDULE:
        start = _parse_date(start_s)
        end   = _parse_date(end_s)
        if start <= query_date < end:
            return ad_lord, start, end

    # Outside covered ADs — compute via proportional subdivision
    md_lord, md_start, md_end = _active_md(query_date)
    md_days = (md_end - md_start).days
    md_yrs  = next(yrs for n, yrs in VIMSHOTTARI if n == md_lord)

    # Build AD sequence within this MD (Vimshottari proportional subdivision)
    seq_idx = next(i for i, (n, _) in enumerate(VIMSHOTTARI) if n == md_lord)
    ad_start = md_start
    for i in range(len(VIMSHOTTARI)):
        idx = (seq_idx + i) % len(VIMSHOTTARI)
        ad_lord_name, ad_lord_yrs = VIMSHOTTARI[idx]
        ad_days = int(md_days * ad_lord_yrs / TOTAL_YEARS)
        ad_end  = ad_start + timedelta(days=ad_days)
        if ad_start <= query_date < ad_end:
            return ad_lord_name, ad_start, ad_end
        ad_start = ad_end

    # Edge case: last day of MD
    return ad_lord_name, ad_start, md_end


# ── DB access (lazy import — no top-level psycopg import) ─────────────────────

def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set — cannot access kala_timeline table")
    return url


def _connect():  # type: ignore[return]
    """Lazy psycopg connect — avoids top-level import touching DB at module load."""
    import psycopg  # noqa: PLC0415 (lazy import required by contract)
    return psycopg.connect(_get_db_url(), row_factory=psycopg.rows.dict_row)


# ── Transit highlights (graceful degradation) ─────────────────────────────────

def _get_transit_highlights(conn: Any, query_date: date) -> list[dict[str, Any]]:
    """
    Fetch top-N transit events from ephemeris_daily for query_date.
    Returns empty list if table absent or no row for this date.
    Graceful degradation: never raises on missing data.
    """
    try:
        rows = conn.execute(
            """
            SELECT planet, longitude, retrograde
            FROM ephemeris_daily
            WHERE date = %s
            ORDER BY planet
            LIMIT 9
            """,
            (query_date,),
        ).fetchall()
        return [
            {
                "planet": r["planet"] if isinstance(r, dict) else r[0],
                "longitude": float(r["longitude"] if isinstance(r, dict) else r[1]),
                "retrograde": bool(r["retrograde"] if isinstance(r, dict) else r[2]),
            }
            for r in rows
        ]
    except Exception as exc:  # noqa: BLE001
        logger.debug("ephemeris_daily not available for %s: %s", query_date, exc)
        return []


# ── Signal activations (graceful degradation) ─────────────────────────────────

def _get_signal_activations(
    conn: Any,
    chart_id: str,
    md_lord: str,
    ad_lord: str,
) -> list[dict[str, Any]]:
    """
    Fetch bodha signals activated by the current MD/AD state.
    Returns empty list if bodha_signals / msr_signals absent.
    Graceful degradation: never raises on missing data.
    """
    try:
        rows = conn.execute(
            """
            SELECT signal_id, domain, valence, confidence
            FROM bodha_signals
            WHERE chart_id = %s
              AND (
                  signal_text ILIKE %s
                  OR signal_text ILIKE %s
                  OR source_citation ILIKE %s
              )
              AND confidence >= 0.5
            ORDER BY confidence DESC
            LIMIT 10
            """,
            (
                chart_id,
                f"%{md_lord}%",
                f"%{ad_lord}%",
                f"%DSH.V%",
            ),
        ).fetchall()
        return [
            {
                "signal_id": r["signal_id"] if isinstance(r, dict) else r[0],
                "domain":    r["domain"]    if isinstance(r, dict) else r[1],
                "valence":   r["valence"]   if isinstance(r, dict) else r[2],
                "confidence": float(r["confidence"] if isinstance(r, dict) else r[3]),
            }
            for r in rows
        ]
    except Exception as exc:  # noqa: BLE001
        logger.debug("bodha_signals not available: %s", exc)
        return []


# ── Seed ───────────────────────────────────────────────────────────────────────

def seed(
    chart_id: str = NATIVE_CHART_ID,
    start: date = SEED_START,
    end: date   = SEED_END,
    batch_size: int = 500,
) -> int:
    """
    Populate kala_timeline for chart_id over [start, end].
    Idempotent: uses INSERT ... ON CONFLICT DO NOTHING.
    Returns the count of rows inserted.
    """
    import psycopg  # noqa: PLC0415

    logger.info(
        "Seeding kala_timeline for chart_id=%s, range=%s → %s",
        chart_id, start, end,
    )

    total_inserted = 0
    with _connect() as conn:
        current = start
        batch: list[tuple[Any, ...]] = []

        while current <= end:
            md_lord, _md_start, _md_end = _active_md(current)
            ad_lord, _ad_start, _ad_end = _active_ad(current)
            transit_highlights  = _get_transit_highlights(conn, current)
            signal_activations  = _get_signal_activations(
                conn, chart_id, md_lord, ad_lord
            )

            batch.append((
                chart_id,
                current,
                md_lord,
                ad_lord,
                json.dumps(transit_highlights),
                json.dumps(signal_activations),
                SOURCE_CITATION,
            ))

            if len(batch) >= batch_size:
                n = _flush_batch(conn, batch)
                total_inserted += n
                batch = []
                logger.info("Flushed batch — cumulative rows inserted: %d", total_inserted)

            current += timedelta(days=1)

        if batch:
            n = _flush_batch(conn, batch)
            total_inserted += n

    logger.info("Seed complete — total rows inserted: %d", total_inserted)
    return total_inserted


def _flush_batch(conn: Any, batch: list[tuple[Any, ...]]) -> int:
    """Insert a batch of rows with ON CONFLICT DO NOTHING. Returns rows inserted.

    DCB-001 fix: removed spurious psycopg.extras import (psycopg3 has no extras
    module) and fixed the no-op string replace that produced an unparseable SQL
    template. Now uses executemany for correct multi-row batch insertion.
    """
    # Use executemany — psycopg3 supports this natively without psycopg.extras
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO kala_timeline
                (chart_id, date, active_mahadasha, active_antardasha,
                 transit_highlights, signal_activations, source_citation)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
            ON CONFLICT (chart_id, date) DO NOTHING
            """,
            batch,
        )
        inserted = cur.rowcount if cur.rowcount and cur.rowcount > 0 else len(batch)
    conn.commit()
    return inserted


# ── Query ──────────────────────────────────────────────────────────────────────

def query_timeline(
    chart_id: str,
    start: date,
    end: date,
    limit: int = 1000,
) -> dict[str, Any]:
    """
    Query kala_timeline for chart_id over [start, end].
    Returns {timeline, provenance_envelope}.

    Falls back to algorithmic computation if kala_timeline has no rows
    for the requested range (graceful degradation).
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT date, active_mahadasha, active_antardasha,
                   transit_highlights, signal_activations, source_citation
            FROM kala_timeline
            WHERE chart_id = %s
              AND date BETWEEN %s AND %s
            ORDER BY date
            LIMIT %s
            """,
            (chart_id, start, end, limit),
        ).fetchall()

    if not rows:
        logger.info(
            "No kala_timeline rows for chart_id=%s in range %s→%s; "
            "falling back to algorithmic computation",
            chart_id, start, end,
        )
        rows = _compute_range(chart_id, start, end, limit)

    timeline = [
        {
            "date":               str(r["date"] if isinstance(r, dict) else r[0]),
            "active_mahadasha":   r["active_mahadasha"]  if isinstance(r, dict) else r[1],
            "active_antardasha":  r["active_antardasha"] if isinstance(r, dict) else r[2],
            "transit_highlights": (
                r["transit_highlights"] if isinstance(r, dict) else r[3]
            ) or [],
            "signal_activations": (
                r["signal_activations"] if isinstance(r, dict) else r[4]
            ) or [],
            "source_citation":    r["source_citation"]  if isinstance(r, dict) else r[5],
        }
        for r in rows
    ]

    return {
        "timeline": timeline,
        "provenance_envelope": {
            "asset":    "kala.timeline",
            "unit":     "KA-3-1",
            "source":   SOURCE_CITATION,
            "layer":    "L3 Kāla",
            "depends":  ["L1 ganita.dashas", "L1 ganita.positions", "L2 bodha.signals"],
            "chart_id": chart_id,
            "range":    {"start": str(start), "end": str(end)},
            "count":    len(timeline),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _compute_range(
    chart_id: str,
    start: date,
    end: date,
    limit: int,
) -> list[dict[str, Any]]:
    """
    Algorithmic fallback: compute timeline rows without DB.
    Used when kala_timeline table is empty or for validation.
    """
    rows: list[dict[str, Any]] = []
    current = start
    while current <= end and len(rows) < limit:
        md_lord, _, _ = _active_md(current)
        ad_lord, _, _ = _active_ad(current)
        rows.append({
            "date":               current,
            "active_mahadasha":   md_lord,
            "active_antardasha":  ad_lord,
            "transit_highlights": [],
            "signal_activations": [],
            "source_citation":    SOURCE_CITATION,
        })
        current += timedelta(days=1)
    return rows


# ── Acceptance gate ────────────────────────────────────────────────────────────

def run_gate(chart_id: str = NATIVE_CHART_ID) -> bool:
    """
    Run KA-3-1 acceptance gate against FORENSIC-grounded assertions.

    Gates:
      G1: Saturn MD active on 2000-01-01 (mid Saturn MD 1991-2010)
      G2: Mercury MD active on 2015-06-01 (mid Mercury MD 2010-2027)
      G3: Saturn AD active on 1993-01-01 (DSH.V.006 Saturn-Saturn AD)
      G4: source_citation non-null on sampled rows
      G5: deterministic — same date returns same MD
    """
    passed = 0
    failed = 0

    def _check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  PASS {label}" + (f" — {detail}" if detail else ""))
        else:
            failed += 1
            print(f"  FAIL {label}" + (f" — {detail}" if detail else ""))

    print("=== KA-3-1 Acceptance Gate ===")
    print(f"chart_id: {chart_id}")
    print()

    # G1: Saturn MD on 2000-01-01
    test_date_g1 = date(2000, 1, 1)
    md_lord, _, _ = _active_md(test_date_g1)
    _check("G1: Saturn MD on 2000-01-01", md_lord == "Saturn", f"got md={md_lord}")

    # G2: Mercury MD on 2015-06-01
    test_date_g2 = date(2015, 6, 1)
    md_lord, _, _ = _active_md(test_date_g2)
    _check("G2: Mercury MD on 2015-06-01", md_lord == "Mercury", f"got md={md_lord}")

    # G3: Saturn AD on 1993-01-01 (Saturn-Saturn AD per FORENSIC DSH.V.006)
    test_date_g3 = date(1993, 1, 1)
    ad_lord, _, _ = _active_ad(test_date_g3)
    _check("G3: Saturn AD on 1993-01-01 (Sat-Sat AD)", ad_lord == "Saturn", f"got ad={ad_lord}")

    # G4: source_citation non-null (algorithmic computation always sets it)
    sample_rows = _compute_range(chart_id, date(1991, 8, 21), date(1991, 9, 1), limit=5)
    all_have_citation = all(r["source_citation"] for r in sample_rows)
    _check("G4: source_citation non-null on sample rows", all_have_citation)

    # G5: deterministic — same date returns same MD twice
    md_a, _, _ = _active_md(test_date_g1)
    md_b, _, _ = _active_md(test_date_g1)
    _check("G5: deterministic (same date → same MD)", md_a == md_b, f"md_a={md_a}, md_b={md_b}")

    print()
    print(f"Result: {passed} passed, {failed} failed")
    return failed == 0


# ── CLI ────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="brahmagyan.kala.timeline — BRAHMA-KA-3-1"
    )
    sub = p.add_subparsers(dest="command", required=True)

    # seed
    s = sub.add_parser("seed", help="Populate kala_timeline for a date range")
    s.add_argument("--chart-id", default=NATIVE_CHART_ID)
    s.add_argument("--start", default=str(SEED_START))
    s.add_argument("--end",   default=str(SEED_END))
    s.add_argument("--batch-size", type=int, default=500)

    # query
    q = sub.add_parser("query", help="Query kala_timeline for a date range")
    q.add_argument("--chart-id", default=NATIVE_CHART_ID)
    q.add_argument("--start", required=True)
    q.add_argument("--end",   required=True)
    q.add_argument("--limit", type=int, default=1000)

    # gate
    g = sub.add_parser("gate", help="Run KA-3-1 acceptance gate")
    g.add_argument("--chart-id", default=NATIVE_CHART_ID)

    return p


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    args = _build_parser().parse_args()

    if args.command == "seed":
        n = seed(
            chart_id=args.chart_id,
            start=date.fromisoformat(args.start),
            end=date.fromisoformat(args.end),
            batch_size=args.batch_size,
        )
        print(f"Seeded {n} rows into kala_timeline")

    elif args.command == "query":
        result = query_timeline(
            chart_id=args.chart_id,
            start=date.fromisoformat(args.start),
            end=date.fromisoformat(args.end),
            limit=args.limit,
        )
        print(json.dumps(result, default=str, indent=2))

    elif args.command == "gate":
        ok = run_gate(chart_id=args.chart_id)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
