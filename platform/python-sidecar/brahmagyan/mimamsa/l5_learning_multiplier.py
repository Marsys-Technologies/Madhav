"""
brahmagyan/mimamsa/l5_learning_multiplier.py — Brahma L5 Mīmāṃsā — learning_multiplier (MI-5-4)
==================================================================================================

Asset:    mimamsa.learning_multiplier (WS-2 l5-mimamsa canonical asset)
Layer:    L5 Mīmāṃsā — Signal confidence learning multipliers
Tool:     (internal to L4 computation — no MCP tool; consumed by l4_phala and l4_anchors)

PURPOSE:
    Maintain a per-signal learning multiplier that adjusts signal confidence when
    outcomes validate (or refute) predictions.

    When future calibration runs update multipliers:
        signal_confidence = base_confidence × multiplier (capped at 0.95)

INITIAL STATE:
    All 569 L2 signal multipliers initialised at 1.0 (neutral — no outcome evidence yet).
    Structure: signal_id → multiplier (1.0), last_updated, evidence_events (empty array)

    The base multiplier module (multiplier.py / MI-5-4) operates on (technique, ayanamsha_id)
    pairs using the Brier-score formula. This module provides the per-SIGNAL scaffold that
    feeds into that engine once calibration data accumulates.

MULTIPLIER FORMULA (from multiplier.py):
    multiplier = CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2)

    mean_brier_score < 0.5 → multiplier > 1.0 (boost technique)
    mean_brier_score > 0.5 → multiplier < 1.0 (down-weight)
    mean_brier_score = 0.5 → multiplier = 1.0 (no change = initial state)

VOLUME FLOOR: 569 multiplier rows (one per L2 scaffold signal).

ISOLATION RULE:
    Multipliers are consumed by L4 Phala only. They NEVER expose LEL event data
    to prediction generation — only pre-aggregated calibration statistics flow in.

Source:  l2_signals_scaffold.py VOLUME_FLOOR=569
         multiplier.py (MI-5-4) — Brier-score engine
         FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)

Native:  Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India
         chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0

Authors: Silpī (WS-2 l5-mimamsa session)
BRAHMA-MI-5-4-SCAFFOLD
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_CITATION = (
    "l2_signals_scaffold.py (BO-2-1 VOLUME_FLOOR=569); "
    "multiplier.py (MI-5-4 Brier-score engine); "
    "FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md); "
    "LIFE_EVENT_LOG_v1_2.md v1.7 §Calibration-outcomes; "
    "Brier (1950) Verification of Forecasts Expressed in Terms of Probability"
)
NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
VOLUME_FLOOR = 569

# Initial multiplier for all signals (neutral — no outcome evidence yet)
INITIAL_MULTIPLIER = 1.0

# Multiplier bounds (from multiplier.py — Brier-score engine)
MULTIPLIER_MIN = 0.8
MULTIPLIER_MAX = 1.2

# Cap on signal_confidence after multiplier application
CONFIDENCE_CAP = 0.95


# ── Signal ID enumeration ─────────────────────────────────────────────────────
#
# 569 L2 scaffold signal IDs from l2_signals_scaffold.py.
# Format: SIG.MSR.<NNN> where NNN in 001-573 (4 known ID gaps: 207, 497-499).
# We generate the full range and emit exactly VOLUME_FLOOR (569) rows.

def _enumerate_signal_ids() -> list[str]:
    """
    Enumerate the 569 valid MSR signal IDs.
    Skips known ID gaps: 207, 497, 498, 499 (confirmed numbering artifacts from MSR v5.0).
    """
    try:
        from brahmagyan.bodha.l2_signals_scaffold import VOLUME_FLOOR as BF  # type: ignore
    except (ImportError, AttributeError):
        BF = VOLUME_FLOOR  # fallback

    # Known gaps from MSR_v5_0 numbering (confirmed in l2_signals_scaffold.py comments)
    KNOWN_GAPS = {207, 497, 498, 499}

    ids: list[str] = []
    n = 1
    while len(ids) < VOLUME_FLOOR and n <= 600:
        if n not in KNOWN_GAPS:
            ids.append(f"SIG.MSR.{n:03d}")
        n += 1
    return ids[:VOLUME_FLOOR]


# ── Multiplier row construction ───────────────────────────────────────────────

def build_multiplier_rows() -> list[dict[str, Any]]:
    """
    Build the 569-row initial multiplier scaffold.

    Each row:
        signal_id:       SIG.MSR.NNN
        multiplier:      1.0 (neutral initial state)
        last_updated:    current UTC timestamp
        evidence_events: []  (no outcome evidence yet)
        mean_brier_score: None  (no calibration data yet)
        sample_size:     0
        status:          'scaffold'  (awaiting calibration data)
        source_citation: SOURCE_CITATION

    Returns:
        List of 569 dicts.
    """
    signal_ids = _enumerate_signal_ids()
    now = datetime.now(timezone.utc).isoformat()

    rows: list[dict[str, Any]] = []
    for sid in signal_ids:
        rows.append({
            "signal_id":        sid,
            "multiplier":       INITIAL_MULTIPLIER,
            "last_updated":     now,
            "evidence_events":  [],       # empty — no resolved predictions yet
            "mean_brier_score": None,     # not yet computed
            "sample_size":      0,        # no calibration evidence
            "status":           "scaffold",  # awaiting WS-3 grounding + calibration
            "source_citation":  SOURCE_CITATION,
        })

    return rows


def get_multiplier_for_signal(
    signal_id: str,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """
    Return the current multiplier row for a signal ID.

    Args:
        signal_id: e.g. 'SIG.MSR.001'
        rows:      Pre-built rows list (if None, builds fresh).

    Returns:
        Multiplier row dict or None if signal not found.
    """
    if rows is None:
        rows = build_multiplier_rows()
    return next((r for r in rows if r["signal_id"] == signal_id), None)


def apply_multiplier_to_signal(
    signal_id: str,
    base_confidence: float,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Apply the learning multiplier to a signal's base confidence.

    Formula:
        adjusted = CLAMP(base_confidence × multiplier, 0.0, CONFIDENCE_CAP)

    Args:
        signal_id:       MSR signal ID.
        base_confidence: Classical layer base confidence [0.0, 1.0].
        rows:            Pre-built rows list.

    Returns:
        {signal_id, base_confidence, multiplier, adjusted_confidence, provenance_envelope}
    """
    if not (0.0 <= base_confidence <= 1.0):
        raise ValueError(
            f"base_confidence must be in [0.0, 1.0], got {base_confidence}"
        )

    row = get_multiplier_for_signal(signal_id, rows)
    multiplier = row["multiplier"] if row else INITIAL_MULTIPLIER
    adjusted_raw = base_confidence * multiplier
    adjusted = min(CONFIDENCE_CAP, max(0.0, adjusted_raw))

    return {
        "signal_id":           signal_id,
        "base_confidence":     base_confidence,
        "multiplier":          multiplier,
        "adjusted_confidence": round(adjusted, 6),
        "confidence_cap":      CONFIDENCE_CAP,
        "provenance_envelope": {
            "source":          "mimamsa.learning_multiplier (l5_learning_multiplier)",
            "asset":           "MI-5-4-SCAFFOLD",
            "formula":         "CLAMP(base × multiplier, 0.0, 0.95)",
            "multiplier_bounds": f"[{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]",
            "leakage_guard":   "multipliers use pre-aggregated Brier scores only — never raw LEL events",
            "queried_at":      datetime.now(timezone.utc).isoformat(),
        },
    }


def get_multiplier_stats(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Return summary statistics for the multiplier scaffold.

    Returns:
        {total, all_at_initial, initial_value, volume_floor_met, ...}
    """
    if rows is None:
        rows = build_multiplier_rows()

    all_at_initial = all(r["multiplier"] == INITIAL_MULTIPLIER for r in rows)
    total_with_evidence = sum(1 for r in rows if r["sample_size"] > 0)

    return {
        "total":               len(rows),
        "all_at_initial":      all_at_initial,
        "initial_value":       INITIAL_MULTIPLIER,
        "volume_floor_met":    len(rows) >= VOLUME_FLOOR,
        "total_with_evidence": total_with_evidence,
        "status":              "scaffold" if all_at_initial else "partially_calibrated",
        "note": (
            "All multipliers at 1.0 — initial neutral state. "
            "Multipliers will update as predictions are logged and outcomes observed. "
            "WS-3 rule_base grounding required for signal-level Brier score computation."
        ),
    }


# ── DB upsert ─────────────────────────────────────────────────────────────────

def seed_learning_multipliers(
    *,
    dry_run: bool = False,
    verbose: bool = False,
    force_reset: bool = False,
) -> dict[str, Any]:
    """
    Upsert the 569-row signal multiplier scaffold into mimamsa_signal_multipliers table.

    This table is SEPARATE from mimamsa_multipliers (which operates on technique×ayanamsha pairs).
    mimamsa_signal_multipliers is the per-signal view, mapping SIG.MSR.NNN → multiplier.

    Args:
        dry_run:      Compute but do not write.
        verbose:      Log each row.
        force_reset:  Force all multipliers back to 1.0 (use with caution).

    Returns:
        Result dict with volume floor check and provenance.
    """
    import json as _json

    rows = build_multiplier_rows()
    stats = get_multiplier_stats(rows)

    if verbose:
        logger.info(
            "[learning_multiplier] %d rows at multiplier=%.1f (scaffold)",
            len(rows), INITIAL_MULTIPLIER,
        )

    if dry_run:
        return {
            "dry_run":          True,
            "total":            len(rows),
            "stats":            stats,
            "volume_floor_met": stats["volume_floor_met"],
            "provenance_envelope": _provenance_envelope(),
        }

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.warning("DATABASE_URL not set — skipping learning multiplier seed")
        return {
            "skipped":   True,
            "reason":    "DATABASE_URL not set",
            "total":     len(rows),
            "stats":     stats,
            "provenance_envelope": _provenance_envelope(),
        }

    try:
        import psycopg  # type: ignore

        upserted = 0
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Create table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS mimamsa_signal_multipliers (
                        signal_id        TEXT PRIMARY KEY,
                        multiplier       FLOAT NOT NULL
                                             CHECK (multiplier >= 0.8 AND multiplier <= 1.2),
                        last_updated     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        mean_brier_score FLOAT,
                        sample_size      INT NOT NULL DEFAULT 0,
                        evidence_events  JSONB NOT NULL DEFAULT '[]'::JSONB,
                        status           TEXT NOT NULL DEFAULT 'scaffold',
                        source_citation  TEXT NOT NULL
                    )
                """)

                for r in rows:
                    if force_reset or r["sample_size"] == 0:
                        # INSERT new or reset-to-scaffold if force_reset
                        cur.execute(
                            """
                            INSERT INTO mimamsa_signal_multipliers
                                (signal_id, multiplier, last_updated, mean_brier_score,
                                 sample_size, evidence_events, status, source_citation)
                            VALUES (%s, %s, %s::TIMESTAMPTZ, %s, %s, %s::JSONB, %s, %s)
                            ON CONFLICT (signal_id) DO UPDATE SET
                                multiplier       = CASE
                                    WHEN %s THEN EXCLUDED.multiplier
                                    ELSE mimamsa_signal_multipliers.multiplier
                                END,
                                last_updated     = EXCLUDED.last_updated,
                                source_citation  = EXCLUDED.source_citation
                            """,
                            (
                                r["signal_id"],
                                r["multiplier"],
                                r["last_updated"],
                                r["mean_brier_score"],
                                r["sample_size"],
                                _json.dumps(r["evidence_events"]),
                                r["status"],
                                r["source_citation"],
                                force_reset,  # controls CASE in DO UPDATE
                            ),
                        )
                    else:
                        # INSERT only — don't overwrite existing calibrated multipliers
                        cur.execute(
                            """
                            INSERT INTO mimamsa_signal_multipliers
                                (signal_id, multiplier, last_updated, mean_brier_score,
                                 sample_size, evidence_events, status, source_citation)
                            VALUES (%s, %s, %s::TIMESTAMPTZ, %s, %s, %s::JSONB, %s, %s)
                            ON CONFLICT (signal_id) DO NOTHING
                            """,
                            (
                                r["signal_id"],
                                r["multiplier"],
                                r["last_updated"],
                                r["mean_brier_score"],
                                r["sample_size"],
                                _json.dumps(r["evidence_events"]),
                                r["status"],
                                r["source_citation"],
                            ),
                        )
                    upserted += 1

            conn.commit()

        logger.info("learning_multiplier: seeded %d signal rows (all at 1.0 scaffold)", upserted)
        return {
            "upserted":          upserted,
            "total":             len(rows),
            "stats":             stats,
            "volume_floor_met":  stats["volume_floor_met"],
            "provenance_envelope": _provenance_envelope(),
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("learning_multiplier seed failed: %s", exc)
        return {
            "error":     str(exc),
            "total":     len(rows),
            "stats":     stats,
            "provenance_envelope": _provenance_envelope(),
        }


def _provenance_envelope() -> dict[str, Any]:
    return {
        "source":            "mimamsa.learning_multiplier (l5_learning_multiplier)",
        "asset":             "MI-5-4-SCAFFOLD",
        "lel_version":       "LIFE_EVENT_LOG_v1_2.md v1.7",
        "total_signals":     VOLUME_FLOOR,
        "initial_value":     INITIAL_MULTIPLIER,
        "multiplier_bounds": f"[{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]",
        "confidence_cap":    CONFIDENCE_CAP,
        "status":            "scaffold — all multipliers at 1.0 pending calibration",
        "source_citation":   SOURCE_CITATION,
        "leakage_guard":     (
            "multipliers consume pre-aggregated Brier scores only — "
            "never raw LEL events or prediction inputs"
        ),
        "computed_at":       datetime.now(timezone.utc).isoformat(),
    }
