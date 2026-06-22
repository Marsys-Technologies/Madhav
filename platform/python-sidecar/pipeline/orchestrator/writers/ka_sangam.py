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
from services.ka_dasha_kala.service import KaDashaKalaService
from services.ka_gochara.service import KaGocharaService

logger = logging.getLogger(__name__)

# Horizon: 5-year forward window (near tier)
_HORIZON_YEARS = 5
_MAX_PREDICATES = 60  # top 60 by dignity_score

# U2 lifetime tier: dāśā-boundary-anchored convergence over the native's full life.
# Anchored at parva spans from kala_jivana_parva (one parva per dāśā-system
# boundary). The near tier sweeps a continuous 5y calendar; the lifetime tier
# instead runs the SAME Mode A + Mode B engine over each parva span, so the
# parvas finally have convergence data to average (kala_jivana_parva.
# avg_effective_score was NULL throughout because no lifetime data existed).
_LIFETIME_HORIZON_YEARS = 100   # birth_date → birth_date + 100y
_LIFETIME_MAX_PREDICATES = 24   # tighter predicate budget per span keeps rows ≤ ~13k
_LIFETIME_MAX_ROWS = 13_000     # row-budget ceiling for the lifetime tier


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

        # CF.L3.6: instantiate real dasha-prior service (read-only; never commits)
        dasha_kala_service = KaDashaKalaService(conn)

        # U3: instantiate gochara service for C8/C9/C10 current computation
        try:
            import swisseph as swe
            gochara_service = KaGocharaService(swe)
        except Exception as exc:
            logger.warning("ka_sangam: could not instantiate KaGocharaService: %s — C8/C9/C10 currents will be 0.0", exc)
            gochara_service = None

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

        # Normalise predicate dicts once (dignity + JSON coercion) for reuse across tiers
        pred_dicts: list[dict] = []
        for pred in predicates:
            pred_dict = dict(pred)
            sig_id = pred_dict.get('signal_id')
            pred_dict['dignity_score'] = dignity_map.get(str(sig_id), 0.5) if sig_id else 0.5
            for jf in ('dasha_eligibility_rule_jsonb', 'transit_trigger_jsonb',
                       'strength_affliction_hook_jsonb', 'derivation_ledger_jsonb'):
                if isinstance(pred_dict.get(jf), str):
                    pred_dict[jf] = json.loads(pred_dict[jf])
                elif pred_dict.get(jf) is None:
                    pred_dict[jf] = {}
            pred_dicts.append(pred_dict)

        # ── Step 3: NEAR tier — 5y forward calendar sweep (unchanged logic) ──────
        from datetime import date, timedelta
        today = date.today()
        horizon_end = date(today.year + _HORIZON_YEARS, today.month, today.day)
        near_windows = self._generate_windows(
            pred_dicts=pred_dicts,
            horizon_start=today,
            horizon_end=horizon_end,
            dasha_kala_service=dasha_kala_service,
            gochara_service=gochara_service,
            chart_id=chart_id,
        )
        near_deduped = self._dedup(near_windows)
        logger.info("ka_sangam: NEAR tier — %d windows after dedup for chart %s",
                    len(near_deduped), chart_id)

        # ── Step 4: LIFETIME tier — dāśā-boundary-anchored, full-life horizon ────
        lifetime_deduped = self._generate_lifetime_windows(
            conn=conn,
            pred_dicts=pred_dicts,
            dasha_kala_service=dasha_kala_service,
            gochara_service=gochara_service,
            chart_id=chart_id,
        )
        logger.info("ka_sangam: LIFETIME tier — %d windows after dedup for chart %s",
                    len(lifetime_deduped), chart_id)

        # ── Step 5: insert both tiers into kala_convergence ──────────────────────
        rows_inserted = 0
        with conn.cursor() as cur:
            rows_inserted += self._insert_windows(cur, chart_id, near_deduped, 'near')
            rows_inserted += self._insert_windows(cur, chart_id, lifetime_deduped, 'lifetime')

        logger.info(
            "ka_sangam: inserted %d rows into kala_convergence for chart %s "
            "(near=%d, lifetime=%d)",
            rows_inserted, chart_id, len(near_deduped), len(lifetime_deduped),
        )
        return WriterResult(asset_id='ka_sangam', rows_inserted=rows_inserted)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _generate_windows(self, pred_dicts, horizon_start, horizon_end,
                          dasha_kala_service, gochara_service, chart_id) -> list[dict]:
        """Run Mode A + Mode B for every predicate over [horizon_start, horizon_end]."""
        horizon_start_jd = _date_to_jd(horizon_start)
        horizon_end_jd   = _date_to_jd(horizon_end)
        all_windows: list[dict] = []
        for pred_dict in pred_dicts:
            sig_id = pred_dict.get('signal_id')
            try:
                all_windows.extend(mode_a_search(
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    dasha_kala_service=dasha_kala_service,
                    gochara_service=gochara_service,
                    muhurta_service=None,
                    chart_id=chart_id,
                ))
            except Exception as exc:
                logger.warning("ka_sangam: Mode A failed for signal %s: %s", sig_id, exc)
            try:
                all_windows.extend(mode_b_sweep(
                    signal_id=sig_id,
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    gochara_service=gochara_service,
                    magnitude_threshold=0.3,
                ))
            except Exception as exc:
                logger.warning("ka_sangam: Mode B failed for signal %s: %s", sig_id, exc)
        return all_windows

    def _generate_lifetime_windows(self, conn, pred_dicts, dasha_kala_service,
                                   gochara_service, chart_id) -> list[dict]:
        """
        Lifetime tier: anchor convergence search at parva spans from
        kala_jivana_parva (one parva per dāśā-system boundary). Each parva span
        is searched with the SAME Mode A + Mode B engine, so the parvas gain the
        convergence data they previously lacked (avg_effective_score was NULL).

        Falls back to a single birth→birth+100y span if no parvas exist yet
        (e.g. first build, before ka_jivana_parva has run). Row-budget capped at
        _LIFETIME_MAX_ROWS; predicate budget tightened to _LIFETIME_MAX_PREDICATES.
        """
        from datetime import date

        # Parva boundaries (start_year/end_year) for this chart
        spans: list[tuple[date, date]] = []
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT start_year, end_year
                FROM kala_jivana_parva
                WHERE chart_id = %s
                ORDER BY start_year
                """,
                (chart_id,),
            )
            for start_y, end_y in cur.fetchall():
                if start_y is None:
                    continue
                s = date(int(start_y), 1, 1)
                e = date(int(end_y), 12, 31) if end_y is not None else date(int(start_y) + 20, 12, 31)
                if e > s:
                    spans.append((s, e))

        if not spans:
            # Fallback: derive lifetime horizon from birth date in chart_dashas
            birth_year = None
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MIN(start_date) FROM chart_dashas WHERE chart_id = %s AND level_n = 1",
                    (chart_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    birth_year = row[0].year
            birth_year = birth_year or 1984
            spans = [(date(birth_year, 1, 1), date(birth_year + _LIFETIME_HORIZON_YEARS, 12, 31))]
            logger.info("ka_sangam: no parvas found — lifetime tier falls back to single %d-year span", _LIFETIME_HORIZON_YEARS)

        # Tighten predicate budget for the lifetime tier to stay under the row ceiling
        lt_preds = pred_dicts[:_LIFETIME_MAX_PREDICATES]

        all_windows: list[dict] = []
        for span_start, span_end in spans:
            all_windows.extend(self._generate_windows(
                pred_dicts=lt_preds,
                horizon_start=span_start,
                horizon_end=span_end,
                dasha_kala_service=dasha_kala_service,
                gochara_service=gochara_service,
                chart_id=chart_id,
            ))

        deduped = self._dedup(all_windows)
        if len(deduped) > _LIFETIME_MAX_ROWS:
            logger.warning(
                "ka_sangam: lifetime tier produced %d windows — capping to %d highest-scoring",
                len(deduped), _LIFETIME_MAX_ROWS,
            )
            deduped = deduped[:_LIFETIME_MAX_ROWS]
        return deduped

    @staticmethod
    def _dedup(all_windows: list[dict]) -> list[dict]:
        """Deduplicate by (mode, peak_date, signal_id) — keep highest score."""
        seen: dict[tuple, dict] = {}
        for w in all_windows:
            key = (w.get('mode'), w.get('peak_date'), str(w.get('signal_id', '')))
            if key not in seen or w['convergence_score'] > seen[key]['convergence_score']:
                seen[key] = w
        return sorted(seen.values(), key=lambda w: w['convergence_score'], reverse=True)

    def _insert_windows(self, cur, chart_id, deduped: list[dict], horizon_tier: str) -> int:
        """Insert a tier's deduped windows into kala_convergence; return count."""
        rows_inserted = 0
        for w in deduped:
                cs = w.get('convergence_score', 0.0)
                orb_s = w.get('orb_strength')
                c_label = confidence_label(cs)

                # Compute independent_current_count from constituent_factors (U3: C7-C12)
                cf = w.get('constituent_factors', {})
                currents = {
                    'dasha': bool(cf.get('dasha_score', 0) > 0.3),
                    'nakshatra_overlay': 'nakshatra' in cf,
                    'transit': True,  # transit always present in both modes
                    'panchanga': False,
                    'benefic_dristi': False,
                    'cross_dasha_agreement': bool(cf.get('cross_dasha_agreement', 0) > 0.0),
                    # U3 C7-C12 currents
                    'ashtakavarga_transit_potency': bool(cf.get('c7_ashtakavarga_potency', 0) > 0.0),
                    'eclipse_proximity': bool(cf.get('c8_eclipse_proximity', 0) > 0.0),
                    'transit_to_transit': bool(cf.get('c9_transit_to_transit', 0) > 0.0),
                    'station_retrograde': bool(cf.get('c10_station_retrograde', 0) > 0.0),
                    'tajika_annual_reinforcement': bool(cf.get('c12_tajika_reinforcement', 0) > 0.0),
                    # U3 C13 school_consensus (post-U4)
                    'school_consensus': bool(cf.get('c13_school_consensus', 0) > 0.0),
                }
                icc = independent_current_count(currents)

                cur.execute(
                    """
                    INSERT INTO kala_convergence (
                        chart_id, window_start, window_end, convergence_score,
                        constituent_factors, source_citation, computed_at,
                        signal_id, mode, peak_date, orb_strength, rarity_years,
                        confidence_score, confidence_label,
                        independent_current_count, is_off_dasha_discovery,
                        horizon_tier
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s::jsonb, %s, NOW(),
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s
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
                        w.get('rarity_years'),  # CF.L3.4: real planet-period rarity
                        cs,     # confidence_score mirrors convergence_score
                        c_label,
                        icc,
                        w.get('is_off_dasha_discovery', False),
                        horizon_tier,
                    ),
                )
                rows_inserted += 1
        return rows_inserted
