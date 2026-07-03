"""
mi_jivanaghatana — Clean-Evidence Vault & Leakage Firewall (L5 Mīmāṃsā root)
==============================================================================
BA-P6 EXT (PD-10): Primary source is now the LEL markdown file
(01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md). The life_events DB table is
empty/chart-less and used only as a fallback. Rows are pinned to
lel_file_sha (MD5 of the file at build time).

FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or closes ctx.db_conn.
PER-CHART scope — provenance rows are keyed to chart_id; a rebuild replaces only
this chart's rows (N.3 delete-then-insert), never other charts'.
Determinism: MD5-hash partition, pure joins, no LLM (D-1).
"""
from __future__ import annotations

import hashlib
import json
import logging
import pathlib
import re
import time
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

PARTITION_SEED_VERSION = "v1_md5_mod10"
LEL_VERSION = "v1.7"
PROVENANCE_FORMULA_VER = "mi_jivanaghatana_v2.0"

# Resolve LEL markdown path relative to this file:
# writers/ → orchestrator/ → pipeline/ → python-sidecar/ → platform/ → repo root
_LEL_MARKDOWN_PATH = pathlib.Path(__file__).parents[4] / "01_FACTS_LAYER" / "LIFE_EVENT_LOG_v1_2.md"

# LEL magnitude labels → canonical event_magnitude values
_MAGNITUDE_NORMALIZE = {
    "life-altering": "rupture",
    "life_altering": "rupture",
    "major": "major",
    "significant": "significant",
    "moderate": "moderate",
    "minor": "minor",
    "trivial": "trivial",
    # fall-through
    "rupture": "rupture",
}


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


def _parse_date(raw: str | None) -> Any:
    """Parse LEL date string (YYYY-MM-DD or YYYY-MM-XX or YYYY-XX-XX → date or None)."""
    if not raw:
        return None
    s = str(raw).replace("X", "0").replace("x", "0")
    try:
        from datetime import date
        parts = s.split("-")
        y = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 and int(parts[1]) > 0 else 1
        d = int(parts[2]) if len(parts) > 2 and int(parts[2]) > 0 else 1
        return date(y, m, d)
    except Exception:
        return None


def _parse_lel_markdown(path: pathlib.Path) -> tuple[list[dict], str]:
    """
    Parse YAML event blocks from the LEL markdown file.
    Returns (events, file_sha) where events is a list of dicts with
    event_id + all yaml fields.
    """
    try:
        import yaml as _yaml
        _has_yaml = True
    except ImportError:
        _has_yaml = False

    text = path.read_text(encoding="utf-8")
    file_sha = hashlib.md5(text.encode("utf-8")).hexdigest()

    # Extract ```yaml ... ``` blocks
    blocks = re.findall(r'```yaml\n(.*?)\n```', text, re.DOTALL)

    events: list[dict] = []
    for block in blocks:
        try:
            if _has_yaml:
                import yaml as _yaml
                data = _yaml.safe_load(block)
            else:
                # Minimal fallback: skip non-yaml builds
                continue
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        for key, val in data.items():
            if not (isinstance(key, str) and key.startswith("EVT.")) or not isinstance(val, dict):
                continue
            events.append({"event_id": key, **val})

    logger.info(
        "[mi_jivanaghatana] parsed %d events from LEL markdown (sha=%s...)",
        len(events), file_sha[:8],
    )
    return events, file_sha


def _lookup_event_class(conn, category: str, subcategory: str | None) -> str | None:
    """SAVEPOINT-guarded lookup of event_class_id from brahma_event_ontology."""
    sp = "sp_evt_class"
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(f"SAVEPOINT {sp}")
            cur.execute(
                "SELECT event_class_id FROM brahma_event_ontology "
                "WHERE category = %s "
                "  AND (subcategory = %s OR subcategory IS NULL) "
                "ORDER BY (subcategory IS NOT NULL) DESC "
                "LIMIT 1",
                (category, subcategory),
            )
            row = cur.fetchone()
            cur.execute(f"RELEASE SAVEPOINT {sp}")
            return row[0] if row else None
    except Exception:
        try:
            with conn.cursor() as cur:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        return None


@register("mi_jivanaghatana")
class MiJivanaghatanaWriter(WriterBase):
    """
    Populates mimamsa_event_provenance from the LEL markdown (primary) or
    life_events DB table (fallback). Per-chart scope — deletes and re-inserts
    only this chart's rows (N.3). BA-P6 EXT: lel_file_sha pinning, lel_source
    tagging, event_class_id mapping.
    """

    asset_id = "mi_jivanaghatana"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id = str(ctx.config.get("chart_id") or "")

        # ── BA-P6 PD-10: try LEL markdown first ─────────────────────────────
        lel_source = "db"
        lel_file_sha: str | None = None
        raw_events: list[dict] = []

        if _LEL_MARKDOWN_PATH.exists():
            try:
                raw_events, lel_file_sha = _parse_lel_markdown(_LEL_MARKDOWN_PATH)
                lel_source = "markdown"
            except Exception as e:
                logger.warning("[mi_jivanaghatana] markdown parse failed (%s); falling back to DB", e)

        if not raw_events:
            # Fall back to life_events DB table
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'life_events' ORDER BY ordinal_position"
                )
                col_rows = cur.fetchall()
            col_names = {r["column_name"] for r in col_rows}

            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                if "chart_id" in col_names:
                    cur.execute(
                        "SELECT * FROM life_events WHERE chart_id = %s ORDER BY event_id",
                        (chart_id,),
                    )
                else:
                    cur.execute("SELECT * FROM life_events ORDER BY event_id")
                raw_events = [dict(r) for r in cur.fetchall()]

        logger.info(
            "[mi_jivanaghatana] loaded %d events from %s for chart %s",
            len(raw_events), lel_source, chart_id,
        )

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(raw_events),
                duration_seconds=time.time() - t0,
                notes=f"dry_run: would insert {len(raw_events)} provenance rows from {lel_source}",
            )

        # ── Build provenance rows ────────────────────────────────────────────
        rows: list[tuple] = []
        for ev in raw_events:
            # Normalize: markdown events use YAML field names; DB events use column names
            event_id = str(
                ev.get("event_id") or ev.get("id") or ""
            )
            if not event_id:
                continue

            # Date field (markdown: "date"; DB: "event_date"|"event_start_date"|etc.)
            raw_date = (
                ev.get("date")
                or ev.get("event_date")
                or ev.get("event_start_date")
                or ev.get("start_date")
            )
            event_date = _parse_date(str(raw_date)) if raw_date else None

            domain_primary = str(
                ev.get("category") or ev.get("domain_primary") or ev.get("domain") or "unknown"
            )

            # domain_secondary from subcategory or domain_secondary
            raw_secondary = ev.get("subcategory") or ev.get("domain_secondary") or ev.get("secondary_domains")
            if isinstance(raw_secondary, list):
                domain_secondary = raw_secondary
            elif isinstance(raw_secondary, str) and raw_secondary:
                domain_secondary = [s.strip() for s in raw_secondary.split(",")]
            else:
                domain_secondary = []

            # Magnitude normalize
            raw_mag = str(ev.get("magnitude") or ev.get("event_magnitude") or "")
            event_magnitude = _MAGNITUDE_NORMALIZE.get(raw_mag.lower()) if raw_mag else None

            disclosure_timing = str(
                ev.get("disclosure_timing") or ev.get("disclosure_type") or "unknown"
            )
            disclosure_date = ev.get("disclosure_date")

            shaped_predictor = bool(ev.get("shaped_predictor", False))
            shaped_predictor_refs = ev.get("shaped_predictor_refs")

            admissible, reason = _admissibility(shaped_predictor, disclosure_timing, event_date)
            held = _held_out(event_id)

            # event_class_id: SAVEPOINT-guarded ontology lookup
            subcategory = str(ev.get("subcategory") or "").strip() or None
            event_class_id = _lookup_event_class(conn, domain_primary, subcategory)

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
                lel_file_sha,   # BA-P6
                lel_source,     # BA-P6
                event_class_id, # BA-P6
            ))

        # Idempotency (N.3)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_event_provenance WHERE chart_id = %s",
                (chart_id,),
            )

        if not rows:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes=f"no events found in {lel_source} — zero provenance rows",
            )

        INSERT_SQL = """
            INSERT INTO mimamsa_event_provenance (
                chart_id, event_id, shaped_predictor, shaped_predictor_refs,
                disclosure_timing, disclosure_date, event_date,
                domain_primary, domain_secondary, event_magnitude,
                held_out, admissible_clean, admissibility_reason,
                partition_seed_version, lel_version, provenance_formula_ver,
                lel_file_sha, lel_source, event_class_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)

        logger.info(
            "[mi_jivanaghatana] inserted %d provenance rows "
            "(source=%s, sha=%s, held_out=%d, clean=%d)",
            len(rows), lel_source,
            (lel_file_sha[:8] if lel_file_sha else "n/a"),
            sum(1 for r in rows if r[10]),
            sum(1 for r in rows if r[11]),
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(rows),
            duration_seconds=time.time() - t0,
        )
