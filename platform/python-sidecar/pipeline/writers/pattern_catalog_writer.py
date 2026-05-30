"""META-β: Pattern Catalog Writer (Π-CATALOG) — aggregates named patterns from all assets.

Implements META_ENHANCEMENTS_SPEC_v1_0.md §2.
Writes to l25_pattern_catalog.
All inserts use ON CONFLICT DO NOTHING.
"""
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PATTERN_KINDS = [
    'yoga',
    'dosha',
    'cdlm_pattern_cluster',
    'cgm_motif',
    'cgm_sub_graph',
    'magnification',
    'anti_magnification',
    'near_miss_yoga',
    'synchronicity',
    'phase_locked_anchor',
    'classical_archetype',
    'sade_sati_phase',
    'time_convergence_cluster',
    'spiritual_progress_marker',
    'karmic_signature_component',
    'negative_space',
]


def write_patterns_from_chart_facts(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """
    Scan chart_facts for pattern-bearing rows and populate l25_pattern_catalog.
    Pattern kinds are detected from fact_category column in chart_facts.
    """
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT fact_id::TEXT, fact_category, fact_key, fact_value_text, confidence_score
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category IN ('yoga', 'dosha', 'structural', 'special_feature', 'classical_pattern')
                LIMIT 500
            """, [chart_id, ayanamsha_id])
            facts = cur.fetchall()
        except Exception as e:
            logger.debug(f"chart_facts query: {e}")
            conn.rollback()
            facts = []

        for (fact_id, category, key, value, confidence) in facts:
            # Map category to pattern_kind
            kind = 'yoga' if category == 'yoga' else \
                   'dosha' if category == 'dosha' else \
                   'classical_archetype' if category in ('structural', 'classical_pattern') else \
                   'near_miss_yoga'

            strength = float(confidence) if confidence else 0.5

            cur.execute("""
                INSERT INTO l25_pattern_catalog
                  (pattern_catalog_id, chart_id, ayanamsha_id, build_id,
                   pattern_kind, pattern_name, pattern_strength, active_flag,
                   source_asset, source_row_id, verification_pass_status, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,%s,%s,%s,true,%s,%s,'pass',NOW())
                ON CONFLICT (chart_id, ayanamsha_id, source_asset, source_row_id, pattern_name) DO NOTHING
            """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                  kind, key, strength, 'chart_facts', fact_id))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-β: wrote {count} pattern catalog rows from chart_facts")
    return count


def write_patterns_from_temporal_events(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """Add temporal patterns (A15 synchronicity, A16 anchors) to pattern catalog."""
    count = 0
    with conn.cursor() as cur:
        # A15 convergence windows → 'synchronicity' pattern kind
        try:
            cur.execute("""
                SELECT id::TEXT, cluster_intensity, convergence_type
                FROM l1_time_synchronicity
                WHERE chart_id = %s AND ayanamsha_id = %s
                LIMIT 200
            """, [chart_id, ayanamsha_id])
            for (row_id, intensity, conv_type) in cur.fetchall():
                strength = min(1.0, (intensity or 5) / 10.0) if intensity else 0.5
                cur.execute("""
                    INSERT INTO l25_pattern_catalog
                      (pattern_catalog_id, chart_id, ayanamsha_id, build_id,
                       pattern_kind, pattern_name, pattern_strength, active_flag,
                       source_asset, source_row_id, verification_pass_status, computed_at)
                    VALUES (%s,%s::UUID,%s,%s::UUID,'synchronicity',%s,%s,true,'A15',%s,'pass',NOW())
                    ON CONFLICT (chart_id, ayanamsha_id, source_asset, source_row_id, pattern_name) DO NOTHING
                """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                      f'synchronicity_{conv_type or "window"}', strength, row_id))
                count += cur.rowcount
        except Exception as e:
            logger.debug(f"A15 patterns: {e}")
            conn.rollback()

        # A16 anchors → 'phase_locked_anchor' pattern kind
        try:
            cur.execute("""
                SELECT id::TEXT, anchor_label, confidence_score
                FROM l1_phase_locked_anchors
                WHERE chart_id = %s AND ayanamsha_id = %s
                LIMIT 100
            """, [chart_id, ayanamsha_id])
            for (row_id, label, conf) in cur.fetchall():
                cur.execute("""
                    INSERT INTO l25_pattern_catalog
                      (pattern_catalog_id, chart_id, ayanamsha_id, build_id,
                       pattern_kind, pattern_name, pattern_strength, active_flag,
                       source_asset, source_row_id, verification_pass_status, computed_at)
                    VALUES (%s,%s::UUID,%s,%s::UUID,'phase_locked_anchor',%s,%s,true,'A16',%s,'pass',NOW())
                    ON CONFLICT (chart_id, ayanamsha_id, source_asset, source_row_id, pattern_name) DO NOTHING
                """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                      f'anchor_{label or row_id[:8]}', float(conf or 0.5), row_id))
                count += cur.rowcount
        except Exception as e:
            logger.debug(f"A16 patterns: {e}")
            conn.rollback()

    conn.commit()
    logger.info(f"META-β: wrote {count} temporal pattern rows (A15+A16)")
    return count


def write_patterns_from_yoga_register(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """Pull yogas from yoga_register into pattern catalog."""
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT yoga_id::TEXT, yoga_name, yoga_type, strength_score, is_active
                FROM yoga_register
                WHERE chart_id = %s AND ayanamsha_id = %s
                LIMIT 300
            """, [chart_id, ayanamsha_id])
            for (row_id, name, ytype, strength, is_active) in cur.fetchall():
                kind = 'dosha' if (ytype or '').lower() in ('dosha', 'adverse') else 'yoga'
                cur.execute("""
                    INSERT INTO l25_pattern_catalog
                      (pattern_catalog_id, chart_id, ayanamsha_id, build_id,
                       pattern_kind, pattern_name, pattern_strength, active_flag,
                       source_asset, source_row_id, verification_pass_status, computed_at)
                    VALUES (%s,%s::UUID,%s,%s::UUID,%s,%s,%s,%s,'yoga_register',%s,'pass',NOW())
                    ON CONFLICT (chart_id, ayanamsha_id, source_asset, source_row_id, pattern_name) DO NOTHING
                """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                      kind, name or row_id, float(strength or 0.5),
                      bool(is_active) if is_active is not None else True, row_id))
                count += cur.rowcount
        except Exception as e:
            logger.debug(f"yoga_register patterns: {e}")
            conn.rollback()
    conn.commit()
    logger.info(f"META-β: wrote {count} yoga_register pattern rows")
    return count
