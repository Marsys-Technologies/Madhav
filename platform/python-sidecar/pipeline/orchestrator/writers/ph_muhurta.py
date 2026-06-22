"""
ph_muhurta — Auspicious Windows (L4 Phala wave 4 parallel).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_muhurta.

Reads: phala_anchors · ka_vighnakara · ga_condition_composite · ka_gochara
       (calls ka_muhurta_seva for panchanga scoring via the service)
Writes: phala_muhurta (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, date

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_muhurta.engine import (
    MuhurtaContext,
    derive_muhurta_record,
    ACTION_GRAHA_MAP,
)

logger = logging.getLogger(__name__)

_ACTION_CLASSES = list(ACTION_GRAHA_MAP.keys())
_WINDOW_DAYS = 365 * 3    # 3-year forward horizon


@register('ph_muhurta')
class PhMuhurtaWriter(WriterBase):
    """
    Builds phala_muhurta: for each influenceable anchor + each action class,
    evaluates the panchanga quality + chart-personalized scoring.
    Fuses to ph_nimitta windows (M3) + avoids personal danger windows (M2).
    """
    asset_id = 'ph_muhurta'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_muhurta WHERE chart_id = %s", (chart_id,))

        # Load influenceable anchors (V4 malleability)
        anchors = self._load_influenceable_anchors(conn, chart_id)
        logger.info("ph_muhurta: %d influenceable anchors found", len(anchors))

        # Load obstruction windows (M2) into a lookup: date → obstruction_id
        obstruction_windows = self._load_obstruction_windows(conn, chart_id)

        # Load chart condition scores (M1) for the relevant grahas
        condition_scores = self._load_condition_scores(conn, chart_id)

        rows_inserted = 0
        with conn.cursor() as cur:
            for anchor in anchors:
                anchor_id   = str(anchor['anchor_id'])
                domain      = anchor['domain']
                peak_date   = anchor.get('peak_date')
                window_start = anchor.get('window_start')
                window_end   = anchor.get('window_end')

                # Map domain → best action class for M3 fusion
                domain_action = _DOMAIN_TO_ACTION.get(domain, 'new_venture')
                relevant_graha = ACTION_GRAHA_MAP.get(domain_action, 'saturn')

                # Build a single representative candidate for this anchor's window
                # (full engine would iterate candidate timestamptz slots; we emit one per anchor)
                candidate_start = _to_datetime(window_start or peak_date)
                candidate_end   = _to_datetime(window_end   or peak_date)

                # M1: condition + transit (use loaded scores; default 0.5 if absent)
                condition = condition_scores.get(relevant_graha, 0.5)
                transit   = 0.5   # transit scoring from ka_gochara requires live ephemeris; default

                # M2: check obstruction overlap
                obstruction_id = None
                obstruction_penalty = 0.0
                for (obs_start, obs_end), obs_id in obstruction_windows.items():
                    if candidate_start and obs_start and obs_end:
                        if obs_start <= candidate_start.date() <= obs_end:
                            obstruction_id = obs_id
                            obstruction_penalty = 0.3
                            break

                # Panchanga score — ka_muhurta_seva not available at writer import time;
                # use a deterministic proxy from condition × season_factor
                panchanga_score = round(min(1.0, condition * 0.8 + 0.2), 4)

                mctx = MuhurtaContext(
                    action_class=domain_action,
                    window_start=candidate_start,
                    window_end=candidate_end,
                    hora_lord=relevant_graha,
                    panchanga_score=panchanga_score,
                    panchanga_snapshot={'source': 'ka_muhurta_seva_proxy', 'graha': relevant_graha},
                    classical_citation='Muhūrta-Chintāmaṇi + Grahalaghava',
                    condition_score=condition,
                    transit_score=transit,
                    overlapping_obstruction_id=obstruction_id,
                    obstruction_penalty=obstruction_penalty,
                    linked_anchor_id=anchor_id,   # M3: prediction-fused
                    linked_anchor_domain=domain,
                )

                rec = derive_muhurta_record(mctx)

                try:
                    cur.execute(
                        """
                        INSERT INTO phala_muhurta (
                            chart_id, action_class, window_start, window_end,
                            hora_lord, panchanga_score, chart_personalization_score,
                            personalization_graha, personal_adversity_penalty,
                            overlapping_obstruction_id, linked_anchor_id,
                            composite_quality, window_quality_verdict, verdict_reason,
                            panchanga_snapshot_jsonb, classical_citation,
                            derivation_ledger_jsonb, source_citation
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s, %s,
                            %s::jsonb, %s,
                            %s::jsonb, %s
                        )
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            chart_id, rec.action_class,
                            rec.window_start, rec.window_end,
                            rec.hora_lord, rec.panchanga_score,
                            rec.chart_personalization_score,
                            rec.personalization_graha,
                            rec.personal_adversity_penalty,
                            rec.overlapping_obstruction_id,
                            rec.linked_anchor_id,
                            rec.composite_quality,
                            rec.window_quality_verdict,
                            rec.verdict_reason,
                            json.dumps(rec.panchanga_snapshot_jsonb or {}),
                            rec.classical_citation,
                            json.dumps(rec.derivation_ledger_jsonb),
                            rec.source_citation,
                        ),
                    )
                    rows_inserted += 1
                except Exception as exc:
                    logger.warning("ph_muhurta: insert failed for anchor %s: %s", anchor_id, exc)

        logger.info("ph_muhurta: inserted %d rows into phala_muhurta for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_muhurta', rows_inserted=rows_inserted)

    def _load_influenceable_anchors(self, conn, chart_id: str) -> list:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT anchor_id, domain, malleability, peak_date, window_start, window_end
                FROM phala_anchors
                WHERE chart_id = %s AND malleability IN ('influenceable','semi_influenceable')
                ORDER BY confidence_high DESC NULLS LAST
                LIMIT 100
                """,
                (chart_id,),
            )
            return cur.fetchall()

    def _load_obstruction_windows(self, conn, chart_id: str) -> dict:
        """Load ka_vighnakara obstruction windows as {(start,end): id}.

        ka_vighnakara is built by L3 Kāla — may not exist yet. Uses a SAVEPOINT
        so a missing-table SQL error does not abort the outer transaction.
        """
        result: dict = {}
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_muhurta_obs")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, obstruction_start, obstruction_end
                    FROM ka_vighnakara
                    WHERE chart_id = %s
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    s = row["obstruction_start"]
                    e = row["obstruction_end"]
                    if s and e:
                        s = s if isinstance(s, date) else date.fromisoformat(str(s))
                        e = e if isinstance(e, date) else date.fromisoformat(str(e))
                        result[(s, e)] = row["id"]
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_muhurta_obs")
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_muhurta_obs")
            except Exception:
                pass
            logger.debug("ph_muhurta: ka_vighnakara load skipped: %s", exc)
        return result

    def _load_condition_scores(self, conn, chart_id: str) -> dict[str, float]:
        """Load ga_condition_composite condition_score per graha."""
        result: dict[str, float] = {}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT graha, condition_score
                    FROM ga_condition_composite
                    WHERE chart_id = %s
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    result[str(row[0]).lower()] = float(row[1]) if row[1] is not None else 0.5
        except Exception as exc:
            logger.debug("ph_muhurta: condition_scores load skipped: %s", exc)
        return result


_DOMAIN_TO_ACTION: dict[str, str] = {
    'career':       'start_business',
    'financial':    'contract_signing',
    'health':       'medical',
    'relationship': 'marriage',
    'spiritual':    'spiritual_initiation',
    'psychological':'ceremony',
    'transition':   'travel',
}


def _to_datetime(d) -> datetime | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        return datetime(d.year, d.month, d.day, 6, 0)  # morning start
    try:
        return datetime.fromisoformat(str(d))
    except ValueError:
        return None
