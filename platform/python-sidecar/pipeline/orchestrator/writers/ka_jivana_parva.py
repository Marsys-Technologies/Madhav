"""ka_jivana_parva writer — life-arc biographical chapter artifact."""
import json
import logging
from datetime import date
from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)


@register('ka_jivana_parva')
class KaJivanaParvaWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']

        # Idempotency
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_jivana_parva WHERE chart_id = %s", (chart_id,))

        # Read level-1 mahadashas from chart_dashas
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lord_graha, start_date, end_date
                FROM chart_dashas
                WHERE chart_id = %s AND level_n = 1
                ORDER BY start_date
            """, (chart_id,))
            dashas = cur.fetchall()

        if not dashas:
            return WriterResult(asset_id='ka_jivana_parva', rows_inserted=0, notes='No mahadashas found in chart_dashas — check L1 build')

        # Read convergence windows for density computation
        with conn.cursor() as cur:
            cur.execute("""
                SELECT kc.peak_date, kc.convergence_score,
                       COALESCE(kd.effective_score, kc.convergence_score) as effective_score
                FROM kala_convergence kc
                LEFT JOIN kala_darshana kd ON kc.convergence_id = kd.convergence_id
                WHERE kc.chart_id = %s AND kc.peak_date IS NOT NULL
            """, (chart_id,))
            conv_windows = cur.fetchall()

        rows = []
        for idx, dasha in enumerate(dashas):
            # dashas is list[dict] (dict_row cursor); unpack by key not position
            planet = dasha['lord_graha']
            start_dt = dasha['start_date']
            end_dt = dasha['end_date']
            start_y = start_dt.year if start_dt else None
            if start_y is None:
                logger.warning("ka_jivana_parva: skipping dasha row idx=%d planet=%s — NULL start_date in chart_dashas", idx, planet)
                continue
            end_y = end_dt.year if end_dt else None
            end_dt_actual = end_dt or date(2100, 1, 1)

            # Windows within this mahadasha span (conv_windows also list[dict])
            span_windows = [
                w for w in conv_windows
                if w['peak_date'] and start_dt and end_dt_actual and start_dt <= w['peak_date'] <= end_dt_actual
            ]

            high_conv_count = sum(1 for w in span_windows if (w['effective_score'] or 0) >= 0.5)
            avg_score = (sum(w['effective_score'] or 0 for w in span_windows) / len(span_windows)) if span_windows else None

            # Parva quality
            quality = _assign_quality(idx, len(dashas), high_conv_count, avg_score, start_y, end_y)

            # Theme and narrative
            theme_keywords = _derive_theme(planet, quality)
            narrative = _build_parva_narrative(planet, start_y, end_y, quality, high_conv_count, avg_score)

            rows.append((
                chart_id,
                idx + 1,
                start_y,
                end_y,
                str(planet),
                None,  # dominant_signal_class: would need frequency analysis; stub as None
                quality,
                theme_keywords,
                json.dumps(narrative),
                high_conv_count,
                avg_score,
                f"ka_jivana_parva:v1.0:dasha={planet}",
            ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO kala_jivana_parva (
                        chart_id, parva_index, start_year, end_year, dasha_planet,
                        dominant_signal_class, parva_quality, theme_keywords,
                        narrative, high_convergence_count, avg_effective_score,
                        source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, rows)

        return WriterResult(asset_id='ka_jivana_parva', rows_inserted=len(rows))


def _assign_quality(idx: int, total: int, high_count: int, avg_score: float | None,
                    start_y: int, end_y: int | None) -> str:
    """Assign parva quality based on position in life arc and convergence density."""
    today_y = date.today().year

    # Is this period ongoing?
    is_ongoing = end_y is None or (end_y >= today_y)
    is_past = end_y is not None and end_y < today_y

    if is_ongoing and avg_score and avg_score >= 0.55:
        return 'peak'
    if is_ongoing:
        return 'building'

    if avg_score is None:
        return 'transitional'

    if avg_score >= 0.60:
        return 'peak'
    if avg_score >= 0.45:
        return 'consolidating' if is_past else 'building'
    if avg_score >= 0.25:
        return 'receding' if is_past else 'transitional'
    return 'transitional'


_PLANET_THEMES = {
    'Sun': ['authority', 'identity', 'recognition'],
    'Moon': ['nourishment', 'emotional_depth', 'home'],
    'Mars': ['action', 'ambition', 'conflict'],
    'Mercury': ['intellect', 'communication', 'commerce'],
    'Jupiter': ['expansion', 'wisdom', 'abundance'],
    'Venus': ['beauty', 'relationship', 'creativity'],
    'Saturn': ['discipline', 'responsibility', 'delay'],
    'Rahu': ['ambition', 'disruption', 'innovation'],
    'Ketu': ['renunciation', 'spirituality', 'detachment'],
}


def _derive_theme(planet: str, quality: str) -> list:
    base = _PLANET_THEMES.get(str(planet), ['transformation'])
    return base[:3] + [quality]


def _build_parva_narrative(planet: str, start_y: int, end_y: int | None, quality: str,
                            high_count: int, avg_score: float | None) -> dict:
    span_str = f"{start_y}–{end_y}" if end_y else f"{start_y}–present"
    themes = _PLANET_THEMES.get(str(planet), ['transformation'])
    theme_str = ', '.join(themes[:2])

    summary = (
        f"{planet} daśā ({span_str}): {quality} phase marked by {theme_str}. "
        f"{high_count} high-convergence window{'s' if high_count != 1 else ''} in this span."
    )

    return {
        'summary': summary,
        'dasha_planet': str(planet),
        'span': span_str,
        'quality': quality,
        'high_convergence_count': high_count,
        'avg_effective_score': round(avg_score, 3) if avg_score else None,
    }
