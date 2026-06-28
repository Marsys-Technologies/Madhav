"""
ph_pramana — Falsifiability Evidence Registry (L4 Phala wave 6).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_pramana.

D5 NO-SCORING gate: this writer NEVER inserts calibration_score,
posterior_probability, accuracy_rate, hit_rate, or Brier_score.
Raises D5ViolationError if any such column is attempted.

Reads: phala_anchors · life_events (LEL)
Writes: phala_pramana (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg

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
                try:
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
                except Exception as exc:
                    logger.warning("ph_pramana: insert failed for anchor %s: %s", rec.anchor_id, exc)

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

    def _load_lel(self, conn, chart_id: str) -> list[LelEntry]:
        """Load life_events (LEL) entries.

        The real table is `life_events` (the prior `life_event_log` name never
        existed). `life_events` is a global, single-native log: it carries no
        chart_id column, so the load is not chart-scoped here. The table may be
        absent on a fresh DB (seeded by the LEL ingest, not the L4 build), in
        which case psycopg raises UndefinedTable; we narrow the except to that
        case and roll back the SAVEPOINT so the outer transaction survives.

        Column map (db_schema.json / live `life_events`):
          id (uuid) · event_date (date) · domain (text) ·
          description -> event_summary · outcome_observed (bool) -> valence.
        `id` is a uuid; `phala_pramana.lel_entry_id` is bigint, so the uuid is
        carried in lel_jsonb (auditable) and lel_id is left unset (None).
        """
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_pramana_lel")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, event_date, domain,
                           description AS event_summary, outcome_observed
                    FROM life_events
                    ORDER BY event_date
                    """,
                )
                entries: list[LelEntry] = []
                for r in cur.fetchall():
                    observed = r.get('outcome_observed')
                    valence = ('observed' if observed
                               else 'not_observed' if observed is False
                               else None)
                    entries.append(LelEntry(
                        lel_id=None,
                        event_date=r['event_date'],
                        domain=str(r.get('domain') or ''),
                        event_summary=str(r.get('event_summary') or ''),
                        outcome_valence=valence,
                        lel_jsonb={'id': str(r['id']), 'event_date': str(r['event_date']),
                                   'summary': str(r.get('event_summary') or '')},
                    ))
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_pramana_lel")
            return entries
        except psycopg.errors.UndefinedTable as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_pramana_lel")
            except Exception:
                pass
            logger.info("ph_pramana: life_events table absent — LEL load skipped: %s", exc)
            return []
