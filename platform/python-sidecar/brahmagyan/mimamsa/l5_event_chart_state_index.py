"""
brahmagyan/mimamsa/l5_event_chart_state_index.py — Brahma L5 Mīmāṃsā — event_chart_state_index (MI-5-2)
=========================================================================================================

Asset:    mimamsa.event_chart_state_index (WS-2 l5-mimamsa canonical asset)
Layer:    L5 Mīmāṃsā — Full chart-state index per LEL event
Tool:     query_event_chart_state(event_id?, lel_id?, date?) → {chart_state, provenance_envelope}

PURPOSE:
    For each of the 57 LEL events, compute the FULL chart state from L1/L2/L3 data:
      - Active Vimshottari dasha (MD + AD, with PD where available)
      - Active slow transits (Saturn, Jupiter, Rahu/Ketu sign positions)
      - Active convergence windows from l3-kala (if any overlap with event date)
      - Active obstruction periods from l3-kala (if any overlap with event date)
      - L2 signal activations: which of the 569 UNGROUNDED signals have documented
        retrodictive_match for this event (from LEL §3 retrodictive_match fields)

    This is the substrate for calibration: when outcomes are observed, chart_state
    tells us which signals were active and whether they correctly predicted the outcome.

VOLUME FLOOR: 57 index entries (one per LEL event).

ISOLATION RULE:
    This index is computed FROM L1 data (LEL + FORENSIC) and L3 data (kala windows).
    It must NEVER feed into prediction generation — it is consumed ONLY by calibration.

Source:  LIFE_EVENT_LOG_v1_2.md v1.7 (all chart_state_at_event blocks)
         FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (Vimshottari dasha authority)
         l3_convergence.py SIGNAL_ANCHORS (convergence window catalog)
         l3_obstruction.py SADE_SATI_WINDOWS + MALEFIC_CLUSTERS (obstruction catalog)
         l2_signals_scaffold.py VOLUME_FLOOR=569 UNGROUNDED signals

Native:  Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India
         chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Authors: Silpī (WS-2 l5-mimamsa session)
BRAHMA-MI-5-2
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_CITATION = (
    "LIFE_EVENT_LOG_v1_2.md v1.7; "
    "FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md); "
    "l3_convergence.py SIGNAL_ANCHORS; "
    "l3_obstruction.py SADE_SATI_WINDOWS; "
    "l2_signals_scaffold.py"
)
VOLUME_FLOOR = 57

# ── L3 data import (graceful fallback if not available) ───────────────────────

def _get_convergence_windows() -> list[dict[str, Any]]:
    """Load convergence windows from l3-kala layer."""
    try:
        from brahmagyan.kala.l3_convergence import SIGNAL_ANCHORS  # type: ignore
        return [
            {
                "window_id":       a.get("anchor_id", ""),
                "start":           a.get("start", ""),
                "end":             a.get("end", ""),
                "convergence_type": a.get("convergence_type", ""),
                "signals":         a.get("signal_ids", []),
            }
            for a in SIGNAL_ANCHORS
        ]
    except (ImportError, AttributeError):
        logger.debug("l3_convergence.SIGNAL_ANCHORS not available — using empty window list")
        return []


def _get_obstruction_periods() -> list[dict[str, Any]]:
    """Load obstruction periods from l3-kala layer."""
    try:
        from brahmagyan.kala.l3_obstruction import SADE_SATI_WINDOWS, MALEFIC_CLUSTERS  # type: ignore
        windows = [
            {
                "period_id":   w.get("period_id", ""),
                "start":       w.get("start", ""),
                "end":         w.get("end", ""),
                "type":        "sade_sati",
                "phase":       w.get("phase", ""),
            }
            for w in SADE_SATI_WINDOWS
        ]
        clusters = [
            {
                "period_id":   c.get("cluster_id", ""),
                "start":       c.get("start", ""),
                "end":         c.get("end", ""),
                "type":        "malefic_cluster",
                "phase":       c.get("planets", ""),
            }
            for c in MALEFIC_CLUSTERS
        ]
        return windows + clusters
    except (ImportError, AttributeError):
        logger.debug("l3_obstruction data not available — using empty obstruction list")
        return []


# ── Slow transit positions (from LEL chart_state_at_event data) ───────────────
#
# These are derived from the LEL corpus key_transits fields and dasha data.
# The LEL corpus already carries the authoritative transit notes per FORENSIC §5.1
# and Swiss Ephemeris derivations (populated in LEL v1.2+).

def _extract_transit_state(event: dict[str, Any]) -> dict[str, Any]:
    """
    Extract slow-transit state from a LEL corpus entry.
    Returns structured Saturn/Jupiter/Rahu-Ketu positions where parseable,
    else returns the raw transit note strings.
    """
    transits = event.get("key_transits", [])

    saturn_note = next((t for t in transits if "Saturn" in t), None)
    jupiter_note = next((t for t in transits if "Jupiter" in t), None)
    rahu_note = next((t for t in transits if "Rahu" in t), None)
    ketu_note = next((t for t in transits if "Ketu" in t), None)

    return {
        "saturn":  saturn_note,
        "jupiter": jupiter_note,
        "rahu":    rahu_note,
        "ketu":    ketu_note,
        "all":     transits,
    }


# ── Window overlap helper ─────────────────────────────────────────────────────

def _windows_active_at(event_date: str, windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return windows whose (start, end) range includes event_date.
    Comparison is lexicographic on ISO date strings (YYYY-MM-DD).
    """
    active = []
    for w in windows:
        start = w.get("start", "")
        end = w.get("end", "")
        if start and end:
            if start <= event_date <= end:
                active.append(w)
        elif start and not end:
            if event_date >= start:
                active.append(w)
    return active


# ── L2 signal activations ─────────────────────────────────────────────────────
#
# For each event, extract which L2 signals were documented in the LEL
# retrodictive_match.signals_that_matched list.
# NOTE: The LEL contains only the 15 deep-analysis signals (SIG.01-SIG.15 + CVG.*/CTR.*)
# The full 569 UNGROUNDED MSR signals are awaiting WS-3 grounding.
# This field therefore contains the LEL-documented signal activations only.

def _extract_signal_activations(event: dict[str, Any]) -> dict[str, Any]:
    """
    Extract signal activations from the LEL corpus entry.
    The LEL corpus (via lel_intake.py) carries pre-aggregated outcome/convergence scores
    but NOT the full retrodictive signal lists (those are in the raw MD source).

    Returns a structured dict with outcome and convergence_score as proxies for
    signal activation density.
    """
    outcome = event.get("outcome")
    convergence = {
        "yes":        1.0,
        "partial":    0.5,
        "no":         0.0,
        "unexamined": None,
        "pending":    None,
        None:         None,
    }.get(outcome)

    # Signal activation scaffold — pre-2020 events have LEL-documented retrodictive matches;
    # post-2020 events have outcome markers but signal activation awaits WS-3 grounding.
    activation_note = (
        "LEL retrodictive signals — see LIFE_EVENT_LOG_v1_2.md §3 per event"
        if outcome in ("yes", "partial", "no")
        else "Awaiting retrodictive assessment or WS-3 grounding"
    )

    return {
        "convergence_score":   convergence,
        "outcome_observed":    outcome,
        "l2_activation_note":  activation_note,
        "ungrounded_signals":  569,  # total L2 scaffold signals — all UNGROUNDED pending WS-3
    }


# ── Build index ───────────────────────────────────────────────────────────────

def build_event_chart_state_index() -> list[dict[str, Any]]:
    """
    Build the full 57-entry chart state index.

    Each entry contains:
        lel_id, event_date, vimshottari (md/ad), slow_transits,
        active_convergence_windows, active_obstruction_periods,
        l2_signal_activations, is_training, is_holdout, source_citation

    Volume floor: 57 entries.

    Returns:
        List of 57 dicts.
    """
    from brahmagyan.mimamsa.l5_lel_intake import build_intake_rows, HOLDOUT_BOUNDARY

    intake = build_intake_rows()
    convergence_windows = _get_convergence_windows()
    obstruction_periods = _get_obstruction_periods()

    index: list[dict[str, Any]] = []

    for row in intake:
        lel_id = row["lel_id"]
        event_date = row["event_date"]

        # Vimshottari state (from LEL corpus dasha fields)
        vimshottari = {
            "md":   row.get("dasha_md"),
            "ad":   row.get("dasha_ad"),
        }

        # Slow transit state (from key_transits field)
        slow_transits = _extract_transit_state(row)

        # Active convergence windows
        active_conv = _windows_active_at(event_date, convergence_windows)

        # Active obstruction periods
        active_obs = _windows_active_at(event_date, obstruction_periods)

        # L2 signal activations
        signal_act = _extract_signal_activations(row)

        index.append({
            "event_id":                   row["event_id"],
            "lel_id":                     lel_id,
            "event_date":                 event_date,
            "vimshottari":                vimshottari,
            "slow_transits":              slow_transits,
            "active_convergence_windows": active_conv,
            "active_obstruction_periods": active_obs,
            "l2_signal_activations":      signal_act,
            "is_training":                row["is_training"],
            "is_holdout":                 row["is_holdout"],
            "source_citation":            SOURCE_CITATION,
        })

    return index


def query_event_chart_state(
    event_id: str | None = None,
    lel_id: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    """
    Query the chart state for a specific LEL event.

    Args:
        event_id: UUID of the event (from life_events table).
        lel_id:   EVT.* identifier from LEL (e.g. 'EVT.2018.11.28.01').
        date:     ISO date string — returns first event on this date.

    Returns:
        {chart_state: {...}, provenance_envelope: {...}}
        or {error: "not found", ...} if no match.
    """
    index = build_event_chart_state_index()

    match = None
    if lel_id:
        match = next((e for e in index if e["lel_id"] == lel_id), None)
    elif event_id:
        match = next((e for e in index if e["event_id"] == event_id), None)
    elif date:
        match = next((e for e in index if e["event_date"].startswith(date)), None)

    if match is None:
        return {
            "error": "event not found",
            "query": {"event_id": event_id, "lel_id": lel_id, "date": date},
            "provenance_envelope": _provenance_envelope(),
        }

    return {
        "chart_state": match,
        "provenance_envelope": _provenance_envelope(),
    }


def get_index_stats(index: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Return summary statistics for the chart state index.

    Returns:
        {total, training, holdout, with_convergence_window, with_obstruction, ...}
    """
    if index is None:
        index = build_event_chart_state_index()

    training = sum(1 for e in index if e["is_training"])
    holdout = sum(1 for e in index if e["is_holdout"])
    with_conv = sum(1 for e in index if e["active_convergence_windows"])
    with_obs = sum(1 for e in index if e["active_obstruction_periods"])
    with_dasha_md = sum(1 for e in index if e["vimshottari"].get("md"))

    return {
        "total":                  len(index),
        "training":               training,
        "holdout":                holdout,
        "with_convergence_window": with_conv,
        "with_obstruction":       with_obs,
        "with_dasha_md":          with_dasha_md,
        "volume_floor_met":       len(index) >= VOLUME_FLOOR,
    }


def _provenance_envelope() -> dict[str, Any]:
    return {
        "source":           "mimamsa.event_chart_state_index (l5_event_chart_state_index)",
        "asset":            "MI-5-2",
        "lel_version":      "LIFE_EVENT_LOG_v1_2.md v1.7",
        "total_events":     VOLUME_FLOOR,
        "l2_signal_count":  569,
        "l2_grounding":     "UNGROUNDED scaffold — awaiting WS-3 rule_base",
        "source_citation":  SOURCE_CITATION,
        "no_leakage_note":  "chart_state_index is calibration substrate only — never fed to prediction generation",
        "queried_at":       datetime.now(timezone.utc).isoformat(),
    }


# ── DB upsert ─────────────────────────────────────────────────────────────────

def seed_event_chart_state_index(
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Upsert the 57-entry chart state index into event_chart_state_index table.

    Extends the base event_chart_state_index rows with:
        - active_convergence_windows (JSONB)
        - active_obstruction_periods (JSONB)
        - l2_signal_activations (JSONB)
        - is_training (BOOLEAN)
        - is_holdout (BOOLEAN)

    Args:
        dry_run: Compute but do not write to DB.
        verbose: Log each row.

    Returns:
        Provenance envelope with volume floor check.
    """
    import json as _json

    index = build_event_chart_state_index()
    stats = get_index_stats(index)

    if verbose:
        for e in index:
            logger.info(
                "[chart_state_index] %s | dasha: %s/%s | conv_windows: %d | obs: %d | training: %s",
                e["lel_id"],
                e["vimshottari"].get("md"),
                e["vimshottari"].get("ad"),
                len(e["active_convergence_windows"]),
                len(e["active_obstruction_periods"]),
                e["is_training"],
            )

    if dry_run:
        logger.info(
            "[dry_run] Would upsert %d rows into event_chart_state_index",
            len(index),
        )
        return {
            "dry_run":          True,
            "total":            len(index),
            "stats":            stats,
            "volume_floor_met": stats["volume_floor_met"],
            "provenance_envelope": _provenance_envelope(),
        }

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.warning("DATABASE_URL not set — cannot seed event_chart_state_index")
        return {
            "skipped":          True,
            "reason":           "DATABASE_URL not set",
            "total":            len(index),
            "stats":            stats,
            "provenance_envelope": _provenance_envelope(),
        }

    try:
        import psycopg  # type: ignore

        upserted = 0
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Ensure extended columns exist
                for col_def in [
                    "active_convergence_windows JSONB",
                    "active_obstruction_periods JSONB",
                    "l2_signal_activations      JSONB",
                    "is_training                BOOLEAN",
                    "is_holdout                 BOOLEAN",
                ]:
                    cur.execute(
                        f"ALTER TABLE event_chart_state_index "
                        f"ADD COLUMN IF NOT EXISTS {col_def}"
                    )

                for e in index:
                    cur.execute(
                        """
                        INSERT INTO event_chart_state_index
                            (event_id, dasha_active, antardasha_active,
                             key_transits, convergence_score, source_citation,
                             active_convergence_windows, active_obstruction_periods,
                             l2_signal_activations, is_training, is_holdout)
                        VALUES (
                            %s, %s, %s, %s::JSONB, %s, %s,
                            %s::JSONB, %s::JSONB, %s::JSONB, %s, %s
                        )
                        ON CONFLICT (event_id) DO UPDATE SET
                            dasha_active                = EXCLUDED.dasha_active,
                            antardasha_active           = EXCLUDED.antardasha_active,
                            key_transits                = EXCLUDED.key_transits,
                            convergence_score           = EXCLUDED.convergence_score,
                            source_citation             = EXCLUDED.source_citation,
                            active_convergence_windows  = EXCLUDED.active_convergence_windows,
                            active_obstruction_periods  = EXCLUDED.active_obstruction_periods,
                            l2_signal_activations       = EXCLUDED.l2_signal_activations,
                            is_training                 = EXCLUDED.is_training,
                            is_holdout                  = EXCLUDED.is_holdout
                        """,
                        (
                            e["event_id"],
                            e["vimshottari"].get("md"),
                            e["vimshottari"].get("ad"),
                            _json.dumps(e["slow_transits"]["all"]),
                            e["l2_signal_activations"]["convergence_score"],
                            SOURCE_CITATION,
                            _json.dumps(e["active_convergence_windows"]),
                            _json.dumps(e["active_obstruction_periods"]),
                            _json.dumps(e["l2_signal_activations"]),
                            e["is_training"],
                            e["is_holdout"],
                        ),
                    )
                    upserted += 1

            conn.commit()

        logger.info("event_chart_state_index: upserted %d rows", upserted)
        return {
            "upserted":          upserted,
            "total":             len(index),
            "stats":             stats,
            "volume_floor_met":  stats["volume_floor_met"],
            "provenance_envelope": _provenance_envelope(),
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("event_chart_state_index seed failed: %s", exc)
        return {
            "error":             str(exc),
            "total":             len(index),
            "stats":             stats,
            "provenance_envelope": _provenance_envelope(),
        }
