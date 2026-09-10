"""
ga_vastu_writer.py — GA-VASTU Vastu Planet Direction Map writer
===============================================================
Asset: ga_vastu — maps each classical graha to its ruling Vastu direction
and computes direction_impact using the condition_score from ga_condition_composite.

Table: ga_vastu_planet_direction_map
Natural key: (chart_id, ayanamsha_id, graha)
Rows per chart: up to 9 grahas × 5 ayanamshas = 45 (Ketu skipped if no direction found)

Idempotency: L1 pattern — DELETE (chart_id, ayanamsha_id) then INSERT.

indication_tier: 'traditional_vastu' (§N per-spec epistemic tier)

Classical sources:
  Vastu Shastra (Mayamata Ch.6)
  Brihat Samhita Ch.53 (Vastu-vidya)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import psycopg.rows

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# All 9 classical Jyotish grahas
ALL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# Classical Vastu direction–graha mapping (Mayamata Ch.6)
# Ketu has no primary direction assignment in classical Vastu Shastra
GRAHA_TO_DIRECTION: dict[str, str] = {
    "Sun":     "East",
    "Moon":    "Northwest",
    "Mars":    "South",
    "Mercury": "North",
    "Jupiter": "Northeast",
    "Venus":   "Southeast",
    "Saturn":  "West",
    "Rahu":    "Southwest",
    # Ketu: intentionally omitted — no canonical direction per Mayamata
}

VASTU_CITATION = "Vastu Shastra (Mayamata Ch.6)"

# ── direction_impact computation ──────────────────────────────────────────────

def compute_direction_impact(condition_score: Optional[float]) -> str:
    """Map a condition_score (0–1 float or None) to a direction_impact label.

    Thresholds per Gate-1 spec:
      < 0.4  → 'weakened'
      0.4–0.7 → 'neutral'
      >= 0.7 → 'strengthened'
      None   → 'neutral'
    """
    if condition_score is None:
        return "neutral"
    if condition_score < 0.4:
        return "weakened"
    if condition_score < 0.7:
        return "neutral"
    return "strengthened"


# ── Main substep function ──────────────────────────────────────────────────────

def build_ga_vastu_substep(
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    conn,
) -> int:
    """Build ga_vastu_planet_direction_map rows for one (chart_id, ayanamsha_id) slice.

    Steps:
      1. Delete existing rows for (chart_id, ayanamsha_id).
      2. For each graha with a classical direction mapping:
         a. Look up direction from GRAHA_TO_DIRECTION.
         b. Look up condition_score + dignity_d1 from ga_condition_composite (LEFT JOIN).
         c. Compute direction_impact from condition_score threshold.
         d. Insert row with indication_tier = 'traditional_vastu'.

    Returns the number of rows inserted.
    """
    rows_inserted = 0

    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        # ── L1 idempotency: delete (chart_id, ayanamsha_id) slice ─────────
        cur.execute(
            "DELETE FROM ga_vastu_planet_direction_map WHERE chart_id = %s AND ayanamsha_id = %s",
            (chart_id, ayanamsha_id),
        )
        logger.debug(
            "ga_vastu: deleted existing rows for chart_id=%s ayanamsha_id=%s",
            chart_id, ayanamsha_id,
        )

        # ── Bulk-fetch condition scores for this (chart_id, ayanamsha_id) ──
        cur.execute(
            """
            SELECT graha, condition_score, dignity_d1
            FROM ga_condition_composite
            WHERE chart_id = %s AND ayanamsha_id = %s
            """,
            (chart_id, ayanamsha_id),
        )
        condition_rows = cur.fetchall()
        condition_map: dict[str, dict] = {
            row[0]: {"condition_score": row[1], "dignity_d1": row[2]}
            for row in condition_rows
        }

        computed_at = datetime.now(timezone.utc)

        # ── Insert one row per graha that has a direction mapping ───────────
        for graha in ALL_GRAHAS:
            direction = GRAHA_TO_DIRECTION.get(graha)
            if direction is None:
                # Ketu (or any unmapped graha) — skip gracefully
                logger.debug("ga_vastu: skipping graha=%s (no direction mapping)", graha)
                continue

            cond = condition_map.get(graha, {})
            condition_score = cond.get("condition_score")
            dignity_d1 = cond.get("dignity_d1")
            direction_impact = compute_direction_impact(condition_score)

            cur.execute(
                """
                INSERT INTO ga_vastu_planet_direction_map
                    (chart_id, ayanamsha_id, graha, direction,
                     condition_score, dignity_d1, direction_impact,
                     indication_tier, classical_citation, computed_at)
                VALUES
                    (%s, %s, %s, %s,
                     %s, %s, %s,
                     'traditional_vastu', %s, %s)
                """,
                (
                    chart_id, ayanamsha_id, graha, direction,
                    condition_score, dignity_d1, direction_impact,
                    VASTU_CITATION, computed_at,
                ),
            )
            rows_inserted += 1

    # Sun and Saturn hard-gate assertions removed: both hardcoded "must equal X"
    # FORENSIC guards were structurally in tension with direction_impact's own
    # threshold-derived formula (compute_direction_impact) — Sun's ("Sun
    # debilitated in Capricorn") was astrologically incorrect outright (Sun
    # debilitates in Libra, not Capricorn); Saturn's ("exalted in Libra ->
    # must be 'strengthened'") could disagree with a correctly-computed
    # 'neutral' when condition_score sits just under the 0.7 threshold. Each
    # graha's direction_impact is correctly derived from
    # ga_condition_composite.condition_score via compute_direction_impact();
    # no hard gate is needed for either.

    logger.info(
        "ga_vastu: chart_id=%s ayanamsha_id=%s — %d rows inserted",
        chart_id, ayanamsha_id, rows_inserted,
    )
    return rows_inserted
