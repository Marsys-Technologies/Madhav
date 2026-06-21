"""ka_kalasutra writer — bounded activation artifact builder."""
import json
from psycopg2.extras import execute_values
from pipeline.orchestrator.writers import WriterBase, WriterResult, register

@register('ka_kalasutra')
class KaKalasutraWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']
        
        # Idempotency: delete-then-insert scoped to chart
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_activation WHERE chart_id = %s", (chart_id,))
        
        # Read ALL activation predicates for this chart (from ka_yojaka output)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    kap.signal_id,
                    kap.ayanamsha_id,
                    kap.signature_class,
                    kap.dasha_eligibility_rule_jsonb,
                    kap.transit_trigger_jsonb,
                    kap.strength_affliction_hook_jsonb,
                    COALESCE(msr.deterministic_strength, 0.5) as strength,
                    msr.is_active_now
                FROM kala_activation_predicates kap
                LEFT JOIN bodha_msr_signals msr ON kap.signal_id = msr.signal_id
                WHERE kap.chart_id = %s
                ORDER BY kap.signature_class, COALESCE(msr.deterministic_strength, 0) DESC
            """, (chart_id,))
            predicates = cur.fetchall()
        
        if not predicates:
            return WriterResult(rows_written=0, warnings=['No predicates — run ka_yojaka first'])
        
        # Read convergence windows for cross-reference
        with conn.cursor() as cur:
            cur.execute("""
                SELECT signal_id, mode, peak_date, orb_strength, convergence_score
                FROM kala_convergence
                WHERE chart_id = %s AND signal_id IS NOT NULL
            """, (chart_id,))
            convergence_rows = cur.fetchall()
        
        # Build signal → best convergence window map
        convergence_map = {}
        for row in convergence_rows:
            sig_id = str(row[0])
            if sig_id not in convergence_map or (row[4] or 0) > (convergence_map[sig_id]['convergence_score'] or 0):
                convergence_map[sig_id] = {
                    'mode': row[1],
                    'peak_date': row[2],
                    'orb_strength': row[3],
                    'convergence_score': row[4],
                }
        
        # Build activation rows
        rows = []
        for pred in predicates:
            signal_id, ayanamsha_id, sig_class, dasha_rule, transit_rule, strength_hook, strength, is_active_now = pred
            sig_id_str = str(signal_id)
            
            # L2 null hooks: filled here at L3 (NEVER by writing bodha_msr_signals)
            # active_dasha_periods_jsonb: derive from dasha_eligibility_rule
            active_dasha_periods = _derive_dasha_periods(dasha_rule)
            
            # activation_predicted_dates_jsonb: derive from transit_trigger + convergence
            conv = convergence_map.get(sig_id_str, {})
            peak = conv.get('peak_date')
            activation_dates = _derive_activation_dates(transit_rule, peak)
            
            # dasha_activation_proximity_score: how close is peak_date to a dasha boundary?
            proximity_score = _derive_proximity_score(dasha_rule, strength_hook, peak)
            
            # Bounded window
            act_start = _compute_activation_start(peak, sig_class)
            act_end = _compute_activation_end(peak, sig_class)
            
            rows.append((
                chart_id,
                signal_id,
                ayanamsha_id,
                sig_class,
                json.dumps(active_dasha_periods),
                json.dumps(activation_dates),
                proximity_score,
                act_start.isoformat() if act_start else None,
                act_end.isoformat() if act_end else None,
                peak.isoformat() if peak else None,
                conv.get('orb_strength'),
                conv.get('convergence_score'),
                f"ka_kalasutra:v1.0:signal={sig_id_str[:8]}",
            ))
        
        if rows:
            with conn.cursor() as cur:
                execute_values(cur, """
                    INSERT INTO kala_activation (
                        chart_id, signal_id, ayanamsha_id, signature_class,
                        active_dasha_periods_jsonb, activation_predicted_dates_jsonb,
                        dasha_activation_proximity_score,
                        activation_start, activation_end, activation_peak_date,
                        orb_strength, convergence_score, source_citation
                    ) VALUES %s
                """, rows)
        
        return WriterResult(rows_written=len(rows))


def _derive_dasha_periods(dasha_rule: dict) -> list:
    """Fill the L2 NULL active_dasha_periods_jsonb hook from the predicate's dasha_eligibility_rule."""
    if not dasha_rule:
        return []
    periods = []
    # Extract constituent lords from the rule
    lords = dasha_rule.get('constituent_lords', [])
    for lord in lords:
        periods.append({'graha': lord, 'level': 'mahadasha', 'source': 'dasha_eligibility_rule'})
    # Extract any explicit period specs
    explicit = dasha_rule.get('periods', [])
    periods.extend(explicit)
    return periods


def _derive_activation_dates(transit_rule: dict, peak_date) -> list:
    """Fill the L2 NULL activation_predicted_dates_jsonb hook."""
    if not transit_rule or not peak_date:
        return []
    from datetime import timedelta
    dates = []
    # Peak date +/- 3 days as the activation cluster
    for delta in range(-3, 4):
        d = peak_date + timedelta(days=delta)
        dates.append({
            'date': d.isoformat(),
            'strength': max(0.0, 1.0 - abs(delta) * 0.2),
            'trigger': transit_rule.get('type', 'unknown'),
        })
    return dates


def _derive_proximity_score(dasha_rule: dict, strength_hook: dict, peak_date) -> float:
    """Fill the L2 NULL dasha_activation_proximity_score hook."""
    if not peak_date:
        return 0.5
    # Proxy: use the dignity_score from the strength_affliction_hook
    dignity = (dasha_rule or {}).get("dignity_score", (strength_hook or {}).get("dignity_score", 0.5))
    non_affliction = (strength_hook or {}).get('non_affliction', 1.0)
    return min(1.0, max(0.0, dignity * non_affliction))


def _compute_activation_start(peak_date, sig_class: str):
    """Compute activation window start based on signature class."""
    if not peak_date:
        return None
    from datetime import timedelta
    # YOGA: 7-day window; DOSHA: 14-day; others: 5-day
    delta_map = {'YOGA': 7, 'DOSHA': 14, 'DIGNITY': 5, 'SENSITIVE_POINT': 5}
    delta = delta_map.get(sig_class, 5)
    return peak_date - timedelta(days=delta)


def _compute_activation_end(peak_date, sig_class: str):
    """Compute activation window end based on signature class."""
    if not peak_date:
        return None
    from datetime import timedelta
    delta_map = {'YOGA': 7, 'DOSHA': 14, 'DIGNITY': 5, 'SENSITIVE_POINT': 5}
    delta = delta_map.get(sig_class, 5)
    return peak_date + timedelta(days=delta)
