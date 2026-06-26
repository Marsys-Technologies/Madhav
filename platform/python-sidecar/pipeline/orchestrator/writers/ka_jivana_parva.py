"""
ka_jivana_parva writer — life-arc biographical chapter artifact.

D7 (Kāla completeness v2): extended from MD-only to MD + AD sub-chapters.
Also populates dominant_signal_class via frequency-count of signature_class
across convergence windows in each MD span.
"""
import json
import logging
from collections import Counter
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

        # Read level-1 (MD) and level-2 (AD) dashas from chart_dashas
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lord_graha, start_date, end_date, level_n,
                       ancestor_lord_1
                FROM chart_dashas
                WHERE chart_id = %s AND level_n IN (1, 2)
                ORDER BY start_date, level_n
            """, (chart_id,))
            all_dashas = cur.fetchall()

        if not all_dashas:
            return WriterResult(
                asset_id='ka_jivana_parva', rows_inserted=0,
                notes='No mahadashas found in chart_dashas — check L1 build',
            )

        # Separate MD and AD rows
        md_dashas = [d for d in all_dashas if d['level_n'] == 1]
        ad_dashas  = [d for d in all_dashas if d['level_n'] == 2]

        if not md_dashas:
            return WriterResult(
                asset_id='ka_jivana_parva', rows_inserted=0,
                notes='No level_n=1 mahadashas in chart_dashas',
            )

        # Read convergence windows with signature_class for dominant_signal_class computation
        with conn.cursor() as cur:
            cur.execute("""
                SELECT kc.peak_date, kc.convergence_score, kc.signature_class,
                       COALESCE(kd.effective_score, kc.convergence_score) AS effective_score
                FROM kala_convergence kc
                LEFT JOIN kala_darshana kd ON kc.convergence_id = kd.convergence_id
                WHERE kc.chart_id = %s AND kc.peak_date IS NOT NULL
            """, (chart_id,))
            conv_windows = cur.fetchall()

        rows = []
        parva_index = 0

        for md_idx, md in enumerate(md_dashas):
            md_planet  = md['lord_graha']
            md_start   = md['start_date']
            md_end     = md['end_date']
            md_start_y = md_start.year if md_start else None
            if md_start_y is None:
                logger.warning(
                    "ka_jivana_parva: skipping MD idx=%d planet=%s — NULL start_date",
                    md_idx, md_planet,
                )
                continue
            md_end_y      = md_end.year if md_end else None
            md_end_actual = md_end or date(2100, 1, 1)

            # Convergence windows within this MD span
            md_windows = [
                w for w in conv_windows
                if w['peak_date'] and md_start and md_start <= w['peak_date'] <= md_end_actual
            ]

            # dominant_signal_class: most frequent signature_class in this span (by count)
            class_counter: Counter = Counter(
                w['signature_class'] for w in md_windows
                if w.get('signature_class') and w['signature_class'] not in ('SUBSYSTEM', 'CLASSIFY_RESIDUAL')
            )
            dominant_class = class_counter.most_common(1)[0][0] if class_counter else None

            high_conv_count = sum(1 for w in md_windows if (w['effective_score'] or 0) >= 0.5)
            avg_score = (
                sum(w['effective_score'] or 0 for w in md_windows) / len(md_windows)
            ) if md_windows else None

            quality       = _assign_quality(md_idx, len(md_dashas), high_conv_count, avg_score, md_start_y, md_end_y)
            theme_keywords = _derive_theme(md_planet, quality)
            narrative      = _build_parva_narrative(md_planet, md_start_y, md_end_y, quality, high_conv_count, avg_score)

            parva_index += 1
            rows.append((
                chart_id,
                parva_index,
                md_start_y,
                md_end_y,
                str(md_planet),
                dominant_class,
                quality,
                theme_keywords,
                json.dumps(narrative),
                high_conv_count,
                avg_score,
                f"ka_jivana_parva:v2.0:MD={md_planet}",
            ))

            # D7: AD sub-chapters — antardashas whose start_date falls within this MD span
            md_ad_rows = [
                d for d in ad_dashas
                if d['start_date'] and md_start
                and md_start <= d['start_date'] <= md_end_actual
            ]
            for ad_idx, ad in enumerate(md_ad_rows):
                ad_planet  = ad['lord_graha']
                ad_start   = ad['start_date']
                ad_end     = ad['end_date']
                ad_start_y = ad_start.year if ad_start else None
                if ad_start_y is None:
                    continue
                ad_end_y      = ad_end.year if ad_end else None
                ad_end_actual = ad_end or date(2100, 1, 1)

                ad_windows = [
                    w for w in md_windows
                    if w['peak_date'] and ad_start and ad_start <= w['peak_date'] <= ad_end_actual
                ]
                ad_class_counter: Counter = Counter(
                    w['signature_class'] for w in ad_windows
                    if w.get('signature_class') and w['signature_class'] not in ('SUBSYSTEM', 'CLASSIFY_RESIDUAL')
                )
                ad_dominant  = ad_class_counter.most_common(1)[0][0] if ad_class_counter else dominant_class
                ad_high_cnt  = sum(1 for w in ad_windows if (w['effective_score'] or 0) >= 0.5)
                ad_avg_score = (
                    sum(w['effective_score'] or 0 for w in ad_windows) / len(ad_windows)
                ) if ad_windows else None
                ad_quality   = _assign_quality(ad_idx, len(md_ad_rows), ad_high_cnt, ad_avg_score, ad_start_y, ad_end_y)
                ad_theme     = _derive_theme(ad_planet, ad_quality)
                ad_narrative = _build_parva_narrative(
                    f"{md_planet}/{ad_planet}", ad_start_y, ad_end_y, ad_quality, ad_high_cnt, ad_avg_score
                )

                parva_index += 1
                rows.append((
                    chart_id,
                    parva_index,
                    ad_start_y,
                    ad_end_y,
                    str(ad_planet),
                    ad_dominant,
                    ad_quality,
                    ad_theme,
                    json.dumps(ad_narrative),
                    ad_high_cnt,
                    ad_avg_score,
                    f"ka_jivana_parva:v2.0:MD={md_planet}:AD={ad_planet}",
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
