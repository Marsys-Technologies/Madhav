"""
UTEE-S2: Backfill writer
Fills UTEE envelope columns on existing rows from existing column values.
Runs after initial data population; safe to re-run (idempotent via COALESCE).

Column reality (confirmed from migrations 142-149):
  A15 l1_time_synchronicity  : cluster_intensity (INT), convergence_score (FLOAT)
  A16 l1_phase_locked_anchors: confidence_score (FLOAT), cluster_intensity (INT); PK=BIGSERIAL anchor_id
  A18 l1_vedha_extended      : severity TEXT CHECK('strong','moderate','weak','cancellation'); PK=BIGSERIAL vedha_id; NO chart_id
  A19 l1_bhrigu_bindu_transits: hit_iso (DATE), strength_score (FLOAT), graha (TEXT); PK=BIGSERIAL transit_id
  A21 l1_graha_aspects_lifetime: exact_date (DATE), aspect_type (TEXT); PK=BIGSERIAL aspect_id
  A22 l1_varsha_digest        : peak_cluster_intensity (INT), confidence_score (FLOAT)
  A20 l1_tajik_varsha_year_lords: varsha_start_iso/varsha_end_iso (TIMESTAMPTZ)
"""

import logging

logger = logging.getLogger(__name__)

SEVERITY_MAP_TEXT_TO_FLOAT = {
    'critical': 1.0, 'high': 0.8, 'significant': 0.7, 'moderate': 0.5,
    'low': 0.3, 'minimal': 0.1, 'none': 0.0,
    # Confidence aliases
    'extreme': 1.0, 'very_high': 0.9, 'medium': 0.5, 'very_low': 0.2,
}

CONFIDENCE_CLASS_FROM_FLOAT = {
    (0.8, 1.01): 'high',
    (0.6, 0.8): 'medium',
    (0.3, 0.6): 'low',
    (0.0, 0.3): 'speculative',
}


def confidence_class_from_float(v: float) -> str:
    for (lo, hi), cls in CONFIDENCE_CLASS_FROM_FLOAT.items():
        if lo <= v < hi:
            return cls
    return 'speculative'


def normalize_severity(raw) -> float:
    if raw is None:
        return 0.5
    if isinstance(raw, (int, float)):
        return min(1.0, max(0.0, float(raw)))
    return SEVERITY_MAP_TEXT_TO_FLOAT.get(str(raw).lower(), 0.5)


def backfill_a15(conn) -> int:
    """
    Backfill UTEE columns on l1_time_synchronicity.
    Source columns (migration 145): cluster_intensity INT, convergence_score FLOAT.
    UTEE columns added by migration 149: severity_normalized_0_1, confidence_normalized_0_1,
      confidence_class, expected_outcome_class, outcome_ontology_class,
      channel_render_priority_jsonb, m6_outcome_tracking_placeholder_jsonb.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_time_synchronicity SET
              severity_normalized_0_1 = CASE
                WHEN cluster_intensity IS NOT NULL
                  THEN LEAST(GREATEST(cluster_intensity::NUMERIC / 9.0, 0.0), 1.0)
                ELSE 0.5
              END,
              confidence_normalized_0_1 = COALESCE(
                confidence_normalized_0_1,
                CASE
                  WHEN convergence_score IS NOT NULL
                    THEN LEAST(GREATEST(convergence_score, 0.0), 1.0)
                  ELSE 0.7
                END
              ),
              confidence_class = COALESCE(confidence_class,
                CASE
                  WHEN convergence_score >= 0.8 THEN 'high'
                  WHEN convergence_score >= 0.6 THEN 'medium'
                  WHEN convergence_score >= 0.3 THEN 'low'
                  ELSE 'speculative'
                END
              ),
              expected_outcome_class = COALESCE(expected_outcome_class, 'temporal_convergence'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'ordinal'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":1,"report":1,"visual":1,"dashboard":1}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A15 backfill: %d rows updated", count)
    return count


def backfill_a16(conn) -> int:
    """
    Backfill UTEE columns on l1_phase_locked_anchors.
    Source columns (migration 146): confidence_score FLOAT, cluster_intensity INT.
    NOTE: there is no 'expected_intensity' or 'prediction_confidence' column —
    use confidence_score and cluster_intensity instead.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_phase_locked_anchors SET
              severity_normalized_0_1 = COALESCE(
                severity_normalized_0_1,
                CASE
                  WHEN cluster_intensity IS NOT NULL
                    THEN LEAST(GREATEST(cluster_intensity::NUMERIC / 9.0, 0.0), 1.0)
                  ELSE 0.5
                END
              ),
              confidence_normalized_0_1 = COALESCE(
                confidence_normalized_0_1,
                confidence_score
              ),
              confidence_class = COALESCE(confidence_class,
                CASE
                  WHEN confidence_score >= 0.8 THEN 'high'
                  WHEN confidence_score >= 0.6 THEN 'medium'
                  WHEN confidence_score >= 0.3 THEN 'low'
                  ELSE 'speculative'
                END
              ),
              expected_outcome_class  = COALESCE(expected_outcome_class, 'phase_locked_activation'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'ordinal'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":2,"report":2,"visual":2,"dashboard":2}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A16 backfill: %d rows updated", count)
    return count


def backfill_a18(conn) -> int:
    """
    Backfill UTEE columns on l1_vedha_extended.
    Source columns (migration 144): severity TEXT CHECK('strong','moderate','weak','cancellation').
    NOTE: column is named 'severity' not 'severity_class'.
    NOTE: l1_vedha_extended has NO chart_id column — it is a reference table.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_vedha_extended SET
              severity_normalized_0_1 = CASE
                WHEN severity = 'strong'       THEN 0.85
                WHEN severity = 'moderate'     THEN 0.55
                WHEN severity = 'weak'         THEN 0.25
                WHEN severity = 'cancellation' THEN 0.0
                ELSE 0.5
              END,
              confidence_normalized_0_1 = COALESCE(confidence_normalized_0_1, 0.65),
              confidence_class = COALESCE(confidence_class, 'medium'),
              expected_outcome_class = COALESCE(expected_outcome_class, 'vedha_obstruction'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'categorical'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":2,"report":2,"visual":2,"dashboard":2}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A18 backfill: %d rows updated", count)
    return count


def backfill_a19(conn) -> int:
    """
    Backfill UTEE columns on l1_bhrigu_bindu_transits.
    Source columns (migration 142): hit_iso DATE, strength_score FLOAT, graha TEXT.
    NOTE: column is 'hit_iso' not 'transit_hit_iso'; 'strength_score' not 'transit_severity_score'.
    UTEE temporal columns added by migration 149: event_iso, event_window_start_iso, event_window_end_iso.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_bhrigu_bindu_transits SET
              event_iso = COALESCE(
                event_iso,
                hit_iso::TIMESTAMPTZ
              ),
              event_window_start_iso = COALESCE(
                event_window_start_iso,
                (hit_iso - INTERVAL '30 days')::TIMESTAMPTZ
              ),
              event_window_end_iso = COALESCE(
                event_window_end_iso,
                (hit_iso + INTERVAL '30 days')::TIMESTAMPTZ
              ),
              severity_normalized_0_1 = COALESCE(
                severity_normalized_0_1,
                CASE
                  WHEN strength_score IS NOT NULL
                    THEN LEAST(GREATEST(strength_score, 0.0), 1.0)
                  WHEN graha IN ('saturn','Saturn') THEN 0.85
                  WHEN graha IN ('mars','Mars')     THEN 0.75
                  WHEN graha IN ('rahu','Rahu')     THEN 0.70
                  WHEN graha IN ('ketu','Ketu')     THEN 0.65
                  ELSE 0.5
                END
              ),
              confidence_normalized_0_1 = COALESCE(confidence_normalized_0_1, 0.75),
              confidence_class = COALESCE(confidence_class, 'high'),
              expected_outcome_class = COALESCE(expected_outcome_class, 'bhrigu_bindu_activation'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'categorical'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":1,"report":1,"visual":2,"dashboard":1}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE event_iso IS NULL OR severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A19 backfill: %d rows updated", count)
    return count


def backfill_a20(conn) -> int:
    """
    Backfill UTEE columns on l1_tajik_varsha_year_lords.
    Source columns (migration 148): varsha_start_iso TIMESTAMPTZ, varsha_end_iso TIMESTAMPTZ.
    UTEE temporal columns added by migration 149: event_iso, event_window_start_iso, event_window_end_iso.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_tajik_varsha_year_lords SET
              event_iso = COALESCE(event_iso, varsha_start_iso),
              event_window_start_iso = COALESCE(event_window_start_iso, varsha_start_iso),
              event_window_end_iso   = COALESCE(event_window_end_iso, varsha_end_iso),
              severity_normalized_0_1 = COALESCE(severity_normalized_0_1, 0.5),
              confidence_normalized_0_1 = COALESCE(confidence_normalized_0_1, 0.6),
              confidence_class = COALESCE(confidence_class, 'medium'),
              expected_outcome_class = COALESCE(expected_outcome_class, 'varsha_year_theme'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'categorical'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":2,"report":1,"visual":2,"dashboard":2}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A20 backfill: %d rows updated", count)
    return count


def backfill_a21(conn) -> int:
    """
    Backfill UTEE columns on l1_graha_aspects_lifetime.
    Source columns (migration 143): exact_date DATE, aspect_type TEXT.
    NOTE: column is 'exact_date' not 'exact_aspect_date' or 'exact_aspect_iso'.
    UTEE temporal columns added by migration 149: event_iso, event_window_start_iso, event_window_end_iso.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_graha_aspects_lifetime SET
              event_iso = COALESCE(
                event_iso,
                exact_date::TIMESTAMPTZ
              ),
              event_window_start_iso = COALESCE(
                event_window_start_iso,
                (exact_date - INTERVAL '15 days')::TIMESTAMPTZ
              ),
              event_window_end_iso = COALESCE(
                event_window_end_iso,
                (exact_date + INTERVAL '15 days')::TIMESTAMPTZ
              ),
              severity_normalized_0_1 = COALESCE(
                severity_normalized_0_1,
                CASE aspect_type
                  WHEN 'opposition'          THEN 0.80
                  WHEN 'conjunction'         THEN 0.75
                  WHEN 'square'              THEN 0.70
                  WHEN 'trine'               THEN 0.50
                  WHEN 'sextile'             THEN 0.40
                  WHEN 'tajik_ithasala'      THEN 0.70
                  WHEN 'tajik_ishrafa'       THEN 0.60
                  WHEN 'parashari_4th'       THEN 0.65
                  WHEN 'parashari_8th'       THEN 0.75
                  ELSE 0.5
                END
              ),
              confidence_normalized_0_1 = COALESCE(confidence_normalized_0_1, 0.85),
              confidence_class = COALESCE(confidence_class, 'high'),
              expected_outcome_class = COALESCE(expected_outcome_class, 'exact_aspect_activation'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'ordinal'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":1,"report":1,"visual":2,"dashboard":1}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE event_iso IS NULL OR severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A21 backfill: %d rows updated", count)
    return count


def backfill_a22(conn) -> int:
    """
    Backfill UTEE columns on l1_varsha_digest.
    Source columns (migration 147): peak_cluster_intensity INT, confidence_score FLOAT.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE l1_varsha_digest SET
              severity_normalized_0_1 = COALESCE(
                severity_normalized_0_1,
                CASE
                  WHEN peak_cluster_intensity IS NOT NULL
                    THEN LEAST(GREATEST(peak_cluster_intensity::NUMERIC / 9.0, 0.0), 1.0)
                  ELSE 0.5
                END
              ),
              confidence_normalized_0_1 = COALESCE(
                confidence_normalized_0_1,
                confidence_score
              ),
              confidence_class = COALESCE(confidence_class,
                CASE
                  WHEN confidence_score >= 0.8 THEN 'high'
                  WHEN confidence_score >= 0.6 THEN 'medium'
                  WHEN confidence_score >= 0.3 THEN 'low'
                  ELSE 'speculative'
                END
              ),
              expected_outcome_class = COALESCE(expected_outcome_class, 'varsha_digest_summary'),
              outcome_ontology_class  = COALESCE(outcome_ontology_class, 'ordinal'),
              channel_render_priority_jsonb = COALESCE(
                channel_render_priority_jsonb,
                '{"chat":2,"report":1,"visual":2,"dashboard":1}'::jsonb
              ),
              m6_outcome_tracking_placeholder_jsonb = COALESCE(
                m6_outcome_tracking_placeholder_jsonb, '{}'::jsonb
              )
            WHERE severity_normalized_0_1 IS NULL
        """)
        count = cur.rowcount
    conn.commit()
    logger.info("UTEE-S2 A22 backfill: %d rows updated", count)
    return count


def run_all_backfills(conn) -> dict:
    """Run all UTEE backfills. Returns dict of table -> row count updated."""
    results = {}
    results['A15'] = backfill_a15(conn)
    results['A16'] = backfill_a16(conn)
    results['A18'] = backfill_a18(conn)
    results['A19'] = backfill_a19(conn)
    results['A20'] = backfill_a20(conn)
    results['A21'] = backfill_a21(conn)
    results['A22'] = backfill_a22(conn)
    total = sum(results.values())
    logger.info("UTEE-S2 complete: %d total rows updated across 7 tables", total)
    return results
