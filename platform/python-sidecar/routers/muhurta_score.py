"""
routers/muhurta_score.py — POST /api/compute/muhurta_score (ka_muhurta_seva, W2 dark-set wiring)

RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0 / DARK_SET_WIRING_PLAN_v1_0's ka_muhurta_seva
row (§F gate ruling item 6 — same stub shape as ka_graha_sancara/GT-50, added to W2 scope).

This is a RAW per-datetime muhurta SCORE (tithi/nakshatra/vara/yoga-based quality for
a named event class), not an electional search — distinct from the already-served
brahmagyan/phala/muhurta.py (`ph_muhurta`, `muhurta_finder`/`kala_muhurta_get`), which
searches a date RANGE for the best window against `action_type` in
{marriage, travel, business, medical, education, property, general} and requires a
chart_id for its dasha/transit sub-scores. Do not conflate the two — this endpoint has
no chart_id, no date-range search, and its own distinct event vocabulary (see below).

Reuses `panchang_engine.muhurat.score_muhurat()` (a backward-compat shim re-exporting
`muhurat.finder.score_muhurat`) — the SAME scoring primitive `ph_muhurta` calls
internally for its panchanga_quality sub-score, not a second scoring engine. Read-only
usage of `muhurat/finder.py` — nothing in that module is modified by this router.

Event vocabulary: EVENTS_MVP (vivah, griha_pravesh, vyapara, yatra, property_purchase,
mantra_initiation, upaya_ritual, sadhana_initiation) — NOT the `call_muhurta_score`
descriptor's pre-existing (marketing/dead-stub) enum (marriage, travel, business,
medical, education, ceremony), which was copy-pasted from `ph_muhurta`'s unrelated
`action_type` vocabulary and never had a live caller (the handler unconditionally
errored before this wave). Since no live caller has ever received real data under the
old enum, this wave corrects the contract to the real, evidence-backed vocabulary
`score_muhurat()` actually accepts, rather than fabricating a marriage→vivah-style
mapping table with no classical basis for every entry (medical/ceremony have no clean
EVENTS_MVP analog). `upaya_ritual`/`sadhana_initiation` were added to EVENTS_MVP
specifically for `ka_muhurta_seva` (see muhurat/finder.py's own comment, "L3 Kāla K1
additions (ka_muhurta_seva, 2026-06-21)") — i.e. this endpoint is the EVENTS_MVP
extension's intended consumer, not a coincidental reuse.

No chart_id / lat / lng in the declared MCP contract (scope: global) — panchang is
location-dependent (sunrise-based tithi/nakshatra transitions), so this endpoint uses
the same canonical default location already established for chart-less panchang lookups
elsewhere in this sidecar (routers/panchang.py's `_fetch_native_context` fallback:
Bhubaneswar, lat=20.27, lon=85.84, tz_offset_minutes=330 / IST) rather than inventing a
new default.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from panchang_engine import compute_panchang
from panchang_engine.exceptions import OutOfRangeError, PanchangEngineError, ValidationError
from panchang_engine.muhurat import EVENTS_MVP, is_supported_event, score_muhurat, _score_to_stars

router = APIRouter()

# Canonical default location for chart-less panchang compute in this sidecar —
# matches routers/panchang.py's `_fetch_native_context` fallback (Bhubaneswar, IST).
_DEFAULT_LAT = 20.27
_DEFAULT_LON = 85.84
_DEFAULT_TZ_OFFSET_MINUTES = 330  # IST = UTC+5:30


class MuhurtaScoreRequest(BaseModel):
    datetime_utc: str        # ISO 8601 UTC instant, e.g. 2026-07-20T12:00:00Z
    event_class: str         # must be in EVENTS_MVP — see module docstring
    ayanamsha_id: str | None = None  # accepted for contract-shape parity with
                                       # call_ephemeris_at_t; panchang_engine's angas
                                       # module is Lahiri-only today (not audited for
                                       # multi-ayanamsha support in this wave) — a
                                       # non-Lahiri value is rejected loud (422) rather
                                       # than silently ignored.


@router.post("/muhurta_score")
def muhurta_score(req: MuhurtaScoreRequest) -> dict:
    """
    Score a muhurta (auspicious-window quality) for an arbitrary UTC instant and a
    named event class. Sub-day input, day-grain panchang output (score_muhurat's
    quality tables are tithi/nakshatra/vara/yoga — all day-grain angas; the specific
    UTC hour only determines WHICH local calendar day's panchang is scored).
    """
    if not is_supported_event(req.event_class):
        raise HTTPException(
            status_code=422,
            detail=(
                f"[EXTERNAL_COMPUTATION_REQUIRED] event_class={req.event_class!r} is not "
                f"recognized. Valid values: {sorted(EVENTS_MVP)}."
            ),
        )

    if req.ayanamsha_id is not None and req.ayanamsha_id not in (
        "lahiri_chitrapaksha", "lahiri",
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                f"[EXTERNAL_COMPUTATION_REQUIRED] ayanamsha_id={req.ayanamsha_id!r} is not "
                f"supported — panchang_engine's anga computation is Lahiri-only in this "
                f"wave. Omit ayanamsha_id or pass 'lahiri_chitrapaksha'."
            ),
        )

    try:
        dt = datetime.fromisoformat(req.datetime_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime_utc: {exc}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)

    # Local calendar date at the canonical default location (UTC + tz offset).
    local_dt = dt_utc + timedelta(minutes=_DEFAULT_TZ_OFFSET_MINUTES)
    local_date = local_dt.date()

    try:
        panchang = compute_panchang(
            local_date, _DEFAULT_LAT, _DEFAULT_LON, _DEFAULT_TZ_OFFSET_MINUTES,
        )
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    score = score_muhurat(panchang, req.event_class)

    return {
        "datetime_utc": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local_date": local_date.isoformat(),
        "event_class": req.event_class,
        "score": round(score, 2),
        "stars": _score_to_stars(score),
        "location": {
            "lat": _DEFAULT_LAT, "lon": _DEFAULT_LON,
            "tz_offset_minutes": _DEFAULT_TZ_OFFSET_MINUTES,
            "note": "canonical default location (Bhubaneswar, IST) — this service's "
                    "declared contract has no chart_id/lat/lng input (scope: global)",
        },
        "panchang_context": {
            "tithi": panchang.tithi.name,
            "nakshatra": panchang.nakshatra.name,
            "vara": panchang.vara.name,
            "yoga": panchang.yoga.name,
        },
    }
