"""
pipeline.build_chart — MARSYS-JIS multi-ayanamsha chart build pipeline entrypoint.

Scaffold (C-01): DAG_ORDER, CANONICAL_AYANAMSHAS, arg parse, DB helpers, stub dispatch.
Real writers are registered in later sessions (C-02+).

Usage:
  python -m pipeline.build_chart --build-id <UUID> --chart-id <UUID> [--db-url DSN]
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)

# ── DAG topology ───────────────────────────────────────────────────────────────
# 14 assets in strict topological order.  Each entry is an asset_id that maps to
# exactly one build_steps.category value.  A later session wires each asset_id to
# a concrete writer; until then dispatch_asset() returns 0 (stub).
DAG_ORDER: list[str] = [
    "A1_engine",
    "A2_forensic_render",
    "A3_chart_facts",
    "A4_panchanga",
    "A5_sensitive_points",
    "A6_vargas",
    "A7_dashas",
    "A8_t1_structural",
    "A9_sade_sati",
    "A10_msr",
    "A11_cdlm",
    "A12_cgm",
    "A13_rm",
    "A14_ucn_digest",
]

# ── Canonical ayanamsha list ───────────────────────────────────────────────────
# Must match the DEFAULT stored in builds.ayanamshas JSONB column.
CANONICAL_AYANAMSHAS: list[str] = [
    "lahiri",
    "true_chitra",
    "kp",
    "raman",
    "surya_siddhanta",
]

# ── Human-readable asset labels (used in logging + future UI) ─────────────────
ASSET_LABELS: dict[str, str] = {
    "A1_engine":          "Natal Engine Output",
    "A2_forensic_render": "Forensic Chart Render",
    "A3_chart_facts":     "Chart Facts (L1 Structured)",
    "A4_panchanga":       "Panchanga Daily Entries",
    "A5_sensitive_points":"Sensitive Points & Upagrahas",
    "A6_vargas":          "Varga Divisional Charts",
    "A7_dashas":          "Dasha / Sub-Dasha Chains",
    "A8_t1_structural":   "T1 Structural Combinations",
    "A9_sade_sati":       "Sade-Sati Phases",
    "A10_msr":            "MSR Signal Store",
    "A11_cdlm":           "CDLM Cross-Domain Links",
    "A12_cgm":            "CGM Graph Nodes + Edges",
    "A13_rm":             "RM Resonance Map",
    "A14_ucn_digest":     "UCN Digest",
}

# ── Production default DSN (Cloud SQL via Cloud Run sidecar proxy) ─────────────
_DEFAULT_DSN = (
    "host=127.0.0.1 port=5433 dbname=amjis user=amjis_app "
    "password=aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF"
)


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for build_chart."""
    parser = argparse.ArgumentParser(
        description="MARSYS-JIS multi-ayanamsha chart build pipeline"
    )
    parser.add_argument(
        "--build-id",
        required=True,
        help="Build UUID (must already exist in builds table as 'queued')",
    )
    parser.add_argument(
        "--chart-id",
        required=True,
        help="Chart UUID (must exist in charts table)",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="PostgreSQL DSN override (defaults to DB_URL env var or production DSN)",
    )
    return parser.parse_args(argv)


# ── DB connection ──────────────────────────────────────────────────────────────

def get_db_connection(db_url: Optional[str] = None):
    """
    Return a psycopg2 connection.

    Resolution order:
      1. db_url argument (explicit override)
      2. DB_URL environment variable
      3. _DEFAULT_DSN (production Cloud SQL proxy)

    The caller is responsible for closing the connection.
    """
    try:
        import psycopg2  # type: ignore[import]
    except ImportError:
        try:
            import psycopg as psycopg2  # type: ignore[no-redef]
        except ImportError as exc:
            raise RuntimeError(
                "Neither psycopg2 nor psycopg is installed. "
                "Run: pip install psycopg2-binary"
            ) from exc

    dsn = db_url or os.environ.get("DB_URL") or _DEFAULT_DSN
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    return conn


# ── Build status helpers ───────────────────────────────────────────────────────

def update_build_status(
    conn,
    build_id: str,
    status: str,
    error_summary: Optional[str] = None,
) -> None:
    """
    Update builds.status and the appropriate timestamp column.

    status='running'    → sets started_at
    status='complete'   → sets finished_at
    status='failed'     → sets failed_at (and error_summary if provided)
    status='cancelled'  → sets cancelled_at
    """
    now = datetime.now(timezone.utc)

    timestamp_col_map = {
        "running":   "started_at",
        "complete":  "finished_at",
        "failed":    "failed_at",
        "cancelled": "cancelled_at",
    }
    ts_col = timestamp_col_map.get(status)

    with conn.cursor() as cur:
        if ts_col and error_summary:
            cur.execute(
                f"UPDATE builds SET status=%s, {ts_col}=%s, error_summary=%s WHERE build_id=%s",
                (status, now, error_summary, build_id),
            )
        elif ts_col:
            cur.execute(
                f"UPDATE builds SET status=%s, {ts_col}=%s WHERE build_id=%s",
                (status, now, build_id),
            )
        else:
            cur.execute(
                "UPDATE builds SET status=%s WHERE build_id=%s",
                (status, build_id),
            )
    conn.commit()
    log.info("build_status_updated", extra={"build_id": build_id, "status": status})


# ── Cancellation check ─────────────────────────────────────────────────────────

def check_cancellation(conn, build_id: str) -> bool:
    """
    Return True if builds.status == 'cancelling' (operator-requested cancellation).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT status FROM builds WHERE build_id = %s",
            (build_id,),
        )
        row = cur.fetchone()
    if row is None:
        log.warning("check_cancellation: build_id not found: %s", build_id)
        return False
    return row[0] == "cancelling"


# ── Build step seeding ─────────────────────────────────────────────────────────

def create_build_steps(conn, build_id: str, ayanamshas: list[str]) -> int:
    """
    Insert pending build_steps rows for all 14 assets × N ayanamshas.

    Uses ON CONFLICT DO NOTHING so the function is idempotent.
    Returns the number of rows inserted (0 if all already existed).
    """
    rows = [
        (build_id, ayanamsha, asset_id)
        for asset_id in DAG_ORDER
        for ayanamsha in ayanamshas
    ]
    inserted = 0
    with conn.cursor() as cur:
        for build_id_val, ayanamsha_id, category in rows:
            cur.execute(
                """
                INSERT INTO build_steps (build_id, ayanamsha_id, category, status)
                VALUES (%s, %s, %s, 'queued')
                ON CONFLICT DO NOTHING
                """,
                (build_id_val, ayanamsha_id, category),
            )
            inserted += cur.rowcount
    conn.commit()
    log.info(
        "build_steps_created",
        extra={"build_id": build_id, "rows_inserted": inserted, "total_slots": len(rows)},
    )
    return inserted


# ── Asset dispatch (stub) ──────────────────────────────────────────────────────

def dispatch_asset(
    asset_id: str,
    build_id: str,
    chart_id: str,
    ayanamshas: list[str],
) -> int:
    """
    Dispatch writer for asset_id.

    C-01: Stub — logs that no writer is registered and returns 0 rows_written.
    C-02+: Real writers are registered here per asset_id via a dispatch table.
    """
    label = ASSET_LABELS.get(asset_id, asset_id)
    log.info("[STUB] %s — no writer registered (asset_id=%s)", label, asset_id)
    return 0


# ── Run loop ───────────────────────────────────────────────────────────────────

async def run_build(build_id: str, chart_id: str, conn) -> bool:
    """
    Execute the full DAG for one build.

    Flow:
      1. Fetch ayanamshas from builds table.
      2. Mark build as 'running'.
      3. Iterate DAG_ORDER:
         a. Check for cancellation before each asset.
         b. Mark step 'running', call dispatch_asset, mark step 'complete'.
         c. On exception: mark step 'failed', build 'failed', return False.
      4. On full success: mark build 'complete', return True.
    """
    # 1. Fetch ayanamshas
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ayanamshas FROM builds WHERE build_id = %s",
            (build_id,),
        )
        row = cur.fetchone()
    if row is None:
        log.error("run_build: build_id not found: %s", build_id)
        return False

    import json as _json
    ayanamshas_raw = row[0]
    if isinstance(ayanamshas_raw, str):
        ayanamshas: list[str] = _json.loads(ayanamshas_raw)
    elif isinstance(ayanamshas_raw, list):
        ayanamshas = ayanamshas_raw
    else:
        ayanamshas = list(ayanamshas_raw)

    # 2. Mark running
    update_build_status(conn, build_id, "running")
    log.info("run_build_start", extra={"build_id": build_id, "ayanamshas": ayanamshas})

    # 3. DAG loop
    for asset_id in DAG_ORDER:
        # Cancellation gate
        if check_cancellation(conn, build_id):
            log.info("run_build_cancelling", extra={"build_id": build_id, "at_asset": asset_id})
            # Cancel all pending steps for this build
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE build_steps
                    SET status = 'skipped'
                    WHERE build_id = %s AND status IN ('queued', 'running')
                    """,
                    (build_id,),
                )
            conn.commit()
            update_build_status(conn, build_id, "cancelled")
            return False

        # Mark all ayanamsha-steps for this asset as running
        now = datetime.now(timezone.utc)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE build_steps
                SET status = 'running', started_at = %s
                WHERE build_id = %s AND category = %s AND status = 'queued'
                """,
                (now, build_id, asset_id),
            )
        conn.commit()

        try:
            rows_written = dispatch_asset(asset_id, build_id, chart_id, ayanamshas)
        except Exception as exc:
            log.error(
                "run_build_asset_failed",
                extra={"build_id": build_id, "asset_id": asset_id, "error": str(exc)},
            )
            # Mark step failed
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE build_steps
                    SET status = 'failed', error_msg = %s
                    WHERE build_id = %s AND category = %s AND status = 'running'
                    """,
                    (str(exc), build_id, asset_id),
                )
            conn.commit()
            update_build_status(conn, build_id, "failed", error_summary=str(exc))
            return False

        # Mark steps complete
        completed_at = datetime.now(timezone.utc)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE build_steps
                SET status = 'complete', completed_at = %s, row_count = %s
                WHERE build_id = %s AND category = %s AND status = 'running'
                """,
                (completed_at, rows_written, build_id, asset_id),
            )
        conn.commit()
        log.info(
            "asset_complete",
            extra={"build_id": build_id, "asset_id": asset_id, "rows_written": rows_written},
        )

    # 4. Full success
    update_build_status(conn, build_id, "complete")
    log.info("run_build_complete", extra={"build_id": build_id})
    return True


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    conn = get_db_connection(db_url=args.db_url)
    try:
        # Fetch ayanamshas from DB before seeding steps (they are stored on the build row)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ayanamshas FROM builds WHERE build_id = %s",
                (args.build_id,),
            )
            row = cur.fetchone()
        if row is None:
            log.error("build_id not found in builds table: %s", args.build_id)
            sys.exit(1)

        import json as _json
        ayanamshas_raw = row[0]
        if isinstance(ayanamshas_raw, str):
            ayanamshas: list[str] = _json.loads(ayanamshas_raw)
        elif isinstance(ayanamshas_raw, list):
            ayanamshas = list(ayanamshas_raw)
        else:
            ayanamshas = list(ayanamshas_raw)

        create_build_steps(conn, args.build_id, ayanamshas)
        success = asyncio.run(run_build(args.build_id, args.chart_id, conn))
        sys.exit(0 if success else 1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
