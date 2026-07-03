"""
brahmagyan.l0_formula_constants — bg_formula_constants L0 global seed.

Populates brahma_formula_constants with 10 canonical constants (excluding
the _bug_* documentation sentinel, which the writer skips in its count).

Classes:
  CLASSICAL       — cite-and-encode; never tune
  NATIVE_JUDGMENT — ratified, versioned, L5-calibratable within bounds
  ENGINEERING     — document only
  CONFLATION_BUG  — document; fix at source, never operationalize

Source: BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md §7

Idempotency: L0 = ON CONFLICT DO UPDATE (global, not per-chart).
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

CONSTANTS: list[dict] = [
    {
        "constant_id": "combustion_orbs",
        "value_jsonb": {
            "Moon":    {"direct": 12, "retrograde": 12},
            "Mars":    {"direct": 17, "retrograde": 15},
            "Mercury": {"direct": 14, "retrograde": 12},
            "Jupiter": {"direct": 11, "retrograde": 9},
            "Venus":   {"direct": 10, "retrograde": 8},
            "Saturn":  {"direct": 15, "retrograde": 12},
            "Rahu":    {"direct": 9,  "retrograde": 7},
            "Ketu":    {"direct": 9,  "retrograde": 7},
        },
        "class": "classical",
        "consumer_assets": ["ga_condition", "ka_vighnakara", "ph_sodhana"],
        "citation_or_ratification": (
            "Sārāvalī ch.6 / BPHS ch.3 (combustion-degrees per graha). "
            "Moon=12 classical; Mars=17/15 d/r; Merc=14/12; Jup=11/9; Ven=10/8; Sat=15/12; Rahu/Ketu=9/7. "
            "Already in bg_combustion_orbs; ka_vighnakara must read from here rather than flat 6° (BA_MASTER C12)."
        ),
        "calibratable": False,
        "bounds": None,
    },
    {
        "constant_id": "obstruction_severity_thresholds",
        "value_jsonb": {"severe": 0.70, "moderate": 0.40, "mild": 0.15},
        "class": "native_judgment",
        "consumer_assets": ["ka_vighnakara", "ph_sodhana"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: ratified at 0.70/0.40/0.15 (severe/moderate/mild); "
            "aligned to house-strength convention."
        ),
        "calibratable": True,
        "bounds": {"severe": [0.60, 0.80], "moderate": [0.30, 0.50], "mild": [0.10, 0.25]},
    },
    {
        "constant_id": "magnitude_tiers",
        "value_jsonb": {
            "life_altering": 0.90, "major": 0.70, "significant": 0.50,
            "moderate": 0.30, "trivial": 0.10,
        },
        "class": "native_judgment",
        "consumer_assets": ["ph_nimitta", "ph_pramana", "mi_outcome"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: ratified at 5-tier scale; aligns LEL magnitude labels "
            "to numeric floors. phala_anchors.magnitude enum source."
        ),
        "calibratable": True,
        "bounds": {
            "life_altering": [0.80, 0.95], "major": [0.60, 0.80],
            "significant": [0.40, 0.60], "moderate": [0.20, 0.40], "trivial": [0.05, 0.20],
        },
    },
    {
        "constant_id": "dignity_scores",
        "value_jsonb": {
            "exalted": 1.00, "moolatrikona": 0.90, "own": 0.80,
            "great_friend_sign": 0.65, "friend_sign": 0.55, "neutral_sign": 0.45,
            "enemy_sign": 0.30, "great_enemy_sign": 0.20, "debilitated": 0.10,
        },
        "class": "native_judgment",
        "consumer_assets": ["ga_condition", "composite_ranker"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: ratified dignity scale. Foundation: Shadbala dignity "
            "component (BPHS), normalized to 0–1. Already in ga_condition_writer.py DIGNITY_SCORES; "
            "this entry is canonical."
        ),
        "calibratable": True,
        "bounds": {"all_bounds": "±0.05 per tier"},
    },
    {
        "constant_id": "house_weights",
        "value_jsonb": {
            "1": 1.15, "2": 0.85, "3": 1.00, "4": 1.15, "5": 1.20, "6": 0.85,
            "7": 1.15, "8": 0.85, "9": 1.20, "10": 1.15, "11": 1.00, "12": 0.85,
            "note": "1 counts as both kendra and trikona",
        },
        "class": "native_judgment",
        "consumer_assets": ["ga_condition", "composite_ranker"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: kendra(1,4,7,10)=1.15; trikona(1,5,9)=1.20 "
            "(1 counts as both); upachaya(3,6,11)=1.00; 2/8/12=0.85; "
            "6/8/12 contextual (dusthana). Based on BPHS bhava-bala."
        ),
        "calibratable": True,
        "bounds": {"all_bounds": "±0.10 per house class"},
    },
    {
        "constant_id": "attention_budget",
        "value_jsonb": {
            "head_pct": 70, "dissent_pct": 20, "tail_pct": 10,
            "description": (
                "head=top-ranking signals for primary response; "
                "dissent=conflicting signals for honest acknowledgment; "
                "tail=weak signals for context"
            ),
        },
        "class": "native_judgment",
        "consumer_assets": ["assess_career", "assess_relationship", "assess_wealth", "assess_health"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: ratified 70/20/10 (head/dissent/tail). "
            "Per-query-class tunable within [50-80]/[10-30]/[5-20]. "
            "Govern Doctrine §1.4 attention allocation."
        ),
        "calibratable": True,
        "bounds": {"head_pct": [50, 80], "dissent_pct": [10, 30], "tail_pct": [5, 20]},
    },
    {
        "constant_id": "dasha_score_flag_threshold",
        "value_jsonb": {
            "threshold": 0.30,
            "description": (
                "ka_sangam convergence windows with dasha_score > 0.30 "
                "are flagged as active temporal windows"
            ),
        },
        "class": "native_judgment",
        "consumer_assets": ["ka_sangam"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: ratified at 0.30; move from inline code to registry."
        ),
        "calibratable": True,
        "bounds": {"threshold": [0.20, 0.40]},
    },
    {
        "constant_id": "mi_sambandha_channel_priors",
        "value_jsonb": {
            "career":       {"signal": 0.40, "dasha": 0.35, "transit": 0.25},
            "relationship": {"signal": 0.35, "dasha": 0.40, "transit": 0.25},
            "health":       {"signal": 0.40, "dasha": 0.30, "transit": 0.30},
            "wealth":       {"signal": 0.35, "dasha": 0.35, "transit": 0.30},
            "spirituality": {"signal": 0.35, "dasha": 0.35, "transit": 0.30},
            "general":      {"signal": 0.40, "dasha": 0.30, "transit": 0.30},
        },
        "class": "native_judgment",
        "consumer_assets": ["mi_sambandha"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: Dirichlet base priors per domain for mi_sambandha "
            "channel attribution. L5 triangulation updates empirically."
        ),
        "calibratable": True,
        "bounds": {"note": "Dirichlet alpha; each domain sum must = 1.00"},
    },
    {
        "constant_id": "mi_gunanaka_divergence_cap",
        "value_jsonb": {
            "cap": 3.0,
            "description": (
                "Maximum ratio between highest and lowest channel weight before "
                "normalization in mi_gunanaka"
            ),
        },
        "class": "native_judgment",
        "consumer_assets": ["mi_gunanaka"],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7: cap=3.0 (MIMAMSA_V2); prevents extreme outlier "
            "weights from dominating. Range [2,4]."
        ),
        "calibratable": True,
        "bounds": {"cap": [2.0, 4.0]},
    },
    {
        "constant_id": "holdout_partition",
        "value_jsonb": {
            "fraction": 0.20,
            "method": "MD5(chart_id)::bigint % 10 >= 8",
            "description": (
                "20% holdout for calibration; chart_ids with MD5 mod 10 >= 8 are held out"
            ),
        },
        "class": "engineering",
        "consumer_assets": ["mi_outcome", "mi_ledger"],
        "citation_or_ratification": (
            "ENGINEERING: holdout partition is a data-split decision, not a classical constant. "
            "Keep=0.20 (20%). Method: MD5 hash of chart_id modulo 10."
        ),
        "calibratable": False,
        "bounds": None,
    },
    # CONFLATION_BUG entry — documented, not operationalized
    {
        "constant_id": "_bug_ka_sangam_confidence_conflation",
        "value_jsonb": {
            "bug": (
                "ka_sangam stores confidence as convergence score (0-1) but this field is not "
                "a prediction confidence — it is a dasha/transit alignment strength. "
                "These are different quantities."
            ),
            "fix": "W4A: separate convergence_strength from prediction_confidence in ka_sangam output",
            "status": "OPEN",
        },
        "class": "conflation_bug",
        "consumer_assets": [],
        "citation_or_ratification": (
            "W1_SEED_PACKAGE_v1_0 §7 BA_MASTER C10: CONFLATION-BUG — fix at source in W4A. "
            "Do NOT seed as a constant."
        ),
        "calibratable": False,
        "bounds": None,
    },
]


def seed_formula_constants(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Upsert CONSTANTS into brahma_formula_constants.
    Returns {"brahma_formula_constants": <operationalizable_rows_upserted>}.

    autocommit: if False, caller owns the transaction (pass False from asset_runner).
    """
    if dry_run:
        logger.info("[L0/formula_constants] dry_run — would upsert %d constants", len(CONSTANTS))
        return {"brahma_formula_constants": len(CONSTANTS)}

    upserted = 0
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='brahma_formula_constants'"
        )
        if cur.fetchone()["count"] == 0:
            raise RuntimeError(
                "brahma_formula_constants table does not exist — apply migration 389 first."
            )

        for row in CONSTANTS:
            cur.execute(
                """
                INSERT INTO brahma_formula_constants
                  (constant_id, value_jsonb, class, consumer_assets,
                   citation_or_ratification, calibratable, bounds, version)
                VALUES (%s, %s::jsonb, %s, %s, %s, %s, %s::jsonb, '1.0')
                ON CONFLICT (constant_id)
                DO UPDATE SET
                    value_jsonb              = EXCLUDED.value_jsonb,
                    class                    = EXCLUDED.class,
                    consumer_assets          = EXCLUDED.consumer_assets,
                    citation_or_ratification = EXCLUDED.citation_or_ratification,
                    calibratable             = EXCLUDED.calibratable,
                    bounds                   = EXCLUDED.bounds
                """,
                (
                    row["constant_id"],
                    json.dumps(row["value_jsonb"]),
                    row["class"],
                    row["consumer_assets"],
                    row["citation_or_ratification"],
                    row["calibratable"],
                    json.dumps(row["bounds"]) if row["bounds"] is not None else None,
                ),
            )
            upserted += 1

    if autocommit:
        conn.commit()

    logger.info("[L0/formula_constants] upserted %d constants", upserted)
    return {"brahma_formula_constants": upserted}
