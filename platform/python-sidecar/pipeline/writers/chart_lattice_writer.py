"""
META-α-S1: Chart Lattice Snapshot Writer
=========================================
Computes l25_chart_lattice_snapshots for a rolling 3-year window per chart.
Runs daily via Cloud Scheduler (operator triggers; Conductor never runs gcloud).

Per: META_ENHANCEMENTS_SPEC_v1_0.md §1

Design notes
------------
- Each row is a single calendar date for one (chart_id, ayanamsha_id) pair.
- The writer joins across A15 / A16 / A19 source tables using try/except with
  conn.rollback() so missing columns (pre-migration or sparse backfill) are
  skipped gracefully rather than crashing the whole run.
- ON CONFLICT upsert keeps the table idempotent: re-running the writer for an
  already-computed window simply refreshes the rows.
- Embedding population (lattice_moment_embedding_vec) is done by a separate
  Vertex AI step — this writer leaves it NULL.

[BUILD-ORCH-STREAM-D-META-ALPHA-S1]
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resonance classification
# ---------------------------------------------------------------------------

RESONANCE_THRESHOLDS = {
    "high": 3,      # total_active_pattern_count >= 3
    "medium": 1,    # total_active_pattern_count >= 1
    "low": 0,       # total_active_pattern_count > 0  (same as medium lower bound)
    "quiescent": -1,  # fallback
}


def classify_resonance(active_count: int) -> str:
    """Map a raw active-pattern count to a resonance class label."""
    if active_count >= 3:
        return "high"
    if active_count >= 1:
        return "medium"
    return "quiescent"


# ---------------------------------------------------------------------------
# Single-date lattice computation
# ---------------------------------------------------------------------------

def compute_lattice_for_date(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: Optional[str],
    target_date: date,
) -> dict:
    """
    Compute the lattice snapshot dict for a single calendar date.

    Each sub-query is wrapped in try/except so that tables or columns not yet
    present (e.g. before a migration runs or before a backfill completes) are
    silently skipped with a debug log.  conn.rollback() is called on every
    error to reset the transaction to a clean state.

    Returns a dict ready for upsert into l25_chart_lattice_snapshots.
    """
    result: dict = {
        "snapshot_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "date_iso": target_date.isoformat(),
        "active_dasha_jsonb": None,
        "active_synchronicity_jsonb": None,
        "active_anchors_jsonb": None,
        "active_vedhas_jsonb": None,
        "nearby_bhrigu_hits_jsonb": None,
        "nearby_exact_aspects_jsonb": None,
        "total_active_pattern_count": 0,
        "resonance_class_at_date": "quiescent",
        "high_priority_attention_flag": False,
    }

    active_count = 0

    # ── A15: active time-synchronicity windows containing target_date ────────
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sync_id, cluster_intensity, convergence_type
                FROM l1_time_synchronicity
                WHERE chart_id = %s
                  AND window_start <= %s
                  AND window_end   >= %s
                LIMIT 5
                """,
                [chart_id, target_date, target_date],
            )
            syncs = cur.fetchall()
        if syncs:
            result["active_synchronicity_jsonb"] = json.dumps(
                [
                    {"window_id": str(s[0]), "intensity": s[1], "type": s[2]}
                    for s in syncs
                ]
            )
            active_count += len(syncs)
    except Exception as exc:
        logger.debug("META-α A15 query skipped for %s / %s: %s", chart_id, target_date, exc)
        conn.rollback()

    # ── A16: predicted-event anchors whose window contains target_date ───────
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT anchor_id, anchor_label, confidence_score
                FROM l1_phase_locked_anchors
                WHERE chart_id    = %s
                  AND window_start <= %s
                  AND window_end   >= %s
                LIMIT 10
                """,
                [chart_id, target_date, target_date],
            )
            anchors = cur.fetchall()
        if anchors:
            result["active_anchors_jsonb"] = json.dumps(
                [
                    {"anchor_id": str(a[0]), "label": a[1], "confidence": a[2]}
                    for a in anchors
                ]
            )
            active_count += len(anchors)
    except Exception as exc:
        logger.debug("META-α A16 query skipped for %s / %s: %s", chart_id, target_date, exc)
        conn.rollback()

    # ── A19: Bhrigu Bindu transits within ±30 days of target_date ───────────
    # hit_iso is a DATE column; cast to TIMESTAMPTZ for the EPOCH arithmetic.
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT transit_id, graha, hit_iso
                FROM l1_bhrigu_bindu_transits
                WHERE chart_id = %s
                  AND ABS(
                        EXTRACT(EPOCH FROM (hit_iso::TIMESTAMPTZ - %s::TIMESTAMPTZ))
                      ) / 86400 <= 30
                LIMIT 5
                """,
                [chart_id, target_date.isoformat()],
            )
            hits = cur.fetchall()
        if hits:
            result["nearby_bhrigu_hits_jsonb"] = json.dumps(
                [{"hit_id": str(h[0]), "graha": h[1]} for h in hits]
            )
            active_count += len(hits)
    except Exception as exc:
        logger.debug("META-α A19 query skipped for %s / %s: %s", chart_id, target_date, exc)
        conn.rollback()

    result["total_active_pattern_count"] = active_count
    result["resonance_class_at_date"] = classify_resonance(active_count)
    # Two or more simultaneous patterns warrant immediate attention
    result["high_priority_attention_flag"] = active_count >= 2

    return result


# ---------------------------------------------------------------------------
# Rolling-window writer
# ---------------------------------------------------------------------------

_UPSERT_SQL = """
INSERT INTO l25_chart_lattice_snapshots (
  snapshot_id, chart_id, ayanamsha_id, build_id, date_iso,
  active_dasha_jsonb, active_synchronicity_jsonb, active_anchors_jsonb,
  active_vedhas_jsonb, nearby_bhrigu_hits_jsonb, nearby_exact_aspects_jsonb,
  total_active_pattern_count, resonance_class_at_date,
  high_priority_attention_flag, computed_at
)
VALUES (
  %s, %s::UUID, %s, %s::UUID, %s,
  %s::JSONB, %s::JSONB, %s::JSONB,
  %s::JSONB, %s::JSONB, %s::JSONB,
  %s, %s,
  %s, NOW()
)
ON CONFLICT (chart_id, ayanamsha_id, date_iso) DO UPDATE SET
  active_dasha_jsonb           = EXCLUDED.active_dasha_jsonb,
  active_synchronicity_jsonb   = EXCLUDED.active_synchronicity_jsonb,
  active_anchors_jsonb         = EXCLUDED.active_anchors_jsonb,
  active_vedhas_jsonb          = EXCLUDED.active_vedhas_jsonb,
  nearby_bhrigu_hits_jsonb     = EXCLUDED.nearby_bhrigu_hits_jsonb,
  nearby_exact_aspects_jsonb   = EXCLUDED.nearby_exact_aspects_jsonb,
  total_active_pattern_count   = EXCLUDED.total_active_pattern_count,
  resonance_class_at_date      = EXCLUDED.resonance_class_at_date,
  high_priority_attention_flag = EXCLUDED.high_priority_attention_flag,
  computed_at                  = NOW()
"""


def write_lattice_window(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: Optional[str],
    start_date: date,
    end_date: date,
) -> int:
    """
    Compute and upsert lattice snapshots for every date in [start_date, end_date].

    The typical caller passes a rolling 3-year window:
        start_date = today - 30 days   (slight lookback so recent history is fresh)
        end_date   = today + 3 years

    Each date is committed individually so a mid-run crash leaves already-written
    rows intact (Cloud Scheduler will retry and the upsert is idempotent).

    Returns the number of rows written.
    """
    count = 0
    current = start_date

    while current <= end_date:
        row = compute_lattice_for_date(conn, chart_id, ayanamsha_id, build_id, current)

        with conn.cursor() as cur:
            cur.execute(
                _UPSERT_SQL,
                (
                    row["snapshot_id"],
                    chart_id,
                    ayanamsha_id,
                    build_id,
                    row["date_iso"],
                    row["active_dasha_jsonb"],
                    row["active_synchronicity_jsonb"],
                    row["active_anchors_jsonb"],
                    row["active_vedhas_jsonb"],
                    row["nearby_bhrigu_hits_jsonb"],
                    row["nearby_exact_aspects_jsonb"],
                    row["total_active_pattern_count"],
                    row["resonance_class_at_date"],
                    row["high_priority_attention_flag"],
                ),
            )
            count += 1

        conn.commit()
        current += timedelta(days=1)

    logger.info(
        "META-α: wrote %d lattice snapshots for chart=%s aya=%s [%s → %s]",
        count, chart_id, ayanamsha_id, start_date, end_date,
    )
    return count
