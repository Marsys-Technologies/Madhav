#!/usr/bin/env python3
"""
poll_daemon.py — Data-build progress polling daemon v1.2.0.

Polls the production amjis Postgres every POLL_INTERVAL seconds, snapshots:
  - Active build_id + build_events timeline
  - Per-asset structured status (brief/code/data) across L1/L2.5/L3 layers
  - L4 retrieval surface status
  - Migration status 140-153
  - Legacy chart_facts matrix (retained for backward compat)

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
DAEMON_VERSION = "1.2.0"
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
TRACKER_STATE_PATH = Path(__file__).parent.parent / "tracker" / "state.json"
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

# ── Asset Registry ─────────────────────────────────────────────────────────
ASSET_REGISTRY = {
    # ── Layer L1 — Raw Facts ─────────────────────────────────────────────────
    "A1":  {"layer": "L1", "name": "Engine (Swiss Ephemeris)",
            "description": "5-ayanamsha compute pass; positions, houses, ASC/MC",
            "deps": [], "tables": [],
            "data_check_kind": "chart_facts_category", "category_prefix": "a1",
            "expected_per_ayanamsha": 1, "expected_per_chart": 5},
    "A2":  {"layer": "L1", "name": "FORENSIC.md Render",
            "description": "Per-ayanamsha canonical chart markdown",
            "deps": ["A1", "A3"], "tables": [],
            "data_check_kind": "chart_facts_category", "category_prefix": "a2",
            "expected_per_ayanamsha": 1, "expected_per_chart": 5},
    "A3":  {"layer": "L1", "name": "chart_facts (base)",
            "description": "147 fact categories — base substrate",
            "deps": ["A1"], "tables": ["chart_facts"],
            "data_check_kind": "chart_facts_category", "category_prefix": "a3",
            "expected_per_ayanamsha": 7000, "expected_per_chart": 35000},
    "A4":  {"layer": "L1", "name": "Panchanga",
            "description": "32 categories: tithi, vara, hora, inauspicious/auspicious windows",
            "deps": ["A1"], "tables": ["chart_facts"],
            "data_check_kind": "chart_facts_category", "category_prefix": "a4",
            "expected_per_ayanamsha": 600, "expected_per_chart": 3000},
    "A5":  {"layer": "L1", "name": "Sensitive Points",
            "description": "30 categories: sahams, arudhas, upagrahas, midpoints, KP",
            "deps": ["A1", "A3"], "tables": ["chart_facts"],
            "data_check_kind": "chart_facts_category", "category_prefix": "a5",
            "expected_per_ayanamsha": 13000, "expected_per_chart": 65000},
    "A6":  {"layer": "L1", "name": "Vargas (30 divisional)",
            "description": "16 Parashari + 11 supplementary + 3 Nadi",
            "deps": ["A1"], "tables": ["chart_facts"],
            "data_check_kind": "chart_facts_category", "category_prefix": "a6",
            "expected_per_ayanamsha": 1500, "expected_per_chart": 7500},
    "A7":  {"layer": "L1", "name": "Dashas (7 systems)",
            "description": "Vimshottari+Yogini+Ashtottari+Chara+Naisargika+Mudda+Kalachakra",
            "deps": ["A1"], "tables": ["chart_dashas"],
            "data_check_kind": "table_chart_id", "table_name": "chart_dashas",
            "expected_per_ayanamsha": 9200, "expected_per_chart": 46000},
    "A8":  {"layer": "L1", "name": "T1 Structural",
            "description": "Aspects + shadbala + ashtakavarga + 200+ yogas + doshas",
            "deps": ["A3", "A6", "A7"], "tables": ["chart_facts"],
            "data_check_kind": "chart_facts_category", "category_prefix": "a8",
            "expected_per_ayanamsha": 11000, "expected_per_chart": 55000},
    "A9":  {"layer": "L1", "name": "Sade Sati Cycles",
            "description": "Saturn-Moon configurations + cancellations + phase intensity",
            "deps": ["A7"], "tables": ["chart_facts"],
            "data_check_kind": "chart_facts_category", "category_prefix": "a9",
            "expected_per_ayanamsha": 900, "expected_per_chart": 4500},
    "A17": {"layer": "L1", "name": "Chakras (geometric)",
            "description": "Sarvatobhadra + Sapta-shalaka + Kalanala + Kota + Chandra Kala Nadi",
            "deps": ["A3"], "tables": ["l1_chakras"],
            "data_check_kind": "table_chart_id", "table_name": "l1_chakras",
            "expected_per_ayanamsha": 500, "expected_per_chart": 2500},
    "A19": {"layer": "L1", "name": "Bhrigu Bindu Transits",
            "description": "Lifetime transit hits to natal Bhrigu Bindu midpoint",
            "deps": ["A5"], "tables": ["l1_bhrigu_bindu_transits"],
            "data_check_kind": "table_chart_id", "table_name": "l1_bhrigu_bindu_transits",
            "expected_per_ayanamsha": 200, "expected_per_chart": 1000},
    "A20": {"layer": "L1", "name": "Tajik Varsha Year-Lords",
            "description": "Hadda + varsha year-lord + Muntha per year (150 yrs)",
            "deps": ["A1", "A8"], "tables": ["l1_tajik_varsha_year_lords"],
            "data_check_kind": "table_chart_id", "table_name": "l1_tajik_varsha_year_lords",
            "expected_per_ayanamsha": 150, "expected_per_chart": 750},
    "A21": {"layer": "L1", "name": "Exact-Aspect Lifetime",
            "description": "Per-graha next-exact-aspect 1950-2100 (Parashari + Tajik)",
            "deps": ["A1"], "tables": ["l1_exact_aspect_lifetime"],
            "data_check_kind": "table_chart_id", "table_name": "l1_exact_aspect_lifetime",
            "expected_per_ayanamsha": 10000, "expected_per_chart": 50000},

    # ── Layer L2.5 — Holistic Synthesis ──────────────────────────────────────
    "A10": {"layer": "L2.5", "name": "MSR (Multi-System Register)",
            "description": "Salience-ranked signals from MSR formula v1",
            "deps": ["A4", "A5", "A6", "A7", "A8", "A9"], "tables": ["l25_msr_signals"],
            "data_check_kind": "table_chart_id", "table_name": "l25_msr_signals",
            "expected_per_ayanamsha": 1000, "expected_per_chart": 5000},
    "A11": {"layer": "L2.5", "name": "CDLM (Cross-Domain Linkage)",
            "description": "9×9 + 27×27 sub-domain + 3-system Maha snapshots + per-tradition",
            "deps": ["A10"], "tables": ["l25_cdlm_cells", "l25_cdlm_chart_summary"],
            "data_check_kind": "table_chart_id", "table_name": "l25_cdlm_cells",
            "expected_per_ayanamsha": 42000, "expected_per_chart": 210000},
    "A12": {"layer": "L2.5", "name": "CGM (Chart Graph Model)",
            "description": "Nodes + 24 edge types + motifs + sub-graphs + topology summary",
            "deps": ["A11"],
            "tables": ["l25_cgm_nodes", "l25_cgm_edges", "l25_cgm_motifs", "l25_cgm_chart_topology_summary"],
            "data_check_kind": "table_chart_id", "table_name": "l25_cgm_nodes",
            "expected_per_ayanamsha": 56000, "expected_per_chart": 280000},
    "A13": {"layer": "L2.5", "name": "RM (Resonance Map)",
            "description": "6 traditions × 18 categories × per-graha prescriptions",
            "deps": ["A11", "A12"],
            "tables": ["l25_rm_resonances", "l25_rm_remedy_prescriptions", "l25_rm_chart_summary"],
            "data_check_kind": "table_chart_id", "table_name": "l25_rm_resonances",
            "expected_per_ayanamsha": 955, "expected_per_chart": 4775},
    "A14": {"layer": "L2.5", "name": "UCD (Unified Chart Digest)", "retired": True,
            "description": "RETIRED — 5 unique items folded into A8/A11/A12 chart_summaries",
            "deps": ["A8", "A11", "A12"], "tables": [],
            "data_check_kind": "none",
            "expected_per_ayanamsha": 0, "expected_per_chart": 0},
    "A15": {"layer": "L2.5", "name": "Time-Synchronicity Stack",
            "description": "Multi-cycle convergence windows 1950-2100",
            "deps": ["A7", "A4", "A9", "A18", "A19", "A21"], "tables": ["l25_time_synchronicity"],
            "data_check_kind": "table_chart_id", "table_name": "l25_time_synchronicity",
            "expected_per_ayanamsha": 300, "expected_per_chart": 1500},
    "A16": {"layer": "L2.5", "name": "Phase-Locked Event Anchors",
            "description": "Predicted-event lattice with falsifiability per anchor",
            "deps": ["A15", "A7", "A8", "A9", "A11", "A12"], "tables": ["l25_phase_locked_event_anchors"],
            "data_check_kind": "table_chart_id", "table_name": "l25_phase_locked_event_anchors",
            "expected_per_ayanamsha": 1600, "expected_per_chart": 8000},
    "A18": {"layer": "L2.5", "name": "Vedha Calculations",
            "description": "6 vedha types (nakshatra/tajik/dasha/transit/sapta-shalaka/argala)",
            "deps": ["A17", "A8"], "tables": ["l25_vedha_calculations"],
            "data_check_kind": "table_chart_id", "table_name": "l25_vedha_calculations",
            "expected_per_ayanamsha": 1000, "expected_per_chart": 5000},
    "A22": {"layer": "L2.5", "name": "Per-Varsha Yearly Digest",
            "description": "Yearly summary joining all temporal sources + active dashas",
            "deps": ["A15", "A16", "A18", "A19", "A20", "A21", "A7", "A9"],
            "tables": ["l25_per_varsha_digest"],
            "data_check_kind": "table_chart_id", "table_name": "l25_per_varsha_digest",
            "expected_per_ayanamsha": 150, "expected_per_chart": 750},

    # ── Layer L3 — META Synthesis ────────────────────────────────────────────
    "META_ALPHA": {"layer": "L3", "name": "META-α LATTICE",
            "description": "Moment-in-time joined view across A7/A11/A12/A13/A15/A16/A8/A9/A4",
            "deps": ["A7", "A11", "A12", "A13", "A15", "A16", "A8", "A9", "A4"],
            "tables": ["l25_chart_lattice_snapshots"],
            "data_check_kind": "table_chart_id", "table_name": "l25_chart_lattice_snapshots",
            "expected_per_ayanamsha": 220, "expected_per_chart": 1100},
    "META_BETA": {"layer": "L3", "name": "META-β PATTERN_CATALOG",
            "description": "16 pattern_kinds unified — yogas, motifs, magnifications, anchors",
            "deps": ["A8", "A10", "A11", "A12", "A13", "A15", "A16", "A18", "A19"],
            "tables": ["l25_pattern_catalog"],
            "data_check_kind": "table_chart_id", "table_name": "l25_pattern_catalog",
            "expected_per_ayanamsha": 150, "expected_per_chart": 750},
    "META_GAMMA": {"layer": "L3", "name": "META-γ DIVERGENCE_LEDGER",
            "description": "Cross-system disagreement audit trail (tradition/ayanamsha/temporal)",
            "deps": ["A10", "A11", "A12", "A13", "A15", "A16"],
            "tables": ["l25_divergence_ledger"],
            "data_check_kind": "table_chart_id", "table_name": "l25_divergence_ledger",
            "expected_per_ayanamsha": 20, "expected_per_chart": 100},
    "META_DELTA": {"layer": "L3", "name": "META-δ NEGATIVE_SPACE_MAP",
            "description": "Absence-as-feature (no exalted graha, no fired raja yoga, etc.)",
            "deps": ["A3", "A6", "A8", "A11", "A12"],
            "tables": ["l25_negative_space_map"],
            "data_check_kind": "table_chart_id", "table_name": "l25_negative_space_map",
            "expected_per_ayanamsha": 15, "expected_per_chart": 75},
    "META_EPSILON": {"layer": "L3", "name": "META-ε DERIVATION_TRAIL",
            "description": "L1 fact → L2.5 claim DAG with corpus citations",
            "deps": ["ALL_L25"],
            "tables": ["l25_derivation_graph_nodes", "l25_derivation_graph_edges"],
            "data_check_kind": "table_chart_id", "table_name": "l25_derivation_graph_nodes",
            "expected_per_ayanamsha": 5400, "expected_per_chart": 27000},
    "META_ZETA": {"layer": "L3", "name": "META-ζ TEMPORAL_UNIFIED_LATTICE",
            "description": "Range-query view across A15/A16/A18/A19/A20/A21/A22 (UTEE envelope)",
            "deps": ["A15", "A16", "A18", "A19", "A20", "A21", "A22"],
            "tables": [],  # vw_temporal_unified_lattice is a VIEW
            "data_check_kind": "view_exists", "view_name": "vw_temporal_unified_lattice",
            "expected_per_ayanamsha": 0, "expected_per_chart": 0},
}

L4_RETRIEVAL_SURFACES = [
    {"id": "mcp_tools", "name": "MCP Tool Registry",
     "description": "~57 tools = 40 base + 17 new (META+UTEE+bridge)", "status_kind": "static_shipped"},
    {"id": "channel_adapters", "name": "Channel Adapters",
     "description": "5 channels: chat/report/visual/audio/dashboard", "status_kind": "static_shipped"},
    {"id": "tier_filtering", "name": "Tier Filtering",
     "description": "3 tiers: super_admin/acharya/client", "status_kind": "static_shipped"},
    {"id": "utee_envelope", "name": "UTEE Envelope Standard",
     "description": "Unified Temporal Event Envelope columns on 7 temporal tables",
     "status_kind": "migration_applied", "migration": "149"},
    {"id": "materialized_views", "name": "Materialized Views",
     "description": "mv_chart_lattice + 11 others", "status_kind": "mv_count"},
]

# Retained for backward compat / legacy chart_facts matrix
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


# ── Asset status helpers ───────────────────────────────────────────────────

def load_tracker_data() -> dict:
    """Load state.json from implementation tracker. Returns {asset_id: item_dict}."""
    tracker_data = {}
    try:
        if TRACKER_STATE_PATH.exists():
            t = json.loads(TRACKER_STATE_PATH.read_text())
            for tr in t.get("tracks", []):
                for it in tr.get("items", []):
                    tracker_data[it["id"]] = it
    except Exception as e:
        logger.warning(f"tracker state.json load failed: {e}")
    return tracker_data


def compute_asset_status(cur, asset_id: str, meta: dict, tracker_data: dict) -> dict:
    """Compute structured status for one asset. Returns dict with brief/code/data + deps + blockers."""
    out = {
        "id": asset_id,
        "layer": meta["layer"],
        "name": meta["name"],
        "description": meta["description"],
        "deps": meta.get("deps", []),
        "retired": meta.get("retired", False),
        "expected_per_chart": meta.get("expected_per_chart", 0),
    }

    # Brief + code status from tracker state.json
    tracker_item = tracker_data.get(asset_id, {})
    out["brief_status"] = tracker_item.get("brief", {}).get("status", "unknown")
    out["impl_status"] = tracker_item.get("impl", {}).get("status", "unknown")

    # Data status from DB
    rows = 0
    if meta.get("retired"):
        out["data_status"] = "retired"
        out["rows"] = 0
        out["completion_pct"] = 0
        return out

    kind = meta["data_check_kind"]

    if kind == "none":
        out["data_status"] = "n/a"
        out["rows"] = 0
        out["completion_pct"] = 0
        return out

    if kind == "chart_facts_category":
        try:
            cur.execute(
                "SELECT COUNT(*) FROM chart_facts WHERE chart_id = %s AND category LIKE %s",
                (CHART_ID, meta["category_prefix"] + "_%")
            )
            rows = cur.fetchone()[0]
        except Exception as e:
            out["data_error"] = str(e)[:100]
            out["data_status"] = "error"
            out["rows"] = 0
            out["completion_pct"] = 0
            return out

    elif kind == "table_chart_id":
        try:
            cur.execute(
                f"SELECT COUNT(*) FROM {meta['table_name']} WHERE chart_id = %s",
                (CHART_ID,)
            )
            rows = cur.fetchone()[0]
        except Exception as e:
            out["data_error"] = str(e)[:100]
            out["data_status"] = "error"
            out["rows"] = 0
            out["completion_pct"] = 0
            return out

    elif kind == "view_exists":
        try:
            cur.execute(
                "SELECT 1 FROM pg_views WHERE viewname = %s",
                (meta.get("view_name"),)
            )
            view_present = cur.fetchone() is not None
            out["data_status"] = "view_present" if view_present else "view_missing"
            out["rows"] = 1 if view_present else 0
            out["completion_pct"] = 100 if view_present else 0
            return out
        except Exception as e:
            out["data_error"] = str(e)[:100]
            out["data_status"] = "error"
            out["rows"] = 0
            out["completion_pct"] = 0
            return out

    out["rows"] = rows
    expected = meta.get("expected_per_chart", 0)
    if expected == 0:
        out["data_status"] = "n/a"
        out["completion_pct"] = 0
    elif rows == 0:
        out["data_status"] = "empty"
        out["completion_pct"] = 0
    elif rows < expected * 0.5:
        out["data_status"] = "partial"
        out["completion_pct"] = round(100.0 * rows / expected, 1)
    elif rows < expected * 0.95:
        out["data_status"] = "near_complete"
        out["completion_pct"] = round(100.0 * rows / expected, 1)
    else:
        out["data_status"] = "complete"
        out["completion_pct"] = round(100.0 * rows / expected, 1)

    return out


def compute_blockers(asset_statuses: dict) -> None:
    """Walk dependencies. For each non-complete asset, identify which deps are also non-complete."""
    l25_ids = [aid for aid, m in ASSET_REGISTRY.items() if m["layer"] == "L2.5"]
    for asset_id, status in asset_statuses.items():
        if status.get("data_status") in ("complete", "n/a", "retired", "view_present"):
            status["blocked_by"] = []
            status["ready_to_run"] = False
            continue
        deps = list(status.get("deps", []))
        if "ALL_L25" in deps:
            deps = [d for d in deps if d != "ALL_L25"] + l25_ids
        blockers = []
        for dep in deps:
            if dep not in asset_statuses:
                continue
            dep_status = asset_statuses[dep].get("data_status", "unknown")
            if dep_status not in ("complete", "near_complete", "n/a", "retired", "view_present"):
                blockers.append({
                    "id": dep,
                    "status": dep_status,
                    "rows": asset_statuses[dep].get("rows", 0),
                })
        status["blocked_by"] = blockers
        status["ready_to_run"] = len(blockers) == 0


# ── Snapshot ───────────────────────────────────────────────────────────────

def snapshot(conn) -> dict:
    """Build one full snapshot. Each section is independently guarded so schema drift
    on one table cannot kill the whole snapshot."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    out = {
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "chart_id": CHART_ID,
        "_daemon": {
            "pid": DAEMON_PID,
            "version": DAEMON_VERSION,
            "started_at": DAEMON_STARTED_AT,
            "poll_interval_sec": POLL_INTERVAL,
        },
    }

    # 1. Active build_id (most recent in last 24h)
    try:
        cur.execute(
            """
            SELECT build_id, MIN(created_at) AS started_at, MAX(created_at) AS last_event_at,
                   COUNT(*) FILTER (WHERE status IN ('failed','errored')) > 0 AS has_failure
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
                "has_failure": row["has_failure"],
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
                    and latest["asset"] in ("meta", "_final", "_complete")
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

    # 2. Per-asset structured status (L1 / L2.5 / L3)
    tracker_data = load_tracker_data()
    asset_statuses = {}

    # Use a plain cursor (not RealDictCursor) for the asset queries so we can use fetchone()[0]
    plain_cur = conn.cursor()
    for aid, meta in ASSET_REGISTRY.items():
        try:
            asset_statuses[aid] = compute_asset_status(plain_cur, aid, meta, tracker_data)
        except Exception as e:
            logger.exception(f"compute_asset_status({aid}) failed: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
            asset_statuses[aid] = {
                "id": aid, "layer": meta["layer"], "name": meta["name"],
                "description": meta.get("description", ""),
                "deps": meta.get("deps", []),
                "retired": meta.get("retired", False),
                "error": str(e)[:200],
                "data_status": "error", "rows": 0,
                "brief_status": "unknown", "impl_status": "unknown",
                "expected_per_chart": meta.get("expected_per_chart", 0),
            }

    compute_blockers(asset_statuses)
    out["assets"] = asset_statuses

    # Group by layer
    out["layers"] = {
        "L1": [a for a in asset_statuses.values() if a.get("layer") == "L1"],
        "L2.5": [a for a in asset_statuses.values() if a.get("layer") == "L2.5"],
        "L3": [a for a in asset_statuses.values() if a.get("layer") == "L3"],
    }

    # Top-level summary
    all_assets = list(asset_statuses.values())
    out["summary"] = {
        "total_assets": len(all_assets),
        "complete": sum(1 for a in all_assets if a.get("data_status") == "complete"),
        "near_complete": sum(1 for a in all_assets if a.get("data_status") == "near_complete"),
        "partial": sum(1 for a in all_assets if a.get("data_status") == "partial"),
        "empty": sum(1 for a in all_assets if a.get("data_status") == "empty"),
        "ready_to_run": [
            a["id"] for a in all_assets
            if a.get("ready_to_run") and a.get("data_status") == "empty"
        ],
        "blocked": sum(1 for a in all_assets if a.get("blocked_by")),
    }

    plain_cur.close()

    # 3. Legacy chart_facts matrix (retained for backward compat)
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

    # 4. Two-pass verification distribution
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

    # 5. Legacy L2.5 + supplementary table populations (retained for backward compat)
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

    # 6. Migration status 140-153
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

    # 7. L4 retrieval surface status
    l4_plain = conn.cursor()
    l4_surfaces = []
    for surf in L4_RETRIEVAL_SURFACES:
        status = {"id": surf["id"], "name": surf["name"], "description": surf["description"]}
        if surf["status_kind"] == "mv_count":
            try:
                l4_plain.execute("SELECT COUNT(*) FROM pg_matviews WHERE schemaname='public'")
                status["count"] = l4_plain.fetchone()[0]
                status["status"] = "deployed"
            except Exception as e:
                status["error"] = str(e)[:100]
                status["status"] = "error"
                try:
                    conn.rollback()
                except Exception:
                    pass
        elif surf["status_kind"] == "migration_applied":
            try:
                l4_plain.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = %s",
                    (surf["migration"],)
                )
                status["status"] = "applied" if l4_plain.fetchone() else "pending"
            except Exception as e:
                status["error"] = str(e)[:100]
                status["status"] = "error"
                try:
                    conn.rollback()
                except Exception:
                    pass
        else:
            status["status"] = "shipped"
        l4_surfaces.append(status)
    l4_plain.close()
    out["l4_surfaces"] = l4_surfaces

    # 8. ETA estimate (retained)
    try:
        build_ok = (
            out.get("build")
            and isinstance(out["build"], dict)
            and not out["build"].get("error")
            and out["build"].get("elapsed_seconds", 0) > 30
        )
        if build_ok:
            total_rows_so_far = (out.get("chart_facts") or {}).get("total_rows", 0)
            expected_total = 5 * sum(EXPECTED_PER_AYANAMSHA.values())
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
            write_snapshot(snap)
            push_to_gcs(SNAPSHOT_PATH, "data_build_status.json")

            # Summary log line
            summ = snap.get("summary", {})
            cf = snap.get("chart_facts") or {}
            total_rows = cf.get("total_rows", 0)
            log_line = (
                f"cf={total_rows:>7} | "
                f"assets={summ.get('complete',0)}✓ {summ.get('partial',0)}~ {summ.get('empty',0)}∅ "
                f"ready={len(summ.get('ready_to_run',[]))} blocked={summ.get('blocked',0)}"
            )
            build = snap.get("build")
            if build and isinstance(build, dict) and not build.get("error"):
                cur_b = build.get("current") or {}
                log_line += (
                    f" | build={build['build_id'][:8]}"
                    f" {cur_b.get('asset', '?')}/{cur_b.get('stage', '?')}"
                    f"={cur_b.get('pct_complete', 0):.0f}%"
                    f" elapsed={build.get('elapsed_seconds', 0):.0f}s"
                )
            logger.info(log_line)

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
