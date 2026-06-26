"""
mi_jivanaghatana — Clean-Evidence Vault & Leakage Firewall (L5 Mīmāṃsā root)
==============================================================================
Loads the Life Event Log (life_events table) and produces per-event provenance
rows in mimamsa_event_provenance with admissibility flags + held-out partition.

FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or closes ctx.db_conn.
GLOBAL scope — processes all charts in life_events.
Determinism: MD5-hash partition, pure joins, no LLM (D-1).
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

PARTITION_SEED_VERSION = "v1_md5_mod10"
LEL_VERSION = "v1.7"
PROVENANCE_FORMULA_VER = "mi_jivanaghatana_v1.0"


def _held_out(event_id: str) -> bool:
    """Deterministic held-out partition: MD5(event_id) mod 10 >= 8 ≈ 20%."""
    digest = hashlib.md5(event_id.encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 10) >= 8


def _admissibility(shaped: bool, disclosure_timing: str, event_date: Any) -> tuple[bool, str]:
    if shaped:
        return False, "excluded: shaped a predictor"
    if disclosure_timing == "post_framework_undated":
        return False, "excluded: post-framework undated disclosure"
    if event_date is None:
        return False, "excluded: no event_date"
    return True, "clean: not a predictor, not post-hoc undated, has event_date"


@register("mi_jivanaghatana")
class MiJivanaghatanaWriter(WriterBase):
    """
    Populates mimamsa_event_provenance from life_events.
    Global scope — deletes all existing rows and re-inserts for all charts.
    """

    asset_id = "mi_jivanaghatana"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # Discover life_events columns (defensive)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'life_events' ORDER BY ordinal_position"
            )
            col_rows = cur.fetchall()
        col_names = {r["column_name"] for r in col_rows}

        # Load all life events
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM life_events ORDER BY event_id")
            events = cur.fetchall()

        logger.info("[mi_jivanaghatana] loaded %d life_events rows", len(events))

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(events),
                duration_seconds=time.time() - t0,
                notes=f"dry_run: would insert {len(events)} provenance rows",
            )

        # Build provenance rows
        rows: list[tuple] = []
        for ev in events:
            event_id = str(ev.get("event_id") or ev.get("id") or "")
            if not event_id:
                continue
            chart_id = str(ctx.config.get("chart_id") or "")

            # Safely extract date field (try multiple common column names)
            event_date = (
                ev.get("event_date")
                or ev.get("event_start_date")
                or ev.get("start_date")
                or ev.get("date")
            )

            domain_primary = str(
                ev.get("domain_primary") or ev.get("domain") or ev.get("life_domain") or "unknown"
            )

            # domain_secondary: if stored as array or comma-list
            raw_secondary = ev.get("domain_secondary") or ev.get("secondary_domains")
            if isinstance(raw_secondary, list):
                domain_secondary = raw_secondary
            elif isinstance(raw_secondary, str) and raw_secondary:
                domain_secondary = [s.strip() for s in raw_secondary.split(",")]
            else:
                domain_secondary = []

            event_magnitude = str(ev.get("magnitude") or ev.get("event_magnitude") or "") or None

            # Disclosure timing: use column if present, default 'unknown'
            disclosure_timing = str(
                ev.get("disclosure_timing") or ev.get("disclosure_type") or "unknown"
            )
            disclosure_date = ev.get("disclosure_date")

            # v1: no predictor ledger yet — shaped_predictor defaults to False
            shaped_predictor = False
            shaped_predictor_refs = None

            admissible, reason = _admissibility(shaped_predictor, disclosure_timing, event_date)
            held = _held_out(event_id)

            rows.append((
                chart_id,
                event_id,
                shaped_predictor,
                json.dumps(shaped_predictor_refs) if shaped_predictor_refs else None,
                disclosure_timing,
                disclosure_date,
                event_date,
                domain_primary,
                domain_secondary if domain_secondary else None,
                event_magnitude,
                held,
                admissible,
                reason,
                PARTITION_SEED_VERSION,
                LEL_VERSION,
                PROVENANCE_FORMULA_VER,
            ))

        # Idempotency: delete all existing rows (global scope) then re-insert
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_event_provenance")
            logger.info("[mi_jivanaghatana] deleted existing provenance rows")

        if not rows:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes="life_events is empty — zero provenance rows written",
            )

        INSERT_SQL = """
            INSERT INTO mimamsa_event_provenance (
                chart_id, event_id, shaped_predictor, shaped_predictor_refs,
                disclosure_timing, disclosure_date, event_date,
                domain_primary, domain_secondary, event_magnitude,
                held_out, admissible_clean, admissibility_reason,
                partition_seed_version, lel_version, provenance_formula_ver
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)

        logger.info(
            "[mi_jivanaghatana] inserted %d provenance rows (held_out=%d, clean=%d)",
            len(rows),
            sum(1 for r in rows if r[10]),   # held_out
            sum(1 for r in rows if r[11]),   # admissible_clean
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(rows),
            duration_seconds=time.time() - t0,
        )
