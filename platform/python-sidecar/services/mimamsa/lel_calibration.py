"""
LEL availability-driven calibration primitives (BA Phase-4 R2.2 / W2.2).

Pure, deterministic decision logic shared by the L4/L5 writers so that
per-chart behaviour is driven by DATA AVAILABILITY (does this chart have
recorded life events?) rather than by CHART IDENTITY (is this the native?).
Killing the `chart_id == NATIVE_CHART_ID` branches removes a silent-error class:
identity gates silently do the wrong thing for any chart that is not the one
they were written for.

Everything here is a pure function of its arguments (no clock, no DB, no env
read except the explicit `pool_enabled()` gate which takes an override for
testing). The single thin DB helper `count_chart_lel_events` is the only
IO-touching function and is trivially fixture-mockable.

NOTHING here writes to the DB or mutates state — callers own persistence.

Post-migration-423 contract this assumes:
  - life_events is chart-scoped: (chart_id, event_id) keyed, chart_id NOT NULL.
  - recorded_at (timestamptz) = when a row entered the instrument (NOT when the
    event occurred). The 57 native rows carry a `pre_instrument` sentinel.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

# ── Calibration state machine ────────────────────────────────────────────────
#
# structural  — no recorded life events; predictions rest on chart structure
#               only (no empirical LEL fit). This is the CORRECT resting state
#               for a fresh chart (e.g. Abhinandan at W3), not an error.
# sparse      — some events, but too few to calibrate reliability bins.
# calibrated  — enough events that per-chart calibration is meaningful.
#
# CALIBRATED_MIN_EVENTS is a tunable — record it as a brahma_formula_constant
# ('mimamsa_calibration_min_events', class=engineering) when the persistence
# migration lands. Chosen so a 2-event synthetic round-trip reads as `sparse`
# (W3 Abhinandan round-trip gate: structural→sparse→structural) and the native's
# 57 events read as `calibrated`.
STATE_STRUCTURAL = "structural"
STATE_SPARSE = "sparse"
STATE_CALIBRATED = "calibrated"

CALIBRATED_MIN_EVENTS = 10

BASIS_STRUCTURAL_NO_LEL = "structural_no_lel"
BASIS_LEL_FIT = "lel_fit"


def calibration_state(event_count: int) -> str:
    """Map a chart's recorded LEL event count to its calibration state."""
    if event_count < 0:
        raise ValueError(f"event_count must be >= 0, got {event_count}")
    if event_count == 0:
        return STATE_STRUCTURAL
    if event_count < CALIBRATED_MIN_EVENTS:
        return STATE_SPARSE
    return STATE_CALIBRATED


def rectification_basis(event_count: int) -> str:
    """Rectification basis for a chart: LEL-fit iff it has any own life events."""
    return BASIS_LEL_FIT if event_count > 0 else BASIS_STRUCTURAL_NO_LEL


def is_load_bearing(event_count: int) -> bool:
    """Whether LEL-derived calibration should be treated as load-bearing.

    Only a `calibrated` chart's empirical calibration is load-bearing; sparse /
    structural charts surface predictions as structural (probabilistic, not
    empirically calibrated) so serve-time never over-claims.
    """
    return calibration_state(event_count) == STATE_CALIBRATED


def judgment_flags(event_count: int) -> dict[str, Any]:
    """Assemble the per-chart calibration judgment flags.

    This is the structured surface a writer stamps onto its output (a JSONB
    judgment_flags column once the persistence migration lands). Deterministic
    in `event_count` alone.
    """
    state = calibration_state(event_count)
    return {
        "calibration": state,
        "calibration_state": state,
        "rectification_basis": rectification_basis(event_count),
        "lel_event_count": event_count,
        "load_bearing": state == STATE_CALIBRATED,
    }


# ── recorded_at leakage routing (code, not convention) ───────────────────────
#
# A recorded event is TRAINING evidence iff it was recorded into the instrument
# BEFORE the prediction snapshot it is being compared against; it is OUTCOME
# evidence iff recorded AFTER. This is the two-key blind path: an outcome can
# only score a prediction that was frozen before the outcome was recorded.
# Enforcing it in code (not by naming convention) is the leakage firewall.
PARTITION_TRAINING = "training"
PARTITION_OUTCOME = "outcome"

# Rows recorded at/at-before this sentinel are pre-instrument (the native's 57
# were recorded before any prediction existed) → always pure training.
PRE_INSTRUMENT_SENTINEL = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _as_aware(dt: datetime) -> datetime:
    """Coerce a datetime to tz-aware UTC (naive is assumed UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def recorded_at_partition(
    recorded_at: datetime,
    snapshot_at: Optional[datetime],
) -> str:
    """Classify an event row as training vs outcome for a given prediction snapshot.

    Args:
        recorded_at:  when the LEL row entered the instrument.
        snapshot_at:  when the prediction being scored was frozen. None means
                      there is no prediction yet → everything is training.

    Rule: recorded strictly BEFORE the snapshot → training; at/after → outcome.
    Pre-instrument sentinel rows are always training.
    """
    r = _as_aware(recorded_at)
    if r <= PRE_INSTRUMENT_SENTINEL:
        return PARTITION_TRAINING
    if snapshot_at is None:
        return PARTITION_TRAINING
    s = _as_aware(snapshot_at)
    return PARTITION_TRAINING if r < s else PARTITION_OUTCOME


# ── Cross-chart pool gate (capture now, consume gated) ───────────────────────
#
# Per-chart consent (pool_consent) is captured at intake, but a chart's events
# are only ever CONSUMED into the cross-chart calibration pool when the pool is
# explicitly switched on. Default OFF — no chart contributes silently.
POOL_ENV_VAR = "MIMAMSA_CROSS_CHART_POOL"
_POOL_ON_VALUES = {"on", "1", "true", "yes", "enabled"}


def pool_enabled(override: Optional[str] = None) -> bool:
    """Whether the cross-chart calibration pool is switched on. Default OFF."""
    raw = override if override is not None else os.environ.get(POOL_ENV_VAR, "off")
    return str(raw).strip().lower() in _POOL_ON_VALUES


def may_consume_into_pool(pool_consent: bool, override: Optional[str] = None) -> bool:
    """A chart's events may enter the pool iff consent is given AND pool is on.

    Both keys required: capture-now (consent) is necessary but not sufficient;
    the global gate must also be on. This is the consume-side firewall.
    """
    return bool(pool_consent) and pool_enabled(override)


# ── Debounced save → targeted-recalibration trigger ──────────────────────────
#
# LEL saves arrive in bursts (a native editing several events). Recalibration is
# expensive, so it is debounced: after the LAST save in a burst settles for
# `debounce_seconds`, one targeted recalibration runs. Pure predicate — the
# caller owns the clock and passes `now`.
DEFAULT_DEBOUNCE_SECONDS = 90.0


def should_recalibrate(
    last_saved_at: Optional[datetime],
    last_recalibrated_at: Optional[datetime],
    now: datetime,
    debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
) -> bool:
    """Whether a targeted recalibration is due.

    True iff there is an unprocessed save (a save newer than the last
    recalibration, or never recalibrated) AND the debounce window has elapsed
    since that save (the burst has settled).
    """
    if last_saved_at is None:
        return False
    saved = _as_aware(last_saved_at)
    now_a = _as_aware(now)
    # Nothing new since the last recalibration → nothing to do.
    if last_recalibrated_at is not None and saved <= _as_aware(last_recalibrated_at):
        return False
    # Still inside the debounce window → wait for the burst to settle.
    return (now_a - saved).total_seconds() >= debounce_seconds


# ── Thin DB helper (the only IO here) ────────────────────────────────────────

def count_chart_lel_events(conn: Any, chart_id: str) -> int:
    """Count THIS chart's recorded life events (post-423 chart-scoped).

    Availability-driven: no chart-identity check. If the chart_id column is not
    present yet (pre-migration environment) the count is reported as 0 for any
    non-legacy path — callers must treat a pre-migration schema as "unknown /
    structural" rather than silently counting another chart's rows. Never
    fabricates; a missing table/column yields 0.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM life_events WHERE chart_id = %s",
                (chart_id,),
            )
            row = cur.fetchone()
    except Exception:
        return 0
    if not row:
        return 0
    # Support both tuple and dict row factories.
    try:
        return int(row[0])
    except (KeyError, TypeError):
        return int(next(iter(row.values())))
