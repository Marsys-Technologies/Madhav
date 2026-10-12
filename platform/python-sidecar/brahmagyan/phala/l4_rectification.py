"""
brahmagyan/phala/l4_rectification.py — Brahma L4 Phala — phala.rectification framework (PH-4-3-v2)
====================================================================================================

Asset:    phala.rectification (v2 — LEL train/test split framework)
Tool:     query_rectification_framework(chart_id, source) →
              {birth, train_events, holdout_events, candidate window, methodology, provenance}

PURPOSE: Birth-time rectification framework for the REQUESTED chart, built from that chart's
own `charts` row (birth details) and its own Life Event Log rows (`life_events`).

NATIVE-DATA POLICY (SS N-384, PR-S6): this module embeds NO chart's birth details and NO life
events. Everything it returns is read, for the chart_id in the request, from the database through
a `RectificationSource`:

  * birth details      -> the `charts` row of that chart (read-only);
  * life events        -> `brahmagyan.phala.life_events_scope.fetch_chart_life_events`, the one
                          sanctioned, chart-scoped, read-only door to `life_events` (SS N-105).
                          Only the minimal columns (event_id, event_date, category, domain) are
                          read; the private free-text description is never selected (SS N-109).

A chart with no row, or with no dated life events of its own, gets an honest `not_available`
answer (or a 404 for an unknown chart). It never gets another chart's data.

CRITICAL LEAKAGE PREVENTION (unchanged):
  - TRAINING SET: this chart's events dated BEFORE 2020-01-01 only.
  - HOLD-OUT SET: this chart's events dated 2020-01-01 onwards.
  - A fit never uses hold-out events; they are published for FUTURE verification only
    (Learning Layer rule #4, binding).

METHODOLOGY:
  Rectification fits a birth-time window (±30 minutes around the recorded birth time) by asking
  which candidate time is most consistent with the training events. The framework does NOT run
  that computation: it needs Swiss Ephemeris (DE441) or Jagannatha Hora stepped through the
  candidate times. It publishes the split, the candidate times and an exact external-computation
  spec, and it states NO Lagna verdict (B.10: no fabricated computation; an honest null beats an
  invented judgment, §N.7.6).

[EXTERNAL_COMPUTATION_REQUIRED]: the ascendant degree at each candidate time for the chart's own
birth date and coordinates (see `external_computation_spec` in the response).

Version: 2.0 — SS N-384 (native data removed; chart-scoped reads).
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterator, Optional, Protocol

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

# Train/test split boundary (STRICT — never use test events for fitting)
TRAIN_TEST_CUTOFF = "2020-01-01"

# Candidate window around the recorded birth time (minutes) and its step.
WINDOW_HALF_WIDTH_MINUTES = 30
WINDOW_STEP_MINUTES = 5

# Columns read from the life-event log: identity, date and class only (SS N-109 data minimisation).
LIFE_EVENT_COLUMNS: tuple[str, ...] = ("event_id", "event_date", "category", "domain")

SOURCE_CITATION = (
    "charts row (birth details) and the chart-scoped life_events view via "
    "brahmagyan/phala/life_events_scope.py (SS N-105); no embedded data"
)

NOT_AVAILABLE_NO_EVENTS = "no_life_events_for_chart"
NOT_AVAILABLE_NO_DATED_EVENTS = "no_dated_life_events_for_chart"


# ── Data source seam (tests inject a fake; production reads the database) ─────

class RectificationSource(Protocol):
    """Read-only access to ONE requested chart's own data."""

    def birth(self, chart_id: str) -> Optional[dict[str, Any]]:
        """The chart's birth details (birth_date, birth_time, birth_lat, birth_lng,
        birth_place, timezone_id), or None when no such chart exists."""

    def life_events(self, chart_id: str) -> list[dict[str, Any]]:
        """The chart's own life events (LIFE_EVENT_COLUMNS), possibly empty."""


class DbRectificationSource:
    """Production source: read-only queries on one psycopg connection."""

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def birth(self, chart_id: str) -> Optional[dict[str, Any]]:
        row = self._conn.execute(
            "SELECT birth_date, birth_time, birth_lat, birth_lng, birth_place, timezone_id "
            "FROM charts WHERE id = %s",
            (chart_id,),
        ).fetchone()
        if row is None:
            return None
        birth_date, birth_time, lat, lng, place, tz_id = row
        return {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_lat": None if lat is None else float(lat),
            "birth_lng": None if lng is None else float(lng),
            "birth_place": place,
            "timezone_id": tz_id,
        }

    def life_events(self, chart_id: str) -> list[dict[str, Any]]:
        # Lazy import: life_events_scope needs psycopg, which a source-only environment lacks.
        from brahmagyan.phala.life_events_scope import fetch_chart_life_events

        return fetch_chart_life_events(
            self._conn, chart_id, LIFE_EVENT_COLUMNS, order_by=("event_date", "event_id"),
        )


def _database_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        url = os.environ.get(key, "")
        if url:
            return url
    return ""


def get_rectification_source() -> Iterator[RectificationSource]:
    """FastAPI dependency: a DB-backed source (503 when no database is configured)."""
    url = _database_url()
    if not url:
        raise HTTPException(status_code=503, detail="database not configured")
    try:
        import psycopg  # lazy: not available in every environment
    except ImportError:
        raise HTTPException(status_code=503, detail="database driver not available")
    try:
        conn = psycopg.connect(url)
    except Exception as exc:  # noqa: BLE001 — surfaced as a 503, never swallowed
        logger.error("[l4_rectification] database connection failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="database unavailable")
    try:
        yield DbRectificationSource(conn)
    finally:
        conn.close()


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _as_date(value: Any) -> Optional[date]:
    """A life_events date as a date, or None when it is missing / not a plain date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _as_time(value: Any) -> Optional[time]:
    if isinstance(value, datetime):
        return value.time().replace(microsecond=0)
    if isinstance(value, time):
        return value.replace(microsecond=0)
    if isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError:
            return None
    return None


def split_events(
    events: list[dict[str, Any]], cutoff: str = TRAIN_TEST_CUTOFF,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """(training, holdout, undated_count): pre-cutoff events train, the rest are held out."""
    cut = date.fromisoformat(cutoff)
    training: list[dict[str, Any]] = []
    holdout: list[dict[str, Any]] = []
    undated = 0
    for ev in events:
        d = _as_date(ev.get("event_date"))
        if d is None:
            undated += 1
            continue
        item = {
            "event_id": ev.get("event_id"),
            "event_date": d.isoformat(),
            "category": ev.get("category"),
            "domain": ev.get("domain"),
        }
        (training if d < cut else holdout).append(item)
    key = lambda e: (e["event_date"], str(e["event_id"]))  # noqa: E731 — total order
    training.sort(key=key)
    holdout.sort(key=key)
    return training, holdout, undated


def candidate_times(birth_time: Optional[time]) -> list[str]:
    """HH:MM candidates every WINDOW_STEP_MINUTES within ±WINDOW_HALF_WIDTH_MINUTES of the
    recorded birth time. Pure arithmetic, not an astrological computation."""
    if birth_time is None:
        return []
    anchor = datetime.combine(date(2000, 1, 1), birth_time)
    steps = WINDOW_HALF_WIDTH_MINUTES // WINDOW_STEP_MINUTES
    return [
        (anchor + timedelta(minutes=WINDOW_STEP_MINUTES * k)).strftime("%H:%M")
        for k in range(-steps, steps + 1)
    ]


def _birth_payload(birth: dict[str, Any]) -> dict[str, Any]:
    bd = _as_date(birth.get("birth_date"))
    bt = _as_time(birth.get("birth_time"))
    return {
        "birth_date": bd.isoformat() if bd else None,
        "birth_time": bt.isoformat() if bt else None,
        "birth_lat": birth.get("birth_lat"),
        "birth_lng": birth.get("birth_lng"),
        "birth_place": birth.get("birth_place"),
        "timezone_id": birth.get("timezone_id"),
    }


def _external_spec(birth: dict[str, Any], cands: list[str]) -> str:
    if not cands:
        return (
            "[EXTERNAL_COMPUTATION_REQUIRED] The chart record has no usable birth time, so no "
            "candidate window can be built. Record the birth time, then compute the ascendant "
            "degree across a ±30 minute window."
        )
    return (
        "[EXTERNAL_COMPUTATION_REQUIRED] Swiss Ephemeris DE441 computation: for birth date "
        f"{birth['birth_date']}, latitude {birth['birth_lat']}, longitude {birth['birth_lng']} "
        f"(timezone {birth['timezone_id']}), compute the Lagna degree at each candidate time "
        f"({', '.join(cands)}). Determine (a) at what time the ascendant changes sign within the "
        "window and (b) whether the recorded birth time is solidly inside one sign or near the "
        "cusp. Jagannatha Hora or Swiss Ephemeris provides Lagna degree to arc-minute precision."
    )


def not_available(chart_id: str, reason: str) -> dict[str, Any]:
    return {"ok": False, "not_available": True, "reason": reason, "chart_id": chart_id}


# ── Core tool function ────────────────────────────────────────────────────────

def query_rectification_framework(chart_id: str, source: RectificationSource) -> dict[str, Any]:
    """
    Return the birth-time rectification framework for THIS chart.

    Reads the chart's own birth details and life events through `source`; embeds nothing.

    Returns the framework dict, or `{"ok": False, "not_available": True, "reason": ...}` when the
    chart has no dated life events of its own. Raises LookupError for an unknown chart.
    """
    birth = source.birth(chart_id)
    if birth is None:
        raise LookupError(f"chart {chart_id!r} not found")

    events = source.life_events(chart_id)
    if not events:
        return not_available(chart_id, NOT_AVAILABLE_NO_EVENTS)

    training, holdout, undated = split_events(events)
    if not training and not holdout:
        return not_available(chart_id, NOT_AVAILABLE_NO_DATED_EVENTS)

    birth_out = _birth_payload(birth)
    cands = candidate_times(_as_time(birth.get("birth_time")))
    return {
        "ok": True,
        "chart_id": chart_id,
        "birth": birth_out,
        "train_test_cutoff": TRAIN_TEST_CUTOFF,
        "training_event_count": len(training),
        "holdout_event_count": len(holdout),
        "events_without_date": undated,
        "training_events": training,
        "holdout_events": holdout,
        "candidate_window": {
            "half_width_minutes": WINDOW_HALF_WIDTH_MINUTES,
            "step_minutes": WINDOW_STEP_MINUTES,
            "candidate_times": cands,
            "external_computation_spec": _external_spec(birth_out, cands),
        },
        "lagna_verdict": None,
        "lagna_verdict_status": "EXTERNAL_COMPUTATION_REQUIRED",
        "verification_protocol": {
            "holdout_event_count": len(holdout),
            "method": (
                "After the external ascendant computation, score each hold-out event against the "
                "candidate Lagnas; hold-out events are never used for fitting."
            ),
        },
        "leakage_prevention_status": (
            "training set uses only events dated before the cutoff; events on or after it are "
            "in the hold-out set"
        ),
        "provenance_envelope": {
            "source": "phala.rectification.v2",
            "asset": "PH-4-3-V2",
            "training_events": len(training),
            "holdout_events": len(holdout),
            "computation_tool": "Swiss Ephemeris DE441 or Jagannatha Hora",
            "citation": SOURCE_CITATION,
            "queried_at": datetime.now(tz=timezone.utc).isoformat(),
        },
    }


# ── FastAPI models ────────────────────────────────────────────────────────────

class RectificationRequest(BaseModel):
    chart_id: uuid.UUID = Field(..., description="Chart UUID (required; no default chart)")


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/phala/rectification_framework")
def api_rectification_framework(
    req: RectificationRequest,
    source: RectificationSource = Depends(get_rectification_source),
) -> dict[str, Any]:
    """
    PH-4-3-V2 rectification_framework tool, for the requested chart only.

    Birth details come from that chart's `charts` row, events from its own life-event log. A
    chart without dated life events gets `not_available`; an unknown chart gets a 404.
    The ascendant computation itself stays [EXTERNAL_COMPUTATION_REQUIRED].
    """
    cid = str(req.chart_id)
    try:
        return query_rectification_framework(cid, source)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"chart {cid} not found")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[l4_rectification] failed for chart %s: %s", cid, type(exc).__name__)
        raise HTTPException(status_code=500, detail="rectification framework failed")


@router.get("/phala/rectification_framework/gate")
def api_rectification_gate(
    chart_id: uuid.UUID = Query(..., description="Chart UUID (required; no default chart)"),
    source: RectificationSource = Depends(get_rectification_source),
) -> dict[str, Any]:
    """PH-4-3-V2 acceptance gate — train/test split integrity for THIS chart's events."""
    cid = str(chart_id)
    try:
        framework = query_rectification_framework(cid, source)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"chart {cid} not found")
    if not framework.get("ok"):
        return {**framework, "gate_passed": None}

    # Measured on the RETURNED framework (not on the splitter's own variables), so a broken
    # split would read false here (§N.8).
    cut = date.fromisoformat(TRAIN_TEST_CUTOFF)
    training = framework["training_events"]
    holdout = framework["holdout_events"]
    leakage_violations = [
        (e["event_id"], e["event_date"]) for e in training
        if date.fromisoformat(e["event_date"]) >= cut
    ] + [
        (e["event_id"], e["event_date"]) for e in holdout
        if date.fromisoformat(e["event_date"]) < cut
    ]
    overlap = sorted(
        {str(e["event_id"]) for e in training} & {str(e["event_id"]) for e in holdout}
    )
    return {
        "ok": True,
        "chart_id": cid,
        "gate_passed": not leakage_violations and not overlap,
        "leakage_violations": leakage_violations,
        "train_holdout_event_id_overlap": overlap,
        "training_event_count": len(training),
        "holdout_event_count": len(holdout),
        "events_without_date": framework["events_without_date"],
        "cutoff": TRAIN_TEST_CUTOFF,
    }
