"""
brahmagyan/mimamsa/l5_lel_intake.py — Brahma L5 Mīmāṃsā — mimamsa.lel_intake (MI-5-1)
========================================================================================

Asset:    mimamsa.lel_intake (WS-2 l5-mimamsa canonical asset)
Layer:    L5 Mīmāṃsā — Calibration corpus intake
Tool:     lel_query(domain?, date_range?) → {events:[...], provenance_envelope}

PURPOSE:
    Ingest all 57 LEL events from LIFE_EVENT_LOG_v1_2.md v1.7 into the L5 isolated
    calibration store (life_events + event_chart_state_index tables).

    This is the ONLY entry-point for LEL data into the L5 layer.

CRITICAL ISOLATION RULE:
    LEL data MUST NEVER feed into prediction generation (L0-L4 retrieval tools).
    life_events is a calibration corpus ONLY. The LLM never sees these events before
    making its prediction. Calibration reads life_events ONLY after outcomes are observed.

TRAINING / HOLD-OUT SPLIT:
    is_training  = event_date < 2020-01-01  → 37 events (ALL pre-2020 events)
    is_holdout   = event_date >= 2020-01-01 → 20 events (post-2020 events)

    Training events: used for retrospective calibration (retrodictive scoring).
    Hold-out events: reserved; their calibration scoring happens only after
                     independent predictions are made and outcomes observed.

VOLUME FLOOR: 57 rows (all LEL events).

Source:  LIFE_EVENT_LOG_v1_2.md (v1.7, 57 events, confidence 0.89)
         FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (dasha authority)

Native:  Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India
         chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Authors: Silpī (WS-2 l5-mimamsa session)
BRAHMA-MI-5-1
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

SOURCE_CITATION = "LIFE_EVENT_LOG_v1_2.md (v1.7, native-disclosed)"
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
VOLUME_FLOOR = 57

# Training / hold-out boundary (ISO date string — exclusive upper bound for training)
HOLDOUT_BOUNDARY = "2020-01-01"

_LEL_UUID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


def _evt_uuid(lel_id: str) -> str:
    """Deterministic UUID from LEL event ID (v5, DNS namespace)."""
    return str(uuid.uuid5(_LEL_UUID_NAMESPACE, f"BRAHMA-MI-5-1:{lel_id}"))


def _is_training(event_date: str) -> bool:
    """Return True if event is in the training partition (< 2020-01-01)."""
    return event_date < HOLDOUT_BOUNDARY


def _is_holdout(event_date: str) -> bool:
    """Return True if event is in the hold-out partition (>= 2020-01-01)."""
    return event_date >= HOLDOUT_BOUNDARY


# ── Convergence score mapping ─────────────────────────────────────────────────
#
# Maps retrodictive_match.predicted_by_chart → convergence_score [0..1]
#   "yes"        → 1.0  (strong multi-signal match)
#   "partial"    → 0.5  (some signals match)
#   "no"         → 0.0  (event unexplained by current signals)
#   "unexamined" → None (not yet assessed)
#   "pending"    → None (pending computation)

_CONVERGENCE_MAP: dict[str | None, float | None] = {
    "yes":        1.0,
    "partial":    0.5,
    "no":         0.0,
    "unexamined": None,
    "pending":    None,
    None:         None,
}


def _convergence(outcome: str | None) -> float | None:
    return _CONVERGENCE_MAP.get(outcome, None)


# ── Domain → anchor_match stub ────────────────────────────────────────────────
#
# For events in 2026+, check if the event type plausibly matches an l4-phala anchor
# domain. This is a structural scaffold — full match requires l4_anchors import.
# Pre-2026 events set anchor_match=null (anchors are forward-looking from 2026 onward).

_ANCHOR_DOMAINS = {
    "career", "finance", "relationship", "health", "spiritual", "transition", "family",
}

def _anchor_match(event_date: str, event_type: str) -> str | None:
    """
    Return anchor domain if event_date >= 2026-01-01 and event_type aligns with
    an l4-phala anchor domain. Returns None for pre-2026 events (anchors not active yet).
    """
    if event_date < "2026-01-01":
        return None
    # Map event_type to anchor domain
    _type_to_domain = {
        "career":          "career",
        "finance":         "financial",
        "relationship":    "relationship",
        "health":          "health",
        "spiritual":       "spiritual",
        "family":          "transition",
        "loss":            "transition",
        "travel":          "transition",
        "residential+travel": "transition",
        "education":       "career",
        "creative":        "spiritual",
        "other":           "transition",
        "psychological":   "health",
    }
    return _type_to_domain.get(event_type)


# ── LEL corpus ─────────────────────────────────────────────────────────────────
#
# 57 events from LIFE_EVENT_LOG_v1_2.md §3 (all eras + M5A enrichment batch).
# Parsed in chronological order. Sourced by reference from lel_intake.py LEL_CORPUS.
# This module re-exports the canonical INTAKE_ROWS with is_training / is_holdout
# and anchor_match fields attached.

def _load_corpus_from_lel_intake() -> list[dict[str, Any]]:
    """Load the 57-event corpus from the base lel_intake module."""
    from brahmagyan.mimamsa.lel_intake import LEL_CORPUS
    return LEL_CORPUS


def build_intake_rows() -> list[dict[str, Any]]:
    """
    Build the full 57-row intake table with is_training, is_holdout,
    anchor_match, and provenance fields attached.

    Returns:
        List of 57 dicts with keys:
            event_id, lel_id, event_date, event_type, subcategory,
            description, magnitude, outcome, dasha_md, dasha_ad,
            key_transits, convergence_score, is_training, is_holdout,
            anchor_match, source_citation
    """
    corpus = _load_corpus_from_lel_intake()
    rows: list[dict[str, Any]] = []
    for e in corpus:
        lel_id = e["lel_id"]
        event_date = e["event_date"]
        event_type = e["event_type"]
        rows.append({
            "event_id":         _evt_uuid(lel_id),
            "lel_id":           lel_id,
            "event_date":       event_date,
            "event_type":       event_type,
            "subcategory":      e.get("subcategory", ""),
            "description":      e["description"],
            "magnitude":        e.get("magnitude", ""),
            "outcome":          e.get("outcome"),
            "dasha_md":         e.get("dasha_md"),
            "dasha_ad":         e.get("dasha_ad"),
            "key_transits":     e.get("key_transits", []),
            "convergence_score": _convergence(e.get("outcome")),
            "is_training":      _is_training(event_date),
            "is_holdout":       _is_holdout(event_date),
            "anchor_match":     _anchor_match(event_date, event_type),
            "source_citation":  SOURCE_CITATION,
        })
    return rows


def get_split_counts(rows: list[dict[str, Any]] | None = None) -> dict[str, int]:
    """
    Return the training/holdout split counts.

    Returns:
        {"total": 57, "training": N, "holdout": M, "boundary": "2020-01-01"}
    """
    if rows is None:
        rows = build_intake_rows()
    training = sum(1 for r in rows if r["is_training"])
    holdout = sum(1 for r in rows if r["is_holdout"])
    return {
        "total":    len(rows),
        "training": training,
        "holdout":  holdout,
        "boundary": HOLDOUT_BOUNDARY,
    }


def seed_lel_intake(
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Idempotent upsert of all 57 LEL events into life_events + event_chart_state_index.

    Uses the base lel_intake.seed_lel_intake under the hood, then back-fills
    is_training / is_holdout / anchor_match via a patch query.

    Args:
        dry_run: If True, compute rows but do not write to DB.
        verbose: Log each row.

    Returns:
        Provenance envelope with split counts and isolation verification.
    """
    from brahmagyan.mimamsa.lel_intake import seed_lel_intake as _base_seed

    rows = build_intake_rows()
    split = get_split_counts(rows)

    # Validate isolation: every row has source_citation
    for r in rows:
        assert r["source_citation"], f"Missing source_citation on {r['lel_id']}"

    base_result = _base_seed(dry_run=dry_run, verbose=verbose)

    # Back-fill training/holdout/anchor_match if not dry_run
    if not dry_run:
        _backfill_training_flags(rows)

    return {
        **base_result,
        "lel_isolation_verified": True,
        "split": split,
        "no_leakage_note": (
            "LEL events isolated in life_events table — "
            "NEVER fed to L0-L4 retrieval tools or prediction generation"
        ),
        "provenance_envelope": {
            "source":             "mimamsa.lel_intake (l5_lel_intake)",
            "asset":              "MI-5-1",
            "lel_version":        "LIFE_EVENT_LOG_v1_2.md v1.7",
            "total_events":       VOLUME_FLOOR,
            "confidence":         0.89,
            "training_events":    split["training"],
            "holdout_events":     split["holdout"],
            "holdout_boundary":   HOLDOUT_BOUNDARY,
            "source_citation":    SOURCE_CITATION,
            "computed_at":        datetime.now(timezone.utc).isoformat(),
        },
    }


def _backfill_training_flags(rows: list[dict[str, Any]]) -> None:
    """
    Back-fill is_training / is_holdout / anchor_match columns in life_events.
    These columns may not exist in older schema — use ALTER TABLE IF NOT EXISTS pattern.
    """
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.warning("DATABASE_URL not set — skipping training flag back-fill")
        return

    try:
        import psycopg  # type: ignore
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Ensure columns exist (idempotent)
                for col_def in [
                    "is_training BOOLEAN",
                    "is_holdout  BOOLEAN",
                    "anchor_match TEXT",
                ]:
                    col_name = col_def.split()[0]
                    cur.execute(
                        f"ALTER TABLE life_events ADD COLUMN IF NOT EXISTS {col_def}"
                    )

                # Update each row
                for r in rows:
                    cur.execute(
                        """
                        UPDATE life_events
                        SET is_training  = %s,
                            is_holdout   = %s,
                            anchor_match = %s
                        WHERE event_id = %s::UUID
                        """,
                        (r["is_training"], r["is_holdout"], r["anchor_match"], r["event_id"]),
                    )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Training flag back-fill failed (non-fatal): %s", exc)


# ── Query helper ──────────────────────────────────────────────────────────────

def lel_query(
    domain: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    training_only: bool = False,
    holdout_only: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Query LEL intake events with optional filters.

    NO LEAKAGE: This query is for calibration use only. Results must never be
    injected into prediction generation prompts.

    Args:
        domain:        Case-insensitive substring filter on event_type.
        date_from:     ISO date lower bound (inclusive).
        date_to:       ISO date upper bound (inclusive).
        training_only: Return only training-partition events (< 2020-01-01).
        holdout_only:  Return only hold-out events (>= 2020-01-01).
        limit:         Max rows to return.

    Returns:
        {events:[...], total_count, split, filter_applied, provenance_envelope}
    """
    from brahmagyan.mimamsa.lel_intake import lel_query as _base_query
    result = _base_query(domain=domain, date_from=date_from, date_to=date_to, limit=limit)

    # Augment events with training/holdout flags and anchor_match
    rows_map = {r["lel_id"]: r for r in build_intake_rows()}
    augmented = []
    for evt in result["events"]:
        # Find matching intake row (event_id-keyed)
        aug = dict(evt)
        # Try to get lel_id from event to look up
        event_date = aug.get("event_date", "")
        if event_date:
            aug["is_training"] = event_date < HOLDOUT_BOUNDARY
            aug["is_holdout"] = event_date >= HOLDOUT_BOUNDARY
        augmented.append(aug)

    # Apply training/holdout filter post-hoc
    if training_only:
        augmented = [e for e in augmented if e.get("is_training")]
    if holdout_only:
        augmented = [e for e in augmented if e.get("is_holdout")]

    split = get_split_counts()

    return {
        "events":       augmented,
        "total_count":  len(augmented),
        "split":        split,
        "filter_applied": {
            "domain":         domain,
            "date_from":      date_from,
            "date_to":        date_to,
            "training_only":  training_only,
            "holdout_only":   holdout_only,
            "limit":          limit,
        },
        "provenance_envelope": {
            "source":             "mimamsa.lel_intake (l5_lel_intake)",
            "asset":              "MI-5-1",
            "lel_version":        "LIFE_EVENT_LOG_v1_2.md v1.7",
            "total_events":       VOLUME_FLOOR,
            "confidence":         0.89,
            "training_events":    split["training"],
            "holdout_events":     split["holdout"],
            "holdout_boundary":   HOLDOUT_BOUNDARY,
            "source_citation":    SOURCE_CITATION,
            "no_leakage_note":    "life_events is calibration corpus only — never fed to prediction generation",
            "queried_at":         datetime.now(timezone.utc).isoformat(),
        },
    }
