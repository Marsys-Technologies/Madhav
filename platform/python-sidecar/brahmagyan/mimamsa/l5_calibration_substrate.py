"""
brahmagyan/mimamsa/l5_calibration_substrate.py — Brahma L5 Mīmāṃsā — calibration_substrate (MI-5-3)
======================================================================================================

Asset:    mimamsa.calibration_substrate (WS-2 l5-mimamsa canonical asset)
Layer:    L5 Mīmāṃsā — Calibration framework for training events
Tool:     query_calibration_substrate(mode?) → {concordance, signal_hit_rates, provenance}

PURPOSE:
    Score the system's retrospective prediction accuracy against the 36 TRAINING events
    (event_date < 2020-01-01). These events are NOT held out — they were used in building
    L1-L4 layers, so retrospective scoring is acceptable.

    HOLD-OUT ISOLATION: The 21 hold-out events (>= 2020-01-01) are NEVER touched by this
    module. Their calibration scoring happens ONLY after predictions are made independently.

CALIBRATION METRICS:
    1. Concordance score: fraction of training events where retrodictive_match is
       "yes" or "partial" (correct-domain prediction in the top-3 chart signals).

    2. Outcome distribution: breakdown of yes/partial/no/pending across training events.

    3. Signal hit rate (scaffold): for each retrodictive outcome category, aggregate
       the convergence_score as a proxy for signal activation density.
       Full hit-rate computation awaits WS-3 grounding (when signals get rule_ids).

    4. Domain-level concordance: per event_type, what fraction of training events
       were correctly "predicted" (yes/partial) vs missed (no/pending/unexamined).

CONCORDANCE DEFINITION:
    An event is concordant if retrodictive_match = "yes" OR "partial".
    concordance_pct = 100 × (concordant_events / total_training_events)

    Only training events (is_training=True) are scored here.
    Hold-out events: NOT TOUCHED in this module.

Source:  LIFE_EVENT_LOG_v1_2.md v1.7 (retrodictive_match fields)
         l5_event_chart_state_index.py (chart state per event)
         FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1

Native:  Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India
         chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0

Authors: Silpī (WS-2 l5-mimamsa session)
BRAHMA-MI-5-3
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_CITATION = (
    "LIFE_EVENT_LOG_v1_2.md v1.7 §retrodictive_match; "
    "l5_event_chart_state_index.py (MI-5-2); "
    "FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1"
)
NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
HOLDOUT_BOUNDARY = "2020-01-01"

# Outcomes that count as "concordant" (correct domain prediction)
CONCORDANT_OUTCOMES = {"yes", "partial"}

# Outcomes that count as "missed" (prediction failure or unresolved)
MISSED_OUTCOMES = {"no", "pending", "unexamined", None}


# ── Core computation ──────────────────────────────────────────────────────────

def compute_calibration_substrate(
    index: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Compute the full calibration substrate from the chart state index.

    Only TRAINING events (is_training=True, event_date < 2020-01-01) are scored.
    Hold-out events are reported in summary but NOT scored.

    Args:
        index: Pre-built chart state index. If None, builds fresh from l5_event_chart_state_index.

    Returns:
        Full calibration substrate dict with concordance, domain breakdown,
        convergence distribution, and provenance.
    """
    if index is None:
        from brahmagyan.mimamsa.l5_event_chart_state_index import build_event_chart_state_index
        index = build_event_chart_state_index()

    # Partition
    training = [e for e in index if e.get("is_training", False)]
    holdout = [e for e in index if e.get("is_holdout", False)]

    # --- Training event scoring ---
    concordant = []
    missed = []
    outcome_dist: Counter[str] = Counter()

    for e in training:
        sig_act = e.get("l2_signal_activations", {})
        outcome = sig_act.get("outcome_observed") or ""
        convergence = sig_act.get("convergence_score")

        outcome_dist[outcome or "null"] += 1

        if outcome in CONCORDANT_OUTCOMES:
            concordant.append(e)
        else:
            missed.append(e)

    total_training = len(training)
    concordant_count = len(concordant)
    concordance_pct = (
        round(100.0 * concordant_count / total_training, 1)
        if total_training > 0
        else 0.0
    )

    # --- Domain-level concordance ---
    domain_scores: dict[str, dict[str, int]] = defaultdict(lambda: {"concordant": 0, "missed": 0, "total": 0})
    for e in training:
        sig_act = e.get("l2_signal_activations", {})
        outcome = sig_act.get("outcome_observed") or ""
        domain = e.get("event_type", "unknown")
        domain_scores[domain]["total"] += 1
        if outcome in CONCORDANT_OUTCOMES:
            domain_scores[domain]["concordant"] += 1
        else:
            domain_scores[domain]["missed"] += 1

    domain_concordance = {}
    for domain, counts in sorted(domain_scores.items()):
        total_d = counts["total"]
        conc_d = counts["concordant"]
        domain_concordance[domain] = {
            "concordant":      conc_d,
            "missed":          counts["missed"],
            "total":           total_d,
            "concordance_pct": round(100.0 * conc_d / total_d, 1) if total_d > 0 else 0.0,
        }

    # --- Convergence score distribution ---
    convergence_vals = [
        e["l2_signal_activations"]["convergence_score"]
        for e in training
        if e["l2_signal_activations"]["convergence_score"] is not None
    ]
    mean_convergence = (
        round(sum(convergence_vals) / len(convergence_vals), 4)
        if convergence_vals
        else None
    )

    # --- Signal hit rate scaffold ---
    # Full hit-rate awaits WS-3 grounding. Currently: convergence_score is the proxy.
    # "yes" events have convergence=1.0, "partial"=0.5, "no"=0.0, pending/unexamined=None
    signal_hit_rate_scaffold = {
        "note": (
            "Full signal hit rate awaits WS-3 rule_base grounding. "
            "Current proxy: mean convergence_score over training events with known outcome."
        ),
        "proxy_mean_convergence": mean_convergence,
        "yes_events":     outcome_dist.get("yes", 0),
        "partial_events": outcome_dist.get("partial", 0),
        "no_events":      outcome_dist.get("no", 0),
        "pending_events": sum(
            v for k, v in outcome_dist.items() if k in ("pending", "unexamined", "null")
        ),
        "l2_ungrounded_signal_count": 569,
        "grounding_status": "UNGROUNDED scaffold — awaiting WS-3 rule_base completion",
    }

    # --- Missed events detail ---
    missed_detail = [
        {
            "lel_id":     e["lel_id"],
            "event_date": e["event_date"],
            "event_type": e.get("event_type", ""),
            "outcome":    e["l2_signal_activations"].get("outcome_observed"),
        }
        for e in missed
    ]

    return {
        # Core metrics
        "concordance_pct":         concordance_pct,
        "concordant_count":        concordant_count,
        "total_training_events":   total_training,
        "total_holdout_events":    len(holdout),
        "total_events":            len(index),

        # Outcome distribution
        "outcome_distribution":    dict(outcome_dist),

        # Domain breakdown
        "domain_concordance":      domain_concordance,

        # Signal hit rate scaffold
        "signal_hit_rate_scaffold": signal_hit_rate_scaffold,

        # Missed events
        "missed_events_detail":    missed_detail,

        # Isolation confirmation
        "holdout_untouched":       True,
        "holdout_note": (
            f"{len(holdout)} hold-out events (>= {HOLDOUT_BOUNDARY}) NOT scored. "
            "Their calibration runs only after independent predictions are made."
        ),

        # Source
        "source_citation":         SOURCE_CITATION,
    }


def get_concordance_summary() -> dict[str, Any]:
    """
    Return a concise concordance summary (used by the orchestrator and smriti).

    Returns:
        {concordance_pct, concordant/total_training, holdout_count, provenance}
    """
    substrate = compute_calibration_substrate()
    return {
        "concordance_pct":       substrate["concordance_pct"],
        "concordant_count":      substrate["concordant_count"],
        "total_training_events": substrate["total_training_events"],
        "total_holdout_events":  substrate["total_holdout_events"],
        "holdout_untouched":     substrate["holdout_untouched"],
        "outcome_distribution":  substrate["outcome_distribution"],
        "provenance_envelope":   _provenance_envelope(),
    }


def _provenance_envelope() -> dict[str, Any]:
    return {
        "source":              "mimamsa.calibration_substrate (l5_calibration_substrate)",
        "asset":               "MI-5-3",
        "lel_version":         "LIFE_EVENT_LOG_v1_2.md v1.7",
        "holdout_boundary":    HOLDOUT_BOUNDARY,
        "concordant_definition": "retrodictive_match in {yes, partial}",
        "signal_hit_rate":     "scaffold only — awaiting WS-3 rule_base grounding",
        "source_citation":     SOURCE_CITATION,
        "no_leakage_note":     "hold-out events NOT scored — calibration runs only after independent predictions",
        "computed_at":         datetime.now(timezone.utc).isoformat(),
    }


# ── DB persistence (optional) ─────────────────────────────────────────────────

def seed_calibration_substrate(
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Compute and optionally persist the calibration substrate to chart_facts.

    Stores as:
        fact_category = 'mimamsa.calibration'
        fact_subject  = 'concordance_summary'
        fact_value    = {concordance_pct, outcome_distribution, domain_concordance, ...}
        source_citation = SOURCE_CITATION

    Args:
        dry_run: Compute but do not write.
        verbose: Log computation details.

    Returns:
        Result dict with concordance metrics and provenance.
    """
    import json as _json
    import os

    substrate = compute_calibration_substrate()

    if verbose:
        logger.info(
            "[calibration_substrate] concordance_pct=%.1f%% (%d/%d training events)",
            substrate["concordance_pct"],
            substrate["concordant_count"],
            substrate["total_training_events"],
        )
        for domain, stats in substrate["domain_concordance"].items():
            logger.info(
                "  domain=%s concordant=%d/%d (%.1f%%)",
                domain,
                stats["concordant"],
                stats["total"],
                stats["concordance_pct"],
            )

    if dry_run:
        return {
            "dry_run":    True,
            "substrate":  substrate,
            "provenance_envelope": _provenance_envelope(),
        }

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.warning("DATABASE_URL not set — skipping calibration_substrate DB persistence")
        return {
            "skipped":   True,
            "reason":    "DATABASE_URL not set",
            "substrate": substrate,
            "provenance_envelope": _provenance_envelope(),
        }

    try:
        import psycopg  # type: ignore
        import uuid

        fact_id = str(uuid.uuid5(
            uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
            f"BRAHMA-MI-5-3:concordance_summary:{NATIVE_CHART_ID}"
        ))

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chart_facts
                        (fact_id, chart_id, fact_category, fact_subject,
                         fact_value, rule_id, source_citation)
                    VALUES (%s::UUID, %s::UUID, %s, %s, %s::JSONB, NULL, %s)
                    ON CONFLICT (fact_id) DO UPDATE SET
                        fact_value      = EXCLUDED.fact_value,
                        source_citation = EXCLUDED.source_citation
                    """,
                    (
                        fact_id,
                        NATIVE_CHART_ID,
                        "mimamsa.calibration",
                        "concordance_summary",
                        _json.dumps({
                            "concordance_pct":        substrate["concordance_pct"],
                            "concordant_count":       substrate["concordant_count"],
                            "total_training_events":  substrate["total_training_events"],
                            "total_holdout_events":   substrate["total_holdout_events"],
                            "outcome_distribution":   substrate["outcome_distribution"],
                            "domain_concordance":     substrate["domain_concordance"],
                            "signal_hit_rate_scaffold": substrate["signal_hit_rate_scaffold"],
                            "holdout_untouched":      True,
                        }),
                        SOURCE_CITATION,
                    ),
                )
            conn.commit()

        logger.info(
            "calibration_substrate seeded: concordance_pct=%.1f%% (%d/%d)",
            substrate["concordance_pct"],
            substrate["concordant_count"],
            substrate["total_training_events"],
        )
        return {
            "seeded":    True,
            "substrate": substrate,
            "provenance_envelope": _provenance_envelope(),
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("calibration_substrate seed failed: %s", exc)
        return {
            "error":     str(exc),
            "substrate": substrate,
            "provenance_envelope": _provenance_envelope(),
        }
