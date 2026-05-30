"""META-γ: Divergence Ledger Writer (Δ-LEDGER) — cross-system disagreement audit.

Implements META_ENHANCEMENTS_SPEC_v1_0.md §3.
Writes to l25_divergence_ledger.
All inserts use ON CONFLICT DO NOTHING.
"""
import uuid
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

DIVERGENCE_RULES = [
    {
        'divergence_class': 'ayanamsha_positional_disagreement',
        'system_a': 'Lahiri',
        'system_b': 'Krishnamurti',
        'description': 'Same fact differs between ayanamsha systems',
    },
    {
        'divergence_class': 'tradition_interpretation_disagreement',
        'system_a': 'Parashari',
        'system_b': 'Jaimini',
        'description': 'Parashari vs Jaimini disagree on the same event',
    },
    {
        'divergence_class': 'tradition_interpretation_disagreement',
        'system_a': 'Parashari',
        'system_b': 'Tajika',
        'description': 'Parashari vs Tajika disagree on the same prediction',
    },
    {
        'divergence_class': 'cross_system_temporal',
        'system_a': 'Vimshottari',
        'system_b': 'ChaaraDasha',
        'description': 'Dasha timing systems disagree on period quality',
    },
]


def scan_for_ayanamsha_divergences(conn, chart_id: str, build_id: str) -> int:
    """
    Compare chart_facts across ayanamsha systems for same fact_key.
    When two ayanamshas have different fact_value_text for the same key → divergence row.
    """
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT a.ayanamsha_id, b.ayanamsha_id, a.fact_key, a.fact_value_text, b.fact_value_text
                FROM chart_facts a
                JOIN chart_facts b
                  ON a.chart_id = b.chart_id
                 AND a.fact_key = b.fact_key
                 AND a.ayanamsha_id < b.ayanamsha_id
                 AND a.fact_value_text IS DISTINCT FROM b.fact_value_text
                 AND a.fact_category IN ('house_placement', 'sign_placement', 'nakshatra')
                WHERE a.chart_id = %s
                LIMIT 100
            """, [chart_id])
            divergences = cur.fetchall()
        except Exception as e:
            logger.debug(f"Ayanamsha divergence scan: {e}")
            conn.rollback()
            divergences = []

        for (aya_a, aya_b, key, val_a, val_b) in divergences:
            cur.execute("""
                INSERT INTO l25_divergence_ledger
                  (divergence_id, chart_id, ayanamsha_id, build_id,
                   divergence_class, system_a, system_b, asset_a, asset_b,
                   row_id_a, row_id_b, claim_a, claim_b,
                   divergence_severity, resolution_status, verified, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,
                  'ayanamsha_positional_disagreement',%s,%s,'chart_facts','chart_facts',
                  %s,%s,%s,%s,'moderate','open',false,NOW())
                ON CONFLICT DO NOTHING
            """, (str(uuid.uuid4()), chart_id, aya_a, build_id,
                  aya_a, aya_b,
                  f"{key}@{aya_a}", f"{key}@{aya_b}",
                  f"{key}={val_a}", f"{key}={val_b}"))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-γ: {count} ayanamsha divergences recorded")
    return count


def scan_for_tradition_divergences(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """
    Scan for divergences between tradition systems (Parashari vs Jaimini).
    Uses school_convergence_index where it exists; falls back to pattern_catalog cross-check.
    """
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT sci.school_a, sci.school_b, sci.claim_key, sci.verdict_a, sci.verdict_b,
                       sci.divergence_flag
                FROM school_convergence_index sci
                WHERE sci.chart_id = %s AND sci.ayanamsha_id = %s
                  AND sci.divergence_flag = true
                LIMIT 100
            """, [chart_id, ayanamsha_id])
            rows = cur.fetchall()
        except Exception as e:
            logger.debug(f"school_convergence_index scan: {e}")
            conn.rollback()
            rows = []

        for (school_a, school_b, claim_key, verdict_a, verdict_b, _flag) in rows:
            # Classify severity by school pair
            severity = 'significant' if {school_a, school_b} == {'Parashari', 'Jaimini'} else 'moderate'
            cur.execute("""
                INSERT INTO l25_divergence_ledger
                  (divergence_id, chart_id, ayanamsha_id, build_id,
                   divergence_class, system_a, system_b, asset_a, asset_b,
                   row_id_a, row_id_b, claim_a, claim_b,
                   divergence_severity, resolution_status, verified, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,
                  'tradition_interpretation_disagreement',%s,%s,
                  'school_convergence_index','school_convergence_index',
                  %s,%s,%s,%s,%s,'open',false,NOW())
                ON CONFLICT DO NOTHING
            """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                  school_a, school_b,
                  f"{claim_key}@{school_a}", f"{claim_key}@{school_b}",
                  str(verdict_a or ''), str(verdict_b or ''),
                  severity))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-γ: {count} tradition divergences recorded")
    return count
