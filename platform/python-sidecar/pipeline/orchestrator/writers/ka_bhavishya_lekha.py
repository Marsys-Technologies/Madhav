"""ka_bhavishya_lekha writer — probabilistic forward projection artifact."""
import json
from datetime import date
from pipeline.orchestrator.writers import WriterBase, WriterResult, register


@register('ka_bhavishya_lekha')
class KaBhavishyaLekhaWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']
        today = date.today()

        # Idempotency
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_bhavishya WHERE chart_id = %s", (chart_id,))

        # Read top-ranked darshana windows in the future (next 3 years)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT kd.convergence_id, kd.signal_id, kd.net_label, kd.effective_score,
                       kd.peak_date, kd.window_start, kd.window_end,
                       kd.narrative, kd.obstruction_summary,
                       kc.confidence_label, kc.rarity_years, kc.mode
                FROM kala_darshana kd
                JOIN kala_convergence kc ON kd.convergence_id = kc.convergence_id
                WHERE kd.chart_id = %s
                  AND kd.peak_date >= %s
                  AND kd.peak_date <= %s
                  AND kd.net_label NOT IN ('obstructed_severe')
                ORDER BY kd.effective_score DESC NULLS LAST
                LIMIT 50
            """, (chart_id, today, date(today.year + 3, today.month, today.day)))
            darshana_rows = cur.fetchall()

        if not darshana_rows:
            return WriterResult(asset_id='ka_bhavishya_lekha', rows_inserted=0, notes='No future darshana windows — run ka_kala_darshana first')

        # CF.L3.5: batch-fetch signal_type_id for domain mapping
        # darshana_rows is list[dict] (dict_row cursor); use key access throughout
        signal_ids_seen = [str(r['signal_id']) for r in darshana_rows if r['signal_id']]
        signal_type_map: dict[str, str] = {}
        if signal_ids_seen:
            placeholders = ','.join(['%s'] * len(signal_ids_seen))
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT signal_id, signal_type_id FROM bodha_msr_signals WHERE signal_id IN ({placeholders})",
                    signal_ids_seen,
                )
                for sig_row in cur.fetchall():
                    if sig_row['signal_type_id']:
                        signal_type_map[str(sig_row['signal_id'])] = str(sig_row['signal_type_id'])

        rows = []
        for rank, row in enumerate(darshana_rows, start=1):
            conv_id = row['convergence_id']
            signal_id = row['signal_id']
            net_label = row['net_label']
            eff_score = row['effective_score']
            peak_date = row['peak_date']
            win_start = row['window_start']
            win_end = row['window_end']
            narrative = row['narrative']
            obs_summary = row['obstruction_summary']
            conf_label = row['confidence_label']
            rarity = row['rarity_years']
            mode = row['mode']

            # Probability tier
            tier = _assign_tier(eff_score, net_label)

            # CF.L3.5: domain from signal_type_id keywords; rank rotation as fallback
            domain = _infer_domain(rank, net_label, signal_type_map.get(str(signal_id) if signal_id else ''))

            # Falsifiability hook
            falsifiability = _build_falsifiability(tier, domain, peak_date, eff_score)

            # Source chain
            source_chain = [{'convergence_id': conv_id, 'mode': mode, 'confidence': conf_label}]

            # Projection narrative
            proj_narrative = _build_projection_narrative(
                tier=tier, domain=domain, peak_date=peak_date,
                eff_score=eff_score, conf_label=conf_label,
                rarity=rarity, net_label=net_label,
            )

            rows.append((
                chart_id,
                rank,
                tier,
                domain,
                peak_date.isoformat() if peak_date and hasattr(peak_date, 'isoformat') else None,
                win_start.isoformat() if win_start and hasattr(win_start, 'isoformat') else None,
                win_end.isoformat() if win_end and hasattr(win_end, 'isoformat') else None,
                conv_id,
                signal_id,
                eff_score,
                json.dumps(falsifiability),
                json.dumps(source_chain),
                json.dumps(proj_narrative),
                False,
                None,
                f"ka_bhavishya_lekha:v1.0:rank={rank}",
            ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO kala_bhavishya (
                        chart_id, projection_rank, probability_tier, domain,
                        peak_date, window_start, window_end,
                        convergence_id, signal_id, effective_score,
                        falsifiability, source_chain, narrative,
                        outcome_recorded, outcome_notes, source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, rows)

        return WriterResult(asset_id='ka_bhavishya_lekha', rows_inserted=len(rows))


def _assign_tier(effective_score: float, net_label: str) -> str:
    """Assign probability tier based on effective score and label."""
    if effective_score is None:
        return 'tier_3_speculative'
    if effective_score >= 0.70 and net_label not in ('obstructed', 'obstructed_severe', 'neutral'):
        return 'tier_1_high'
    if effective_score >= 0.45:
        return 'tier_2_moderate'
    return 'tier_3_speculative'


_DOMAINS = ['career', 'health', 'relationship', 'finance', 'spiritual', 'education', 'general']

# CF.L3.5: keyword sets for signal_type_id → domain mapping.
# Checked in order; first match wins; falls through to rank rotation.
_DOMAIN_KEYWORDS: list[tuple[str, list[str]]] = [
    ('career',       ['raja_yoga', 'amatyakaraka', 'tenth', 'karma', 'arudha', 'dasamsha',
                      'profession', 'status', 'power', 'authority']),
    ('relationship', ['kalatra', 'seventh', 'upapada', 'navamsha', 'spouse', 'partner',
                      'union', 'marriage', 'venus_yoga']),
    ('finance',      ['dhana', 'second', 'eleventh', 'artha', 'wealth', 'income',
                      'lakshmi', 'kubera', 'dhan']),
    ('health',       ['ayur', 'sixth', 'eighth', 'maraka', 'bala', 'disease',
                      'vitality', 'longevity', 'immunity']),
    ('spiritual',    ['dharma', 'ninth', 'twelfth', 'moksha', 'guru', 'bhakti',
                      'tapas', 'jnana', 'liberation']),
    ('education',    ['vidya', 'fourth', 'fifth', 'learning', 'intellect', 'mercury_yoga',
                      'saraswati', 'knowledge']),
]


def _infer_domain(rank: int, net_label: str, signal_type_id: str | None = None) -> str:
    """
    CF.L3.5: infer domain from signal_type_id keywords first; rank rotation as fallback.
    """
    if signal_type_id:
        tid_lower = signal_type_id.lower()
        for domain, keywords in _DOMAIN_KEYWORDS:
            if any(kw in tid_lower for kw in keywords):
                return domain
    # Domain rotation removed: produces false-precision labels violating MACRO_PLAN ethical
    # framework (calibrated/falsifiable outputs). Unclassified signals use 'general'.
    return 'general'


def _build_falsifiability(tier: str, domain: str, peak_date, eff_score: float) -> dict:
    """Build falsifiability hooks for this projection."""
    peak_str = str(peak_date) if peak_date else 'the projected window'

    domain_confirms = {
        'career': 'significant career event (new role, promotion, venture launch, client gain)',
        'health': 'notable health event (condition onset, recovery milestone, medical event)',
        'relationship': 'significant relational event (union, separation, new connection)',
        'finance': 'measurable financial event (income jump, loss, investment event)',
        'spiritual': 'notable spiritual shift (practice deepening, teacher encounter, insight)',
        'education': 'educational milestone (enrollment, completion, certification)',
        'general': 'notable life event (relocation, legal matter, public recognition)',
    }

    confirm = f"Observable within ±21 days of {peak_str}: {domain_confirms.get(domain, 'notable life event')}"
    deny = f"No observable {domain} event within ±21 days of {peak_str} despite favorable circumstances"
    eval_date = str(peak_date) if peak_date else 'peak_date'

    return {
        'confirm_observable': confirm,
        'deny_observable': deny,
        'evaluation_date': eval_date,
        'evaluation_window_days': 21,
    }


_TIER_LABELS = {
    'tier_1_high': 'High probability (>=70% convergence, clear activation)',
    'tier_2_moderate': 'Moderate probability (45-70% convergence)',
    'tier_3_speculative': 'Speculative (<45% convergence or obstructed)',
}


def _build_projection_narrative(tier: str, domain: str, peak_date, eff_score: float,
                                conf_label: str, rarity: float, net_label: str) -> dict:
    peak_str = str(peak_date) if peak_date else 'unknown date'
    tier_desc = _TIER_LABELS.get(tier, tier)
    rarity_str = f"{rarity:.1f}-year cycle" if rarity else "event"

    headline = f"{domain.capitalize()} activation near {peak_str}"
    prob_stmt = (
        f"{tier_desc}. Effective convergence: {eff_score:.2f}. "
        f"Confidence: {conf_label or 'speculative'}."
    )
    domain_ctx = f"Domain: {domain}. Cycle type: {rarity_str}."
    caveat = (
        "This projection is probabilistic and calibrated. "
        "Record actual outcomes at evaluation_date for calibration refinement."
    )

    return {
        'headline': headline,
        'probability_statement': prob_stmt,
        'domain_context': domain_ctx,
        'caveat': caveat,
    }
