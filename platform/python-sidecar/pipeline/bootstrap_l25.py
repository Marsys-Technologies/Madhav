#!/usr/bin/env python3
"""
bootstrap_l25.py — Unit 2a loader.

One-shot job that builds the L2.5 corpus from the natal_engine output for
a given (chart_id, ayanamsha_id) pair and:

  1. Emits a deterministic canonical-JSONL artifact per table to
     `artifacts/l25_build/<build_id>/<table>.jsonl`.
  2. (Live mode only) Upserts the rows into `<table>_staging` tables.
  3. (Live mode + --promote) Runs the atomic staging→live swap inside a single
     transaction following the Phase 4C pattern.

Operator post-merge runbook:
  $ python platform/python-sidecar/pipeline/bootstrap_l25.py \
        --chart-id abhisek_mohanty_native_v1 \
        --ayanamsha jh_true_chitra \
        --build-id l25-build-$(date -u +%Y%m%d-%H%M%S) \
        --dry-run                     # emit JSONL, no DB
  $ # verify JSONL determinism: run twice with same build_id, diff outputs
  $ python platform/python-sidecar/pipeline/bootstrap_l25.py ... --promote

Idempotent via build_id (mirrors bootstrap_panchanga.py pattern).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow running as `python pipeline/bootstrap_l25.py` from the sidecar dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from natal_engine import compute_chart
from natal_engine.l25_builder import build_all, canonical_jsonl

logger = logging.getLogger("bootstrap_l25")


# ─── Canonical inputs registry ──────────────────────────────────────────────
# Maps stable chart_id → engine inputs dict. The NATIVE chart inputs are the
# canonical L1 chart data (FORENSIC_v8_0). To register a new chart, add a row
# here AND in the `charts` DB table (migration 086).
KNOWN_CHARTS: dict[str, dict[str, Any]] = {
    "abhisek_mohanty_native_v1": {
        "datetime_iso": "1984-02-05T10:43:00",
        "tz_offset_hours": 5.5,
        "latitude_deg": 20.2961,
        "longitude_deg": 85.8245,
        "place_name": "Bhubaneswar, Odisha, India",
        "subject_label": "Abhisek Mohanty",
    },
}

# Table → canonical sort keys for JSONL determinism.
TABLE_SORT_KEYS: dict[str, list[str]] = {
    "chart_facts":         ["fact_id", "chart_id", "ayanamsha_id"],
    "l25_msr_signals":     ["signal_id", "chart_id", "ayanamsha_id"],
    "l25_cdlm_links":      ["link_id", "chart_id", "ayanamsha_id"],
    "l25_cgm_nodes":       ["node_id", "chart_id", "ayanamsha_id"],
    "l25_cgm_edges":       ["edge_id", "chart_id", "ayanamsha_id"],
    "l25_rm_resonances":   ["resonance_id", "chart_id", "ayanamsha_id"],
    "l25_ucn_sections":    ["section_id", "chart_id", "ayanamsha_id"],
}


def emit_jsonl(
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    out_dir: Path,
    *,
    computed_at_iso: str | None = None,
) -> dict[str, int]:
    """Build the L2.5 row dicts + write canonical-JSONL artifacts. Returns
    per-table row counts. Pure: no DB I/O.

    `computed_at_iso` — pin for determinism in tests / repeated runs.
    """
    if chart_id not in KNOWN_CHARTS:
        raise SystemExit(f"unknown chart_id {chart_id!r}; register it in KNOWN_CHARTS")

    inputs = KNOWN_CHARTS[chart_id]
    chart_output = compute_chart(
        inputs,
        ayanamsha_id=ayanamsha_id,
        computed_at_iso=computed_at_iso,
    )
    all_rows = build_all(chart_output, chart_id, build_id)

    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for tbl, rows in all_rows.items():
        sort_keys = TABLE_SORT_KEYS[tbl]
        canonical = canonical_jsonl(rows, sort_keys)
        out_path = out_dir / f"{tbl}.jsonl"
        out_path.write_text(canonical + ("\n" if canonical else ""), encoding="utf-8")
        counts[tbl] = len(rows)
        logger.info("emitted %s: %d rows → %s", tbl, len(rows), out_path)
    return counts


# ─── DB swap (live mode only) ───────────────────────────────────────────────


def _connect(db_url: str):
    """Lazy psycopg2 import — keeps dry-run path importable without psycopg2."""
    import psycopg2  # type: ignore
    return psycopg2.connect(db_url)


def _upsert_to_staging(
    conn, table: str, rows: list[dict[str, Any]], build_id: str
) -> int:
    """Generic upsert. Caller wraps in a transaction."""
    if not rows:
        return 0
    # Build column list from the first row (all rows share keys).
    cols = list(rows[0].keys())
    placeholders = ",".join(f"%({c})s" for c in cols)
    col_csv = ",".join(cols)
    sql = f"INSERT INTO {table}_staging ({col_csv}) VALUES ({placeholders})"
    with conn.cursor() as cur:
        # JSONB-typed columns need json.dumps before psycopg2 serialises.
        for r in rows:
            payload = {
                k: (json.dumps(v) if isinstance(v, (dict, list)) and k in (
                    "provenance", "value_json", "signature_payload"
                ) else v)
                for k, v in r.items()
            }
            cur.execute(sql, payload)
    return len(rows)


def _register_build_manifest(
    conn, *, build_id: str, chart_id: str, ayanamsha_id: str,
    counts: dict[str, int], engine_version: str,
) -> None:
    """Auto-register build in build_manifests. (See Phase 4C lesson —
    bootstrap writer MUST register a manifest row so operator rollback is
    auditable.)"""
    notes = json.dumps({
        "unit": "2a",
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "engine_version": engine_version,
        "counts": counts,
    })
    sql = """
    INSERT INTO build_manifests
      (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
       embedding_model, embedding_dim, chunk_count, embedding_count,
       status, manifest_uri, notes)
    VALUES
      (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (build_id) DO UPDATE SET notes = EXCLUDED.notes
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            build_id,
            "bootstrap_l25",
            f"l25:{chart_id}:{ayanamsha_id}",
            "n/a-bootstrap_l25",
            "n/a",   # embedding_model
            0,       # embedding_dim
            sum(counts.values()),
            0,
            "staging",
            f"local://artifacts/l25_build/{build_id}",
            notes,
        ))


def _atomic_swap(conn, table: str, build_id: str) -> int:
    """Swap rows from <table>_staging → <table> for build_id.

    Strangler-safe: NEVER deletes legacy rows (chart_id IS NULL). Only purges
    prior engine rows for the SAME (chart_id, ayanamsha_id) tuple, then
    copies fresh ones from staging.
    """
    with conn.cursor() as cur:
        # Fetch unique (chart_id, ayanamsha_id) tuples for this build.
        cur.execute(
            f"SELECT DISTINCT chart_id, ayanamsha_id FROM {table}_staging "
            f"WHERE build_id = %s",
            (build_id,),
        )
        tuples = cur.fetchall()
        for chart_id_v, ayan_v in tuples:
            # Purge engine rows for this tuple — leave legacy NULL rows alone.
            cur.execute(
                f"DELETE FROM {table} "
                f"WHERE chart_id = %s AND ayanamsha_id = %s",
                (chart_id_v, ayan_v),
            )
        # Copy staging→live for this build.
        cur.execute(
            f"INSERT INTO {table} SELECT * FROM {table}_staging "
            f"WHERE build_id = %s",
            (build_id,),
        )
        moved = cur.rowcount
        # Clear staging rows we've promoted.
        cur.execute(
            f"DELETE FROM {table}_staging WHERE build_id = %s",
            (build_id,),
        )
    return moved


def run_db(
    *, db_url: str, chart_id: str, ayanamsha_id: str, build_id: str,
    artifacts_dir: Path, promote: bool, computed_at_iso: str | None,
) -> None:
    """Build → write JSONL → upsert staging → optional atomic swap."""
    counts = emit_jsonl(
        chart_id, ayanamsha_id, build_id, artifacts_dir,
        computed_at_iso=computed_at_iso,
    )
    if not db_url:
        logger.warning("--db-url not provided; skipping DB stage. JSONL ready at %s", artifacts_dir)
        return

    # Re-build rows in memory (cheaper than re-reading JSONL).
    inputs = KNOWN_CHARTS[chart_id]
    chart_output = compute_chart(
        inputs, ayanamsha_id=ayanamsha_id, computed_at_iso=computed_at_iso,
    )
    all_rows = build_all(chart_output, chart_id, build_id)
    engine_version = chart_output.get("provenance", {}).get("engine_version", "")

    conn = _connect(db_url)
    conn.autocommit = False
    try:
        _register_build_manifest(
            conn, build_id=build_id, chart_id=chart_id,
            ayanamsha_id=ayanamsha_id, counts=counts,
            engine_version=engine_version,
        )
        for tbl, rows in all_rows.items():
            n = _upsert_to_staging(conn, tbl, rows, build_id)
            logger.info("staging %s: upserted %d rows", tbl, n)
        if not promote:
            conn.commit()
            logger.info("--promote NOT set; rows live in *_staging only.")
            return
        # Atomic swap inside the SAME transaction.
        for tbl in all_rows:
            moved = _atomic_swap(conn, tbl, build_id)
            logger.info("swap %s: %d rows promoted to live", tbl, moved)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE build_manifests SET status='live', promoted_at=NOW() "
                "WHERE build_id=%s",
                (build_id,),
            )
        conn.commit()
        logger.info("L2.5 build %s atomically promoted.", build_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bootstrap the L2.5 corpus (Unit 2a).")
    p.add_argument("--chart-id", required=True,
                   help="stable chart_id (e.g., abhisek_mohanty_native_v1)")
    p.add_argument("--ayanamsha", required=True,
                   help="ayanamsha_id from natal_engine.ayanamsha_registry")
    p.add_argument("--build-id",
                   default=f"l25-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}")
    p.add_argument("--artifacts-dir", default="artifacts/l25_build",
                   help="where to write canonical JSONL artifacts")
    p.add_argument("--db-url", default=os.getenv("DATABASE_URL", ""),
                   help="Postgres DSN; if empty, runs in dry-run JSONL-only mode")
    p.add_argument("--promote", action="store_true",
                   help="atomic staging→live swap after upsert (live mode only)")
    p.add_argument("--computed-at-iso", default=None,
                   help="pin computed_at_iso for deterministic builds")
    p.add_argument("--dry-run", action="store_true",
                   help="JSONL-only emit; ignores --db-url")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    artifacts = Path(args.artifacts_dir) / args.build_id
    if args.dry_run or not args.db_url:
        emit_jsonl(
            args.chart_id, args.ayanamsha, args.build_id, artifacts,
            computed_at_iso=args.computed_at_iso,
        )
    else:
        run_db(
            db_url=args.db_url,
            chart_id=args.chart_id,
            ayanamsha_id=args.ayanamsha,
            build_id=args.build_id,
            artifacts_dir=artifacts,
            promote=args.promote,
            computed_at_iso=args.computed_at_iso,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
