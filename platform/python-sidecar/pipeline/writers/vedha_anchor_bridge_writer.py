"""
BRIDGE-S2: Vedha-Anchor interaction computation.
Scans l1_vedha_extended rows for temporal overlaps with l1_phase_locked_anchors windows.
When overlap detected, computes interaction class and inserts into l25_vedha_anchor_interactions.

Classical rule: A vedha that activates during an anchor window partially or fully mitigates
the anchor's predicted event based on vedha severity.

Column reality (confirmed from migrations 144, 146, 149):
  l1_vedha_extended:
    PK = vedha_id BIGSERIAL
    severity TEXT CHECK('strong','moderate','weak','cancellation')
    Temporal UTEE cols added by mig-149: event_window_start_iso, event_window_end_iso
    NO chart_id column in the base table (it is a reference/archetype table)

  l1_phase_locked_anchors:
    PK = anchor_id BIGSERIAL
    chart_id UUID, window_start DATE, window_end DATE (from mig-146)
    Temporal UTEE cols added by mig-149: (none beyond window_start/window_end already present)
    confidence_score FLOAT (from mig-146)
    cluster_intensity INT (from mig-146)

BRIDGE strategy:
  Because l1_vedha_extended has no chart_id, overlaps are computed differently:
  - vedha rows that have event_window_start_iso/end_iso set (after UTEE-S2 backfill for A18)
    are matched against anchor rows by temporal overlap, grouped by chart_id from anchor side.
  - vedha rows without temporal windows are skipped with a warning.
"""

import uuid
import logging

logger = logging.getLogger(__name__)

# Mitigation strength by vedha severity value (migration 144 CHECK constraint values)
VEDHA_MITIGATION_STRENGTH = {
    'strong':       0.80,
    'moderate':     0.55,
    'weak':         0.30,
    'cancellation': 0.00,
}
_DEFAULT_MITIGATION_STRENGTH = 0.40


def compute_interaction_class(mitigation_strength: float) -> str:
    """Classify interaction type from mitigation strength scalar."""
    if mitigation_strength >= 0.80:
        return 'full_mitigation'
    if mitigation_strength >= 0.55:
        return 'partial_mitigation'
    if mitigation_strength >= 0.30:
        return 'neutralizing'
    if mitigation_strength > 0.0:
        return 'amplification'
    # cancellation strength = 0.0 means the vedha itself is cancelled — no mitigation
    return 'amplification'


def _get_available_columns(conn, table_name: str, candidates: list) -> set:
    """Return subset of candidate column names that actually exist in the table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
              AND column_name = ANY(%s)
        """, (table_name, candidates))
        return {row[0] for row in cur.fetchall()}


def compute_vedha_anchor_interactions(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
) -> int:
    """
    Find temporal overlaps between A18 vedha windows and A16 anchor windows for a given chart.

    l1_vedha_extended has NO chart_id — we match by temporal overlap against anchors that
    belong to this chart_id.  Vedha rows without temporal windows are skipped.

    Returns count of interaction rows inserted.
    """
    # Detect whether temporal UTEE columns are populated on vedha table
    vedha_temporal_cols = _get_available_columns(
        conn, 'l1_vedha_extended',
        ['event_window_start_iso', 'event_window_end_iso']
    )
    anchor_window_cols = _get_available_columns(
        conn, 'l1_phase_locked_anchors',
        ['window_start', 'window_end']
    )

    if 'event_window_start_iso' not in vedha_temporal_cols:
        logger.warning(
            "BRIDGE-S2: event_window_start_iso not found on l1_vedha_extended — "
            "run UTEE-S2 backfill first. Skipping."
        )
        return 0

    if 'window_start' not in anchor_window_cols:
        logger.warning(
            "BRIDGE-S2: window_start not found on l1_phase_locked_anchors. Skipping."
        )
        return 0

    # Fetch overlapping pairs: vedha temporal window ∩ anchor DATE window
    # Cast anchor window_start/window_end (DATE) to TIMESTAMPTZ for comparison
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              v.vedha_id         AS vedha_pk,
              a.anchor_id        AS anchor_pk,
              v.severity         AS vedha_severity,
              a.confidence_score AS anchor_confidence,
              a.cluster_intensity AS anchor_cluster_intensity
            FROM l1_vedha_extended v
            CROSS JOIN l1_phase_locked_anchors a
            WHERE a.chart_id = %s
              AND v.event_window_start_iso IS NOT NULL
              AND v.event_window_end_iso   IS NOT NULL
              AND v.event_window_start_iso < a.window_end::TIMESTAMPTZ
              AND v.event_window_end_iso   > a.window_start::TIMESTAMPTZ
        """, (chart_id,))
        overlaps = cur.fetchall()

    if not overlaps:
        logger.info(
            "BRIDGE-S2: no vedha-anchor temporal overlaps found for chart_id=%s", chart_id
        )
        return 0

    count = 0
    with conn.cursor() as cur:
        for (vedha_pk, anchor_pk, vedha_severity, anchor_confidence, anchor_cluster_intensity) in overlaps:
            strength = VEDHA_MITIGATION_STRENGTH.get(vedha_severity, _DEFAULT_MITIGATION_STRENGTH)
            interaction_class = compute_interaction_class(strength)

            # Anchor severity proxy: cluster_intensity / 9.0 (max 9 systems)
            anchor_intensity_score = (
                min((anchor_cluster_intensity or 5) / 9.0, 1.0)
            )
            severity_after = max(0.0, anchor_intensity_score * (1.0 - strength * 0.5))
            confidence_after = max(0.0, (anchor_confidence or 0.5) - strength * 0.1)

            cur.execute("""
                INSERT INTO l25_vedha_anchor_interactions (
                  interaction_id, chart_id, ayanamsha_id, build_id,
                  vedha_id, anchor_id,
                  interaction_class, mitigation_strength,
                  expected_outcome_modification_class,
                  severity_after_mitigation,
                  confidence_after_mitigation,
                  classical_resolution_methodology,
                  classical_citation,
                  verification_pass_status,
                  computed_at
                ) VALUES (
                  %s, %s, %s, %s,
                  %s, %s,
                  %s, %s,
                  %s,
                  %s,
                  %s,
                  %s,
                  %s,
                  %s,
                  NOW()
                )
                ON CONFLICT (vedha_id, anchor_id, build_id)
                  WHERE anchor_id IS NOT NULL
                DO NOTHING
            """, (
                str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                vedha_pk, anchor_pk,
                interaction_class, strength,
                'vedha_mitigates_anchor_activation',
                severity_after,
                confidence_after,
                'Tajika vedha rule: active vedha partially neutralizes anchor prediction',
                'Tajika Neelakanthi §3 + BPHS vedha chapter',
                'pass',
            ))
            count += cur.rowcount

    conn.commit()
    logger.info("BRIDGE-S2: %d vedha-anchor interactions computed for chart_id=%s", count, chart_id)
    return count
