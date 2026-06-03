"""
brahmagyan/mimamsa/multiplier.py — Brahma L5 Mīmāṃsā — mimamsa.multiplier (MI-5-4)

Asset:    mimamsa.multiplier
Layer:    L5 Mīmāṃsā (final layer — internal to L4 computation; no MCP tool)
Table:    mimamsa_multipliers (technique TEXT, ayanamsha_id TEXT, multiplier FLOAT, ...)

Algorithm:
    learning_multiplier(technique, ayanamsha_id) =
        CLAMP(1.0 + 0.1 × (0.5 - mean_brier_score), 0.8, 1.2)

    Interpretation:
        mean_brier_score < 0.5 (better than random) → multiplier > 1.0 (boost technique)
        mean_brier_score > 0.5 (worse than random)  → multiplier < 1.0 (down-weight)
        mean_brier_score = 0.5 (random baseline)    → multiplier = 1.0 (no change)

    The Brier score is a strictly proper scoring rule for probabilistic predictions:
        BS = (forecast_probability - actual_outcome)^2  [0.0 = perfect, 1.0 = worst]
    Random (uninformative) predictor: BS = 0.25 for binary events.
    We normalise to [0.0, 1.0] scale where 0.5 is the reference random baseline.

Contract (BRAHMA MI-5-4):
    - source_citation non-null on all rows (B.3 mandate)
    - multiplier CHECK(0.8 <= multiplier <= 1.2) in DB and at compute time
    - sample_size > 0 required to trigger an update (reject updates with 0 samples)
    - provenance_envelope on all retrieval responses
    - NO LEAKAGE: life_events feed only into calibration, never into prediction generation
    - Migration: brahma_mimamsa_multiplier.sql (IF NOT EXISTS)
    - Internal to L4 computation — no FastAPI endpoint / no MCP tool

Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0

Depends:  phala_anchors (for mean_brier_score calibration input)
          FORENSIC v8.0 §5.1 (canonical L1 chart ground-truth)
          LEL v1.7 §Events 1–57 (calibration outcomes ONLY — never into prediction)

Authors:  Silpī (MI-5-4 session)
Version:  1.0 — 2026-06-04
BRAHMA-MI-5-4
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
import psycopg.rows

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Multiplier bounds — classical layer modulated, NOT overwritten
MULTIPLIER_MIN: float = 0.8
MULTIPLIER_MAX: float = 1.2

# Brier score reference (random/uninformative baseline for normalised binary events)
BRIER_REFERENCE: float = 0.5

# Scaling coefficient for multiplier sensitivity
MULTIPLIER_SCALE: float = 0.1

# Source citation — mandatory for every row (B.3 mandate)
DEFAULT_SOURCE_CITATION = (
    "FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes; "
    "Brier (1950) Verification of Forecasts Expressed in Terms of Probability; "
    "BRAHMA MI-5-4"
)


# ── DB URL ────────────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── Core engine ───────────────────────────────────────────────────────────────

def compute_multiplier(mean_brier_score: float) -> float:
    """
    Compute the bounded learning multiplier from a mean Brier score.

    Formula:
        raw = 1.0 + MULTIPLIER_SCALE × (BRIER_REFERENCE - mean_brier_score)
        multiplier = CLAMP(raw, MULTIPLIER_MIN, MULTIPLIER_MAX)

    Args:
        mean_brier_score: Mean Brier score over calibration sample [0.0, 1.0].
                          0.0 = perfect predictions; 0.5 = random baseline; 1.0 = worst.

    Returns:
        float: Multiplier in [MULTIPLIER_MIN, MULTIPLIER_MAX] = [0.8, 1.2].

    Raises:
        ValueError: If mean_brier_score is not in [0.0, 1.0].

    Examples:
        >>> compute_multiplier(0.3)   # better than random → boost
        1.02
        >>> compute_multiplier(0.5)   # random baseline → no change
        1.0
        >>> compute_multiplier(0.7)   # worse than random → down-weight
        0.98
    """
    if not (0.0 <= mean_brier_score <= 1.0):
        raise ValueError(
            f"mean_brier_score must be in [0.0, 1.0], got {mean_brier_score}"
        )
    raw = 1.0 + MULTIPLIER_SCALE * (BRIER_REFERENCE - mean_brier_score)
    return float(max(MULTIPLIER_MIN, min(MULTIPLIER_MAX, raw)))


def get_multiplier(
    technique: str,
    ayanamsha_id: str,
) -> Optional[dict[str, Any]]:
    """
    Retrieve the current multiplier for a (technique, ayanamsha_id) pair.

    Args:
        technique:    Classical technique name (e.g. 'vimshottari_dasha', 'kp_sub_lord').
        ayanamsha_id: Ayanamsha identifier (e.g. 'lahiri', 'raman', 'krishnamurti').

    Returns:
        dict with keys {technique, ayanamsha_id, multiplier, last_updated,
                        sample_size, source_citation, provenance_envelope}
        or None if no row exists for the pair.

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    db_url = _get_db_url()
    sql = """
        SELECT
            technique, ayanamsha_id, multiplier,
            last_updated, sample_size, source_citation
        FROM public.mimamsa_multipliers
        WHERE technique = %s AND ayanamsha_id = %s
    """

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [technique, ayanamsha_id])
            row = cur.fetchone()

    if row is None:
        return None

    queried_at = datetime.now(tz=timezone.utc).isoformat()
    return {
        "technique": row["technique"],
        "ayanamsha_id": row["ayanamsha_id"],
        "multiplier": float(row["multiplier"]),
        "last_updated": row["last_updated"].isoformat() if row["last_updated"] else None,
        "sample_size": row["sample_size"],
        "source_citation": row["source_citation"],
        "provenance_envelope": {
            "source": "mimamsa.multiplier",
            "asset": "MI-5-4",
            "algorithm": (
                f"CLAMP(1.0 + {MULTIPLIER_SCALE} × ({BRIER_REFERENCE} - mean_brier_score), "
                f"{MULTIPLIER_MIN}, {MULTIPLIER_MAX})"
            ),
            "l1_ground_truth": "FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes",
            "leakage_guard": "life_events used for calibration ONLY — never fed into prediction generation",
            "queried_at": queried_at,
            "b3_citation_compliant": bool(row["source_citation"]),
        },
    }


def list_multipliers() -> dict[str, Any]:
    """
    List all current multipliers in mimamsa_multipliers.

    Returns:
        {
            "ok": True,
            "multipliers": [...],
            "count": int,
            "provenance_envelope": {...}
        }

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    db_url = _get_db_url()
    sql = """
        SELECT
            technique, ayanamsha_id, multiplier,
            last_updated, sample_size, source_citation
        FROM public.mimamsa_multipliers
        ORDER BY technique ASC, ayanamsha_id ASC
    """

    rows: list[dict[str, Any]] = []
    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            for row in cur.fetchall():
                rows.append({
                    "technique": row["technique"],
                    "ayanamsha_id": row["ayanamsha_id"],
                    "multiplier": float(row["multiplier"]),
                    "last_updated": (
                        row["last_updated"].isoformat() if row["last_updated"] else None
                    ),
                    "sample_size": row["sample_size"],
                    "source_citation": row["source_citation"],
                })

    queried_at = datetime.now(tz=timezone.utc).isoformat()
    b3_compliant = all(bool(r["source_citation"]) for r in rows)

    return {
        "ok": True,
        "multipliers": rows,
        "count": len(rows),
        "provenance_envelope": {
            "source": "mimamsa.multiplier",
            "asset": "MI-5-4",
            "algorithm": (
                f"CLAMP(1.0 + {MULTIPLIER_SCALE} × ({BRIER_REFERENCE} - mean_brier_score), "
                f"{MULTIPLIER_MIN}, {MULTIPLIER_MAX})"
            ),
            "l1_ground_truth": "FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes",
            "leakage_guard": "life_events used for calibration ONLY — never fed into prediction generation",
            "queried_at": queried_at,
            "b3_citation_compliant": b3_compliant,
        },
    }


def update_multiplier(
    technique: str,
    ayanamsha_id: str,
    mean_brier_score: float,
    sample_size: int,
    source_citation: Optional[str] = None,
) -> dict[str, Any]:
    """
    Compute and upsert a learning multiplier for a (technique, ayanamsha_id) pair.

    CONTRACT:
        - sample_size must be > 0 (reject zero-sample updates)
        - source_citation must be non-null (B.3 mandate)
        - multiplier is clamped to [0.8, 1.2] before write
        - Idempotent: ON CONFLICT updates multiplier + last_updated + sample_size

    LEAKAGE GUARD:
        Life events (LEL) must only enter this function as pre-aggregated calibration
        statistics (mean_brier_score). The raw LEL event data MUST NOT be passed here
        or used in prediction generation. Only outcomes-already-observed feed calibration.

    Args:
        technique:         Classical technique name.
        ayanamsha_id:      Ayanamsha identifier.
        mean_brier_score:  Mean Brier score [0.0, 1.0] over sample_size outcomes.
        sample_size:       Number of resolved predictions used to compute mean_brier_score.
                           Must be > 0 to trigger an update.
        source_citation:   B.3 source citation. Defaults to DEFAULT_SOURCE_CITATION.

    Returns:
        {
            "ok": True,
            "technique": str,
            "ayanamsha_id": str,
            "multiplier": float,
            "mean_brier_score_used": float,
            "sample_size": int,
            "source_citation": str,
            "provenance_envelope": {...}
        }

    Raises:
        ValueError: sample_size <= 0; mean_brier_score out of [0.0, 1.0];
                    source_citation empty.
        RuntimeError: DATABASE_URL not configured.
    """
    # Guard: sample_size must be > 0
    if sample_size <= 0:
        raise ValueError(
            f"sample_size must be > 0 to trigger an update, got {sample_size}. "
            "A zero-sample update would corrupt the multiplier with no evidence."
        )

    # Guard: mean_brier_score range
    if not (0.0 <= mean_brier_score <= 1.0):
        raise ValueError(
            f"mean_brier_score must be in [0.0, 1.0], got {mean_brier_score}"
        )

    # Guard: source_citation non-null (B.3 mandate)
    effective_citation = source_citation or DEFAULT_SOURCE_CITATION
    if not effective_citation.strip():
        raise ValueError(
            "source_citation must be non-empty (B.3 mandate). "
            "Every mimamsa_multipliers row requires a traceable citation."
        )

    # Compute bounded multiplier
    multiplier = compute_multiplier(mean_brier_score)

    # Upsert into DB
    db_url = _get_db_url()
    sql = """
        INSERT INTO public.mimamsa_multipliers
            (technique, ayanamsha_id, multiplier, last_updated, sample_size, source_citation)
        VALUES
            (%s, %s, %s, NOW() AT TIME ZONE 'UTC', %s, %s)
        ON CONFLICT (technique, ayanamsha_id)
        DO UPDATE SET
            multiplier    = EXCLUDED.multiplier,
            last_updated  = EXCLUDED.last_updated,
            sample_size   = EXCLUDED.sample_size,
            source_citation = EXCLUDED.source_citation
        RETURNING technique, ayanamsha_id, multiplier, last_updated, sample_size, source_citation
    """

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [technique, ayanamsha_id, multiplier, sample_size, effective_citation])
            result_row = cur.fetchone()
        conn.commit()

    queried_at = datetime.now(tz=timezone.utc).isoformat()
    stored_multiplier = float(result_row["multiplier"]) if result_row else multiplier

    logger.info(
        "mimamsa.multiplier updated: technique=%s ayanamsha_id=%s "
        "mean_brier_score=%.4f sample_size=%d multiplier=%.4f",
        technique, ayanamsha_id, mean_brier_score, sample_size, stored_multiplier,
    )

    return {
        "ok": True,
        "technique": technique,
        "ayanamsha_id": ayanamsha_id,
        "multiplier": stored_multiplier,
        "mean_brier_score_used": mean_brier_score,
        "sample_size": sample_size,
        "source_citation": effective_citation,
        "provenance_envelope": {
            "source": "mimamsa.multiplier",
            "asset": "MI-5-4",
            "algorithm": (
                f"CLAMP(1.0 + {MULTIPLIER_SCALE} × ({BRIER_REFERENCE} - mean_brier_score), "
                f"{MULTIPLIER_MIN}, {MULTIPLIER_MAX})"
            ),
            "mean_brier_score_used": mean_brier_score,
            "l1_ground_truth": "FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes",
            "leakage_guard": (
                "life_events used for calibration ONLY — never fed into prediction generation"
            ),
            "queried_at": queried_at,
            "b3_citation_compliant": True,
        },
    }


def apply_multiplier(
    base_value: float,
    technique: str,
    ayanamsha_id: str,
    fallback_multiplier: float = 1.0,
) -> dict[str, Any]:
    """
    Apply the learning multiplier to a classical base value (L4 → L5 modulation).

    This is the primary L4 consumption interface. The classical layer value is
    MODULATED (multiplied), NOT overwritten.

    LEAKAGE GUARD: This function only reads from mimamsa_multipliers (calibration
    outcomes already encoded as a bounded float). It never sees raw LEL events or
    prediction inputs.

    Args:
        base_value:          The classical layer base score [0.0, 1.0] from L4 Phala.
        technique:           Classical technique name (must match mimamsa_multipliers key).
        ayanamsha_id:        Ayanamsha identifier.
        fallback_multiplier: Used when no row exists for (technique, ayanamsha_id).
                             Defaults to 1.0 (no modulation). Must be in [0.8, 1.2].

    Returns:
        {
            "modulated_value": float,   # base_value × multiplier, clamped to [0.0, 1.0]
            "base_value": float,
            "multiplier_applied": float,
            "technique": str,
            "ayanamsha_id": str,
            "fallback_used": bool,
            "provenance_envelope": {...}
        }

    Raises:
        ValueError: base_value out of [0.0, 1.0]; fallback_multiplier out of [0.8, 1.2].
        RuntimeError: DATABASE_URL not configured.
    """
    if not (0.0 <= base_value <= 1.0):
        raise ValueError(
            f"base_value must be in [0.0, 1.0], got {base_value}. "
            "L4 Phala base scores must be unit-interval."
        )
    if not (MULTIPLIER_MIN <= fallback_multiplier <= MULTIPLIER_MAX):
        raise ValueError(
            f"fallback_multiplier must be in [{MULTIPLIER_MIN}, {MULTIPLIER_MAX}], "
            f"got {fallback_multiplier}"
        )

    row = get_multiplier(technique, ayanamsha_id)

    if row is not None:
        multiplier = row["multiplier"]
        fallback_used = False
    else:
        multiplier = fallback_multiplier
        fallback_used = True
        logger.debug(
            "mimamsa.multiplier: no row for technique=%s ayanamsha_id=%s — using fallback %.2f",
            technique, ayanamsha_id, fallback_multiplier,
        )

    # Modulate classical layer (NOT overwrite)
    modulated_raw = base_value * multiplier
    modulated_value = float(max(0.0, min(1.0, modulated_raw)))

    queried_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "modulated_value": modulated_value,
        "base_value": base_value,
        "multiplier_applied": multiplier,
        "technique": technique,
        "ayanamsha_id": ayanamsha_id,
        "fallback_used": fallback_used,
        "provenance_envelope": {
            "source": "mimamsa.multiplier",
            "asset": "MI-5-4",
            "algorithm": "modulated = CLAMP(base_value × multiplier, 0.0, 1.0)",
            "multiplier_bounds": f"[{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]",
            "l1_ground_truth": "FORENSIC v8.0 §5.1; LEL v1.7 §Calibration-outcomes",
            "leakage_guard": (
                "life_events used for calibration ONLY — never fed into prediction generation"
            ),
            "queried_at": queried_at,
            "b3_citation_compliant": True,
        },
    }
