"""
ph_pramana — Falsifiability Evidence Registry (L4 Phala wave 6).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_pramana.

D5 NO-SCORING gate: this writer NEVER inserts calibration_score,
posterior_probability, accuracy_rate, hit_rate, or Brier_score.
Raises D5ViolationError if any such column is attempted.

Reads: phala_anchors · life_events (LEL; THIS chart's rows only, via brahmagyan.phala.life_events_scope)
Writes: phala_pramana (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg

from brahmagyan.phala.life_events_scope import fetch_chart_life_events
from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_pramana.engine import (
    AnchorForPramana,
    LelEntry,
    PramanaContext,
    D5ViolationError,
    derive_pramana_records,
)

logger = logging.getLogger(__name__)

# D5: forbidden scoring column names — writer checks its own INSERT at boot
_D5_FORBIDDEN_COLUMNS = {
    'calibration_score', 'posterior_probability', 'accuracy_rate',
    'hit_rate', 'precision', 'recall', 'brier_score', 'empirical_score',
}


@register('ph_pramana')
class PhPramanaWriter(WriterBase):
    """
    Builds phala_pramana: one falsifiability record per phala_anchors entry.
    Classifies window_status + evidence_type from LEL; NEVER scores outcomes.
    """
    asset_id = 'ph_pramana'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']
        today = date.today()

        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_pramana WHERE chart_id = %s", (chart_id,))

        anchors   = self._load_anchors(conn, chart_id)
        lel_rows  = self._load_lel(conn, chart_id)

        logger.info("ph_pramana: %d anchors / %d LEL entries", len(anchors), len(lel_rows))

        pctx = PramanaContext(
            chart_id=chart_id,
            today=today,
            anchors=anchors,
            lel_entries=lel_rows,
        )

        records = derive_pramana_records(pctx)

        rows_inserted = 0
        with conn.cursor() as cur:
            for rec in records:
                # D5 gate: verify record has no forbidden scoring fields
                self._d5_gate(rec)
                cur.execute(
                    """
                    INSERT INTO phala_pramana (
                        chart_id, anchor_id,
                        evidence_type, evidence_strength_label,
                        falsifier_text, observable_criteria_jsonb,
                        window_status,
                        lel_entry_id, lel_entry_jsonb,
                        linked_sodhana_id,
                        derivation_ledger_jsonb, source_citation
                    ) VALUES (
                        %s, %s,
                        %s, %s,
                        %s, %s::jsonb,
                        %s,
                        %s, %s::jsonb,
                        %s,
                        %s::jsonb, %s
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        chart_id, rec.anchor_id,
                        rec.evidence_type, rec.evidence_strength_label,
                        rec.falsifier_text,
                        json.dumps(rec.observable_criteria_jsonb),
                        rec.window_status,
                        rec.lel_entry_id,
                        json.dumps(rec.lel_entry_jsonb) if rec.lel_entry_jsonb else None,
                        rec.linked_sodhana_id,
                        json.dumps(rec.derivation_ledger_jsonb), rec.source_citation,
                    ),
                )
                rows_inserted += 1

        logger.info("ph_pramana: inserted %d rows into phala_pramana for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_pramana', rows_inserted=rows_inserted)

    def _d5_gate(self, rec) -> None:
        """D5 hard gate: any scoring attribute on the record is a build-halt."""
        for col in _D5_FORBIDDEN_COLUMNS:
            if hasattr(rec, col):
                raise D5ViolationError(
                    f"ph_pramana D5 VIOLATION: PramanaRecord has forbidden scoring field '{col}'. "
                    "L5 Mimamsa owns all calibration. This is a build-halt event."
                )

    def _load_anchors(self, conn, chart_id: str) -> list[AnchorForPramana]:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT anchor_id, domain, anchor_source,
                       falsifier, window_start, window_end, peak_date,
                       magnitude, confidence_high, derivation_ledger_jsonb
                FROM phala_anchors
                WHERE chart_id = %s
                ORDER BY anchor_id
                """,
                (chart_id,),
            )
            rows: list[AnchorForPramana] = []
            for r in cur.fetchall():
                ledger = r.get('derivation_ledger_jsonb') or {}
                if isinstance(ledger, str):
                    try:
                        import json as _j
                        ledger = _j.loads(ledger)
                    except Exception:
                        ledger = {}
                rows.append(AnchorForPramana(
                    anchor_id=str(r['anchor_id']),
                    domain=str(r.get('domain') or ''),
                    anchor_source=str(r.get('anchor_source') or ''),
                    falsifier=str(r.get('falsifier') or ''),
                    window_start=r.get('window_start'),
                    window_end=r.get('window_end'),
                    peak_date=r.get('peak_date'),
                    magnitude=str(r.get('magnitude') or '') or None,
                    confidence_high=float(r['confidence_high']) if r.get('confidence_high') is not None else None,
                    derivation_ledger_jsonb=ledger if isinstance(ledger, dict) else {},
                ))
            return rows

    def _load_lel(self, conn, chart_id) -> list[LelEntry]:
        """Load THIS chart's life_events (LEL) entries, and only this chart's.

        SS ruling N-105: `life_events` is people-entered, private and chart-scoped (`chart_id` NOT NULL since
        migration 423). This loader used to read the WHOLE table (the old docstring called it "a global,
        single-native log" with "no chart_id column": both false since migration 423), so every chart it built was
        classified against every other chart's life events. It now goes through
        `brahmagyan.phala.life_events_scope.fetch_chart_life_events`, the one door for L4 reads: chart-scoped by
        the build's chart_id (UUID or str), via the chart-scoped security-barrier view where the role has it
        (migration 1274) and the explicit `WHERE chart_id = %s` everywhere, with a runtime guard that a foreign
        row can never be returned.

        The table may be absent on a fresh DB (seeded by the LEL ingest, not the L4 build), in which case psycopg
        raises UndefinedTable; we narrow the except to that case (the helper has already rolled back its
        SAVEPOINT, so the outer transaction survives). A privilege error is NOT an empty log: it propagates.

        Column map (live `life_events`):
          id (uuid) - event_date (date) - category (text) - description -> event_summary -
          outcome_observed (bool) -> valence.
        `id` is a uuid; `phala_pramana.lel_entry_id` is bigint, so the uuid is carried in lel_jsonb (auditable)
        and lel_id is left unset (None).

        F2 (L4_W1_ANALYSIS_BATCH_D.md section ph_pramana): LelEntry.domain is built from
        `category` here, NOT the raw `domain` column -- `domain` is a compound
        "<category>/<subtype>" slug (e.g. 'career/award_selection'); `category` is
        the coarse bucket already aligned with the canonical L4 domain vocabulary
        that the engine's `_normalize_domain()` compares against.
        """
        try:
            rows = fetch_chart_life_events(
                conn, chart_id,
                ("id", "event_date", "category", "description", "outcome_observed"),
                order_by=("event_date",),
            )
        except psycopg.errors.UndefinedTable as exc:
            logger.info("ph_pramana: life_events table absent — LEL load skipped: %s", exc)
            return []
        entries: list[LelEntry] = []
        for r in rows:
            observed = r.get('outcome_observed')
            valence = ('observed' if observed
                       else 'not_observed' if observed is False
                       else None)
            entries.append(LelEntry(
                lel_id=None,
                event_date=r['event_date'],
                domain=str(r.get('category') or ''),
                event_summary=str(r.get('description') or ''),
                outcome_valence=valence,
                lel_jsonb={'id': str(r['id']), 'event_date': str(r['event_date']),
                           'summary': str(r.get('description') or '')},
            ))
        return entries
