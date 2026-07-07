"""
mi_jivanaghatana — Clean-Evidence Vault & Leakage Firewall (L5 Mīmāṃsā root)
==============================================================================
Every chart — including the native — sources its life events exclusively from
its own `life_events` DB rows (WHERE chart_id = $1). There is no native-only
markdown branch: the chart-scoped DB read is the ONLY source path, so no chart
can ever ingest another chart's events (the native-contamination gate is
structural). A presence check (count_chart_lel_events) distinguishes a genuinely
empty chart from a sourcing/packaging bug.

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
import time
from datetime import datetime
from typing import Any, Optional

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.mimamsa.lel_calibration import (
    PRE_INSTRUMENT_SENTINEL,
    count_chart_lel_events,
    recorded_at_partition,
)

logger = logging.getLogger(__name__)

PARTITION_SEED_VERSION = "v1_md5_mod10"
LEL_VERSION = "v1.7"
PROVENANCE_FORMULA_VER = "mi_jivanaghatana_v2.0"


def classify_leakage_partition(
    recorded_at: Any,
    snapshot_at: Optional[datetime],
) -> str:
    """Partition one life-event row as training vs outcome (Step-5 leakage routing).

    Delegates to lel_calibration.recorded_at_partition (the code-not-convention
    leakage firewall): an event recorded BEFORE the frozen prediction snapshot is
    training evidence; recorded AT/AFTER is outcome evidence.

    A row with no `recorded_at` is treated as pre-instrument (PRE_INSTRUMENT_SENTINEL
    → always training) — the safe default for the current pre-instrument corpus,
    e.g. the 57 native rows that carry the sentinel.
    """
    if recorded_at is None:
        recorded_at = PRE_INSTRUMENT_SENTINEL
    return recorded_at_partition(recorded_at, snapshot_at)


def _resolve_snapshot_at(ctx) -> Optional[datetime]:
    """The frozen-prediction snapshot to partition events against.

    Read from ctx.config['prediction_snapshot_at'] (datetime or ISO string). None
    means there is no prediction yet → every event classifies as training, which
    is correct for the current pre-instrument corpus. Wiring is present so a
    future recorded_at=now() event after a real snapshot routes to 'outcome'.
    """
    raw = ctx.config.get("prediction_snapshot_at")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(str(raw))
    except Exception:
        return None


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
    Populates mimamsa_event_provenance from the chart-scoped `life_events` DB
    table (the sole source path). Per-chart scope — deletes and re-inserts only
    this chart's rows (N.3). BA-P6 EXT: lel_file_sha pinning, lel_source
    tagging, event_class_id mapping.
    """

    asset_id = "mi_jivanaghatana"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id = str(ctx.config.get("chart_id") or "")

        # Step-5 leakage routing: partition each event training-vs-outcome against
        # the frozen prediction snapshot (None → all training). Exposed per-event
        # on self.leakage_partitions so downstream can honor the two-key blind path.
        snapshot_at = _resolve_snapshot_at(ctx)
        self.leakage_partitions: list[dict[str, str]] = []

        # ── Chart-scoped life_events DB read is the ONLY source ──────────────
        # Every chart — including the native — sources its events exclusively
        # from its own `life_events` rows (WHERE chart_id = $1). There is no
        # native-only markdown branch, so no chart can ever ingest another
        # chart's events (native-contamination gate is structural).
        lel_source = "db"
        lel_file_sha: str | None = None
        raw_events: list[dict] = []

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
            # Anti-masking (presence-based, BA-P4 R2.2/W2.2): if THIS chart has
            # recorded life_events rows but the build produced zero, that is a
            # sourcing/packaging bug, not a healthy empty chart. Presence, not
            # identity — a chart-scoped count > 0 flags exactly that case, and
            # correctly stays silent for a genuinely empty chart (e.g. Abhinandan).
            expected_rows = count_chart_lel_events(conn, chart_id)
            if expected_rows > 0:
                logger.warning(
                    "[mi_jivanaghatana] chart_id=%s has %d life_events rows but "
                    "built ZERO provenance events — the configured source (%s) was "
                    "unreachable/empty. This is NOT a healthy empty build; verify "
                    "the life_events rows are present and readable for this chart.",
                    chart_id, expected_rows, lel_source,
                )
            # Graceful empty (FIX 1(b)): zero per-chart life events is the
            # normal, valid build for most (non-native) clients — never raise.
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes=f"no events found in {lel_source} — zero provenance rows",
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

            # Step-5 leakage routing (code, not convention): classify this row as
            # training vs outcome against the frozen snapshot. The 57 native rows
            # carry the pre_instrument sentinel → 'training'. Emitted per-event on
            # self.leakage_partitions so downstream honors the two-key blind path.
            leakage_partition = classify_leakage_partition(
                ev.get("recorded_at"), snapshot_at
            )
            self.leakage_partitions.append(
                {"event_id": event_id, "leakage_partition": leakage_partition}
            )

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

        n_outcome = sum(
            1 for p in self.leakage_partitions if p["leakage_partition"] == "outcome"
        )
        n_training = len(self.leakage_partitions) - n_outcome
        logger.info(
            "[mi_jivanaghatana] inserted %d provenance rows "
            "(source=%s, sha=%s, held_out=%d, clean=%d, "
            "leakage: training=%d, outcome=%d)",
            len(rows), lel_source,
            (lel_file_sha[:8] if lel_file_sha else "n/a"),
            sum(1 for r in rows if r[10]),
            sum(1 for r in rows if r[11]),
            n_training, n_outcome,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(rows),
            duration_seconds=time.time() - t0,
        )
