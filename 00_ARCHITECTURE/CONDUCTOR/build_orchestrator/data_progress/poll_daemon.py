#!/usr/bin/env python3
"""
poll_daemon.py — Data-build progress polling daemon v1.1.0.

Polls the production amjis Postgres every POLL_INTERVAL seconds, snapshots:
  - Active build_id + build_events timeline
  - chart_facts row count by (ayanamsha, asset)
  - L2.5 + supplementary table populations
  - Migration status 140-153
  - Two-pass verification distribution
  - Estimated time-remaining

Writes the snapshot to data_build_status.json (atomic temp+rename) and pushes
to GCS bucket marsys-tracker-public so the HTML page can fetch it.

Also writes daemon_heartbeat.json every iteration for liveness detection.

Usage:
  bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/run_daemon.sh

Optional env:
  CHART_ID          (default 362f9f17-95a5-490b-a5a7-027d3e0efda0)
  POLL_INTERVAL_SEC (default 20)
  PSQL_URL          (default uses cloud-sql-proxy + amjis-db-password secret)
  PUSH_TO_GCS       (default true)
  GCS_BUCKET        (default marsys-tracker-public)
"""
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# ── Identity ───────────────────────────────────────────────────────────────
DAEMON_VERSION = "1.1.0"
DAEMON_PID = os.getpid()
DAEMON_STARTED_AT = datetime.now(timezone.utc).isoformat()

# ── Config ─────────────────────────────────────────────────────────────────
CHART_ID = os.environ.get("CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SEC", "20"))
PUSH_TO_GCS = os.environ.get("PUSH_TO_GCS", "true").lower() == "true"
GCS_BUCKET = os.environ.get("GCS_BUCKET", "marsys-tracker-public")

SNAPSHOT_PATH = Path(__file__).parent / "data_build_status.json"
HEARTBEAT_PATH = Path(__file__).parent / "daemon_heartbeat.json"
LOG_PATH = Path(__file__).parent / "daemon.log"
MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MB before rotation

# ── Logging ────────────────────────────────────────────────────────────────
logger = logging.getLogger("poll_daemon")
logger.setLevel(logging.INFO)
_file_handler = RotatingFileHandler(LOG_PATH, maxBytes=MAX_LOG_BYTES, backupCount=3)
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_file_handler)
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_stream_handler)

# ── Graceful shutdown ──────────────────────────────────────────────────────
SHUTDOWN_REQUESTED = False


def _handle_signal(signum, frame):
    global SHUTDOWN_REQUESTED
    SHUTDOWN_REQUESTED = True
    logger.info(f"signal {signum} received — graceful shutdown")


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

# ── Domain constants ───────────────────────────────────────────────────────
EXPECTED_PER_AYANAMSHA = {
    "a3": 8000, "a4": 600, "a5": 13000, "a6": 1500, "a7": 9200,
    "a8": 11000, "a9": 900, "a10": 5000, "a11": 200000, "a12": 250000,
    "a13": 4800, "a15": 1600, "a16": 8000, "a17": 2500, "a18": 5000,
    "a19": 1000, "a20": 750, "a21": 10000, "a22": 750,
}

L25_TABLES = [
    "chart_dashas", "l25_msr_signals", "l25_cdlm_cells", "l25_cdlm_chart_summary",
    "l25_cgm_nodes", "l25_cgm_edges", "l25_cgm_motifs", "l25_cgm_chart_topology_summary",
    "l25_rm_resonances", "l25_rm_remedy_prescriptions", "l25_rm_chart_summary",
    "l1_chakras", "l25_vedha_calculations", "l1_bhrigu_bindu_transits",
    "l1_exact_aspect_lifetime", "l25_time_synchronicity", "l25_phase_locked_event_anchors",
    "l25_per_varsha_digest", "l1_tajik_varsha_year_lords", "l25_vedha_anchor_interactions",
    "l25_pattern_catalog", "l25_divergence_ledger", "l25_negative_space_map",
    "l25_derivation_graph_nodes", "l25_derivation_graph_edges", "l25_chart_lattice_snapshots",
]


# ── Connection ─────────────────────────────────────────────────────────────

def get_psql_url() -> str:
    if os.environ.get("PSQL_URL"):
        return os.environ["PSQL_URL"]
    pw = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest", "--secret=amjis-db-password"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return f"postgresql://amjis_app:{pw}@localhost:5433/amjis"


def get_connection(psql_url: str):
    """Connect to Postgres with exponential-backoff retry. Raises RuntimeError after 5 attempts."""
    for attempt in range(5):
        try:
            conn = psycopg2.connect(psql_url, connect_timeout=10)
            conn.autocommit = True
            return conn
        except psycopg2.OperationalError as e:
            wait = min(2 ** attempt, 30)
            logger.warning(f"connect failed ({e}); retry in {wait}s")
            if attempt == 2:
                logger.warning("PROXY MAY BE DOWN — verify with: pg_isready -h localhost -p 5433")
            time.sleep(wait)
    raise RuntimeError("Could not connect to Postgres after 5 retries")


# ── Heartbeat ──────────────────────────────────────────────────────────────

def write_heartbeat() -> None:
    heartbeat = {
        "daemon_pid": DAEMON_PID,
        "daemon_version": DAEMON_VERSION,
        "daemon_started_at": DAEMON_STARTED_AT,
        "last_heartbeat_at": datetime.now(timezone.utc).isoformat(),
        "poll_interval_sec": POLL_INTERVAL,
        "chart_id": CHART_ID,
    }
    tmp = HEARTBEAT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(heartbeat, indent=2))
    tmp.replace(HEARTBEAT_PATH)


# ── Snapshot ───────────────────────────────────────────────────────────────

def snapshot(conn) -> dict:
    """Build one full snapshot. Each section is independently guarded so schema drift
    on one table cannot kill the whole snapshot."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    out = {
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "chart_id": CHART_ID,
    }

    # 1. Active build_id (most recent in last 24h)
    try:
        cur.execute(
            """
            SELECT build_id, MIN(created_at) AS started_at, MAX(created_at) AS last_event_at
            FROM build_events
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY build_id
            ORDER BY MAX(created_at) DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row:
            out["build"] = {
                "build_id": str(row["build_id"]),
                "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                "last_event_at": row["last_event_at"].isoformat() if row["last_event_at"] else None,
                "elapsed_seconds": (row["last_event_at"] - row["started_at"]).total_seconds() if row["started_at"] else 0,
            }
            bid = row["build_id"]

            # Latest stage
            cur.execute(
                "SELECT asset, stage, status, pct_complete, created_at "
                "FROM build_events WHERE build_id = %s ORDER BY created_at DESC LIMIT 1",
                (bid,),
            )
            latest = cur.fetchone()
            if latest:
                out["build"]["current"] = {
                    "asset": latest["asset"], "stage": latest["stage"],
                    "status": latest["status"],
                    "pct_complete": float(latest["pct_complete"] or 0),
                    "at": latest["created_at"].isoformat(),
                }
                out["build"]["is_complete"] = (
                    latest["status"] in ("success", "completed")
                    and latest["asset"] in ("meta", "_final")
                )
                out["build"]["is_failed"] = latest["status"] in ("failed", "errored")

            # Last 40 events for timeline
            cur.execute(
                "SELECT asset, stage, status, pct_complete, created_at "
                "FROM build_events WHERE build_id = %s ORDER BY created_at DESC LIMIT 40",
                (bid,),
            )
            out["build"]["timeline"] = [
                {
                    "at": r["created_at"].isoformat(), "asset": r["asset"],
                    "stage": r["stage"], "status": r["status"],
                    "pct": float(r["pct_complete"] or 0),
                }
                for r in cur.fetchall()
            ]
        else:
            out["build"] = None
    except Exception as e:
        logger.error(f"build_events query failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        out["build"] = {"error": str(e)[:200]}

    # 2. chart_facts by (ayanamsha, asset_num)
    try:
        cur.execute(
            """
            SELECT ayanamsha_id,
                   SUBSTRING(category FROM '^a([0-9]+)') AS asset_num,
                   COUNT(*)::int AS rows
            FROM chart_facts
            WHERE chart_id = %s
            GROUP BY ayanamsha_id, asset_num
            ORDER BY ayanamsha_id, asset_num
            """,
            (CHART_ID,),
        )
        cf_rows = cur.fetchall()
        out["chart_facts"] = {
            "total_rows": sum(r["rows"] for r in cf_rows),
            "by_ayanamsha_asset": [
                {
                    "ayanamsha": r["ayanamsha_id"],
                    "asset": f"a{r['asset_num']}" if r["asset_num"] else "(unknown)",
                    "rows": r["rows"],
                    "expected": EXPECTED_PER_AYANAMSHA.get(f"a{r['asset_num']}", 0),
                }
                for r in cf_rows
            ],
        }
        by_ay = {}
        expected_total_per_ay = sum(EXPECTED_PER_AYANAMSHA.values())
        for r in cf_rows:
            ay = r["ayanamsha_id"]
            by_ay.setdefault(ay, {"rows": 0, "expected": expected_total_per_ay})
            by_ay[ay]["rows"] += r["rows"]
        out["chart_facts"]["by_ayanamsha_rollup"] = [
            {
                "ayanamsha": ay, "rows": v["rows"], "expected": v["expected"],
                "pct": round(100.0 * v["rows"] / v["expected"], 1) if v["expected"] else 0,
            }
            for ay, v in sorted(by_ay.items())
        ]
    except Exception as e:
        logger.error(f"chart_facts query failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        out["chart_facts"] = {"error": str(e)[:200], "total_rows": 0}

    # 3. Two-pass verification distribution
    try:
        cur.execute(
            """
            SELECT verification_pass_status, COUNT(*)::int AS rows
            FROM chart_facts
            WHERE chart_id = %s
            GROUP BY verification_pass_status
            """,
            (CHART_ID,),
        )
        out.setdefault("chart_facts", {})["verification"] = {
            r["verification_pass_status"] or "(null)": r["rows"] for r in cur.fetchall()
        }
    except Exception as e:
        logger.error(f"verification query failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        out.setdefault("chart_facts", {})["verification"] = {"error": str(e)[:200]}

    # 4. L2.5 + supplementary table populations
    try:
        l25 = []
        for tbl in L25_TABLES:
            try:
                cur.execute(
                    f"SELECT COUNT(*)::int AS rows FROM {tbl} WHERE chart_id = %s",
                    (CHART_ID,),
                )
                r = cur.fetchone()
                l25.append({"table": tbl, "rows": r["rows"]})
            except Exception as e:
                l25.append({"table": tbl, "rows": -1, "error": str(e)[:120]})
                try:
                    conn.rollback()
                except Exception:
                    pass
        out["l25_tables"] = l25
    except Exception as e:
        logger.error(f"l25_tables section failed: {e}")
        out["l25_tables"] = []

    # 5. Migration status 140-153
    try:
        cur.execute(
            """
            SELECT version, applied_at FROM schema_migrations
            WHERE version::text ~ '^14[0-9]$|^15[0-3]$'
            ORDER BY version::int
            """
        )
        applied = {str(r["version"]): r["applied_at"].isoformat() for r in cur.fetchall()}
        out["migrations"] = [
            {"version": v, "applied_at": applied.get(str(v)), "applied": str(v) in applied}
            for v in range(140, 154)
        ]
        out["migrations_applied_count"] = sum(1 for m in out["migrations"] if m["applied"])
    except Exception as e:
        logger.error(f"migrations query failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        out["migrations"] = []
        out["migrations_applied_count"] = 0

    # 6. ETA estimate
    try:
        build_ok = (
            out.get("build")
            and isinstance(out["build"], dict)
            and not out["build"].get("error")
            and out["build"].get("elapsed_seconds", 0) > 30
        )
        if build_ok:
            total_rows_so_far = (out.get("chart_facts") or {}).get("total_rows", 0)
            expected_total = 5 * sum(EXPECTED_PER_AYANAMSHA.values())  # 5 ayanamshas
            if total_rows_so_far > 0 and out["build"]["elapsed_seconds"] > 0:
                rate = total_rows_so_far / out["build"]["elapsed_seconds"]
                remaining = max(0, expected_total - total_rows_so_far)
                eta_s = remaining / rate if rate > 0 else None
                out["eta"] = {
                    "expected_total_rows": expected_total,
                    "actual_rows_so_far": total_rows_so_far,
                    "completion_pct": round(100.0 * total_rows_so_far / expected_total, 1),
                    "rows_per_second": round(rate, 1),
                    "eta_seconds_remaining": int(eta_s) if eta_s else None,
                    "eta_minutes_remaining": int(eta_s / 60) if eta_s else None,
                }
            else:
                out["eta"] = {
                    "expected_total_rows": expected_total,
                    "actual_rows_so_far": 0,
                    "completion_pct": 0,
                }
    except Exception as e:
        logger.error(f"ETA computation failed: {e}")
        out["eta"] = None

    cur.close()
    return out


# ── I/O ────────────────────────────────────────────────────────────────────

def write_snapshot(snap: dict) -> None:
    tmp = SNAPSHOT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snap, indent=2, ensure_ascii=False))
    tmp.replace(SNAPSHOT_PATH)


def push_to_gcs(local_path: Path, remote_name: str = None) -> None:
    if not PUSH_TO_GCS:
        return
    remote = remote_name or local_path.name
    for attempt in range(3):
        try:
            subprocess.run(
                ["gcloud", "storage", "cp", str(local_path),
                 f"gs://{GCS_BUCKET}/{remote}",
                 "--cache-control=no-cache,max-age=0"],
                check=True, capture_output=True, timeout=30,
            )
            return
        except subprocess.SubprocessError as e:
            wait = 2 ** attempt
            logger.warning(
                f"gcs push of {remote} failed (attempt {attempt + 1}): {e}; retry in {wait}s"
            )
            time.sleep(wait)
    logger.error(f"gcs push of {remote} FAILED after 3 attempts (continuing)")


# ── Main loop ──────────────────────────────────────────────────────────────

def main():
    logger.info(
        f"poll_daemon v{DAEMON_VERSION} starting "
        f"pid={DAEMON_PID} chart_id={CHART_ID} interval={POLL_INTERVAL}s gcs={PUSH_TO_GCS}"
    )
    psql_url = get_psql_url()
    conn = None
    while not SHUTDOWN_REQUESTED:
        try:
            # Heartbeat first — written even if DB is down
            write_heartbeat()
            push_to_gcs(HEARTBEAT_PATH, "daemon_heartbeat.json")

            # Reconnect if needed
            if conn is None or conn.closed != 0:
                conn = get_connection(psql_url)

            snap = snapshot(conn)
            snap["_daemon"] = {
                "pid": DAEMON_PID,
                "version": DAEMON_VERSION,
                "started_at": DAEMON_STARTED_AT,
                "poll_interval_sec": POLL_INTERVAL,
            }
            write_snapshot(snap)
            push_to_gcs(SNAPSHOT_PATH, "data_build_status.json")

            # Summary log line
            cf = snap.get("chart_facts") or {}
            total_rows = cf.get("total_rows", 0)
            summary = f"cf={total_rows:>7}"
            build = snap.get("build")
            if build and isinstance(build, dict) and not build.get("error"):
                cur_b = build.get("current") or {}
                summary += (
                    f" | build={build['build_id'][:8]}"
                    f" | {cur_b.get('asset', '?')}/{cur_b.get('stage', '?')}"
                    f"={cur_b.get('pct_complete', 0):.0f}%"
                    f" | elapsed={build.get('elapsed_seconds', 0):.0f}s"
                )
                eta = snap.get("eta") or {}
                if eta.get("eta_minutes_remaining") is not None:
                    summary += f" | eta~{eta['eta_minutes_remaining']}m"
            logger.info(summary)

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"connection lost ({e}); reconnecting next iteration")
            try:
                conn.close()
            except Exception:
                pass
            conn = None
        except Exception as e:
            logger.exception(f"poll iteration failed: {e}")

        # Shutdown-aware sleep: responds to SIGTERM within 1s
        for _ in range(POLL_INTERVAL):
            if SHUTDOWN_REQUESTED:
                break
            time.sleep(1)

    logger.info("poll_daemon shutting down cleanly")
    if conn:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
