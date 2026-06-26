"""ka_kala_darshana writer — display-ready temporal view synthesizer."""
import json
from pipeline.orchestrator.writers import WriterBase, WriterResult, register

@register('ka_kala_darshana')
class KaKalaDarshanaWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']

        # Idempotency: delete-then-insert scoped to chart
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_darshana WHERE chart_id = %s", (chart_id,))

        # Read convergence windows
        with conn.cursor() as cur:
            cur.execute("""
                SELECT kc.convergence_id, kc.signal_id, kc.mode,
                       kc.peak_date, kc.window_start, kc.window_end,
                       kc.convergence_score, kc.confidence_label,
                       kc.orb_strength, kc.rarity_years
                FROM kala_convergence kc
                WHERE kc.chart_id = %s
                ORDER BY kc.convergence_score DESC NULLS LAST
                LIMIT 750
            """, (chart_id,))
            convergence_rows = cur.fetchall()

        if not convergence_rows:
            return WriterResult(asset_id='ka_kala_darshana', rows_inserted=0, notes='No convergence windows — run ka_sangam first')

        # Read obstruction data grouped by convergence_id
        with conn.cursor() as cur:
            cur.execute("""
                SELECT convergence_id, obstruction_type, severity, override_score, obstruction_detail
                FROM kala_obstruction
                WHERE chart_id = %s
            """, (chart_id,))
            obstruction_rows = cur.fetchall()

        # Group obstructions by convergence_id
        obs_by_conv = {}
        for obs_row in obstruction_rows:
            conv_id = obs_row[0]
            if conv_id not in obs_by_conv:
                obs_by_conv[conv_id] = []
            obs_by_conv[conv_id].append({
                'type': obs_row[1],
                'severity': obs_row[2],
                'override_score': obs_row[3],
                'detail': obs_row[4],
            })

        rows = []
        for conv in convergence_rows:
            (conv_id, signal_id, mode, peak_date, win_start, win_end,
             conv_score, conf_label, orb_str, rarity) = conv

            # Get obstructions for this window
            obstructions = obs_by_conv.get(conv_id, [])

            # Compute effective score
            effective = _compute_effective_score(conv_score or 0.5, obstructions)

            # Compute net label
            label = _compute_net_label(effective, obstructions)

            # Obstruction summary (for display)
            obs_summary = [{'type': o['type'], 'severity': o['severity'], 'override_score': o['override_score']}
                           for o in obstructions]

            # Narrative
            narrative = _build_narrative(
                mode=mode,
                effective_score=effective,
                net_label=label,
                peak_date=peak_date,
                conf_label=conf_label,
                obstructions=obstructions,
                orb_strength=orb_str,
                rarity_years=rarity,
            )

            rows.append((
                chart_id,
                conv_id,
                signal_id,
                effective,
                label,
                peak_date.isoformat() if peak_date and hasattr(peak_date, 'isoformat') else None,
                win_start.isoformat() if win_start and hasattr(win_start, 'isoformat') else None,
                win_end.isoformat() if win_end and hasattr(win_end, 'isoformat') else None,
                json.dumps(obs_summary),
                json.dumps(narrative),
                f"ka_kala_darshana:v1.0:conv={conv_id}",
            ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO kala_darshana (
                        chart_id, convergence_id, signal_id,
                        effective_score, net_label, peak_date, window_start, window_end,
                        obstruction_summary, narrative, source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    rows,
                )

        return WriterResult(asset_id='ka_kala_darshana', rows_inserted=len(rows))


def _compute_effective_score(convergence_score: float, obstructions: list) -> float:
    """
    Effective score = convergence_score × (1 - max override_score across obstructions).
    Multiple obstructions: use max override (not additive) to avoid collapse.
    Clamped to [0, 1].
    """
    if not obstructions:
        return min(1.0, max(0.0, convergence_score))
    max_override = max(o.get('override_score', 0.0) for o in obstructions)
    effective = convergence_score * (1.0 - max_override)
    return min(1.0, max(0.0, effective))


def _compute_net_label(effective_score: float, obstructions: list) -> str:
    """
    Net label based on effective score and obstruction severity.
    """
    has_severe = any(o.get('severity') == 'severe' for o in obstructions)
    has_moderate = any(o.get('severity') == 'moderate' for o in obstructions)

    if has_severe:
        return 'obstructed_severe'
    if has_moderate and effective_score < 0.4:
        return 'obstructed'
    if effective_score >= 0.70:
        return 'auspicious_strong'
    if effective_score >= 0.45:
        return 'auspicious_moderate'
    if effective_score >= 0.20:
        return 'auspicious_speculative'
    if obstructions:
        return 'obstructed'
    return 'neutral'


def _build_narrative(mode: str, effective_score: float, net_label: str,
                     peak_date, conf_label: str, obstructions: list,
                     orb_strength: float, rarity_years: float) -> dict:
    """
    Build a structured narrative for display.
    Returns: {headline, context, caution}
    """
    peak_str = str(peak_date) if peak_date else 'unknown date'
    rarity_str = f"{rarity_years:.1f}-year" if rarity_years else ''
    conf_str = conf_label or 'speculative'

    mode_label = 'daśā-aligned' if mode == 'A' else 'independent sweep'

    headline_map = {
        'auspicious_strong': f"Strong activation window near {peak_str}",
        'auspicious_moderate': f"Moderate activation window near {peak_str}",
        'auspicious_speculative': f"Speculative window near {peak_str}",
        'obstructed': f"Suppressed window near {peak_str}",
        'obstructed_severe': f"Severely obstructed window near {peak_str}",
        'neutral': f"Neutral window near {peak_str}",
    }
    headline = headline_map.get(net_label, f"Window near {peak_str}")

    context = (
        f"{rarity_str + ' event' if rarity_str else 'Event'} ({mode_label}); "
        f"confidence: {conf_str}; "
        f"orb strength: {orb_strength:.2f}" if orb_strength else f"confidence: {conf_str}"
    )

    caution = None
    if obstructions:
        severe = [o for o in obstructions if o.get('severity') == 'severe']
        moderate = [o for o in obstructions if o.get('severity') == 'moderate']
        if severe:
            caution = f"Severe obstruction: {severe[0]['type']}. Window may not manifest."
        elif moderate:
            caution = f"Moderate obstruction: {moderate[0]['type']}. Intensity reduced."

    return {'headline': headline, 'context': context, 'caution': caution}
