"""ka_kalasutra writer — bounded activation artifact builder.

WP-2.1 / R-45 (LANE0 root cause): date-population no longer depends solely on
`kala_convergence.peak_date`. Each predicate is resolved against the chart's L1
Vimśottarī daśā timeline (`chart_dashas`) via the shared, deterministic
`services.ka_temporal` helper. When a convergence peak exists it refines the
window (legacy behaviour); when it does not — the ~99% NULL-date case — the
matched daśā period supplies real, L1-sourced start/end/peak dates and a
non-empty `activation_predicted_dates_jsonb` fallback. No fabricated dates
(B.10): every date traces to a chart_dashas row (§N.5).
"""
import json
from datetime import date as _date

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_temporal import load_dasha_timeline, resolve_activation_windows


@register('ka_kalasutra')
class KaKalasutraWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']

        # Idempotency: delete-then-insert scoped to chart (§N.3)
        with conn.cursor() as _timeout_cur:
            _timeout_cur.execute("SET LOCAL statement_timeout = 0")
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
                    kap.strength_affliction_hook_jsonb
                FROM kala_activation_predicates kap
                WHERE kap.chart_id = %s
                ORDER BY kap.signature_class
            """, (chart_id,))
            predicates = cur.fetchall()

        if not predicates:
            return WriterResult(asset_id='ka_kalasutra', rows_inserted=0, notes='No predicates — run ka_yojaka first')

        # WP-2.1: load the L1 dasha timeline ONCE — the deterministic date source
        # that lets us resolve activations even when convergence has no peak.
        dasha_timeline = load_dasha_timeline(conn, chart_id)

        # Read convergence windows for cross-reference (peak REFINES a window)
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
            sig_id = str(row['signal_id'])
            if sig_id not in convergence_map or (row['convergence_score'] or 0) > (convergence_map[sig_id]['convergence_score'] or 0):
                convergence_map[sig_id] = {
                    'mode': row['mode'],
                    'peak_date': row['peak_date'],
                    'orb_strength': row['orb_strength'],
                    'convergence_score': row['convergence_score'],
                }

        # Build activation rows
        rows = []
        dated = 0
        for pred in predicates:
            signal_id = pred['signal_id']
            ayanamsha_id = pred['ayanamsha_id']
            sig_class = pred['signature_class']
            dasha_rule = pred['dasha_eligibility_rule_jsonb']
            transit_rule = pred['transit_trigger_jsonb']
            strength_hook = pred['strength_affliction_hook_jsonb']
            sig_id_str = str(signal_id)

            conv = convergence_map.get(sig_id_str, {})
            peak = _coerce_date(conv.get('peak_date'))

            # WP-2.1: single deterministic resolution — convergence peak when
            # present, else the matched dasha period from the L1 timeline.
            windows = resolve_activation_windows(
                dasha_rule,
                dasha_timeline,
                transit_rule=transit_rule,
                strength_hook=strength_hook,
                convergence_peak=peak,
                signature_class=sig_class,
            )

            if windows.activation_start is not None:
                dated += 1

            rows.append((
                chart_id,
                signal_id,
                ayanamsha_id,
                sig_class,
                json.dumps(windows.active_dasha_periods),
                json.dumps(windows.predicted_dates),
                windows.proximity_score,
                windows.activation_start.isoformat() if windows.activation_start else None,
                windows.activation_end.isoformat() if windows.activation_end else None,
                windows.activation_peak.isoformat() if windows.activation_peak else None,
                conv.get('orb_strength'),
                conv.get('convergence_score'),
                f"ka_kalasutra:v1.0:signal={sig_id_str[:8]}:src={windows.resolution_source}",
            ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO kala_activation (
                        chart_id, signal_id, ayanamsha_id, signature_class,
                        active_dasha_periods_jsonb, activation_predicted_dates_jsonb,
                        dasha_activation_proximity_score,
                        activation_start, activation_end, activation_peak_date,
                        orb_strength, convergence_score, source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    rows,
                )

        return WriterResult(
            asset_id='ka_kalasutra',
            rows_inserted=len(rows),
            notes=f"{dated}/{len(rows)} activations dated",
        )


def _coerce_date(d):
    """Accept a date or ISO string (or None), return a date or None."""
    if d is None or isinstance(d, _date):
        return d
    try:
        return _date.fromisoformat(str(d))
    except (TypeError, ValueError):
        return None


# ── Legacy convergence-only helpers (retained for backward-compat + unit tests).
# The writer now routes through services.ka_temporal.resolve_activation_windows;
# these remain as the documented convergence-path primitives.

def _derive_dasha_periods(dasha_rule: dict) -> list:
    """Fill the L2 NULL active_dasha_periods_jsonb hook from the predicate's dasha_eligibility_rule."""
    if not dasha_rule:
        return []
    periods = []
    lords = dasha_rule.get('constituent_lords', [])
    for lord in lords:
        periods.append({'graha': lord, 'level': 'mahadasha', 'source': 'dasha_eligibility_rule'})
    explicit = dasha_rule.get('periods', [])
    periods.extend(explicit)
    return periods


def _derive_activation_dates(transit_rule: dict, peak_date) -> list:
    """Fill the L2 NULL activation_predicted_dates_jsonb hook (convergence path)."""
    if not transit_rule or not peak_date:
        return []
    from datetime import timedelta
    dates = []
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
    dignity = (dasha_rule or {}).get("dignity_score", (strength_hook or {}).get("dignity_score", 0.5))
    non_affliction = (strength_hook or {}).get('non_affliction', 1.0)
    return min(1.0, max(0.0, dignity * non_affliction))


def _compute_activation_start(peak_date, sig_class: str):
    """Compute activation window start based on signature class (convergence path)."""
    if not peak_date:
        return None
    from datetime import timedelta
    delta_map = {'YOGA': 7, 'DOSHA': 14, 'DIGNITY': 5, 'SENSITIVE_POINT': 5}
    delta = delta_map.get(sig_class, 5)
    return peak_date - timedelta(days=delta)


def _compute_activation_end(peak_date, sig_class: str):
    """Compute activation window end based on signature class (convergence path)."""
    if not peak_date:
        return None
    from datetime import timedelta
    delta_map = {'YOGA': 7, 'DOSHA': 14, 'DIGNITY': 5, 'SENSITIVE_POINT': 5}
    delta = delta_map.get(sig_class, 5)
    return peak_date + timedelta(days=delta)
