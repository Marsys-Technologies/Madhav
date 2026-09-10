#!/usr/bin/env python3
"""
rollback_authority.py — PARIṢKĀRA MR-30 / MR-08 gochara authority rollback.

Rolls back a chart's kala_gochara_authority entry by deleting the row, so the
COALESCE serving path falls back to 'v1' (the absent-row default defined in
migration 527's table comment).

CAMPAIGN CONTEXT
----------------
Companion to flip_authority.py. During GOCHARA-UTKARṢA W6.1–W6.3 rollback
was performed via chart-specific one-off scripts (utk-w61/
dispatch_utkarsha_w63_rollback_abhinandan.py). PARIṢKĀRA MR-30 commits this
as versioned, chart-agnostic tooling so MR-08's closure gate is satisfied.

RELATIONSHIP TO MR-08
---------------------
After a rollback the operator should run probe_gochara.py to confirm the
deployed MCP product is serving from the v1 corpus (probe_gochara.py calls
the live MCP HTTP endpoint, not just SQL).

SCHEMA CONTRACT (migration 527)
--------------------------------
kala_gochara_authority: ABSENT ROW = v1 authoritative by COALESCE.
Rollback = DELETE the row. NO kala_gochara_windows row is ever touched.
Re-apply the flip: run flip_authority.py.

DB CONNECTION
-------------
Reads the Postgres connection string from DATABASE_URL. Falls back to
gcloud secrets if not set:

    gcloud secrets versions access latest --secret=amjis-pipeline-db-url

Usage:
    python3 rollback_authority.py --chart-id <uuid>
    python3 rollback_authority.py --chart-id <uuid> --dry-run
    python3 rollback_authority.py --help
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# DB connection helper
# ---------------------------------------------------------------------------

def _resolve_db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest",
             "--secret=amjis-pipeline-db-url"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        url = result.stdout.strip()
        if url:
            return url
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(
            f"ERROR: DATABASE_URL not set and gcloud fallback failed: {exc}\n"
            "Set DATABASE_URL or ensure gcloud is authenticated and "
            "cloud-sql-proxy is running on 127.0.0.1:5433."
        ) from exc
    raise SystemExit(
        "ERROR: DATABASE_URL not set and gcloud returned empty output.\n"
        "Set DATABASE_URL or ensure gcloud is authenticated."
    )


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rollback kala_gochara_authority for a chart by deleting its row "
            "(reverts serving to v1 via COALESCE fallback). "
            "PARIṢKĀRA MR-30/MR-08 versioned tooling — replaces ad-hoc "
            "dispatch_utkarsha_w63_rollback_*.py one-offs."
        ),
    )
    parser.add_argument(
        "--chart-id", required=True,
        help="UUID of the chart to roll back (e.g. 482012f1-710e-4a25-994a-93821f5871aa)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without making any DB write.",
    )
    args = parser.parse_args(argv)

    chart_id: str = args.chart_id
    dry_run: bool = args.dry_run

    db_url = _resolve_db_url()

    try:
        import psycopg
        import psycopg.rows
    except ImportError as exc:
        raise SystemExit(
            f"ERROR: psycopg not available: {exc}\n"
            "Install via: pip install 'psycopg[binary]'"
        ) from exc

    conn = psycopg.connect(db_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # ── Read current state ───────────────────────────────────────────────────
    cur.execute(
        "SELECT authoritative_generation, flipped_at, flipped_by, evidence_ref "
        "FROM kala_gochara_authority WHERE chart_id = %s",
        (chart_id,),
    )
    existing = cur.fetchone()

    if existing is None:
        print(
            f"ROLLBACK COMPLETE: chart {chart_id} -> v1 (no authority row)\n"
            f"  (Already rolled back — no row existed to delete.)"
        )
        conn.close()
        return 0

    print(
        f"[rollback_authority] Found authority row for chart {chart_id[:8]}…:\n"
        f"  authoritative_generation={existing['authoritative_generation']!r}\n"
        f"  flipped_at={existing['flipped_at']}\n"
        f"  flipped_by={existing['flipped_by']!r}\n"
        f"  evidence_ref={existing['evidence_ref']!r}",
        file=sys.stderr,
    )

    if dry_run:
        print(
            f"[rollback_authority] DRY RUN — would execute: "
            f"DELETE FROM kala_gochara_authority WHERE chart_id={chart_id!r}\n"
            f"  After deletion, COALESCE returns 'v1' (absent-row default)."
        )
        conn.close()
        return 0

    # ── DELETE ───────────────────────────────────────────────────────────────
    cur.execute(
        "DELETE FROM kala_gochara_authority WHERE chart_id = %s",
        (chart_id,),
    )

    # ── Verify deletion ──────────────────────────────────────────────────────
    cur.execute(
        "SELECT authoritative_generation FROM kala_gochara_authority "
        "WHERE chart_id = %s",
        (chart_id,),
    )
    still_there = cur.fetchone()
    if still_there is not None:
        print(
            f"[rollback_authority] ERROR: row still present after DELETE: "
            f"{still_there}. Rolling back.",
            file=sys.stderr,
        )
        conn.rollback()
        conn.close()
        return 1

    conn.commit()
    conn.close()

    print(
        f"ROLLBACK COMPLETE: chart {chart_id} -> v1 (no authority row)"
    )
    print(
        f"  kala_gochara_authority row deleted. Serving now defaults to "
        f"generation='v1' via COALESCE fallback.",
        file=sys.stderr,
    )
    print(
        f"  To re-apply flip: "
        f"python3 flip_authority.py --chart-id {chart_id} --generation <gen>",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
