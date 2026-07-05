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
import os
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


def _resolve_lel_markdown_path() -> pathlib.Path:
    """
    Resolve the LEL markdown path. An env var override takes priority (for
    deployment/container layouts where the repo root isn't a fixed number of
    parents above this file). Falls back to the on-disk repo-relative path.

    __file__ is platform/python-sidecar/pipeline/orchestrator/writers/mi_jivanaghatana.py
    parents: [0]=writers [1]=orchestrator [2]=pipeline [3]=python-sidecar
             [4]=platform [5]=repo root
    The prior code used parents[4] ("platform"), which resolves to
    platform/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md — a path that has never
    existed (01_FACTS_LAYER lives at the repo root, one level above
    platform/). This silently produced a non-existent path, `.exists()`
    returned False, and every build fell through to the empty life_events
    DB fallback — the root cause of the 0-row root-asset finding.
    """
    override = os.environ.get("MI_LEL_MARKDOWN_PATH")
    if override:
        return pathlib.Path(override)
    return pathlib.Path(__file__).parents[5] / "01_FACTS_LAYER" / "LIFE_EVENT_LOG_v1_2.md"


_LEL_MARKDOWN_PATH = _resolve_lel_markdown_path()

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


_EVENT_ID_RE = re.compile(r'^(EVT\.\S+):\s*$')
_TOP_LEVEL_FIELD_RE = re.compile(r'^ {2}([a-z_]+):[ \t]?(.*)$')

# The only fields mi_jivanaghatana actually reads off an event (see run()
# below) — narrative fields (description/native_reflection/notes) and the
# nested chart_state_at_event/retrodictive_match blocks are never consumed,
# so they don't need to survive parsing.
_CONSUMED_RAW_KEYS = {
    "date", "event_date", "event_start_date", "start_date",
    "category", "domain_primary", "domain",
    "subcategory", "domain_secondary", "secondary_domains",
    "magnitude", "event_magnitude",
    "disclosure_timing", "disclosure_type", "disclosure_date",
    "shaped_predictor", "shaped_predictor_refs",
}


def _unquote(raw: str) -> str:
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    return v


def _parse_block_raw(block: str) -> dict | None:
    """
    Fallback for blocks that fail strict YAML parsing. Reads event_id plus
    the handful of top-level scalar fields this writer consumes as raw,
    uninterpreted strings — line by line, independent of YAML syntax.

    This sidesteps the recurring LEL authoring failure mode: narrative prose
    fields (description / native_reflection / notes) routinely contain
    unquoted colons ("Doc framing: ...") that break YAML block-mapping,
    even though this writer never reads those fields. Losing the whole
    event over an unrelated field is unnecessary.
    """
    lines = block.splitlines()
    if not lines:
        return None
    id_match = _EVENT_ID_RE.match(lines[0])
    if not id_match:
        return None
    data: dict[str, Any] = {"event_id": id_match.group(1)}
    for line in lines[1:]:
        m = _TOP_LEVEL_FIELD_RE.match(line)
        if not m or m.group(1) not in _CONSUMED_RAW_KEYS:
            continue
        val = _unquote(m.group(2))
        if val:
            data[m.group(1)] = val
    return data


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
    skipped = 0
    recovered = 0
    for block in blocks:
        try:
            if _has_yaml:
                import yaml as _yaml
                data = _yaml.safe_load(block)
            else:
                # Minimal fallback: skip non-yaml builds
                skipped += 1
                continue
        except Exception as exc:
            # Recover via the raw top-level-field fallback (see
            # _parse_block_raw) instead of dropping the event outright.
            fallback = _parse_block_raw(block)
            if fallback is not None:
                events.append(fallback)
                recovered += 1
                logger.info(
                    "[mi_jivanaghatana] recovered %s via raw-field fallback "
                    "after YAML parse failure: %s",
                    fallback["event_id"], exc,
                )
                continue
            skipped += 1
            logger.warning(
                "[mi_jivanaghatana] skipping malformed YAML block (%s): %s",
                exc, block[:80].replace("\n", " "),
            )
            continue

        if not isinstance(data, dict):
            skipped += 1
            continue

        for key, val in data.items():
            if not (isinstance(key, str) and key.startswith("EVT.")) or not isinstance(val, dict):
                continue
            events.append({"event_id": key, **val})

    logger.info(
        "[mi_jivanaghatana] parsed %d events from %d yaml blocks (%d recovered "
        "via raw-field fallback, %d skipped as malformed/non-EVT) from LEL "
        "markdown (sha=%s...)",
        len(events), len(blocks), recovered, skipped, file_sha[:8],
    )
    if skipped > 0:
        logger.warning(
            "[mi_jivanaghatana] %d of %d LEL yaml blocks still unrecoverable — "
            "no EVT.* key found on the block's first line",
            skipped, len(blocks),
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

        if not raw_events and not ctx.dry_run:
            # This is the L5 root asset — a 0-row build here silently collapses
            # the entire downstream evidentiary chain (mimamsa_calibration,
            # mimamsa_reliability, mimamsa_attribution, mimamsa_discoveries all
            # also read as 0), yet previously returned a benign WriterResult
            # that reported a clean 'lit' build with no error. Fail loudly
            # instead of silently absorbing a packaging/path or DB-population
            # problem as a legitimate zero-event chart.
            raise RuntimeError(
                f"[mi_jivanaghatana] chart_id={chart_id}: both the LEL markdown "
                f"({_LEL_MARKDOWN_PATH}, exists={_LEL_MARKDOWN_PATH.exists()}) and "
                "the life_events DB fallback yielded zero events. Verify the "
                "LEL markdown ships at this resolved path in the runtime "
                "container and that life_events is populated, before treating "
                "this as a healthy build."
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
