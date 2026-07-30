"""
routers/panchang.py — FastAPI router for /api/compute/panchanga endpoints.

Engine-direct path: calls panchang_engine.compute_panchang() on demand.
No SQL cache this session — 4C-2 will add panchang_daily cache below
the endpoint without changing this router.

Phase: 4C-3 (initial); 4C-5 (NativeContext hydration + chart_id wiring)
"""
import os
from datetime import date as DateType, time as TimeType
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import psycopg

from panchang_engine import compute_panchang, panchang_range
from panchang_engine.serialize import panchang_to_dict
from panchang_engine.exceptions import PanchangEngineError, OutOfRangeError, ValidationError
from panchang_engine.shastra_tables import NAKSHATRA_NAMES, SIGN_NAMES

router = APIRouter()


# ── NativeContext ──────────────────────────────────────────────────────────────

class NativeContext(BaseModel):
    """
    Minimal native overlay computed from birth chart for Tara Bala / Chandra Bala.
    Attached to the /api/compute/panchanga response when chart_id is provided.
    """
    chart_id: str
    native_name: str                  # chart name for UI display (e.g. "Abhisek")
    birth_nakshatra_id: int           # 1..27 (Moon nakshatra at birth, sidereal)
    birth_nakshatra_name: str         # e.g. "Purva Bhadrapada"
    moon_sign_id: int                 # 1..12 (1 = Aries … 12 = Pisces)
    moon_sign_name: str               # Sanskrit sign name, e.g. "Kumbha"
    active_dasha_lord: Optional[str] = None  # for future dasha-aware muhurat in 4C-6


# ── Chart fetcher ──────────────────────────────────────────────────────────────

def _fetch_native_context(chart_id: str) -> NativeContext:
    """
    Fetch chart from DB, compute birth nakshatra + Moon sign via panchang_engine,
    and return NativeContext.

    Uses DATABASE_URL (same pattern as dasha_chain router).
    Raises HTTPException 503 if DB is unreachable, 404 if chart not found.

    Security: caller must already have confirmed chart access (auth is enforced
    at the Next.js proxy layer; the sidecar trusts the proxy's chart_id).
    """
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

    try:
        with psycopg.connect(db_url) as conn:
            row = conn.execute(
                """
                SELECT name, birth_date, birth_time, birth_lat, birth_lng
                FROM charts
                WHERE id = %s
                """,
                (chart_id,),
            ).fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DB error: {exc}")

    if row is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id!r} not found")

    chart_name, birth_date, birth_time, birth_lat, birth_lng = row

    # birth_lat / birth_lng can be None if the chart was created without coordinates;
    # fall back to Bhubaneswar (project canonical default per §8 / D1 decisions).
    lat = float(birth_lat) if birth_lat is not None else 20.27
    lon = float(birth_lng) if birth_lng is not None else 85.84

    # birth_time may come as a `datetime.time` or string depending on driver
    if isinstance(birth_time, TimeType):
        birth_hour = birth_time.hour
        birth_min  = birth_time.minute
    else:
        # parse HH:MM or HH:MM:SS string
        parts = str(birth_time).split(":")
        birth_hour = int(parts[0])
        birth_min  = int(parts[1]) if len(parts) > 1 else 0

    # Compute panchang at birth moment using IST (+330 min) by default.
    # (Charts may carry a different TZ in future; for this release, IST is canonical.)
    #
    # ṢAḌ-DARŚANA W1 verify-reopen fix (items 29 + 32), 2026-07-30 — ROOT CAUSE, keyword-name
    # mismatch: this call passed `tz_offset_minutes=330`, but `panchang_engine.compute_panchang`
    # declares its fourth parameter `tz_offset` (see panchang_engine/__init__.py). Python
    # raised `TypeError: compute_panchang() got an unexpected keyword argument
    # 'tz_offset_minutes'`, which the `except (ValidationError, OutOfRangeError,
    # PanchangEngineError)` clause below does NOT catch — so it propagated out of the endpoint
    # as an unhandled HTTP 500.
    #
    # `_fetch_native_context` is reached ONLY from the single-date POST /api/compute/panchanga
    # path AND only when `chart_id` is supplied. That is exactly the call `kala_now_get` makes
    # (mode=single + chart_id) and exactly the call `kala_ahead_get` does NOT make (mode=range,
    # no chart_id) — which is why the range path served real data while every single-date call
    # returned 500 and `kala_now_get` reported "L0 panchāṅga service unreachable this call" for
    # disha_shula / gulika_kalam_now / chandrashtama / hora_now / janma_resonance on every
    # chart, on every date, deterministically. Not an outage: a persistent code defect.
    #
    # The two OTHER call sites in this module (the endpoints at the bottom of this file) pass
    # all four arguments positionally, which is why they were never affected.
    try:
        birth_panchang = compute_panchang(birth_date, lat, lon, tz_offset=330)
    except (ValidationError, OutOfRangeError, PanchangEngineError) as exc:
        raise HTTPException(status_code=422, detail=f"Birth chart compute error: {exc}")

    # Extract Moon's nakshatra and sign from the birth-moment planet positions.
    # birth_panchang.planets is list[PlanetState]; find Moon by name.
    moon = next(
        (ps for ps in birth_panchang.planets if getattr(ps, "name", "").lower() == "moon"),
        None
    )

    if moon is None:
        raise HTTPException(status_code=500, detail="Moon position not found in birth panchang")

    nak_id   = int(moon.nakshatra_id)      # 1..27
    nak_name = NAKSHATRA_NAMES[nak_id - 1]  # 0-indexed list
    sign_id  = int(moon.sign_id)           # 1..12
    sign_name = SIGN_NAMES[sign_id - 1]    # 0-indexed list

    return NativeContext(
        chart_id=chart_id,
        native_name=chart_name or "",
        birth_nakshatra_id=nak_id,
        birth_nakshatra_name=nak_name,
        moon_sign_id=sign_id,
        moon_sign_name=sign_name,
        active_dasha_lord=None,  # populated in 4C-6
    )


# ── Request / Response models ──────────────────────────────────────────────────

class PanchangaRequest(BaseModel):
    date: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)
    chart_id: Optional[str] = None  # personalise overlay; hydrated this session (4C-5)
    fields: Optional[list[str]] = None  # field projection for token-budget control


class PanchangaRangeRequest(BaseModel):
    date_from: DateType
    date_to: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/panchanga")
async def compute_panchanga_endpoint(req: PanchangaRequest):
    """
    Returns full Panchang for a single (date, lat, lon, tz). Engine-direct;
    no cache layer this session. 4C-2 will add panchang_daily cache below.

    When chart_id is provided, also returns native_context (NativeContext) with
    birth nakshatra + moon sign for Tara Bala / Chandra Bala overlay.

    Response:
        {ok: true, panchang: {...}, native_context: NativeContext|null, cache_hit: false}

    EL-49 fix (2026-07-25, β.C): every timestamp in `panchang` now carries an
    explicit local-offset sibling (`*_ist` when tz_offset_minutes==330, else
    `*_local`) alongside the existing UTC-only `*_utc` field — closes the
    "ambiguous UTC-midnight-for-an-IST-day" gap for the ALREADY-LIVE
    call_panchanga_service MCP tool (platform/src/lib/retrieval/registry/
    layers/L0_brahmagyan/call_panchanga_service.ts), which calls this exact
    endpoint and passes `panchang` through verbatim — so this fix reaches a
    live tool with zero TS-side change required, unlike the dedicated
    /panchanga_get endpoint below (a new capability, not yet wired to any
    tool — see BETA_C.md for the required α-side wiring note).
    """
    try:
        panchang = compute_panchang(req.date, req.lat, req.lon, req.tz_offset_minutes)
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    payload = panchang_to_dict(panchang)
    _add_local_time_fields(
        payload, req.tz_offset_minutes, "ist" if req.tz_offset_minutes == 330 else "local"
    )

    # Field projection — clip server-side; query_panchanga.ts also clips client-side
    if req.fields:
        payload = {k: v for k, v in payload.items() if k in req.fields}

    # Native context — hydrated when chart_id is present.
    #
    # ṢAḌ-DARŚANA W1 verify-reopen hardening, 2026-07-30. `native_context` is by this
    # capability's own contract an OPTIONAL enrichment overlay (call_panchanga_service.ts:
    # "chart_id is optional and, when provided, hydrates a native_context overlay"). Before
    # this change, ANY failure inside `_fetch_native_context` — the tz_offset kwarg TypeError
    # fixed above, a 503 on a missing DATABASE_URL, a 404 on an unbuilt chart — propagated out
    # of this endpoint and destroyed the ENTIRE already-successfully-computed panchāṅga
    # payload. That is how one keyword-name typo in an optional overlay blanked five unrelated
    # `kala_now_get` fields (disha_shula / gulika_kalam_now / chandrashtama / hora_now /
    # janma_resonance) on every chart and every date.
    #
    # Now: the overlay fails soft and DISCLOSES why (`native_context_error`, never a silent
    # null — CLAUDE.md §N.8: an honest, attributable gap beats both a fabricated value and an
    # undifferentiated failure). The five aṅgas, timings and horā ladder — which never needed
    # the chart at all — are served regardless. A caller that genuinely requires the overlay
    # reads `native_context_error` and reports THAT specific reason rather than mislabelling a
    # deterministic defect as service unreachability.
    native_context: Optional[NativeContext] = None
    native_context_error: Optional[str] = None
    if req.chart_id:
        try:
            native_context = _fetch_native_context(req.chart_id)
        except HTTPException as exc:
            native_context_error = f"HTTP {exc.status_code}: {exc.detail}"
        except Exception as exc:  # noqa: BLE001 — disclosed, never swallowed silently
            native_context_error = f"{type(exc).__name__}: {exc}"

    return {
        "ok": True,
        "panchang": payload,
        "native_context": native_context.model_dump() if native_context else None,
        "native_context_error": native_context_error,
        "cache_hit": False,
    }


class PanchangaRefreshRequest(BaseModel):
    """R5.1 C3 — scheduled monthly refresh request body. All fields optional."""
    days: Optional[int] = Field(
        None, ge=1, le=730,
        description="Window length in days from today (default: 365, the rolling +12-month contract).",
    )


@router.post("/panchanga/refresh")
async def refresh_panchanga_daily_endpoint(req: PanchangaRefreshRequest = PanchangaRefreshRequest()):
    """
    R5.1 C3 — triggers panchanga_daily_writer.write_window() for a rolling
    window starting today. Intended to be called by the monthly Cloud Scheduler
    job (infra/scheduler/panchanga_refresh.tf — documented, not yet applied;
    see that file's header) via the Next.js cron proxy
    (/api/admin/cron/refresh-panchanga-daily), matching the existing
    watchdog-reaper / mv-refresh / pending-stream-reaper pattern.

    Idempotent: panchanga_daily_writer upserts (ON CONFLICT (date) DO UPDATE),
    so re-running never accretes duplicate rows and always reflects the
    current computation_version/ephemeris_version.

    Deterministic-first (B.10): calls panchang_engine.compute_panchang()
    (Swiss Ephemeris) directly — no LLM involved anywhere in this path.
    """
    from datetime import date as _date, timedelta as _timedelta
    from scripts.panchanga_daily_writer import write_window, DEFAULT_WINDOW_DAYS

    days = req.days or DEFAULT_WINDOW_DAYS
    date_from = _date.today()
    date_to = date_from + _timedelta(days=days)

    try:
        n = write_window(date_from, date_to, dry_run=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"panchanga_daily_writer failed: {exc}")

    return {
        "ok": True,
        "rows_written": n,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }


@router.post("/panchanga/range")
async def compute_panchanga_range_endpoint(req: PanchangaRangeRequest):
    """
    Range variant for calendar feed / week views. Same engine-direct logic.
    date_from and date_to are both inclusive.

    Response:
        {ok: true, panchangs: [...], count: N}

    EL-49 fix (2026-07-25, β.C): same explicit-local-time enrichment as the
    single-date /panchanga endpoint above, applied per day — closes the
    original register complaint's "muhūrta windows serve start-date only"
    root concern for any consumer of the RANGE variant directly (this route
    already serves every day in range, not just the start date; the
    ambiguity gap was purely the missing local-time siblings).
    """
    # Sanity-check: cap at 31 days to prevent runaway sidecar calls
    delta = (req.date_to - req.date_from).days
    if delta < 0:
        raise HTTPException(status_code=422, detail="date_to must be >= date_from")
    if delta > 30:
        raise HTTPException(status_code=422, detail="Range exceeds 31-day limit; split the request")

    try:
        panchangs = panchang_range(
            req.date_from, req.date_to, req.lat, req.lon, req.tz_offset_minutes
        )
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    suffix = "ist" if req.tz_offset_minutes == 330 else "local"
    panchangs_out = []
    for p in panchangs:
        d = panchang_to_dict(p)
        _add_local_time_fields(d, req.tz_offset_minutes, suffix)
        panchangs_out.append(d)

    return {
        "ok": True,
        "panchangs": panchangs_out,
        "count": len(panchangs_out),
    }


# ── EL-49: first-class panchanga_get(date, location?) ───────────────────────
#
# ELEVATION_REGISTER_v1_0.md EL-49: panchāṅga was reachable only through 2-day
# muhūrta windows serving start-date panchāṅga only, missing karaṇa, sunrise/
# sunset, and horā timing outright. Investigation (β.C, 2026-07-25) found the
# underlying compute path (panchang_engine.compute_panchang(), already wired
# to POST /api/compute/panchanga above) was NOT the gap — it already computes
# all five aṅgas (including BOTH karaṇas of the tithi), sunrise/sunset, and a
# full 24-slot horā table. Verified offline (no live DB needed):
#   compute_panchang(date(1984,2,5), 20.27, 85.84, 330) reproduces all 5
#   birth-panchāṅga FORENSIC anchors exactly (Tithi=Shukla Tritiya,
#   Vara=Ravivara, Yoga=Shiva, Karana(first)=Garaja, Nakshatra=Purva
#   Bhadrapada) — see BETA_C.md for the full evidence block.
# The actual gap was serving-side: no single first-class date+location lookup
# existed; muhūrta windows serve only the start date. This endpoint closes
# that gap directly over the engine (not over the panchanga_daily cache,
# which is Bhubaneswar-fenced AND stores only one karana per day — the
# "missing karana outright" complaint the register names — so a first-class
# route needs full engine-direct fidelity, not the abbreviated cache row).

from datetime import datetime as _DateTime, timedelta as _TimeDelta, timezone as _TZ  # noqa: E402

# Named-location gazetteer (deliberately minimal — NOT a general geocoder).
# "Bhubaneswar" here matches the exact coordinates ga_panchanga_writer.py's
# FORENSIC gate uses (20.27, 85.84, +330 min = IST) — this is what makes the
# birth-date verify below reproduce the 7 FORENSIC anchors exactly. This is
# DELIBERATELY the same pair as panchang_daily_reader.py's BHUBANESWAR_LAT/LON
# and panchang.py's _fetch_native_context() fallback above — NOT
# l0_ephemeris.py's NATIVE_LAT/NATIVE_LON (20.2961/85.8245), which is a
# separate, more-precise coordinate pair used for ephemeris_daily's spot
# checks. This is a pre-existing three-way "Bhubaneswar" coordinate
# inconsistency in the codebase (see ephemeris_routes.py's
# native_lifetime_meta docstring for the third instance) — this endpoint
# intentionally uses the FORENSIC-matching pair, not the ephemeris one, since
# panchāṅga (not raw ephemeris position) is what must reproduce FORENSIC here.
_PANCHANGA_KNOWN_LOCATIONS: dict[str, dict[str, float]] = {
    "bhubaneswar": {"lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330},
}
_PANCHANGA_DEFAULT_LOCATION_KEY = "bhubaneswar"


class PanchangaGetLocationError(ValueError):
    """Raised when `location` is not a recognized named location and no
    explicit lat/lon was supplied. Never silently falls back to a guessed
    coordinate (B.10)."""


def _resolve_panchanga_get_location(
    location: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    tz_offset_minutes: Optional[int],
) -> tuple[float, float, int, str]:
    """
    Resolve (lat, lon, tz_offset_minutes, location_label) for panchanga_get.

    Priority: explicit lat/lon wins (tz_offset_minutes defaults to +330/IST if
    omitted — documented, not silent, since this project's whole panchāṅga
    surface is IST-anchored) > named `location` (must be a recognized key,
    else a loud error — never a silent geocode guess) > no params at all
    (defaults to Bhubaneswar, the project's canonical native location, per
    the same fallback panchang.py::_fetch_native_context already uses).
    """
    if lat is not None and lon is not None:
        resolved_tz = tz_offset_minutes if tz_offset_minutes is not None else 330
        label = location or f"lat={lat},lon={lon}"
        return lat, lon, resolved_tz, label

    if location:
        key = location.strip().lower()
        if key not in _PANCHANGA_KNOWN_LOCATIONS:
            raise PanchangaGetLocationError(
                f"[EXTERNAL_COMPUTATION_REQUIRED] Unknown location={location!r}. "
                f"Known named locations: {sorted(_PANCHANGA_KNOWN_LOCATIONS)}. "
                f"Pass lat/lon/tz_offset_minutes explicitly for any other location — "
                f"this endpoint never guesses coordinates for an unrecognized name."
            )
        loc = _PANCHANGA_KNOWN_LOCATIONS[key]
        return loc["lat"], loc["lon"], int(loc["tz_offset_minutes"]), location

    loc = _PANCHANGA_KNOWN_LOCATIONS[_PANCHANGA_DEFAULT_LOCATION_KEY]
    return loc["lat"], loc["lon"], int(loc["tz_offset_minutes"]), "Bhubaneswar (default)"


def _format_offset_suffix(tz_offset_minutes: int) -> str:
    sign = "+" if tz_offset_minutes >= 0 else "-"
    off_abs = abs(tz_offset_minutes)
    hh, mm = divmod(off_abs, 60)
    return f"{sign}{hh:02d}:{mm:02d}"


def _utc_z_to_local_iso(utc_iso: Optional[str], tz_offset_minutes: int) -> Optional[str]:
    """
    'YYYY-MM-DDTHH:MM:SSZ' -> 'YYYY-MM-DDTHH:MM:SS+HH:MM' (explicit local offset).
    EL-49 fix: every panchang_engine timestamp is UTC-only (ends 'Z'), which is
    the exact "ambiguous UTC-midnight-for-an-IST-day" risk class the register
    names — a caller must convert in their head to know which IST calendar day
    a UTC-late-evening timestamp actually falls on. This adds the explicit
    local-offset sibling for every such field so no conversion is implicit.
    """
    if not utc_iso:
        return None
    dt = _DateTime.strptime(utc_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_TZ.utc)
    local_dt = dt + _TimeDelta(minutes=tz_offset_minutes)
    return local_dt.strftime("%Y-%m-%dT%H:%M:%S") + _format_offset_suffix(tz_offset_minutes)


def _add_local_time_fields(obj, tz_offset_minutes: int, suffix: str):
    """
    Recursively walk a panchang_to_dict()-shaped structure and, for every dict
    key ending in '_utc', add a sibling '<field>_<suffix>' key with the
    explicit local-offset ISO string. Mutates and returns `obj` in place.
    `suffix` is 'ist' for the IST case (tz_offset_minutes == 330) and
    'local' otherwise (a non-IST location must not be mislabelled "ist").
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key.endswith("_utc") and isinstance(obj[key], (str, type(None))):
                base = key[: -len("_utc")]
                obj[f"{base}_{suffix}"] = _utc_z_to_local_iso(obj[key], tz_offset_minutes)
        for v in obj.values():
            _add_local_time_fields(v, tz_offset_minutes, suffix)
    elif isinstance(obj, list):
        for item in obj:
            _add_local_time_fields(item, tz_offset_minutes, suffix)
    return obj


@router.get("/panchanga_get")
def panchanga_get_endpoint(
    date: DateType = Query(..., description="Date in YYYY-MM-DD format (the CIVIL date at the "
                                             "resolved location's local timezone, not UTC)."),
    location: Optional[str] = Query(
        None,
        description="Named location (currently: 'Bhubaneswar'). Omit together with lat/lon to "
                    "default to Bhubaneswar (the project's canonical native location).",
    ),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Explicit latitude (overrides `location`)."),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="Explicit longitude (overrides `location`)."),
    tz_offset_minutes: Optional[int] = Query(
        None, ge=-720, le=840,
        description="UTC offset in minutes for the civil date and all local-time fields. "
                    "Defaults to +330 (IST) — every named location in this endpoint's gazetteer "
                    "is IST-anchored, matching the project's canonical panchāṅga convention.",
    ),
):
    """
    EL-49: first-class panchāṅga lookup for one date at one location, in a
    single call. Returns all 5 aṅgas (tithi, nakshatra, yoga, BOTH karaṇas,
    vara), sunrise/sunset, and a complete horā table for the day — every
    timestamp carries both its UTC value (`*_utc`, as computed) and an
    explicit local-offset sibling (`*_ist` when the resolved location is IST,
    else `*_local`), so no caller has to silently assume which civil day a
    UTC timestamp falls on.

    This IS the FORENSIC correctness oracle: `panchanga_get(date="1984-02-05",
    location="Bhubaneswar")` must reproduce the birth panchāṅga subset of the
    7 FORENSIC anchors exactly (Tithi=Shukla Tritiya, Vara=Ravivara,
    Yoga=Shiva, Karana=Garaja) — see BETA_C.md for the live-verified payload.
    """
    try:
        resolved_lat, resolved_lon, resolved_tz, location_label = _resolve_panchanga_get_location(
            location, lat, lon, tz_offset_minutes
        )
    except PanchangaGetLocationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        panchang = compute_panchang(date, resolved_lat, resolved_lon, resolved_tz)
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    payload = panchang_to_dict(panchang)

    suffix = "ist" if resolved_tz == 330 else "local"
    _add_local_time_fields(payload, resolved_tz, suffix)

    # Convenience top-level aliases — the "5 angas" framing EL-49 asks for,
    # plus a single `karana` alias (= karana_first) since FORENSIC's single
    # "Karana = Garaja" anchor refers to the karana active at the reference
    # moment, which is karana_first for a day that does not cross a karana
    # boundary before the reference time. karana_first/karana_second (the
    # full two-half-tithi picture) remain available in `panchang` below.
    angas_summary = {
        "tithi": payload["tithi"],
        "nakshatra": payload["nakshatra"],
        "yoga": payload["yoga"],
        "karana": payload["karana_first"],
        "vara": payload["vara"],
    }

    return {
        "ok": True,
        "date": date.isoformat(),
        "location": {
            "label": location_label,
            "lat": resolved_lat,
            "lon": resolved_lon,
            "tz_offset_minutes": resolved_tz,
            "timezone_label": f"UTC{_format_offset_suffix(resolved_tz)}"
                               + (" (IST)" if resolved_tz == 330 else ""),
        },
        "angas": angas_summary,
        "sunrise": {"utc": payload["sunrise_utc"], suffix: payload[f"sunrise_{suffix}"]},
        "sunset": {"utc": payload["sunset_utc"], suffix: payload[f"sunset_{suffix}"]},
        "moonrise": {"utc": payload["moonrise_utc"], suffix: payload[f"moonrise_{suffix}"]},
        "moonset": {"utc": payload["moonset_utc"], suffix: payload[f"moonset_{suffix}"]},
        "hora": payload["hora"],
        "hora_count": len(payload["hora"]),
        "choghadiya": payload["choghadiya"],
        "inauspicious": payload["inauspicious"],
        "auspicious": payload["auspicious"],
        "special_yogas": payload["special_yogas"],
        "panchang": payload,
        "source": "panchang_engine.compute_panchang (engine-direct; not the panchanga_daily cache — "
                  "see this endpoint's module-level comment for why)",
        "computed_at": _DateTime.now(_TZ.utc).isoformat(),
    }
