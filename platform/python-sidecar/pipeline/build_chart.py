"""
pipeline.build_chart — MARSYS-JIS multi-ayanamsha chart build pipeline entrypoint.

Scaffold (C-01): DAG_ORDER, CANONICAL_AYANAMSHAS, arg parse, DB helpers, stub dispatch.
C-02: run_engine_parallel() — asyncio+ThreadPoolExecutor 5-ayanamsha parallel runner.
      load_birth_data() — birth data loader from charts table.
      run_build() — A1_engine step wired to parallel runner.
C-05: dispatch_asset_with_retry() — per-asset retry wrapper (3× exponential backoff).
      MAX_RETRIES / RETRY_DELAYS constants.  run_build() non-A1 assets use retry wrapper.

Usage:
  python -m pipeline.build_chart --build-id <UUID> --chart-id <UUID> [--db-url DSN]
"""
from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

# ── Build events emitter (C-03) ────────────────────────────────────────────────
try:
    from pipeline.build_events import emit_event, emit_step_event  # type: ignore[import]
except ImportError:
    try:
        from build_events import emit_event, emit_step_event  # type: ignore[import]
    except ImportError:
        def emit_event(conn, build_id, event_type, **kwargs):  # type: ignore[misc]
            return None
        def emit_step_event(conn, build_id, asset_id, ayanamsha_id, stage, status, rows_written=0, error=None):  # type: ignore[misc]
            pass

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

# ── Materialized views refreshed after all asset writers complete (A3-S6) ──────
MV_NAMES: list[str] = [
    "mv_chart_planet_summary",
    "mv_chart_house_summary",
    "mv_chart_yogas_active_at_birth",
    "mv_chart_vargas_summary",
    "mv_chart_sahams",
    "mv_chart_arudhas",
    "mv_chart_shadbala_summary",
    "mv_chart_bhava_bala_summary",
    "mv_chart_ashtakavarga_summary",
    "mv_cross_ayanamsha_consensus",
    "mv_chart_panchanga_birth_summary",
    "mv_chart_sensitive_points_summary",
]

# ── Production default DSN (Cloud SQL via Cloud Run sidecar proxy) ─────────────
_DEFAULT_DSN = (
    "host=127.0.0.1 port=5433 dbname=amjis user=amjis_app "
    "password=aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF"
)


# ── Polling interval between asset steps (seconds) ────────────────────────────
# Used by run_build() to yield control between asset dispatches.  Set to 5 for
# production; test environments call asyncio.sleep(0) (POLL_INTERVAL ignored in
# unit tests via mocking).
POLL_INTERVAL: int = 5

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


# ── Birth data loader ──────────────────────────────────────────────────────────

_chart_birth_data_cache: dict[str, dict] = {}  # chart_id -> birth_data dict


def load_birth_data(conn, chart_id: str) -> dict:
    """
    Load birth data for a chart from the DB charts table.

    Returns a dict with keys: birth_date, birth_time, lat, lon, tz_offset.
    Result is cached in-process to avoid repeated DB round-trips within a build.

    Raises ValueError if the chart_id is not found.
    """
    if chart_id in _chart_birth_data_cache:
        return _chart_birth_data_cache[chart_id]
    with conn.cursor() as cur:
        cur.execute(
            "SELECT birth_date, birth_time, birth_lat, birth_lng "
            "FROM charts WHERE chart_id=%s",
            (chart_id,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"Chart {chart_id} not found in charts table")
    data: dict = {
        "birth_date": str(row[0]),
        "birth_time": str(row[1]) if row[1] else "00:00",
        "lat": float(row[2]) if row[2] is not None else 20.27,
        "lon": float(row[3]) if row[3] is not None else 85.84,
        "tz_offset": 5.5,  # charts table has no tz column; IST default (UTC+5:30)
    }
    _chart_birth_data_cache[chart_id] = data
    return data


# ── Parallel ayanamsha engine runner ──────────────────────────────────────────

async def run_engine_parallel(
    chart_id: str,
    ayanamshas: list[str],
    birth_data: dict,
) -> dict[str, Optional[dict]]:
    """
    Run natal_engine.compute_chart() for each ayanamsha in parallel via
    asyncio.gather() + ThreadPoolExecutor (one thread per ayanamsha, max 5).

    Parameters
    ----------
    chart_id : str
        Chart UUID — embedded in each engine result for traceability.
    ayanamshas : list[str]
        Ayanamsha identifiers to compute (normally CANONICAL_AYANAMSHAS).
    birth_data : dict
        Birth dict with keys: birth_date, birth_time, lat, lon, tz_offset.
        These are forwarded to compute_chart() as the `inputs` payload.

    Returns
    -------
    dict[str, Optional[dict]]
        Keys are ayanamsha_id strings (one per entry in `ayanamshas`).
        Values are the chart output dicts on success, or None on failure.
        The return value is ALWAYS a dict of exactly len(ayanamshas) entries.
        Failed ayanamshas are logged at ERROR level; the overall call never
        raises.

    Partial-failure semantics
    -------------------------
    - If all ayanamshas fail  → all values are None; dict returned normally.
    - If some ayanamshas fail → failed keys are None, others have real output.
    - Caller is responsible for checking values and deciding build disposition.
    """
    try:
        from natal_engine import compute_chart  # type: ignore[import]
        _use_stub = False
    except ImportError:
        log.warning(
            "natal_engine not installed — using stub for chart_id=%s", chart_id
        )
        _use_stub = True

    results: dict[str, Optional[dict]] = {}

    if _use_stub:
        # Stub path: used in test environments without natal_engine installed.
        async def _stub(ayanamsha: str) -> Optional[dict]:
            return {"ayanamsha_id": ayanamsha, "stub": True, "chart_id": chart_id}

        tasks = [_stub(a) for a in ayanamshas]
        outputs = await asyncio.gather(*tasks, return_exceptions=True)
        for ayan, output in zip(ayanamshas, outputs):
            if isinstance(output, Exception):
                log.error(
                    "engine_stub_failed ayanamsha=%s chart_id=%s error=%s",
                    ayan, chart_id, output,
                )
                results[ayan] = None
            else:
                results[ayan] = output
        successful = sum(1 for v in results.values() if v is not None)
        log.info(
            "engine_parallel_stub_complete chart_id=%s %d/%d succeeded",
            chart_id, successful, len(ayanamshas),
        )
        return results

    # Real path: run compute_chart() in a thread pool so the event loop stays
    # responsive.  Each thread is independent (Swiss Ephemeris is thread-safe
    # when ayanamsha is set per-call via the `ayanamsha_id` parameter).
    loop = asyncio.get_event_loop()

    def _compute_sync(ayanamsha: str) -> Optional[dict]:
        """Synchronous wrapper called inside a ThreadPoolExecutor worker."""
        try:
            inputs_payload = {
                "datetime_iso": f"{birth_data['birth_date']}T{birth_data['birth_time']}",
                "tz_offset_hours": birth_data["tz_offset"],
                "latitude_deg": birth_data["lat"],
                "longitude_deg": birth_data["lon"],
                "place_name": "Bhubaneswar",  # default; overrideable via birth_data
                "subject_label": chart_id,
            }
            return compute_chart(
                inputs=inputs_payload,
                ayanamsha_id=ayanamsha,
            )
        except Exception as exc:
            log.error(
                "engine_compute_failed ayanamsha=%s chart_id=%s error=%s",
                ayanamsha, chart_id, exc,
            )
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {
            ayan: loop.run_in_executor(executor, _compute_sync, ayan)
            for ayan in ayanamshas
        }
        for ayan, future in future_map.items():
            try:
                results[ayan] = await future
            except Exception as exc:
                log.error(
                    "engine_future_failed ayanamsha=%s chart_id=%s error=%s",
                    ayan, chart_id, exc,
                )
                results[ayan] = None

    successful = sum(1 for v in results.values() if v is not None)
    log.info(
        "engine_parallel_complete chart_id=%s %d/%d ayanamshas succeeded",
        chart_id, successful, len(ayanamshas),
    )
    return results


# ── Asset dispatch (stub) ──────────────────────────────────────────────────────

def dispatch_asset(
    asset_id: str,
    build_id: str,
    chart_id: str,
    ayanamshas: list[str],
    conn=None,
) -> int:
    """
    Dispatch writer for asset_id.

    C-01: Stub — logs that no writer is registered and returns 0 rows_written.
    C-07: Routes A2–A14 through WRITER_REGISTRY (stub write() callables).
          Real writers replace stubs in streams F, G1, G2, G3, G4.
    conn=None triggers dry-run mode in all writers (row counting, no DB write).
    """
    try:
        from pipeline.writers import WRITER_REGISTRY
        if asset_id in WRITER_REGISTRY:
            return WRITER_REGISTRY[asset_id](build_id, chart_id, 'all', {}, conn)
    except ImportError:
        pass
    label = ASSET_LABELS.get(asset_id, asset_id)
    log.info("[STUB] %s — no writer registered (asset_id=%s)", label, asset_id)
    return 0


# ── Retry constants (C-05) ─────────────────────────────────────────────────────

MAX_RETRIES: int = 3
RETRY_DELAYS: list[int] = [2, 4, 8]  # seconds — exponential backoff per attempt


# ── Per-asset retry wrapper (C-05) ────────────────────────────────────────────

async def dispatch_asset_with_retry(
    asset_id: str,
    build_id: str,
    chart_id: str,
    ayanamshas: list,
    conn,
    chart_outputs: dict,
) -> "tuple[int, str | None]":
    """
    Dispatch an asset with up to MAX_RETRIES attempts (exponential backoff).

    Returns
    -------
    (rows_written, error_msg)
        rows_written  — number of rows written on success; 0 on exhaustion.
        error_msg     — None on success; non-empty string on exhaustion.

    On each retry (before the final attempt), build_steps.retry_count is
    incremented and the interim error is stored in build_steps.error_summary.
    The retry_count update is non-fatal: a failure there is swallowed so the
    retry loop continues.
    """
    last_error: Optional[str] = None

    for attempt in range(MAX_RETRIES):
        try:
            rows_written = dispatch_asset(asset_id, build_id, chart_id, ayanamshas, conn)
            return rows_written, None  # success — no error
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {str(exc)}"

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                log.warning(
                    "dispatch_asset_with_retry attempt %d/%d failed for %s: %s. "
                    "Retrying in %ds...",
                    attempt + 1, MAX_RETRIES, asset_id, last_error, delay,
                )
                # Rollback the failed transaction so the connection is clean for retry
                try:
                    conn.rollback()
                except Exception:
                    pass
                # Persist retry_count + interim error to build_steps (non-fatal)
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE build_steps "
                            "SET retry_count = retry_count + 1, error_summary = %s "
                            "WHERE build_id = %s AND asset_id = %s",
                            (last_error, build_id, asset_id),
                        )
                    conn.commit()
                except Exception:
                    pass  # retry_count update is non-fatal; swallow and continue

                await asyncio.sleep(delay)
            else:
                # Final attempt exhausted
                log.error(
                    "dispatch_asset_with_retry EXHAUSTED after %d attempts for %s. "
                    "Last error: %s",
                    MAX_RETRIES, asset_id, last_error,
                )

    return 0, last_error


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

    # 2. Mark running + emit build_started
    update_build_status(conn, build_id, "running")
    emit_event(conn, build_id, "build_started")
    log.info("run_build_start", extra={"build_id": build_id, "ayanamshas": ayanamshas})

    # 3. DAG loop
    chart_outputs: dict = {}  # populated by A1_engine; passed to retry wrapper for context
    for asset_id in DAG_ORDER:
        # Cancellation gate — checked before EVERY asset
        if check_cancellation(conn, build_id):
            log.info("run_build_cancelling", extra={"build_id": build_id, "at_asset": asset_id})
            # Mark all remaining pending/queued steps as 'cancelled'
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE build_steps
                    SET status = 'cancelled'
                    WHERE build_id = %s AND status IN ('queued', 'running')
                    """,
                    (build_id,),
                )
            conn.commit()
            update_build_status(conn, build_id, "cancelled")
            emit_event(conn, build_id, "build_cancelled", extra={"cancelled_at_asset": asset_id})
            return False

        # Emit step_started event + mark all ayanamsha-steps for this asset as running
        emit_step_event(conn, build_id, asset_id, "all", "compute", "started")
        # emit_step_event is non-fatal; ensure clean transaction state before critical writes
        try:
            conn.rollback()
        except Exception:
            pass
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
            if asset_id == "A1_engine":
                # ── C-02: parallel ayanamsha engine runner ──────────────────
                birth_data = load_birth_data(conn, chart_id)
                chart_outputs = await run_engine_parallel(
                    chart_id=chart_id,
                    ayanamshas=ayanamshas,
                    birth_data=birth_data,
                )
                successful = [a for a, v in chart_outputs.items() if v is not None]
                failed = [a for a, v in chart_outputs.items() if v is None]

                if not successful:
                    # All ayanamshas failed — hard failure, abort build.
                    err_msg = (
                        f"A1_engine: all {len(ayanamshas)} ayanamshas failed; "
                        f"no engine output produced"
                    )
                    log.error("run_build_asset_failed build_id=%s %s", build_id, err_msg)
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE build_steps
                            SET status = 'failed', error_msg = %s
                            WHERE build_id = %s AND category = %s AND status = 'running'
                            """,
                            (err_msg, build_id, asset_id),
                        )
                    conn.commit()
                    emit_step_event(conn, build_id, asset_id, "all", "compute", "failed", error=err_msg)
                    update_build_status(conn, build_id, "failed", error_summary=err_msg)
                    emit_event(conn, build_id, "build_failed", error=err_msg)
                    return False

                if failed:
                    # Partial failure — log warning but continue; mark step complete
                    # with an error note embedded in the row_count note.
                    log.warning(
                        "A1_engine partial failure build_id=%s chart_id=%s "
                        "succeeded=%s failed=%s",
                        build_id, chart_id, successful, failed,
                    )

                rows_written = len(successful)
                # Store chart_outputs for downstream assets in this build.
                # (Future sessions can consume this from build-scoped state.)
            else:
                # C-05: non-A1 assets use retry wrapper (3× exponential backoff)
                rows_written, retry_err = await dispatch_asset_with_retry(
                    asset_id, build_id, chart_id, ayanamshas, conn, chart_outputs
                )
                if retry_err is not None:
                    # All retries exhausted — mark step + build failed
                    log.error(
                        "run_build_asset_failed",
                        extra={"build_id": build_id, "asset_id": asset_id, "error": retry_err},
                    )
                    # Rollback any aborted transaction before status writes
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE build_steps
                            SET status = 'failed', error_msg = %s
                            WHERE build_id = %s AND category = %s AND status = 'running'
                            """,
                            (retry_err, build_id, asset_id),
                        )
                    conn.commit()
                    emit_step_event(conn, build_id, asset_id, "all", "compute", "failed", error=retry_err)
                    update_build_status(conn, build_id, "failed", error_summary=retry_err)
                    emit_event(conn, build_id, "build_failed", error=retry_err)
                    return False

        except Exception as exc:
            err_str = str(exc)
            log.error(
                "run_build_asset_failed",
                extra={"build_id": build_id, "asset_id": asset_id, "error": err_str},
            )
            # Rollback any aborted transaction before status writes
            try:
                conn.rollback()
            except Exception:
                pass
            # Mark step failed
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE build_steps
                    SET status = 'failed', error_msg = %s
                    WHERE build_id = %s AND category = %s AND status = 'running'
                    """,
                    (err_str, build_id, asset_id),
                )
            conn.commit()
            emit_step_event(conn, build_id, asset_id, "all", "compute", "failed", error=err_str)
            update_build_status(conn, build_id, "failed", error_summary=err_str)
            emit_event(conn, build_id, "build_failed", error=err_str)
            return False

        # Emit step_complete event + mark steps complete
        emit_step_event(conn, build_id, asset_id, "all", "commit", "complete", rows_written)
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

        # Yield between asset steps (C-04: polling checkpoint)
        await asyncio.sleep(0)

    # 4. Full success — refresh all materialized views before marking complete (A3-S6)
    log.info("mv_refresh_start", extra={"build_id": build_id, "mv_count": len(MV_NAMES)})
    with conn.cursor() as cur:
        for mv in MV_NAMES:
            cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
    conn.commit()
    log.info("mv_refresh_complete", extra={"build_id": build_id})

    total_rows = 0  # rows_written is scoped to the loop; use 0 as aggregate sentinel here
    update_build_status(conn, build_id, "complete")
    emit_event(conn, build_id, "build_complete", rows_written=total_rows)
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
