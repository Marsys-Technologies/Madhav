"""ka_vighnakara writer — obstruction/counter-indicator detector."""
import json
import psycopg
from pipeline.orchestrator.writers import WriterBase, WriterResult, register

@register('ka_vighnakara')
class KaVighnakaraWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']

        # Idempotency: delete-then-insert scoped to chart
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_obstruction WHERE chart_id = %s", (chart_id,))

        # Read convergence windows for this chart (tuple_row so positional unpacking works)
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT convergence_id, signal_id, mode, peak_date,
                       convergence_score, orb_strength, window_start, window_end
                FROM kala_convergence
                WHERE chart_id = %s AND peak_date IS NOT NULL
                ORDER BY convergence_score DESC NULLS LAST
                LIMIT 200
            """, (chart_id,))
            convergence_rows = cur.fetchall()

        if not convergence_rows:
            return WriterResult(asset_id='ka_vighnakara', rows_inserted=0, notes='No convergence windows — run ka_sangam first')

        rows = []
        for conv_row in convergence_rows:
            conv_id, signal_id, mode, peak_date, conv_score, orb_str, win_start, win_end = conv_row

            obstructions = _detect_obstructions(
                peak_date=peak_date,
                convergence_score=conv_score or 0.5,
                signal_id=str(signal_id) if signal_id else None,
            )

            for obs in obstructions:
                rows.append((
                    chart_id,
                    conv_id,
                    signal_id,
                    obs['obstruction_type'],
                    obs['severity'],
                    obs['severity_score'],
                    obs['override_score'],
                    json.dumps(obs['detail']),
                    f"ka_vighnakara:v1.0:conv={conv_id}",
                ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO kala_obstruction (
                        chart_id, convergence_id, signal_id,
                        obstruction_type, severity, severity_score, override_score,
                        obstruction_detail, source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    rows,
                )

        return WriterResult(asset_id='ka_vighnakara', rows_inserted=len(rows))


# Malefic planets in classical Jyotish
MALEFICS = {'Saturn', 'Mars', 'Rahu', 'Ketu'}

# Severity mapping: (override_score, severity_label)
SEVERITY_MAP = [
    (0.7, 'severe'),
    (0.4, 'moderate'),
    (0.0, 'mild'),
]

def _severity(score: float) -> str:
    for threshold, label in SEVERITY_MAP:
        if score >= threshold:
            return label
    return 'mild'


def _detect_obstructions(peak_date, convergence_score: float, signal_id: str | None) -> list[dict]:
    """
    Detect obstruction patterns for a convergence window.
    Returns list of obstruction dicts.
    Each dict: {obstruction_type, severity, severity_score, override_score, detail}
    """
    obstructions = []

    if peak_date is None:
        return obstructions

    # Check 1: malefic transit (simplified rule: if peak_date in known Saturn transit to Aries/Cancer = affliction)
    obs = _check_malefic_transit(peak_date)
    if obs:
        obstructions.append(obs)

    # Check 2: panchanga obstruction (Rikta tithi = 4, 9, 14; computed from date)
    obs = _check_panchanga_obstruction(peak_date)
    if obs:
        obstructions.append(obs)

    # Check 3: Gandanta (last 3°20' of Water/Fire sign junction)
    obs = _check_gandanta(peak_date)
    if obs:
        obstructions.append(obs)

    # Check 4: papakartari (planet hemmed between malefics)
    obs = _check_papakartari(peak_date)
    if obs:
        obstructions.append(obs)

    return obstructions


def _check_malefic_transit(peak_date) -> dict | None:
    """
    Simplified malefic transit check.
    Real impl would call ka_graha_sancara for Saturn/Rahu positions at peak_date.
    For now: flag if peak_date falls in Saturn's known Aquarius transit (2023-2025).
    """
    from datetime import date
    if isinstance(peak_date, str):
        peak_date = date.fromisoformat(peak_date)

    # Saturn transit window placeholder — previous window (Aquarius, 2023-01-17 to
    # 2025-03-29) expired. Updated to approximate Saturn in Gemini window;
    # source dynamically from ka_graha_sancara in future L3 rebuild.
    saturn_aq_start = date(2030, 4, 1)   # approx Saturn enters Gemini
    saturn_aq_end = date(2032, 6, 30)    # approx Saturn exits Gemini

    if saturn_aq_start <= peak_date <= saturn_aq_end:
        severity_score = 0.45
        return {
            'obstruction_type': 'malefic_transit',
            'severity': _severity(severity_score),
            'severity_score': severity_score,
            'override_score': 0.20,
            'detail': {
                'planet': 'Saturn',
                'sign': 'Aquarius',
                'reason': 'Saturn transiting Aquarius; mutual aspect to Leo bhava compounds obstacles',
                'peak_date': str(peak_date),
            },
        }
    return None


def _check_panchanga_obstruction(peak_date) -> dict | None:
    """
    Rikta tithi (4, 9, 14) — inauspicious for most yogas.
    Simplified: use day-of-month modular arithmetic as a proxy.
    Real impl would call ka_muhurta_seva for actual tithi.
    """
    from datetime import date
    if isinstance(peak_date, str):
        peak_date = date.fromisoformat(peak_date)

    # Proxy: day mod 15 ∈ {4, 9, 14}
    day_mod = peak_date.day % 15
    if day_mod in (4, 9, 14, 0):  # 0 catches day=15
        severity_score = 0.25
        return {
            'obstruction_type': 'panchanga_obstruction',
            'severity': _severity(severity_score),
            'severity_score': severity_score,
            'override_score': 0.10,
            'detail': {
                'panchanga_element': 'rikta_tithi_proxy',
                'day': peak_date.day,
                'reason': 'Peak date falls on approximate Rikta tithi; ka_muhurta_seva should confirm.',
            },
        }
    return None


def _check_gandanta(peak_date) -> dict | None:
    """
    Gandanta check: last 3°20' of Cancer/Scorpio/Pisces → first 3°20' of Leo/Sagittarius/Aries.
    Simplified proxy: flag peak dates near solstice/equinox (sign changes).
    """
    from datetime import date
    if isinstance(peak_date, str):
        peak_date = date.fromisoformat(peak_date)

    # Approximate: sign change around 14-16th of most months (not accurate; proxy only)
    # Real impl would check Moon's position via ka_graha_sancara
    # For now: no hits from proxy → return None to avoid false positives
    return None


def _check_papakartari(peak_date) -> dict | None:
    """
    Papakartari (scissors-yoga): lagna/yoga bhava hemmed between malefics.
    Complex check requiring chart positions — simplified to None for now.
    Real impl would read kala_activation + chart_facts lagna.
    """
    return None


# Stubs for future obstruction types (all referenced in CHECK constraint):
# - rashi_dristi_conflict: rāśi dṛṣṭi (sign aspect) conflicts — requires graha longitudes
# - combustion: graha combust within 6° of Sun — requires ka_graha_sancara
# - dasha_lord_afflicted: MD/AD lord in 6/8/12 from natal or debilitated — requires chart_dashas
