"""
bulk_signal_activator.py — Bulk-populates the signal_states DB table for a date range.

Thin orchestration wrapper around signal_activator.activate(). Calls activate()
once per date in the range, then batch-INSERTs all resulting rows using
ON CONFLICT DO NOTHING for full idempotence (safe to re-run after interruption).

Phase 2B deliverable — authored 2026-05-18.

CLI:
    python3 platform/scripts/temporal/bulk_signal_activator.py \\
        --chart-id abhisek_mohanty_primary \\
        --start-date 2024-01-01 \\
        --end-date 2028-12-31 \\
        --dasha-system vimshottari

Requires env:
    DATABASE_URL   — PostgreSQL connection URL (proxy must be running on 5433)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Generator

import psycopg2
import psycopg2.extras

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from signal_activator import activate, parse_iso8601  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ROOT = SCRIPT_DIR.parents[2]
DEFAULT_MSR              = ROOT / "025_HOLISTIC_SYNTHESIS" / "MSR_v5_0.md"
DEFAULT_VIMSHOTTARI_RAW  = ROOT / "05_TEMPORAL_ENGINES/dasha/vimshottari/VIMSHOTTARI_RAW_v1_0.json"
DEFAULT_BIRTH            = "1984-02-05T10:43:00+05:30"

INSERT_SQL = """
    INSERT INTO signal_states
        (chart_id, signal_id, query_date, state, confidence, dasha_system, computed_by, ayanamsha)
    VALUES %s
    ON CONFLICT (chart_id, signal_id, query_date, dasha_system) DO NOTHING
"""

BATCH_SIZE = 2000  # rows per executemany call


@contextmanager
def get_db() -> Generator[psycopg2.extensions.connection, None, None]:
    url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def get_already_done_dates(
    conn: psycopg2.extensions.connection, chart_id: str, dasha_system: str
) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT query_date::text FROM signal_states "
            "WHERE chart_id = %s AND dasha_system = %s",
            (chart_id, dasha_system),
        )
        return {row[0] for row in cur.fetchall()}


def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--chart-id", default="abhisek_mohanty_primary")
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--dasha-system", default="vimshottari")
    parser.add_argument("--birth", default=DEFAULT_BIRTH)
    parser.add_argument("--msr", default=str(DEFAULT_MSR))
    parser.add_argument("--vimshottari-raw", default=str(DEFAULT_VIMSHOTTARI_RAW))
    parser.add_argument("--ayanamsha", default="lahiri")
    args = parser.parse_args()

    if not os.environ.get("DATABASE_URL"):
        log.error("DATABASE_URL not set")
        return 1

    start = date.fromisoformat(args.start_date)
    end   = date.fromisoformat(args.end_date)
    birth_dt = parse_iso8601(args.birth)
    msr_path = Path(args.msr)
    vim_path = Path(args.vimshottari_raw)

    if not msr_path.exists():
        log.error("MSR file not found: %s", msr_path)
        return 1
    if not vim_path.exists():
        log.error("VIMSHOTTARI_RAW file not found: %s", vim_path)
        return 1

    log.info("=== Bulk signal activator (Phase 2B) ===")
    log.info("chart_id=%s  range=%s → %s  dasha=%s  msr=%s",
             args.chart_id, start, end, args.dasha_system, msr_path.name)

    total_days = (end - start).days + 1
    log.info("Total date range: %d days", total_days)

    with get_db() as conn:
        already_done = get_already_done_dates(conn, args.chart_id, args.dasha_system)
    log.info("Already populated: %d dates (will skip)", len(already_done))

    pending_dates = [d for d in date_range(start, end) if d.isoformat() not in already_done]
    log.info("Pending: %d dates to process", len(pending_dates))

    if not pending_dates:
        log.info("Nothing to do — all dates already in signal_states.")
        _print_final_stats(args.chart_id, args.dasha_system)
        return 0

    batch: list[tuple] = []
    total_inserted = 0
    total_skipped  = 0

    with get_db() as conn:
        for i, qdate in enumerate(pending_dates):
            if i % 30 == 0:
                log.info("Progress: %d/%d dates processed  (%.1f%%)",
                         i, len(pending_dates), 100.0 * i / len(pending_dates))

            try:
                payload = activate(
                    chart_id=args.chart_id,
                    query_date=qdate,
                    birth_dt=birth_dt,
                    msr_path=msr_path,
                    vimshottari_raw_path=vim_path,
                    ayanamsha=args.ayanamsha,
                )
            except Exception as exc:
                log.warning("activate() failed for %s: %s — skipping date", qdate, exc)
                continue

            for row in payload["signals"]:
                batch.append((
                    row["chart_id"],
                    row["signal_id"],
                    row["query_date"],
                    row["state"],
                    row["confidence"],
                    row["dasha_system"],
                    row["computed_by"],
                    row["ayanamsha"],
                ))

            if len(batch) >= BATCH_SIZE:
                n = _flush_batch(conn, batch)
                total_inserted += n
                total_skipped  += len(batch) - n
                batch = []

        # Flush remainder
        if batch:
            n = _flush_batch(conn, batch)
            total_inserted += n
            total_skipped  += len(batch) - n

    log.info("=== DONE ===")
    log.info("Inserted: %d  Skipped (conflict): %d", total_inserted, total_skipped)
    _print_final_stats(args.chart_id, args.dasha_system)
    return 0


def _flush_batch(conn: psycopg2.extensions.connection, batch: list[tuple]) -> int:
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, INSERT_SQL, batch, page_size=500)
        inserted = cur.rowcount if cur.rowcount >= 0 else 0
    conn.commit()
    return inserted


def _print_final_stats(chart_id: str, dasha_system: str) -> None:
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*), COUNT(DISTINCT signal_id), "
                    "MIN(query_date::text), MAX(query_date::text) "
                    "FROM signal_states WHERE chart_id=%s AND dasha_system=%s",
                    (chart_id, dasha_system),
                )
                row = cur.fetchone()
        if row:
            log.info("Final signal_states: rows=%d  distinct_signals=%d  range=%s→%s",
                     row[0], row[1], row[2], row[3])
    except Exception as exc:
        log.warning("Could not fetch final stats: %s", exc)


if __name__ == "__main__":
    sys.exit(main())
