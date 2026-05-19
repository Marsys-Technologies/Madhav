---
canonical_id: PHASE_4D_TRANSIT_SEARCH_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
sub_phase: 4D
authored_on: 2026-05-19
estimated_sessions: 2
two_stream_branch: analysis/backend-data-pipeline-perf-audit
depends_on: 4A (bd41f13), 4B (c63ef9f), 4C (abab885)
campaign_role: FINAL — close-out of Phase 4 ephemeris accessibility campaign
---

# §4.D — `query_transit_event` Retrieval Tool + Sidecar `/transit_search`

## §1 Scope

The first three sub-phases gave the planner LOOKUP power — "what is happening on date X?". §4.D adds SEARCH power — "when does X happen?". This is the difference between asking the database what *is* and asking it to find *when*. Four event classes become first-class planner-answerable:

| Event class | Question shape | Surface |
|---|---|---|
| **Ingress** | "When does Jupiter next enter Aries?" | `ephemeris_daily.sign_ingress_today` (§4.B-precomputed) |
| **Station** | "When is Mercury retrograde next?" | `retrogrades` (existing table, migration 016) |
| **Aspect** | "When does Saturn next aspect my natal Moon?" | Sidecar `/transit_search` live compute |
| **Conjunction** | "When do Jupiter and Saturn next conjunct?" | Sidecar `/transit_search` live compute |

Eclipses are intentionally OUT of scope — already planner-reachable via `temporal.eclipse_query`. No duplication.

What ships:

1. **No new migration** — reuses `ephemeris_daily` (§4.B-enriched) + `retrogrades` (migration 016).
2. **Sidecar `/transit_search` endpoint** — aspect + conjunction live compute via `swe.solcross`/`swe.mooncross` for Sun/Moon, root-finding for the other 7 planets. ±10 year window cap.
3. **`platform/src/lib/retrieve/query_transit_event.ts`** — 29th retrieval tool. Routes event_type to the right backend (table vs sidecar).
4. **PLANNER_PROMPT amendment** — new R-TE (Transit Event) rule. Triggers: "when next" / "when will" / "next time" / ingress keywords / aspect keywords / conjunction keywords / station keywords.
5. **Graha-yuddha docstring update** in `ephemeris_derivations.compute_graha_yuddha` — formal documentation that longitude-only form is the accepted Vedic approximation per modern practitioner consensus (carries forward the §4.B executor note; no code change).
6. **Tests** — ~5 TS vitest cases + ~12 Python pytest cases for the sidecar transit-search algorithm.
7. **Golden set** — GT.078–GT.082 covering all four event classes + one negative.
8. **RUNBOOK addendum** — `/transit_search` endpoint requires the sidecar to be running; no precompute needed.
9. **Campaign close artifact** — `PHASE_4_CLOSE_v1_0.md` sealing the campaign (per master plan §E). Documents final tool count (26 → 29), what's deferred to native (3 production bootstraps), and the consolidated-batch answer:eval handoff.

What does NOT ship (intentional non-scope):

- Tropical-zodiac queries (everything stays Lahiri sidereal per §6 approved decision).
- Vedic special-aspect detection (Mars 4/8, Jupiter 5/9, Saturn 3/10) — degree-orb-based aspect search covers the universal 7th opposition + degree-orb cases; special-aspect interpretation stays at the synthesis layer via `cgm_graph_walk` ASPECTS_* edges + chart_facts house-distance logic.
- Asteroid event detection. Lahiri-only.
- Date ranges outside 1900–2100. Out-of-window queries return a diagnostic row.

## §2 What you must NOT do

- **No branch other than `analysis/backend-data-pipeline-perf-audit`**. Verify before starting.
- **No Chat V2 files**. Same off-limits globs as 4A/B/C.
- **No autonomous `npm run answer:eval`**. Pre-commit gates only. The consolidated batch answer:eval runs AFTER §4.D ships, triggered by native per campaign discipline.
- **No new ephemeris_daily migration** — the data §4.D needs is already there from §4.B.
- **No mutation of the existing `retrogrades` schema**. Read-only.
- **No deletion of the existing `temporal` tool's eclipse handling**. Eclipses stay where they are.
- **No live API calls from unit tests**. Sidecar `/transit_search` is mocked in vitest; real-call integration is operator-supervised.

## §3 Approved decisions to honor (re-stated from research §6 + previous executor notes)

1. **Lahiri sidereal ayanamsha** — consistent across all event computations.
2. **MEAN_NODE for Rahu/Ketu** — when transit-search needs Rahu/Ketu positions, use MEAN. (Inherited from §4.B fix; bootstrap_ephemeris already produces MEAN-anchored rows.)
3. **Aspect-degree convention** — degree-orb-based search supports the universal Western aspects {0, 60, 90, 120, 180}. Vedic special aspects deferred to synthesis-layer reasoning via `cgm_graph_walk`. Default orb = 1.0° (tight); param can override up to 3.0°.
4. **Window cap = ±10 years** from query date. Larger windows are queryable in chunks; this is a latency guard.
5. **Tithi/event boundary convention** (carry-forward from §4.C executor note) — `swe.solcross`/`mooncross` return the **exact JD at which longitude equals the target**, not "the day of the crossing". The result JD is precise to the second; the calling tool converts to ISO datetime in **IST** for presentation (per §4.C vara-datetime carry-forward) but stores the canonical UTC JD as well.
6. **Graha-yuddha longitude-only form** — formally documented as the accepted Vedic approximation; no code change. `compute_graha_yuddha` gets a docstring + module comment explaining the convention.

## §4 Files to create or modify

### §4.1 New file — `platform/python-sidecar/pipeline/transit_search.py`

Pure-Python search algorithms. Importable from the new sidecar router. Imports `SIGNS` + `SIGN_TO_IDX` from `ephemeris_derivations` per the established pattern.

```python
"""
transit_search — Swiss Ephemeris event-search primitives for §4.D.

Three search algorithms:
  - find_aspect_events(transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd)
  - find_conjunction_events(planet_a, planet_b, orb, start_jd, end_jd)
  - find_ingress_events(planet, target_sign, start_jd, end_jd) — when planet enters a sign

For Sun/Moon, longitude crossings use swe.solcross / swe.mooncross (fast, exact).
For Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu, longitude crossings are found via
adaptive sign-bracketing + bisection.

All returned events carry:
  - event_jd (UTC Julian Day, second-precision)
  - event_datetime_ist (datetime, IST = UTC + 5:30)
  - exact_longitude_deg (Lahiri sidereal)
  - orb_at_event (degrees)

Window cap: caller supplies start_jd + end_jd. Internal logic does not extend.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

# Swiss Ephemeris planet codes (matched to bootstrap_ephemeris.py conventions).
# Rahu = MEAN_NODE per §4.B fix; Ketu = MEAN_NODE + 180°.
PLANET_TO_SWE = {
    "sun":     "SUN",      # placeholder string — caller maps to swe.SUN
    "moon":    "MOON",
    "mars":    "MARS",
    "mercury": "MERCURY",
    "jupiter": "JUPITER",
    "venus":   "VENUS",
    "saturn":  "SATURN",
    "rahu":    "MEAN_NODE",  # NOT TRUE_NODE — §4.B locked decision
}

IST_OFFSET_HOURS = 5.5


@dataclass
class TransitEvent:
    event_type: str            # 'ingress' | 'aspect' | 'conjunction' | 'station'
    event_jd: float            # Julian Day UTC
    event_datetime_ist: str    # ISO datetime in IST
    transit_planet: str
    secondary_planet: Optional[str]   # for conjunctions / aspects-to-natal-planet
    exact_longitude_deg: float
    orb_at_event_deg: float
    sign: str
    nakshatra: str
    extra: dict                 # event-type-specific (e.g., aspect_degrees, target_sign)


def jd_to_ist_iso(swe, jd_utc: float) -> str:
    """Convert UTC Julian Day to ISO datetime string in IST (UTC+5:30)."""
    y, m, d, hour_dec = swe.revjul(jd_utc)
    h = int(hour_dec)
    mn = int((hour_dec - h) * 60)
    s = int(((hour_dec - h) * 60 - mn) * 60)
    dt_utc = datetime(y, m, d, h, mn, s)
    dt_ist = dt_utc + timedelta(hours=IST_OFFSET_HOURS)
    return dt_ist.isoformat()


def find_aspect_events(
    swe,
    transit_planet: str,
    target_longitude_deg: float,
    aspect_degrees: list[int],
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list[TransitEvent]:
    """
    Find all events where transit_planet's sidereal longitude crosses
    (target + aspect_degree) % 360 within orb, between start_jd and end_jd.

    For Sun/Moon: uses swe.solcross / swe.mooncross for exact crossing.
    For other planets: adaptive day-step bracketing + bisection.
    """
    events: list[TransitEvent] = []
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    planet_code = _swe_planet(swe, transit_planet)

    for aspect_deg in aspect_degrees:
        target_lon = (target_longitude_deg + aspect_deg) % 360.0

        # Sun/Moon: direct crossing via solcross/mooncross.
        if transit_planet.lower() == "sun":
            jd = start_jd
            while jd < end_jd:
                next_jd = swe.solcross(target_lon, jd, flags)
                if next_jd < 0 or next_jd > end_jd:
                    break
                events.append(_build_event(swe, "aspect", next_jd, transit_planet,
                                            None, target_lon, aspect_deg, 0.0))
                jd = next_jd + 1.0  # advance past the crossing
        elif transit_planet.lower() == "moon":
            jd = start_jd
            while jd < end_jd:
                next_jd = swe.mooncross(target_lon, jd, flags)
                if next_jd < 0 or next_jd > end_jd:
                    break
                events.append(_build_event(swe, "aspect", next_jd, transit_planet,
                                            None, target_lon, aspect_deg, 0.0))
                jd = next_jd + 1.0
        else:
            # Other planets: day-step + bisection.
            events.extend(_find_crossings_by_bisection(
                swe, planet_code, target_lon, orb_deg, start_jd, end_jd,
                event_type="aspect", transit_planet=transit_planet,
                aspect_deg=aspect_deg,
            ))

    return sorted(events, key=lambda e: e.event_jd)


def find_conjunction_events(
    swe,
    planet_a: str,
    planet_b: str,
    orb_deg: float,
    start_jd: float,
    end_jd: float,
) -> list[TransitEvent]:
    """
    Find times when planet_a and planet_b are within orb_deg of each other.
    Day-step iteration + bisection on the signed longitude difference.
    """
    code_a = _swe_planet(swe, planet_a)
    code_b = _swe_planet(swe, planet_b)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    events: list[TransitEvent] = []
    step = 1.0  # 1 day
    jd = start_jd
    prev_diff = _shortest_arc_diff(_planet_lon(swe, code_a, start_jd, flags),
                                    _planet_lon(swe, code_b, start_jd, flags))
    while jd < end_jd:
        jd_next = jd + step
        lon_a = _planet_lon(swe, code_a, jd_next, flags)
        lon_b = _planet_lon(swe, code_b, jd_next, flags)
        diff = _shortest_arc_diff(lon_a, lon_b)
        if abs(diff) <= orb_deg and abs(prev_diff) > orb_deg:
            # Entered orb — bisect to find exact moment of |diff| == orb.
            exact_jd = _bisect_diff(swe, code_a, code_b, jd, jd_next, orb_deg, flags)
            events.append(_build_event(swe, "conjunction", exact_jd, planet_a,
                                       planet_b, lon_a, None, abs(diff)))
        prev_diff = diff
        jd = jd_next

    return events


def find_ingress_events(
    swe,
    planet: str,
    target_sign: str,
    start_jd: float,
    end_jd: float,
) -> list[TransitEvent]:
    """
    Find when planet enters target_sign (longitude crosses sign boundary).
    Used as a sidecar fallback when ephemeris_daily window is exceeded.
    For 1900-2100 queries, the tool routes to ephemeris_daily.sign_ingress_today
    instead; this is the backstop for outside-window or sub-day-precision needs.
    """
    sign_idx = SIGN_TO_IDX[target_sign]
    target_lon = sign_idx * 30.0
    # Reuse the same crossing logic: search for longitude crossing target_lon.
    code = _swe_planet(swe, planet)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    return _find_crossings_by_bisection(
        swe, code, target_lon, orb_deg=0.0, start_jd=start_jd, end_jd=end_jd,
        event_type="ingress", transit_planet=planet, aspect_deg=None,
        target_sign=target_sign,
    )


# ── Helpers (private) ─────────────────────────────────────────────────────────

def _swe_planet(swe, name: str) -> int:
    name_lower = name.lower()
    if name_lower == "ketu":
        # Ketu is computed as Rahu + 180°. Caller must add 180 to longitude.
        return swe.MEAN_NODE  # marker; caller knows to invert
    return getattr(swe, PLANET_TO_SWE[name_lower])


def _planet_lon(swe, code: int, jd: float, flags: int) -> float:
    pos, _ = swe.calc_ut(jd, code, flags)
    return pos[0] % 360.0


def _shortest_arc_diff(lon_a: float, lon_b: float) -> float:
    diff = (lon_a - lon_b) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return diff


def _bisect_diff(swe, code_a: int, code_b: int, jd_lo: float, jd_hi: float,
                 orb_deg: float, flags: int, max_iter: int = 30) -> float:
    """Bisect to find the JD where |diff| crosses orb_deg."""
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2.0
        lon_a = _planet_lon(swe, code_a, jd_mid, flags)
        lon_b = _planet_lon(swe, code_b, jd_mid, flags)
        diff = abs(_shortest_arc_diff(lon_a, lon_b))
        if abs(diff - orb_deg) < 0.001:  # ~ minute precision
            return jd_mid
        if diff > orb_deg:
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2.0


def _find_crossings_by_bisection(swe, planet_code: int, target_lon: float,
                                   orb_deg: float, start_jd: float, end_jd: float,
                                   event_type: str, transit_planet: str,
                                   aspect_deg: Optional[int] = None,
                                   target_sign: Optional[str] = None,
                                   step: float = 1.0) -> list[TransitEvent]:
    """Day-step bracketing + bisection for longitude crossings."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    events: list[TransitEvent] = []
    jd = start_jd
    prev_lon = _planet_lon(swe, planet_code, jd, flags)
    while jd < end_jd:
        jd_next = jd + step
        cur_lon = _planet_lon(swe, planet_code, jd_next, flags)
        # Detect crossing of target_lon via shortest-arc sign change.
        prev_diff = (prev_lon - target_lon) % 360.0
        cur_diff = (cur_lon - target_lon) % 360.0
        if (prev_diff < 180.0) != (cur_diff < 180.0):
            # Hemisphere swap — crossing happened in [jd, jd_next].
            exact_jd = _bisect_longitude_to_target(
                swe, planet_code, target_lon, jd, jd_next, flags
            )
            extra = {}
            if aspect_deg is not None:
                extra["aspect_deg"] = aspect_deg
            if target_sign is not None:
                extra["target_sign"] = target_sign
            events.append(_build_event(swe, event_type, exact_jd, transit_planet,
                                        None, target_lon, aspect_deg, 0.0, extra))
        prev_lon = cur_lon
        jd = jd_next

    return events


def _bisect_longitude_to_target(swe, code: int, target: float, jd_lo: float,
                                  jd_hi: float, flags: int, max_iter: int = 30) -> float:
    for _ in range(max_iter):
        jd_mid = (jd_lo + jd_hi) / 2.0
        lon = _planet_lon(swe, code, jd_mid, flags)
        diff = (lon - target) % 360.0
        if diff > 180.0:
            diff -= 360.0
        if abs(diff) < 0.001:
            return jd_mid
        # Bisect based on sign of diff.
        lo_lon = _planet_lon(swe, code, jd_lo, flags)
        lo_diff = (lo_lon - target) % 360.0
        if lo_diff > 180.0:
            lo_diff -= 360.0
        if (diff > 0) == (lo_diff > 0):
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2.0


def _build_event(swe, event_type: str, jd: float, transit_planet: str,
                  secondary_planet: Optional[str], longitude: float,
                  aspect_deg: Optional[int], orb: float,
                  extra: Optional[dict] = None) -> TransitEvent:
    from .ephemeris_derivations import SIGNS, SIGN_TO_IDX
    # Re-fetch sign/nakshatra for the exact JD
    sign_idx = int(longitude // 30) % 12
    sign = SIGNS[sign_idx]
    nak_idx = int(longitude / (360.0 / 27)) % 27
    NAKSHATRAS = [  # local copy; could import from panchanga_derivations
        "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
        "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
        "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Moola","Purva Ashadha",
        "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
        "Uttara Bhadrapada","Revati",
    ]
    return TransitEvent(
        event_type=event_type,
        event_jd=jd,
        event_datetime_ist=jd_to_ist_iso(swe, jd),
        transit_planet=transit_planet,
        secondary_planet=secondary_planet,
        exact_longitude_deg=round(longitude, 7),
        orb_at_event_deg=round(orb, 4),
        sign=sign,
        nakshatra=NAKSHATRAS[nak_idx],
        extra=extra or {},
    )
```

**Important**: the executor should refactor the duplicated NAKSHATRAS list — import from `panchanga_derivations` rather than re-declare (mirrors the §4.B/§4.C SIGNS pattern).

### §4.2 New file — `platform/python-sidecar/routers/transit_search.py`

FastAPI router exposing `/transit_search` POST endpoint.

```python
"""
Sidecar /transit_search — live-compute aspect + conjunction search.
For ingress/station queries, the TS query_transit_event tool reads tables
directly. This endpoint is only invoked for aspect + conjunction cases.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
import swisseph as swe
from pipeline.transit_search import (
    find_aspect_events, find_conjunction_events, TransitEvent,
)

router = APIRouter()


class TransitSearchRequest(BaseModel):
    event_type: Literal["aspect", "conjunction"]
    start_date: str    # ISO YYYY-MM-DD
    end_date: str      # ISO YYYY-MM-DD; max 10 years from start_date
    # For aspect:
    transit_planet: Optional[str] = None
    target_longitude_deg: Optional[float] = None   # or target_planet (natal)
    target_planet_natal_longitude_deg: Optional[float] = None
    aspect_degrees: list[int] = Field(default_factory=lambda: [0, 60, 90, 120, 180])
    # For conjunction:
    planet_a: Optional[str] = None
    planet_b: Optional[str] = None
    # Common:
    orb_deg: float = 1.0


class TransitEventResponse(BaseModel):
    event_type: str
    event_jd: float
    event_datetime_ist: str
    transit_planet: str
    secondary_planet: Optional[str]
    exact_longitude_deg: float
    orb_at_event_deg: float
    sign: str
    nakshatra: str
    extra: dict


@router.post("/transit_search", response_model=list[TransitEventResponse])
async def transit_search(req: TransitSearchRequest):
    from datetime import datetime as _dt
    try:
        start_dt = _dt.fromisoformat(req.start_date)
        end_dt = _dt.fromisoformat(req.end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date: {e}")
    # Window cap
    if (end_dt - start_dt).days > 365 * 10:
        raise HTTPException(status_code=400, detail="Window exceeds 10-year cap")
    start_jd = swe.julday(start_dt.year, start_dt.month, start_dt.day, 0.0)
    end_jd = swe.julday(end_dt.year, end_dt.month, end_dt.day, 0.0)
    orb = max(0.0, min(3.0, req.orb_deg))

    if req.event_type == "aspect":
        if not req.transit_planet:
            raise HTTPException(status_code=400, detail="transit_planet required for aspect")
        target_lon = req.target_planet_natal_longitude_deg or req.target_longitude_deg
        if target_lon is None:
            raise HTTPException(status_code=400, detail="target longitude required")
        events = find_aspect_events(
            swe, req.transit_planet, target_lon, req.aspect_degrees,
            orb, start_jd, end_jd,
        )
    else:  # conjunction
        if not req.planet_a or not req.planet_b:
            raise HTTPException(status_code=400, detail="planet_a + planet_b required")
        events = find_conjunction_events(
            swe, req.planet_a, req.planet_b, orb, start_jd, end_jd,
        )
    return [e.__dict__ for e in events]
```

Register in `platform/python-sidecar/main.py`:

```python
from routers import (..., transit_search)
app.include_router(transit_search.router, prefix="", dependencies=[Depends(verify_api_key)])
```

(No prefix; the router declares `/transit_search` directly.)

### §4.3 New file — `platform/src/lib/retrieve/query_transit_event.ts`

29th retrieval tool. Routes by `event_type`:

```ts
/**
 * MARSYS-JIS Retrieval tool — query_transit_event (Phase 4D)
 *
 * Finds WHEN a transit event happens (versus query_ephemeris which lookups
 * WHAT is happening on a date). Four event classes:
 *   - 'ingress'      — planet enters a sign. Reads ephemeris_daily.sign_ingress_today.
 *   - 'station'      — planet stations retrograde or direct. Reads retrogrades table.
 *   - 'aspect'       — transit aspects natal-planet by N degrees. Live-compute via sidecar.
 *   - 'conjunction'  — two transit planets within orb. Live-compute via sidecar.
 *
 * Date range: 1900-01-01 to 2100-12-31 for table-backed queries; ±10 year
 * window cap for sidecar live-compute. Lahiri sidereal throughout.
 */

const TOOL_NAME = 'query_transit_event'
const TOOL_VERSION = '1.0.0'

export interface QueryTransitEventInput {
  event_type: 'ingress' | 'station' | 'aspect' | 'conjunction'
  start_date?: string   // YYYY-MM-DD; default: today
  end_date?: string     // YYYY-MM-DD; default: start + 1 year for ingress/station, + 2 years for aspect/conjunction
  // ingress:
  planet?: string
  target_sign?: string
  // station:
  station_type?: 'retrograde_start' | 'retrograde_end' | 'both'
  // aspect:
  transit_planet?: string
  natal_planet?: string                    // tool will look up natal longitude from chart_facts
  natal_longitude_deg?: number             // alternative if planner already has it
  aspect_degrees?: number[]                // default [0, 60, 90, 120, 180]
  orb_deg?: number                         // default 1.0, max 3.0
  // conjunction:
  planet_a?: string
  planet_b?: string
  // Common:
  limit?: number  // default 50, max 200
}
```

Implementation routes:

- `ingress`: `SELECT FROM ephemeris_daily WHERE sign_ingress_today = true AND planet = $1 AND sign = $2 AND date BETWEEN $3 AND $4 ORDER BY date ASC LIMIT $5`
- `station`: `SELECT FROM retrogrades WHERE planet = $1 [AND station_type = $2] AND date BETWEEN $3 AND $4 ORDER BY date ASC LIMIT $5`
- `aspect` / `conjunction`: POST sidecar `/transit_search` with the request body assembled from input

For `aspect` with `natal_planet`, the tool first SELECTs the natal longitude from `chart_facts` (category='planet', planet=$1) before calling the sidecar.

Same diagnostic-row fallback pattern as query_ephemeris when no events match.

### §4.4 Registry updates

- `platform/src/lib/retrieve/index.ts`: import `queryTransitEvent` + append to `RETRIEVAL_TOOLS` (count 28 → 29).
- `platform/src/lib/router/retrieval_capability_spec.ts`: append `query_transit_event` entry.
- `platform/src/lib/trace/types.ts`: append `'query_transit_event'` to `ALL_21_RETRIEVAL_TOOLS` (literal count 28 → 29).

### §4.5 RCS entry

```ts
const query_transit_event: RetrievalCapabilityEntry = {
  tool_name: 'query_transit_event',
  description:
    'Find WHEN transit events happen (versus query_ephemeris which is WHAT on a ' +
    'date). Four event classes: ingress (planet enters a sign — reads ' +
    'ephemeris_daily.sign_ingress_today from §4.B), station (planet stations ' +
    'retrograde/direct — reads retrogrades table), aspect (transit-to-natal by ' +
    'degree+orb — live compute via sidecar), conjunction (two transit planets ' +
    'within orb — live compute via sidecar). Lahiri sidereal. ' +
    'Use whenever the query asks "when next" / "when will" / "next time" / ' +
    '"when does X enter/aspect/conjunct/station". Pairs with query_ephemeris + ' +
    'query_panchanga under R-TC/R-PA for context; R-TE handles the search trigger.',
  data_surface:
    'L1 — table ephemeris_daily (sign_ingress_today + table-backed) + table ' +
    'retrogrades (station_type rows from migration 016). ' +
    'Live compute — sidecar POST /transit_search using swe.solcross/mooncross ' +
    'for Sun/Moon, day-step + bisection root-finding for other planets. ' +
    'Window cap ±10 years for sidecar queries.',
  supported_params:
    '{ event_type: "ingress"|"station"|"aspect"|"conjunction" (required); ' +
    'start_date?: YYYY-MM-DD; end_date?: YYYY-MM-DD; ' +
    'planet?: string (ingress); target_sign?: string (ingress); ' +
    'station_type?: "retrograde_start"|"retrograde_end"|"both" (station); ' +
    'transit_planet?: string (aspect); natal_planet?: string (aspect); ' +
    'natal_longitude_deg?: number (aspect, alternative to natal_planet); ' +
    'aspect_degrees?: number[] (aspect, default [0,60,90,120,180]); ' +
    'orb_deg?: number (default 1.0, max 3.0); ' +
    'planet_a?: string + planet_b?: string (conjunction); ' +
    'limit?: number (default 50, max 200) }',
  optimal_patterns: [
    'Next Jupiter sign-ingress: {event_type:"ingress", planet:"Jupiter", start_date:"2026-05-19", limit:5}',
    'Next Jupiter into Aries: {event_type:"ingress", planet:"Jupiter", target_sign:"Aries", start_date:"2026-05-19"}',
    'Mercury retrograde periods 2026: {event_type:"station", planet:"Mercury", start_date:"2026-01-01", end_date:"2026-12-31"}',
    'Saturn aspects to natal Moon next 2 years: {event_type:"aspect", transit_planet:"Saturn", natal_planet:"Moon", aspect_degrees:[180,90,60,120], orb_deg:1.5}',
    'Next Jupiter-Saturn conjunction: {event_type:"conjunction", planet_a:"Jupiter", planet_b:"Saturn", start_date:"2026-05-19", orb_deg:1.0}',
  ],
  cost_tier: 'medium',
  requires_temporal: true,
}
```

### §4.6 PLANNER_PROMPT amendment — R-TE rule

Append to `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` §3, after R-PA:

```
  R-TE. TRANSIT EVENT SEARCH: For queries asking WHEN an event happens (versus
       WHAT is happening at a date), attach `query_transit_event` at priority 1.
       This is search-mode; R-TC (query_ephemeris lookup) and R-PA (panchanga
       lookup) can also fire as priority-2 context if the search result will be
       interpreted.

       Trigger keywords:
         - "when next" / "when will" / "next time" / "next occurrence"
         - "when does X enter Y" / "Jupiter going into" / "ingress"
         - "when X aspects Y" / "transit aspect" / "Saturn aspecting my"
         - "when X conjuncts Y" / "Jupiter-Saturn conjunction" / "graha-yuddha"
         - "when X retrograde" / "station retrograde" / "Mercury retrograde next"
         - "when X turns direct" / "station direct"

       Event-type selection:
         - "ingress" — query mentions sign/zodiac entry: "enters Cancer",
           "into Aries", "sign change"
         - "station" — query mentions retrograde or direct: "Mercury retrograde
           next", "Saturn stations direct"
         - "aspect" — query mentions aspect/conjunction to a NATAL planet:
           "Saturn aspecting my Moon", "transit Jupiter trine natal Sun"
         - "conjunction" — query mentions two TRANSIT planets coming together:
           "Jupiter-Saturn conjunction", "when do Mars and Saturn meet"

       Date param selection:
         - Default end_date = start_date + 1 year for ingress/station,
           + 2 years for aspect/conjunction.
         - "in 2027" / specific year → start_date + end_date both within year.
         - "in my X dasha" → start_date + end_date matching dasha window.

       Exclusions:
         - Pure positional queries (WHAT, not WHEN): use query_ephemeris under R-TC.
         - Eclipse search: continues to use temporal.eclipse_query (existing,
           not duplicated in query_transit_event).
         - Vedic special-aspect queries (Mars 4/8, Jupiter 5/9, Saturn 3/10):
           the planner emits aspect_degrees per planet's classical pattern, OR
           leaves it to synthesis to interpret 7th-aspect (180°) and let
           cgm_graph_walk surface Vedic special-aspect membership separately.
```

Also append a §4.27 few-shot example showing R-TE firing for a transit aspect search.

### §4.7 Graha-yuddha docstring update — `ephemeris_derivations.compute_graha_yuddha`

No code change. Update docstring:

```python
def compute_graha_yuddha(
    planet: str,
    longitude_deg: float,
    same_day_positions: dict[str, float],
) -> Optional[str]:
    """
    Return the OTHER planet's name when this planet is within 1° of another.
    Only checked among {mars, mercury, jupiter, venus, saturn}.

    Note on form (carried forward from §4.B executor scope-note, resolved in §4.D):
    This function uses the LONGITUDE-ONLY form of graha-yuddha — the classical
    BPHS strict form additionally requires the planets' ecliptic latitudes to
    differ by less than ~0.5°. Modern Vedic practice (including most production
    Jyotish software: Jagannatha Hora, Parashara's Light) commonly relaxes the
    latitude requirement because planet pairs at the same ecliptic longitude
    nearly always have similar enough latitudes for visual conjunction, and
    surface-level Vedic interpretation uses sign+degree position primarily.
    The longitude-only form is therefore the ACCEPTED VEDIC APPROXIMATION for
    this codebase. If a future workstream requires BPHS strict-form, extend
    this function to accept a `latitudes` dict and add the latitude check.
    """
```

Same explicit acceptance documented in the function's module-header comment block.

### §4.8 Tests

**Python pytest** — new file `platform/python-sidecar/pipeline/__tests__/test_transit_search.py`. ~12 tests, mocked `swe` where possible:

1. `test_aspect_finds_zero_crossing` — synthetic case: Sun at longitude approaching target; assert event returned at expected JD.
2. `test_aspect_orb_filter_excludes_far_misses` — events outside orb_deg are excluded.
3. `test_conjunction_finds_close_approach` — two planets approaching within orb; assert event.
4. `test_conjunction_excludes_when_orb_too_wide` — planets within orb 5° not returned when orb_deg=1.
5. `test_ingress_finds_aries_crossing` — synthetic ascending longitude; crossing at 0°/Aries returns event.
6. `test_window_cap_rejects_over_10_years` — request with 11-year window raises.
7. `test_sun_uses_solcross` — mock `swe.solcross`, assert it's called for transit_planet="sun".
8. `test_moon_uses_mooncross` — same for moon.
9. `test_mars_uses_bisection` — `swe.solcross` NOT called for transit_planet="mars"; `swe.calc_ut` called multiple times instead.
10. `test_event_datetime_in_ist` — event_datetime_ist string is UTC+5:30 of event_jd (carries forward §4.C vara-IST note).
11. `test_jd_to_ist_iso_handles_day_rollover` — JD whose UTC is 23:00 returns IST 04:30 next day.
12. `test_lahiri_set_sid_mode_called` — verify `swe.set_sid_mode(swe.SIDM_LAHIRI)` invoked before computations.

**TypeScript vitest** — new file `platform/src/lib/retrieve/__tests__/query_transit_event.test.ts`. ~5 tests:

1. `routes ingress query to ephemeris_daily WHERE sign_ingress_today` — mock storage, assert SQL.
2. `routes station query to retrogrades table` — mock storage, assert SQL contains `FROM retrogrades`.
3. `routes aspect query to sidecar POST` — mock fetch, assert URL ends with `/transit_search` and body has `event_type: 'aspect'`.
4. `looks up natal longitude from chart_facts when natal_planet provided` — mock storage returns natal Moon longitude; assert sidecar request body has the resolved longitude.
5. `returns diagnostic row when no events match` — empty result, single confidence-0 row.

### §4.9 Golden-set entries GT.078–GT.082

```json
{
  "id": "GT.078",
  "query": "When does Jupiter next enter Aries?",
  "query_class": "factual",
  "required_tools": ["query_transit_event"],
  "forbidden_tools": ["vector_search", "pattern_register"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Jupiter"],
  "domains": [],
  "forward_looking": true,
  "notes": "R-TE event_type=ingress, planet=Jupiter, target_sign=Aries. R-FACT enforces single-tool synthesis."
},
{
  "id": "GT.079",
  "query": "When is Mercury retrograde next?",
  "query_class": "factual",
  "required_tools": ["query_transit_event"],
  "forbidden_tools": ["vector_search"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Mercury"],
  "domains": [],
  "forward_looking": true,
  "notes": "R-TE event_type=station, planet=Mercury, station_type=retrograde_start."
},
{
  "id": "GT.080",
  "query": "When will Saturn aspect my natal Moon next?",
  "query_class": "predictive",
  "required_tools": ["query_transit_event", "msr_sql"],
  "forbidden_tools": [],
  "asset_bundle_must_include": ["FORENSIC", "CGM"],
  "planets": ["Saturn", "Moon"],
  "domains": [],
  "forward_looking": true,
  "notes": "R-TE event_type=aspect, transit_planet=Saturn, natal_planet=Moon, aspect_degrees=[180,90,60,120]. msr_sql for natal Moon signals to interpret the upcoming aspect."
},
{
  "id": "GT.081",
  "query": "When do Jupiter and Saturn next conjunct?",
  "query_class": "factual",
  "required_tools": ["query_transit_event"],
  "forbidden_tools": ["vector_search"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Jupiter", "Saturn"],
  "domains": [],
  "forward_looking": true,
  "notes": "R-TE event_type=conjunction, planet_a=Jupiter, planet_b=Saturn. orb_deg default 1.0."
},
{
  "id": "GT.082",
  "query": "What sign is Jupiter in right now?",
  "query_class": "factual",
  "required_tools": ["query_ephemeris"],
  "forbidden_tools": ["query_transit_event", "vector_search"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Jupiter"],
  "domains": [],
  "forward_looking": false,
  "notes": "NEGATIVE for R-TE. WHAT-not-WHEN query → query_ephemeris (R-TC) is the right surface. query_transit_event FORBIDDEN — search-mode doesn't fire for positional lookups."
}
```

Paired regression-baseline extension same shape.

### §4.10 Runbook addendum — `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md` §5

Append:

```markdown
## §5 Transit Search Sidecar Endpoint (Phase 4D)

No bootstrap or precompute needed. The new `/transit_search` endpoint is live-compute via Swiss Ephemeris. It depends on the sidecar service being running and reachable from the web tier.

### Verification post-merge

1. Confirm sidecar deployment includes the new router:
   ```bash
   curl -X POST https://<sidecar>/transit_search \
     -H "x-api-key: $SIDECAR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"event_type":"conjunction","planet_a":"Jupiter","planet_b":"Saturn","start_date":"2026-05-19","end_date":"2027-05-19","orb_deg":1.0}'
   ```
   Expect: JSON array of conjunction events (likely empty or 1-2 events for that window).

2. Latency expectation: aspect/conjunction searches over 2-year windows ~500ms-2s. Ingress and station queries hit Postgres directly via the TS tool and are <100ms.
```

## §5 Verification gates (pre-commit, NOT post-deploy)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

# G1: TypeScript compiles
npx tsc --noEmit

# G2: TS unit tests
npx vitest run src/lib/retrieve/__tests__/query_transit_event.test.ts
npx vitest run src/lib/retrieve/__tests__/

# G3: Python sidecar unit tests
cd python-sidecar
python -m pytest pipeline/__tests__/test_transit_search.py -v
cd ..

# G4: planner_regression_gate
npx vitest run tests/eval/planner_regression_gate.test.ts
```

All gates green before commit.

## §6 Commit + push + Campaign close

```bash
git add platform/python-sidecar/pipeline/transit_search.py \
        platform/python-sidecar/routers/transit_search.py \
        platform/python-sidecar/main.py \
        platform/python-sidecar/pipeline/__tests__/test_transit_search.py \
        platform/python-sidecar/pipeline/ephemeris_derivations.py \
        platform/src/lib/retrieve/query_transit_event.ts \
        platform/src/lib/retrieve/__tests__/query_transit_event.test.ts \
        platform/src/lib/retrieve/index.ts \
        platform/src/lib/router/retrieval_capability_spec.ts \
        platform/src/lib/trace/types.ts \
        00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md \
        00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md \
        platform/tests/eval/planner_golden_set.json \
        platform/tests/eval/fixtures/regression_baseline.json

git commit -m "feat(transit-search): query_transit_event tool + sidecar /transit_search (§4.D)

Phase 4D — the FINAL sub-phase of the ephemeris accessibility campaign.
Adds event-SEARCH (when does X happen?) on top of the lookup surface from
§4.A-§4.C (what is happening on date Y?).

Tool: query_transit_event (29th in registry)
Routes four event classes:
  - ingress      → ephemeris_daily.sign_ingress_today (§4.B-precomputed)
  - station      → retrogrades table (migration 016)
  - aspect       → sidecar /transit_search live compute
  - conjunction  → sidecar /transit_search live compute

Sidecar /transit_search uses swe.solcross/mooncross for Sun/Moon longitude
crossings (fast, exact) and day-step + bisection root-finding for other
planets. ±10 year window cap. Lahiri sidereal throughout.

PLANNER_PROMPT v2.0.5: R-TE (Transit Event) rule. Fires for 'when next' /
'when will' / 'when does X enter/aspect/conjunct/retrograde' queries.

Graha-yuddha (compute_graha_yuddha in ephemeris_derivations.py) docstring
update: formally documents longitude-only form as the accepted Vedic
approximation per modern practitioner consensus. Resolves §4.B executor
scope-note carry-forward. No code change.

Tests: 12 Python pytest cases (aspect/conjunction/ingress synthetic cases,
solcross/mooncross routing, window cap, IST datetime carry-forward from §4.C)
+ 5 TS vitest cases (routing logic, natal-lookup, diagnostic fallback).

Golden set: GT.078-082 (4 positive event-search + 1 negative WHAT-not-WHEN).
RUNBOOK §5 addendum for sidecar endpoint verification.

PHASE 4 EPHEMERIS ACCESSIBILITY CAMPAIGN CLOSED.
Tool count: 26 → 29. Next: PHASE_4_CLOSE_v1_0.md sealing artifact
+ consolidated answer:eval batch (operator-supervised, post-deploy).

Refs: 00_ARCHITECTURE/briefs/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md
Refs: 00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md"

git push origin analysis/backend-data-pipeline-perf-audit
```

### §6.1 Campaign close artifact

After the §4.D commit lands, author `00_ARCHITECTURE/PHASE_4_CLOSE_v1_0.md` per master plan §E. Contents:

```markdown
---
canonical_id: PHASE_4_CLOSE
version: 1.0
status: CURRENT (campaign sealing artifact)
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
closed_on: 2026-05-19
final_commit: <§4.D closing SHA>
---

# Phase 4 — Ephemeris Accessibility Campaign · CLOSE

## What shipped (4 sub-phases, 4 days)

| Sub | Commit | Headline |
|---|---|---|
| 4A | bd41f13 | query_ephemeris tool (27th) + R-TC transit-context rule |
| 4B | c63ef9f | Migration 059 + 7 derived columns + MEAN_NODE Rahu + BPHS dignity/combust |
| 4C | abab885 | Migration 060 + panchanga_daily + query_panchanga (28th) + R-PA rule |
| 4D | <SHA>   | query_transit_event (29th) + sidecar /transit_search + R-TE rule |

Tool count: 26 → 29.
Planner rules: R-TC, R-PA, R-TE added.

## Production deploys deferred to native

Three operator-supervised data operations remain (none execute autonomously):
- ephemeris_daily full rebuild (Path A — MEAN_NODE + 7 derived columns) → ~4-6h
- panchanga_daily bootstrap → ~30 min
- /transit_search sidecar verification (~5 min)

All steps in RUNBOOK_EPHEMERIS_REBUILD_v1_0.md.

## Consolidated answer:eval

Per campaign discipline (declared 2026-05-17), production answer:eval against
the new 29-tool registry runs AFTER all 3 operator data operations complete.
This is the consolidated batch the native referenced in the original
retrieval-tools campaign agreement.

## Lessons captured

- ephemeris_derivations.py established the pure-Python derivation-module
  pattern. §4.C and §4.D both reused it, importing canonical constants
  (SIGNS, SIGN_TO_IDX, NAKSHATRAS) rather than re-declaring. Single source
  of truth for naming.
- Pre-commit verification + native-supervised data operation = the right
  split for data-infrastructure work. Code merges fast; data rebuilds get
  the human review they need.
- Two semantics-carry-forwards from sub-phase to sub-phase (tithi
  integer-floor, vara IST datetime) demonstrated that executor scope-notes
  ARE the right loop-back channel between sub-phases.
```

## §7 Acceptance criteria

- [ ] `transit_search.py` ships with three search algorithms + TransitEvent dataclass + IST conversion helper.
- [ ] `routers/transit_search.py` exposes POST `/transit_search` with ±10y window cap and request validation.
- [ ] Sidecar `main.py` registers the new router with API-key dependency.
- [ ] `query_transit_event.ts` (29th tool) routes ingress→ephemeris_daily, station→retrogrades, aspect+conjunction→sidecar. Natal-longitude lookup from chart_facts when `natal_planet` provided.
- [ ] Registry counts: 28 → 29 in all three (RETRIEVAL_TOOLS, RCS, ALL_21_RETRIEVAL_TOOLS).
- [ ] RCS entry with description + params + 5 optimal patterns.
- [ ] R-TE rule appended to PLANNER_PROMPT_v2_0.md §3 + §4.27 few-shot example.
- [ ] Graha-yuddha docstring + module-header comment updated in `ephemeris_derivations.py` documenting longitude-only acceptance (no code change).
- [ ] 12 Python pytests pass; 5 TS vitests pass.
- [ ] GT.078-082 added to golden set + paired regression baseline (4 positive + 1 negative).
- [ ] RUNBOOK §5 sidecar verification section added.
- [ ] `tsc --noEmit` clean.
- [ ] `planner_regression_gate.test.ts` green (no drop on existing 77-entry set after adding 5).
- [ ] Commit lands on `analysis/backend-data-pipeline-perf-audit`.
- [ ] No Chat V2 files touched; no autonomous answer:eval.
- [ ] Master plan §B 4D block → `status: CLOSED` + closing_commit_sha.
- [ ] `PHASE_4_CLOSE_v1_0.md` authored at `00_ARCHITECTURE/` per §6.1 above.

## §8 Report back (final report for the campaign)

When complete:

1. Closing commit SHA + `git log --oneline -5`.
2. All gates pass/fail.
3. Python pytest output (full).
4. TS vitest summary (full retrieve suite count).
5. Confirmation that `PHASE_4_CLOSE_v1_0.md` was authored.
6. Final tool-count check: 29 in all three registries.
7. Recommendation: should the operator-supervised data operations (Path A rebuild + panchanga bootstrap) run BEFORE the consolidated answer:eval, or in parallel with it? (Path A rebuild changes Rahu longitudes; answer:eval results will be different pre-rebuild vs post.)

The native will then trigger the operator data operations + the consolidated answer:eval.
