"""
pipeline.ingest_msr — Re-ingest MSR signals into msr_signals table.
KARN-W2-R1: populates the 8 new source columns via UPDATE on existing signal_id rows.

Usage:
    python -m pipeline.ingest_msr \
        --source <path-to-MSR_v5_0.md> \
        --native abhisek_mohanty \
        --upsert

Environment:
    DATABASE_URL  (or PGPASSWORD + psql-compatible env vars via the --dsn flag)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Re-ingest MSR signals with new columns")
    p.add_argument("--source", required=True, help="Path to MSR_v5_0.md")
    p.add_argument("--native", default="abhisek_mohanty", help="native_id")
    p.add_argument("--upsert", action="store_true", help="Use UPSERT (required)")
    p.add_argument(
        "--dsn",
        default=None,
        help="Postgres DSN; defaults to DATABASE_URL env var",
    )
    return p.parse_args()


def _get_dsn(dsn_arg: str | None) -> str:
    if dsn_arg:
        return dsn_arg
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return url
    # Fallback: build from env vars (for local Auth Proxy sessions)
    pgpass = os.environ.get("PGPASSWORD", "")
    if pgpass:
        return f"postgresql://amjis_app@127.0.0.1:5433/amjis"
    raise RuntimeError(
        "No DSN: set DATABASE_URL, or pass --dsn, or set PGPASSWORD for Auth Proxy"
    )


import re as _re


def _regex_scalar(yaml_body: str, field: str) -> str | None:
    """Extract a single-line scalar field using regex (fallback for malformed YAML)."""
    for line in yaml_body.split("\n"):
        m = _re.match(rf"^\s{{2}}{_re.escape(field)}:\s*(.+)$", line)
        if m:
            val = m.group(1).strip().strip('"').strip("'")
            return val if val else None
    return None


def _regex_inline_list(yaml_body: str, field: str) -> list | None:
    """Extract an inline-array field: 'field: [a, b, c]' → ['a', 'b', 'c']."""
    for line in yaml_body.split("\n"):
        m = _re.match(rf"^\s{{2}}{_re.escape(field)}:\s*\[(.+)\]", line)
        if m:
            items = [s.strip() for s in m.group(1).split(",") if s.strip()]
            return items if items else None
    return None


def _extract_signals(source_path: Path) -> list[dict[str, Any]]:
    """Parse MSR_v5_0.md and return one dict per signal with all 8 new fields.

    Uses yaml.safe_load first; falls back to regex extraction for signals
    where YAML parse fails (typically due to inline quotes in supporting_rules).
    """
    from rag.chunkers.msr_signal import _parse_signals  # type: ignore[import]

    raw = _parse_signals(source_path)
    rows: list[dict[str, Any]] = []

    def _list_or_none(val: Any) -> list | None:
        if isinstance(val, list) and val:
            return val
        return None

    for sig_id, yaml_body, data in raw:
        if data:
            # YAML parse succeeded — use structured dict
            rows.append({
                "signal_id": sig_id,
                "signal_type": data.get("signal_type") or None,
                "temporal_activation": data.get("temporal_activation") or None,
                "valence": data.get("valence") or None,
                "entities_involved": _list_or_none(data.get("entities_involved")),
                "supporting_rules": _list_or_none(data.get("supporting_rules")),
                "rpt_deep_dive": data.get("rpt_deep_dive") or None,
                "v6_ids_consumed": _list_or_none(data.get("v6_ids_consumed")),
                "prior_id": str(data.get("prior_id")) if data.get("prior_id") else None,
            })
        else:
            # YAML parse failed — fall back to regex for scalar fields
            entities = _regex_inline_list(yaml_body, "entities_involved")
            v6_ids = _regex_inline_list(yaml_body, "v6_ids_consumed")
            rows.append({
                "signal_id": sig_id,
                "signal_type": _regex_scalar(yaml_body, "signal_type"),
                "temporal_activation": _regex_scalar(yaml_body, "temporal_activation"),
                "valence": _regex_scalar(yaml_body, "valence"),
                "entities_involved": entities,
                "supporting_rules": None,  # skip malformed multiline list
                "rpt_deep_dive": _regex_scalar(yaml_body, "rpt_deep_dive"),
                "v6_ids_consumed": v6_ids,
                "prior_id": _regex_scalar(yaml_body, "prior_id"),
            })

    return rows


_UPDATE_SQL = """
UPDATE msr_signals SET
  signal_type         = %(signal_type)s,
  temporal_activation = %(temporal_activation)s,
  valence             = %(valence)s,
  entities_involved   = %(entities_involved)s,
  supporting_rules    = %(supporting_rules)s,
  rpt_deep_dive       = %(rpt_deep_dive)s,
  v6_ids_consumed     = %(v6_ids_consumed)s,
  prior_id            = %(prior_id)s,
  ingested_at         = NOW()
WHERE signal_id = %(signal_id)s
"""


def _run_upsert(dsn: str, rows: list[dict[str, Any]]) -> int:
    import psycopg2
    import psycopg2.extras

    updated = 0
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            for row in rows:
                params = {
                    "signal_id": row["signal_id"],
                    "signal_type": row["signal_type"],
                    "temporal_activation": row["temporal_activation"],
                    "valence": row["valence"],
                    "entities_involved": (
                        psycopg2.extras.Json(row["entities_involved"])
                        if row["entities_involved"] is not None
                        else None
                    ),
                    "supporting_rules": (
                        psycopg2.extras.Json(row["supporting_rules"])
                        if row["supporting_rules"] is not None
                        else None
                    ),
                    "rpt_deep_dive": row["rpt_deep_dive"],
                    "v6_ids_consumed": (
                        psycopg2.extras.Json(row["v6_ids_consumed"])
                        if row["v6_ids_consumed"] is not None
                        else None
                    ),
                    "prior_id": row["prior_id"],
                }
                cur.execute(_UPDATE_SQL, params)
                updated += cur.rowcount
        conn.commit()
    return updated


def main() -> None:
    args = _parse_args()

    if not args.upsert:
        log.error("--upsert flag required")
        sys.exit(1)

    source = Path(args.source).resolve()
    if not source.exists():
        log.error("Source not found: %s", source)
        sys.exit(1)

    dsn = _get_dsn(args.dsn)

    log.info("Parsing signals from %s", source)
    rows = _extract_signals(source)
    log.info("Parsed %d signals", len(rows))

    log.info("Running UPDATE for %d signals on native=%s", len(rows), args.native)
    updated = _run_upsert(dsn, rows)
    log.info("Updated %d rows", updated)

    if updated != len(rows):
        log.warning(
            "Expected to update %d rows, updated %d — "
            "some signal_ids may not exist in msr_signals",
            len(rows),
            updated,
        )
        sys.exit(2)

    log.info("MSR re-ingest complete: %d signals updated", updated)


if __name__ == "__main__":
    main()
