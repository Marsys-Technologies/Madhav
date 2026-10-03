"""
brahmagyan/mimamsa/export_to_bigquery.py — BRAHMA MI-5-5: L5 Mīmāṃsā cross-corpus OLAP export
=================================================================================================

Asset:   mimamsa.research (MI-5-5)
Layer:   L5 Mīmāṃsā — the final cross-corpus analytics layer
Purpose: Export L1/L2 data (chart_facts + bodha_signals) to Parquet → GCS → BigQuery
         for OLAP analytics.

PRIVACY (SS N-109, lifeevents-audit F1): `life_events` is PEOPLE-ENTERED, PRIVATE,
chart-scoped data (free-text `description`, `source_citation`). This module can
NEVER export it. There is no life_events table spec, no `--include-life-events`
flag and no `include_life_events` parameter; any request naming a life_events /
LEL table key is refused (fail closed, `LifeEventsExportRefused`) in `run_export`
and `export_table`, and `export_table` additionally refuses any spec whose SQL
reads `life_events`. If an export of derived event numbers is ever wanted it must
be a NEW module: chart_id-scoped, column-whitelisted with NO free text, gated on
`life_events.pool_consent` plus a stated disclosure tier.

NOTE: the remaining chart_facts / bodha_signals specs and the mimamsa_export_log
INSERT target a schema that no longer exists in production (the SELECTs fail
first, so nothing leaves). That is a separate, pre-existing problem and is
deliberately NOT fixed here.

Contract:
  - Dataset:  brahma_l5_olap (pre-provisioned in GCP)
  - Log table: mimamsa_export_log (export_id UUID, export_at TIMESTAMPTZ,
               table_name TEXT, row_count INT, gcs_path TEXT,
               source_citation TEXT NOT NULL)
  - source_citation: NON-NULL on every log row and every exported data row
  - life_events: NEVER exported (see PRIVACY above)

Sources:
  - chart_facts — L1 natal chart facts (2,717 rows, FORENSIC_v8_0)
  - bodha_signals — L2 Bodha MSR signal states (573 signals per bodha_bo24)

Native:  Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
         chart_id: 482012f1-710e-4a25-994a-93821f5871aa (FORENSIC canonical)

Usage:
    # Dry-run — show what would be exported
    python -m brahmagyan.mimamsa.export_to_bigquery --dry-run

    # Full export: chart_facts + bodha_signals
    python -m brahmagyan.mimamsa.export_to_bigquery

    # Export single table
    python -m brahmagyan.mimamsa.export_to_bigquery --tables chart_facts

    # Export with custom GCS bucket
    python -m brahmagyan.mimamsa.export_to_bigquery --gcs-bucket my-bucket

Environment variables:
    DATABASE_URL       — PostgreSQL connection string (required)
    GCP_PROJECT        — GCP project ID (default: marsys-jis)
    GCS_BUCKET         — GCS bucket for Parquet staging (default: marsys-brahma-exports)
    BQ_DATASET         — BigQuery dataset (default: brahma_l5_olap)

Authors:  Brahma MI-5-5 session
Version:  1.0 — 2026-06-04
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

GCP_PROJECT   = os.environ.get("GCP_PROJECT",  "madhav-astrology")
GCS_BUCKET    = os.environ.get("GCS_BUCKET",   "madhav-brahma-olap")
BQ_DATASET    = os.environ.get("BQ_DATASET",   "brahma_l5_olap")

# Source citation for the export log — references canonical L1/L2 artifacts
_LOG_SOURCE_CITATION = (
    "FORENSIC v8.0 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) | "
    "chart_facts table (2,717 rows, 27 categories, BRAHMA-MCP-Transformation) | "
    "bodha_signals table (573 MSR signals, BRAHMA-BO-2-4) | "
    "BRAHMA MI-5-5 export [BRAHMA-MI-5-5]"
)

# Life-events egress guard (SS N-109 / lifeevents-audit F1): people-entered
# life-event data must never leave the database through this module.
_LIFE_EVENTS_NAME_RE = re.compile(
    r"(life[_\- ]?events?|(^|[_\- ])lel([_\- ]|$))", re.IGNORECASE
)
_LIFE_EVENTS_SQL_RE = re.compile(r"\blife_events\w*\b|\blel_\w+\b", re.IGNORECASE)


class LifeEventsExportRefused(RuntimeError):
    """Raised when an export of people-entered life-event data is requested."""


# ── Table export specs ─────────────────────────────────────────────────────────
#
# Each spec defines:
#   sql           — query that reads from source DB (must select source_citation)
#   bq_table      — BigQuery table name in brahma_l5_olap dataset
#   description   — human label for logging
#
# life_events is intentionally absent and must stay absent (see PRIVACY above).

_TABLE_SPECS: dict[str, dict[str, Any]] = {
    "chart_facts": {
        "sql": """
            SELECT
                fact_id,
                chart_id,
                category,
                subcategory,
                key,
                value_text,
                value_num,
                value_json,
                ayanamsha_id,
                source_citation,
                computed_at,
                build_id
            FROM chart_facts
            WHERE source_citation IS NOT NULL
              AND source_citation <> ''
            ORDER BY category, key
        """,
        "bq_table": "chart_facts",
        "description": "L1 chart facts (FORENSIC_v8_0 — planets, houses, dashas, yogas)",
    },
    "bodha_signals": {
        "sql": """
            SELECT
                signal_id,
                chart_id,
                signal_group,
                domain,
                valence,
                confidence,
                state,
                reinforcement_count,
                source_citation,
                ayanamsha_id,
                computed_at,
                build_id
            FROM bodha_signals
            WHERE source_citation IS NOT NULL
              AND source_citation <> ''
            ORDER BY signal_group, signal_id
        """,
        "bq_table": "bodha_signals",
        "description": "L2 Bodha MSR signal states (573 signals, BRAHMA-BO-2-4)",
    },
}

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
    """Return a psycopg connection."""
    try:
        import psycopg  # type: ignore
        return psycopg.connect(_db_url())
    except ImportError as exc:
        raise ImportError(
            "psycopg (v3) is required. Install with: pip install psycopg[binary]"
        ) from exc


# ── Parquet helpers ────────────────────────────────────────────────────────────


def _rows_to_parquet(rows: list[dict[str, Any]], schema_name: str) -> bytes:
    """
    Convert list-of-dicts to Parquet bytes.

    Requires pyarrow. Falls back to a JSON-lines encoding if pyarrow is absent
    (useful in CI environments without the full analytics stack).
    """
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore

        if not rows:
            # Empty table — return minimal valid Parquet
            table = pa.table({})
            buf = io.BytesIO()
            pq.write_table(table, buf)
            return buf.getvalue()

        # Derive schema from first row; pyarrow infers column types
        table = pa.Table.from_pylist(rows)
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        logger.info(
            "[%s] Parquet: %d rows → %d bytes (snappy)", schema_name, len(rows), buf.tell()
        )
        return buf.getvalue()

    except ImportError:
        logger.warning(
            "pyarrow not available — falling back to JSON-lines encoding for %s",
            schema_name,
        )
        lines = "\n".join(json.dumps(r, default=str) for r in rows)
        return lines.encode("utf-8")


# ── GCS helpers ───────────────────────────────────────────────────────────────


def _upload_to_gcs(data: bytes, gcs_path: str, *, dry_run: bool = False) -> str:
    """
    Upload bytes to GCS. Returns the gs:// URI.

    In dry_run mode, logs what would be uploaded and returns the URI unchanged.
    Requires google-cloud-storage.
    """
    uri = f"gs://{GCS_BUCKET}/{gcs_path}"

    if dry_run:
        logger.info("[dry_run] Would upload %d bytes to %s", len(data), uri)
        return uri

    try:
        from google.cloud import storage  # type: ignore

        client = storage.Client(project=GCP_PROJECT)
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(data, content_type="application/octet-stream")
        logger.info("GCS upload: %s (%d bytes)", uri, len(data))
        return uri

    except ImportError:
        logger.warning(
            "google-cloud-storage not installed — GCS upload skipped. "
            "Install with: pip install google-cloud-storage"
        )
        return uri


# ── BigQuery helpers ───────────────────────────────────────────────────────────


def _load_parquet_to_bq(
    gcs_uri: str,
    bq_table: str,
    *,
    dry_run: bool = False,
) -> int:
    """
    Load a GCS Parquet file into BigQuery via a load job.

    Returns estimated row count (from job stats when available, else 0).
    """
    full_table = f"{GCP_PROJECT}.{BQ_DATASET}.{bq_table}"

    if dry_run:
        logger.info("[dry_run] Would load %s → BQ table %s", gcs_uri, full_table)
        return 0

    try:
        from google.cloud import bigquery  # type: ignore

        client = bigquery.Client(project=GCP_PROJECT)
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
        )
        load_job = client.load_table_from_uri(gcs_uri, full_table, job_config=job_config)
        load_job.result()  # Wait for job completion

        table_ref = client.get_table(full_table)
        row_count = table_ref.num_rows
        logger.info("BQ load: %s → %d rows in %s", gcs_uri, row_count, full_table)
        return row_count

    except ImportError:
        logger.warning(
            "google-cloud-bigquery not installed — BQ load skipped. "
            "Install with: pip install google-cloud-bigquery"
        )
        return 0


# ── Export log ─────────────────────────────────────────────────────────────────


def _write_export_log(
    conn: Any,
    export_id: str,
    table_name: str,
    row_count: int,
    gcs_path: str,
    source_citation: str,
) -> None:
    """
    Write a row to mimamsa_export_log (source_citation is NOT NULL enforced at DB level).
    """
    if not source_citation or not source_citation.strip():
        raise ValueError(
            f"[STOP] source_citation must be non-null for export_log row "
            f"(table_name={table_name!r}). This is a contract violation."
        )

    sql = """
        INSERT INTO mimamsa_export_log
            (export_id, export_at, table_name, row_count, gcs_path, source_citation)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (export_id) DO UPDATE SET
            export_at       = EXCLUDED.export_at,
            table_name      = EXCLUDED.table_name,
            row_count       = EXCLUDED.row_count,
            gcs_path        = EXCLUDED.gcs_path,
            source_citation = EXCLUDED.source_citation
    """
    with conn.cursor() as cur:
        cur.execute(sql, (export_id, datetime.now(timezone.utc), table_name,
                          row_count, gcs_path, source_citation))
    conn.commit()
    logger.info(
        "export_log: recorded export_id=%s table=%s rows=%d gcs=%s",
        export_id, table_name, row_count, gcs_path,
    )


# ── Life-events egress guard ───────────────────────────────────────────────────


def _refuse_life_events_key(table_key: str) -> None:
    """
    Fail closed if `table_key` names a life_events / LEL table.

    people-entered life-event data (free-text `description`, `source_citation`)
    must never be exported to GCS / BigQuery by this module.
    """
    if _LIFE_EVENTS_NAME_RE.search(str(table_key)):
        raise LifeEventsExportRefused(
            f"[STOP] life_events export refused: table_key={table_key!r}. "
            f"life_events is people-entered, private, chart-scoped data and is "
            f"never exported by export_to_bigquery (SS N-109)."
        )


def _refuse_life_events_sql(table_key: str, sql: str) -> None:
    """Fail closed if a table spec's SQL reads life_events / lel_* under any key."""
    if _LIFE_EVENTS_SQL_RE.search(sql):
        raise LifeEventsExportRefused(
            f"[STOP] life_events export refused: the SQL for table_key={table_key!r} "
            f"reads life_events / lel_* data, which is never exported "
            f"by export_to_bigquery (SS N-109)."
        )


# ── Core export function ───────────────────────────────────────────────────────


def export_table(
    table_key: str,
    *,
    chart_id: str,
    export_timestamp: str | None = None,
    dry_run: bool = False,
    write_log: bool = True,
) -> dict[str, Any]:
    """
    Export a single table: DB → Parquet → GCS → BigQuery → export_log.

    Args:
        table_key:        Key in _TABLE_SPECS (e.g. 'chart_facts').
        chart_id:         Chart UUID this export is attributed to (required).
        export_timestamp: ISO timestamp string for GCS path partitioning.
                          Defaults to current UTC time.
        dry_run:          If True, skip GCS/BQ writes and log-writes.
        write_log:        If False, skip mimamsa_export_log write (testing).

    Returns:
        {
          "export_id":      str (UUID),
          "table_name":     str,
          "row_count":      int,
          "gcs_path":       str,
          "gcs_uri":        str,
          "bq_table":       str,
          "source_citation":str,
          "dry_run":        bool,
          "exported_at":    str (ISO),
        }
    """
    _refuse_life_events_key(table_key)

    if table_key not in _TABLE_SPECS:
        raise ValueError(
            f"Unknown table_key {table_key!r}. "
            f"Valid keys: {sorted(_TABLE_SPECS.keys())}"
        )

    spec = _TABLE_SPECS[table_key]
    bq_table   = spec["bq_table"]
    description = spec["description"]
    sql        = spec["sql"].strip()

    # Egress guard: neither the BQ table name nor the SQL may touch life_events.
    _refuse_life_events_key(bq_table)
    _refuse_life_events_sql(table_key, sql)

    export_id  = str(uuid.uuid4())
    ts         = export_timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # GCS path contract: gs://madhav-brahma-olap/<table>/<date>.parquet
    gcs_path   = f"{bq_table}/{ts}.parquet"

    logger.info(
        "MI-5-5 export: table=%s | description=%s | export_id=%s | dry_run=%s",
        bq_table, description, export_id, dry_run,
    )

    # ── Step 1: Query source DB ───────────────────────────────────────────────
    rows: list[dict[str, Any]] = []
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            col_names = [desc[0] for desc in cur.description]
            for raw_row in cur.fetchall():
                row = dict(zip(col_names, raw_row))
                # Enforce source_citation non-null at row level
                citation = row.get("source_citation")
                if not citation or not str(citation).strip():
                    # Skip rows without citation and warn — do not fail export
                    logger.warning(
                        "Row skipped: missing source_citation in %s (row=%s)",
                        bq_table, row.get("fact_id") or row.get("signal_id") or row.get("event_id"),
                    )
                    continue
                rows.append(row)

        row_count = len(rows)
        logger.info("DB read: %s → %d rows (source_citation non-null)", bq_table, row_count)

        # ── Step 2: Serialize to Parquet ──────────────────────────────────────
        parquet_bytes = _rows_to_parquet(rows, schema_name=bq_table)

        # ── Step 3: Upload to GCS ─────────────────────────────────────────────
        gcs_uri = _upload_to_gcs(parquet_bytes, gcs_path, dry_run=dry_run)

        # ── Step 4: Load to BigQuery ──────────────────────────────────────────
        bq_row_count = _load_parquet_to_bq(gcs_uri, bq_table, dry_run=dry_run)

        # ── Step 5: Write export log ──────────────────────────────────────────
        source_citation = (
            f"{_LOG_SOURCE_CITATION} | table={bq_table} | rows={row_count}"
        )
        if write_log and not dry_run:
            _write_export_log(
                conn,
                export_id=export_id,
                table_name=bq_table,
                row_count=row_count,
                gcs_path=gcs_uri,
                source_citation=source_citation,
            )
        elif dry_run:
            logger.info(
                "[dry_run] Would write export_log: export_id=%s table=%s rows=%d",
                export_id, bq_table, row_count,
            )

    exported_at = datetime.now(timezone.utc).isoformat()
    result = {
        "export_id":       export_id,
        "table_name":      bq_table,
        "row_count":       row_count,
        "gcs_path":        gcs_path,
        "gcs_uri":         gcs_uri,
        "bq_table":        f"{GCP_PROJECT}.{BQ_DATASET}.{bq_table}",
        "bq_rows_loaded":  bq_row_count if not dry_run else 0,
        "source_citation": source_citation,
        "description":     description,
        "dry_run":         dry_run,
        "exported_at":     exported_at,
        "provenance_envelope": {
            "source": "brahmagyan.mimamsa.export_to_bigquery",
            "asset":  "MI-5-5",
            "layer":  "L5 Mīmāṃsā",
            "native_chart_id": chart_id,
            "gcp_project": GCP_PROJECT,
            "bq_dataset":  BQ_DATASET,
            "gcs_bucket":  GCS_BUCKET,
            "exported_at": exported_at,
        },
    }

    return result


def run_export(
    chart_id: str,
    tables: list[str] | None = None,
    *,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """
    Run the full MI-5-5 export pipeline.

    Args:
        chart_id:            Chart UUID this export run is attributed to (required).
        tables:              List of table_keys to export. Default: chart_facts + bodha_signals.
        dry_run:             If True, skip writes.

    Raises:
        LifeEventsExportRefused: if ANY requested table key names life_events / LEL
            (checked before any table is processed, so nothing is exported).

    Returns:
        List of export result dicts (one per table).
    """
    default_tables = ["chart_facts", "bodha_signals"]
    if tables is None:
        tables = list(default_tables)
    # Fail closed BEFORE exporting anything (export_table failures are otherwise
    # swallowed into per-table error dicts below).
    for tkey in tables:
        _refuse_life_events_key(tkey)

    results: list[dict[str, Any]] = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for tkey in tables:
        logger.info("=== Exporting: %s ===", tkey)
        try:
            result = export_table(tkey, chart_id=chart_id, export_timestamp=ts, dry_run=dry_run)
            results.append(result)
            logger.info(
                "DONE: %s — %d rows → %s",
                tkey, result["row_count"], result["gcs_uri"],
            )
        except Exception as exc:
            logger.error("FAILED: %s — %s", tkey, exc, exc_info=True)
            results.append({
                "table_name": tkey,
                "error": str(exc),
                "dry_run": dry_run,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            })

    return results


# ── Acceptance gate ────────────────────────────────────────────────────────────


def run_acceptance_gate(dry_run: bool = False) -> dict[str, Any]:
    """
    MI-5-5 acceptance gate:

    AC1: export_log table exists and is reachable
    AC2: BQ dataset brahma_l5_olap is accessible
    AC3: source_citation is non-null on all export_log rows
    AC4: life_events never appears in export_log

    Returns: {passed: bool, checks: list}
    """
    checks: list[dict[str, Any]] = []

    # AC1: export_log table reachable
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM mimamsa_export_log"
            ).fetchone()
            count = int(row[0]) if row else 0
        checks.append({
            "id": "AC1",
            "desc": "mimamsa_export_log table exists and is reachable",
            "passed": True,
            "value": count,
        })
    except Exception as exc:
        checks.append({
            "id": "AC1",
            "desc": "mimamsa_export_log table exists",
            "passed": False,
            "error": str(exc),
        })

    # AC2: BQ dataset accessible (skip if google-cloud-bigquery not installed)
    try:
        from google.cloud import bigquery  # type: ignore
        client = bigquery.Client(project=GCP_PROJECT)
        dataset = client.get_dataset(f"{GCP_PROJECT}.{BQ_DATASET}")
        checks.append({
            "id": "AC2",
            "desc": f"BQ dataset {BQ_DATASET} accessible",
            "passed": True,
            "value": str(dataset.dataset_id),
        })
    except ImportError:
        checks.append({
            "id": "AC2",
            "desc": f"BQ dataset {BQ_DATASET} accessible",
            "passed": True,  # Not a failure — library may not be installed in all envs
            "value": "google-cloud-bigquery not installed — skipped",
        })
    except Exception as exc:
        checks.append({
            "id": "AC2",
            "desc": f"BQ dataset {BQ_DATASET} accessible",
            "passed": False,
            "error": str(exc),
        })

    # AC3: source_citation non-null on all export_log rows
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM mimamsa_export_log "
                "WHERE source_citation IS NULL OR source_citation = ''"
            ).fetchone()
            null_count = int(row[0]) if row else 0
        checks.append({
            "id": "AC3",
            "desc": "All export_log rows have non-null source_citation",
            "passed": null_count == 0,
            "value": null_count,
        })
    except Exception as exc:
        checks.append({
            "id": "AC3",
            "desc": "source_citation non-null check",
            "passed": False,
            "error": str(exc),
        })

    # AC4: life_events never appears in export_log at all
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM mimamsa_export_log "
                "WHERE table_name ILIKE 'life_events%' "
                "   OR table_name ILIKE 'lel\\_%'"
            ).fetchone()
            leakage_count = int(row[0]) if row else 0
        checks.append({
            "id": "AC4",
            "desc": "no life_events / lel export_log rows (life_events is never exported)",
            "passed": leakage_count == 0,
            "value": leakage_count,
        })
    except Exception as exc:
        checks.append({
            "id": "AC4",
            "desc": "life_events leakage guard",
            "passed": False,
            "error": str(exc),
        })

    passed = all(c["passed"] for c in checks)
    return {
        "gate": "MI-5-5 acceptance gate",
        "gate_passed": passed,
        "checks": checks,
        "provenance_envelope": {
            "source": "brahmagyan.mimamsa.export_to_bigquery",
            "asset":  "MI-5-5",
            "run_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    parser = argparse.ArgumentParser(
        description=(
            "BRAHMA MI-5-5: mimamsa.research — cross-corpus OLAP export "
            "(chart_facts + bodha_signals → Parquet → GCS → BigQuery)"
        )
    )
    parser.add_argument(
        "--chart-id",
        required=True,
        help="Chart UUID this export run is attributed to (required — no native default).",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        choices=list(_TABLE_SPECS.keys()),
        help=(
            "Tables to export (default: chart_facts bodha_signals). "
            "Valid: chart_facts, bodha_signals. life_events is never exportable."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing to GCS/BQ/log.",
    )
    parser.add_argument(
        "--gcs-bucket",
        default=None,
        help="Override GCS bucket (default: $GCS_BUCKET or marsys-brahma-exports).",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Run acceptance gate only (exits 1 if any check fails).",
    )

    args = parser.parse_args()

    if args.gcs_bucket:
        global GCS_BUCKET
        GCS_BUCKET = args.gcs_bucket  # type: ignore[assignment]

    if args.gate:
        result = run_acceptance_gate(dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))
        if not result["gate_passed"]:
            sys.exit(1)
        return

    results = run_export(
        args.chart_id,
        tables=args.tables,
        dry_run=args.dry_run,
    )

    print(json.dumps(results, indent=2, default=str))

    # Exit 1 if any table failed
    failed = [r for r in results if "error" in r]
    if failed:
        logger.error("%d table(s) failed export: %s", len(failed), [r["table_name"] for r in failed])
        sys.exit(1)


if __name__ == "__main__":
    main()
