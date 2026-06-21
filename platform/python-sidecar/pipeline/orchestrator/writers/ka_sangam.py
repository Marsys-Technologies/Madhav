"""
ka_sangam — Convergence engine (L3 K4-a).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER calls ctx.db_conn.commit() or .rollback()
NEVER writes to any bodha_* table.

Reads kala_activation_predicates (written by ka_yojaka), runs Mode A + Mode B
convergence search, inserts ranked windows into kala_convergence.
"""
import json
import logging
from datetime import date

import psycopg2.extras

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_sangam.engine import (
    mode_a_search,
    mode_b_sweep,
    convergence_score,
    confidence_label,
    independent_current_count,
    _date_to_jd,
)

logger = logging.getLogger(__name__)

# Horizon: 5-year forward window
_HORIZON_YEARS = 5
_MAX_PREDICATES = 60  # top 60 by dignity_score


@register('ka_sangam')
class KaSangamWriter(WriterBase):
    """
    Convergence engine: Mode A (daśā-prior funnel) + Mode B (off-daśā sweep).
    Inserts into kala_convergence with full rigor-stratum columns.
    """
    asset_id = 'ka_sangam'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # orchestrator owns the transaction; writer NEVER commits
        chart_id = ctx.config['chart_id']

        # Step 1: delete existing rows for this chart (delete-then-insert idempotency §N.3)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_convergence WHERE chart_id = %s",
                (chart_id,),
            )
        logger.info("ka_sangam: deleted existing kala_convergence rows for %s", chart_id)

        # Step 2: load top predicates from kala_activation_predicates
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, chart_id, ayanamsha_id, signal_id, signature_class,
                       dasha_eligibility_rule_jsonb, transit_trigger_jsonb,
                       strength_affliction_hook_jsonb, derivation_ledger_jsonb
                FROM kala_activation_predicates
                WHERE chart_id = %s
                ORDER BY (dasha_eligibility_rule_jsonb->>'eligibility_score')::float DESC NULLS LAST
                LIMIT %s
                """,
                (chart_id, _MAX_PREDICATES),
            )
            predicates = cur.fetchall()

        logger.info("ka_sangam: loaded %d predicates for chart %s", len(predicates), chart_id)

        if not predicates:
            logger.warning("ka_sangam: no predicates found for chart %s — zero rows written", chart_id)
            return WriterResult(asset_id='ka_sangam', rows_inserted=0)

        # Step 3: determine horizon (from today forward _HORIZON_YEARS years)
        from datetime import date, timedelta
        today = date.today()
        horizon_end = date(today.year + _HORIZON_YEARS, today.month, today.day)
        horizon_start_jd = _date_to_jd(today)
        horizon_end_jd   = _date_to_jd(horizon_end)

        # Step 4: for each predicate run Mode A + Mode B
        all_windows: list[dict] = []

        # Load dignity_score from bodha_msr_signals for each predicate
        signal_ids = list({str(p['signal_id']) for p in predicates if p['signal_id']})
        dignity_map: dict[str, float] = {}
        if signal_ids:
            with conn.cursor() as cur:
                placeholders = ','.join(['%s'] * len(signal_ids))
                cur.execute(
                    f"SELECT signal_id, dignity_score FROM bodha_msr_signals WHERE signal_id IN ({placeholders})",
                    signal_ids,
                )
                for row in cur.fetchall():
                    dignity_map[str(row[0])] = float(row[1]) if row[1] is not None else 0.5

        for pred in predicates:
            pred_dict = dict(pred)
            sig_id = pred_dict.get('signal_id')
            pred_dict['dignity_score'] = dignity_map.get(str(sig_id), 0.5) if sig_id else 0.5

            # Ensure JSON fields are dicts (psycopg2 may return them as dicts already)
            for jf in ('dasha_eligibility_rule_jsonb', 'transit_trigger_jsonb',
                       'strength_affliction_hook_jsonb', 'derivation_ledger_jsonb'):
                if isinstance(pred_dict.get(jf), str):
                    pred_dict[jf] = json.loads(pred_dict[jf])
                elif pred_dict.get(jf) is None:
                    pred_dict[jf] = {}

            # Mode A
            try:
                a_windows = mode_a_search(
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    dasha_kala_service=None,
                    gochara_service=None,
                    muhurta_service=None,
                    chart_id=chart_id,
                )
                all_windows.extend(a_windows)
            except Exception as exc:
                logger.warning("ka_sangam: Mode A failed for signal %s: %s", sig_id, exc)

            # Mode B
            try:
                b_windows = mode_b_sweep(
                    signal_id=sig_id,
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    gochara_service=None,
                    magnitude_threshold=0.3,
                )
                all_windows.extend(b_windows)
            except Exception as exc:
                logger.warning("ka_sangam: Mode B failed for signal %s: %s", sig_id, exc)

        logger.info("ka_sangam: generated %d raw windows before dedup", len(all_windows))

        # Step 5: deduplicate by (mode, peak_date, signal_id) — keep highest score
        seen: dict[tuple, dict] = {}
        for w in all_windows:
            key = (w.get('mode'), w.get('peak_date'), str(w.get('signal_id', '')))
            if key not in seen or w['convergence_score'] > seen[key]['convergence_score']:
                seen[key] = w
        deduped = sorted(seen.values(), key=lambda w: w['convergence_score'], reverse=True)

        logger.info("ka_sangam: %d windows after dedup for chart %s", len(deduped), chart_id)

        # Step 6: batch insert into kala_convergence
        rows_inserted = 0
        with conn.cursor() as cur:
            for w in deduped:
                cs = w.get('convergence_score', 0.0)
                orb_s = w.get('orb_strength')
                c_label = confidence_label(cs)

                # Compute independent_current_count from constituent_factors
                cf = w.get('constituent_factors', {})
                currents = {
                    'dasha': bool(cf.get('dasha_score', 0) > 0.3),
                    'nakshatra_overlay': 'nakshatra' in cf,
                    'transit': True,  # transit always present in both modes
                    'panchanga': False,
                    'benefic_dristi': False,
                    'cross_dasha_agreement': False,
                }
                icc = independent_current_count(currents)

                cur.execute(
                    """
                    INSERT INTO kala_convergence (
                        chart_id, window_start, window_end, convergence_score,
                        constituent_factors, source_citation, computed_at,
                        signal_id, mode, peak_date, orb_strength, rarity_years,
                        confidence_score, confidence_label,
                        independent_current_count, is_off_dasha_discovery
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s::jsonb, %s, NOW(),
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s
                    )
                    """,
                    (
                        chart_id,
                        w.get('window_start'),
                        w.get('window_end'),
                        cs,
                        json.dumps(w.get('constituent_factors', {})),
                        w.get('source_citation', ''),
                        str(w.get('signal_id')) if w.get('signal_id') else None,
                        w.get('mode'),
                        w.get('peak_date'),
                        orb_s,
                        None,   # rarity_years: computed by a downstream service
                        cs,     # confidence_score mirrors convergence_score
                        c_label,
                        icc,
                        w.get('is_off_dasha_discovery', False),
                    ),
                )
                rows_inserted += 1

        logger.info("ka_sangam: inserted %d rows into kala_convergence for chart %s",
                    rows_inserted, chart_id)
        return WriterResult(asset_id='ka_sangam', rows_inserted=rows_inserted)
