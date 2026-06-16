"""
brahmagyan/mimamsa/l5_bigquery_export.py — Brahma L5 Mīmāṃsā — bigquery_export (MI-5-5)
==========================================================================================

Asset:    mimamsa.bigquery_export (WS-2 l5-mimamsa canonical asset)
Layer:    L5 Mīmāṃsā — OLAP export path
Tool:     (operator CLI — not an MCP tool)

PURPOSE:
    Export the L5 Mīmāṃsā substrate tables to BigQuery (or JSONL fallback) for
    offline OLAP analysis across the calibration corpus.

    Exports:
        1. mimamsa_events           — 57 LEL events with chart state and split flags
        2. event_chart_state_index  — 57 per-event chart state entries
        3. calibration_substrate    — concordance summary and domain breakdown
        (optional: mimamsa_signal_multipliers — 569 signal multiplier rows)

    Target dataset: brahma_l5_mimamsa (BigQuery) | fallback: JSONL local file.

    EXPORT STRATEGY:
        - Append-only: each run creates a new partition keyed by export_date.
        - If BigQuery credentials not available in CI → writes to JSONL fallback file.
        - The JSONL fallback is idempotent (overwrites on re-run with same export_date).

ISOLATION RULE:
    life_events data exported here is CALIBRATION ONLY. It must never be injected into
    prediction generation. The export carries a 'calibration_only' flag on every row.

Source:  l5_lel_intake.py (MI-5-1)
         l5_event_chart_state_index.py (MI-5-2)
         l5_calibration_substrate.py (MI-5-3)
         l5_learning_multiplier.py (MI-5-4-SCAFFOLD)

Native:  Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India
         chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Authors: Silpī (WS-2 l5-mimamsa session)
BRAHMA-MI-5-5
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_CITATION = (
    "l5_lel_intake.py (MI-5-1); "
    "l5_event_chart_state_index.py (MI-5-2); "
    "l5_calibration_substrate.py (MI-5-3); "
    "l5_learning_multiplier.py (MI-5-4-SCAFFOLD); "
    "LIFE_EVENT_LOG_v1_2.md v1.7"
)
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# BigQuery settings (overridable via environment)
BQ_DATASET = os.environ.get("BQ_DATASET", "brahma_l5_mimamsa")
GCP_PROJECT = os.environ.get("GCP_PROJECT", "marsys-jis")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "marsys-brahma-exports")

# JSONL fallback path (used when BigQuery credentials not available)
_FALLBACK_DIR = Path(__file__).parent
JSONL_FALLBACK_PATH = _FALLBACK_DIR / "bigquery_export_preview.jsonl"


# ── Payload builders ──────────────────────────────────────────────────────────

def _build_mimamsa_events_payload(export_date: str) -> list[dict[str, Any]]:
    """Build the mimamsa_events export payload (57 rows)."""
    from brahmagyan.mimamsa.l5_lel_intake import build_intake_rows
    rows = build_intake_rows()
    return [
        {
            "export_date":      export_date,
            "table_name":       "mimamsa_events",
            "chart_id":         NATIVE_CHART_ID,
            "event_id":         r["event_id"],
            "lel_id":           r["lel_id"],
            "event_date":       r["event_date"],
            "event_type":       r["event_type"],
            "subcategory":      r["subcategory"],
            "description":      r["description"],
            "magnitude":        r["magnitude"],
            "outcome":          r["outcome"],
            "dasha_md":         r["dasha_md"],
            "dasha_ad":         r["dasha_ad"],
            "convergence_score": r["convergence_score"],
            "is_training":      r["is_training"],
            "is_holdout":       r["is_holdout"],
            "anchor_match":     r["anchor_match"],
            "calibration_only": True,   # isolation flag — never fed to prediction generation
            "source_citation":  SOURCE_CITATION,
        }
        for r in rows
    ]


def _build_chart_state_index_payload(export_date: str) -> list[dict[str, Any]]:
    """Build the event_chart_state_index export payload (57 rows)."""
    from brahmagyan.mimamsa.l5_event_chart_state_index import build_event_chart_state_index
    index = build_event_chart_state_index()
    return [
        {
            "export_date":                export_date,
            "table_name":                 "event_chart_state_index",
            "chart_id":                   NATIVE_CHART_ID,
            "event_id":                   e["event_id"],
            "lel_id":                     e["lel_id"],
            "event_date":                 e["event_date"],
            "dasha_md":                   e["vimshottari"].get("md"),
            "dasha_ad":                   e["vimshottari"].get("ad"),
            "saturn_transit":             e["slow_transits"].get("saturn"),
            "jupiter_transit":            e["slow_transits"].get("jupiter"),
            "rahu_transit":               e["slow_transits"].get("rahu"),
            "ketu_transit":               e["slow_transits"].get("ketu"),
            "active_convergence_windows": e["active_convergence_windows"],
            "active_obstruction_periods": e["active_obstruction_periods"],
            "convergence_score":          e["l2_signal_activations"]["convergence_score"],
            "outcome":                    e["l2_signal_activations"]["outcome_observed"],
            "is_training":                e["is_training"],
            "is_holdout":                 e["is_holdout"],
            "calibration_only":           True,
            "source_citation":            SOURCE_CITATION,
        }
        for e in index
    ]


def _build_calibration_substrate_payload(export_date: str) -> list[dict[str, Any]]:
    """Build the calibration_substrate export payload (1 summary row)."""
    from brahmagyan.mimamsa.l5_calibration_substrate import compute_calibration_substrate
    substrate = compute_calibration_substrate()
    return [
        {
            "export_date":              export_date,
            "table_name":               "calibration_substrate",
            "chart_id":                 NATIVE_CHART_ID,
            "concordance_pct":          substrate["concordance_pct"],
            "concordant_count":         substrate["concordant_count"],
            "total_training_events":    substrate["total_training_events"],
            "total_holdout_events":     substrate["total_holdout_events"],
            "outcome_distribution":     substrate["outcome_distribution"],
            "domain_concordance":       substrate["domain_concordance"],
            "signal_hit_rate_scaffold": substrate["signal_hit_rate_scaffold"],
            "holdout_untouched":        substrate["holdout_untouched"],
            "calibration_only":         True,
            "source_citation":          SOURCE_CITATION,
        }
    ]


def _build_multiplier_payload(export_date: str) -> list[dict[str, Any]]:
    """Build the signal multiplier export payload (569 rows)."""
    from brahmagyan.mimamsa.l5_learning_multiplier import build_multiplier_rows
    rows = build_multiplier_rows()
    return [
        {
            "export_date":       export_date,
            "table_name":        "mimamsa_signal_multipliers",
            "chart_id":          NATIVE_CHART_ID,
            "signal_id":         r["signal_id"],
            "multiplier":        r["multiplier"],
            "mean_brier_score":  r["mean_brier_score"],
            "sample_size":       r["sample_size"],
            "status":            r["status"],
            "calibration_only":  True,
            "source_citation":   SOURCE_CITATION,
        }
        for r in rows
    ]


# ── Export assembly ───────────────────────────────────────────────────────────

def build_export_payload(
    *,
    include_multipliers: bool = False,
    export_date: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Build the full export payload as a dict of table_name → rows.

    Args:
        include_multipliers: Include the 569-row signal multiplier table.
        export_date:         Export partition date (ISO string). Defaults to today.

    Returns:
        {
            "mimamsa_events":          [...57 rows...],
            "event_chart_state_index": [...57 rows...],
            "calibration_substrate":   [...1 row...],
            "mimamsa_signal_multipliers": [...569 rows...] if include_multipliers
        }
    """
    if export_date is None:
        export_date = date.today().isoformat()

    payload: dict[str, list[dict[str, Any]]] = {
        "mimamsa_events":          _build_mimamsa_events_payload(export_date),
        "event_chart_state_index": _build_chart_state_index_payload(export_date),
        "calibration_substrate":   _build_calibration_substrate_payload(export_date),
    }

    if include_multipliers:
        payload["mimamsa_signal_multipliers"] = _build_multiplier_payload(export_date)

    return payload


def _export_summary(payload: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {table: len(rows) for table, rows in payload.items()}


# ── BigQuery export ───────────────────────────────────────────────────────────

def export_to_bigquery(
    payload: dict[str, list[dict[str, Any]]],
    *,
    project: str = GCP_PROJECT,
    dataset: str = BQ_DATASET,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Export payload tables to BigQuery.

    Each table is appended (WRITE_APPEND) to preserve partition history.

    Args:
        payload:  Dict of table_name → rows.
        project:  GCP project ID.
        dataset:  BigQuery dataset.
        dry_run:  Validate but do not write.

    Returns:
        {ok, written_tables, row_counts, provenance_envelope}
    """
    try:
        from google.cloud import bigquery  # type: ignore
    except ImportError:
        return {
            "ok":     False,
            "reason": "google-cloud-bigquery not installed — use JSONL fallback",
            "provenance_envelope": _provenance_envelope(),
        }

    if dry_run:
        return {
            "ok":          True,
            "dry_run":     True,
            "row_counts":  _export_summary(payload),
            "provenance_envelope": _provenance_envelope(),
        }

    try:
        client = bigquery.Client(project=project)
        written: dict[str, int] = {}

        for table_name, rows in payload.items():
            if not rows:
                continue
            table_ref = f"{project}.{dataset}.{table_name}"
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                autodetect=True,
            )
            # Convert rows to NDJSON
            ndjson = "\n".join(json.dumps(r, default=str) for r in rows)
            load_job = client.load_table_from_json(
                rows,
                table_ref,
                job_config=job_config,
            )
            load_job.result()  # Wait for completion
            written[table_name] = len(rows)
            logger.info("BigQuery: exported %d rows → %s", len(rows), table_ref)

        return {
            "ok":            True,
            "written_tables": list(written.keys()),
            "row_counts":    written,
            "dataset":       f"{project}.{dataset}",
            "provenance_envelope": _provenance_envelope(),
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("BigQuery export failed: %s", exc)
        return {
            "ok":     False,
            "error":  str(exc),
            "reason": "BigQuery export failed — consider JSONL fallback",
            "provenance_envelope": _provenance_envelope(),
        }


# ── JSONL fallback export ─────────────────────────────────────────────────────

def export_to_jsonl(
    payload: dict[str, list[dict[str, Any]]],
    *,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """
    Export payload to a local JSONL file (fallback when BigQuery not available).

    Each line is a JSON object with table_name, row data, and isolation flags.
    Overwrites on re-run (file is idempotent per export_date partition).

    Args:
        payload:      Dict of table_name → rows.
        output_path:  Output JSONL path. Defaults to bigquery_export_preview.jsonl.

    Returns:
        {ok, path, total_rows, row_counts, provenance_envelope}
    """
    if output_path is None:
        output_path = JSONL_FALLBACK_PATH

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    row_counts: dict[str, int] = {}

    with output_path.open("w", encoding="utf-8") as fh:
        for table_name, rows in payload.items():
            for row in rows:
                fh.write(json.dumps(row, default=str) + "\n")
            row_counts[table_name] = len(rows)
            total_rows += len(rows)

    logger.info("JSONL export: %d rows written to %s", total_rows, output_path)

    return {
        "ok":            True,
        "path":          str(output_path),
        "total_rows":    total_rows,
        "row_counts":    row_counts,
        "provenance_envelope": _provenance_envelope(),
    }


# ── Primary export function ───────────────────────────────────────────────────

def run_export(
    *,
    include_multipliers: bool = False,
    export_date: str | None = None,
    dry_run: bool = False,
    force_jsonl: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Run the L5 Mīmāṃsā OLAP export.

    Attempts BigQuery first. Falls back to JSONL if BQ credentials unavailable.

    Args:
        include_multipliers: Include 569-row signal multiplier table.
        export_date:         Export partition date (ISO string). Defaults to today.
        dry_run:             Build payload but do not write.
        force_jsonl:         Skip BigQuery attempt and write JSONL only.
        verbose:             Log export details.

    Returns:
        {ok, method, row_counts, export_date, provenance_envelope}
    """
    if export_date is None:
        export_date = date.today().isoformat()

    payload = build_export_payload(
        include_multipliers=include_multipliers,
        export_date=export_date,
    )

    summary = _export_summary(payload)

    if verbose:
        for table, count in summary.items():
            logger.info("[export] table=%s rows=%d", table, count)

    if dry_run:
        return {
            "ok":          True,
            "dry_run":     True,
            "method":      "dry_run",
            "export_date": export_date,
            "row_counts":  summary,
            "provenance_envelope": _provenance_envelope(),
        }

    # Try BigQuery first (unless forced JSONL)
    if not force_jsonl:
        bq_result = export_to_bigquery(payload, dry_run=False)
        if bq_result.get("ok"):
            return {
                **bq_result,
                "method":      "bigquery",
                "export_date": export_date,
                "row_counts":  bq_result.get("row_counts", summary),
            }
        logger.info("BigQuery unavailable (%s) — falling back to JSONL", bq_result.get("reason"))

    # JSONL fallback
    jsonl_result = export_to_jsonl(payload)
    return {
        **jsonl_result,
        "method":      "jsonl_fallback",
        "export_date": export_date,
        "row_counts":  jsonl_result.get("row_counts", summary),
    }


def _provenance_envelope() -> dict[str, Any]:
    return {
        "source":           "mimamsa.bigquery_export (l5_bigquery_export)",
        "asset":            "MI-5-5",
        "lel_version":      "LIFE_EVENT_LOG_v1_2.md v1.7",
        "dataset_target":   f"{GCP_PROJECT}.{BQ_DATASET}",
        "jsonl_fallback":   str(JSONL_FALLBACK_PATH),
        "append_only":      True,
        "calibration_only_note": (
            "All exported tables carry calibration_only=True flag. "
            "life_events must NEVER feed into prediction generation."
        ),
        "source_citation":  SOURCE_CITATION,
        "exported_at":      datetime.now(timezone.utc).isoformat(),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="BRAHMA-MI-5-5: mimamsa.bigquery_export — L5 OLAP export"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Build payload but do not write"
    )
    parser.add_argument(
        "--jsonl", action="store_true", help="Force JSONL output (skip BigQuery)"
    )
    parser.add_argument(
        "--include-multipliers", action="store_true",
        help="Include 569-row signal multiplier table"
    )
    parser.add_argument(
        "--export-date", default=None, help="Export partition date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Log export details"
    )

    args = parser.parse_args()
    result = run_export(
        include_multipliers=args.include_multipliers,
        export_date=args.export_date,
        dry_run=args.dry_run,
        force_jsonl=args.jsonl,
        verbose=args.verbose,
    )
    print(json.dumps(result, indent=2, default=str))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
