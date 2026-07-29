"""
pipeline/orchestrator/writers/bg_sky_calendar.py
L0 Brahmagyan chart-independent sky-event diary writer — seeds bg_sky_events.

ṢAḌ-DARŚANA campaign, registry item 3 ("Sky-event calendar: ingresses, stations,
eclipse-to-natal, returns, Guru-Śani double-transit"). SHAD_DARSHANA_BRIEF_v2_0.md
§2 names this writer `bg_sky_calendar.py` — "chart-independent sky-event diary
(ingresses, stations, eclipses, returns, double-transit geometry); per-chart
contact joins live in `ka_kshetra` stage 1."

WHAT THIS WRITER BUILDS (and does not build)
─────────────────────────────────────────────
A single chart-INDEPENDENT reference table of real astronomical events — an
almanac, like `bg_ephemeris` (daily positions) or `bg_cohort` (synthetic
population), not a per-chart artifact. Four event families, all real
pyswisseph computations (CLAUDE.md §N.4 / B.10 — no fabricated values):

  1. SIGN INGRESSES — for each of the 9 grahas (Sun, Moon, Mars, Mercury,
     Jupiter, Venus, Saturn, Rahu, Ketu), every sidereal-sign-boundary
     crossing across the horizon.
  2. STATIONS (retrograde/direct) — for the 5 classical planets that station
     (Mars, Mercury, Jupiter, Venus, Saturn). Sun/Moon never station (no
     retrograde motion in geocentric longitude) and are correctly excluded.
     **Rahu/Ketu decision (documented, not silently omitted): this writer
     does NOT synthesize station events for the nodes.** The underlying
     TRUE_NODE model does have brief prograde excursions (a real oscillation
     around its mean retrograde motion), but classical Vedic convention
     treats Rahu/Ketu as ALWAYS retrograde and assigns no "station"
     significance to those excursions — assigning one would be inventing a
     classical event category that does not exist in the tradition this
     instrument serves. This mirrors `pipeline.transit_search.
     find_station_events`'s own existing exclusion of Rahu/Ketu/Sun/Moon
     (see REUSE note below) — an inherited, pre-existing convention in this
     codebase, applied consistently here, not a new judgment call.
  3. ECLIPSES — solar and lunar eclipse TIMING only (max/begin/end instants +
     classical type: total/annular/partial/hybrid for solar,
     total/partial/penumbral for lunar). Computed via pyswisseph's dedicated
     global eclipse-finding functions (`sol_eclipse_when_glob`,
     `lun_eclipse_when`) — NOT via the node-luminary conjunction proxy in
     `pipeline.transit_search.find_eclipse_proximity_events` (that function
     flags "Rahu/Ketu near Sun/Moon" windows, which is a coarse orb-based
     proxy, not real eclipse geometry; a global almanac deserves the real
     computation, which pyswisseph already provides natively — still zero
     custom astronomical math). Per-location visibility/magnitude
     (`sol_eclipse_how`/`lun_eclipse_how`) is deliberately NOT computed here:
     both require a geographic position, which makes them chart/observer-
     specific, not chart-independent — exactly the boundary the brief draws
     for "eclipse-to-natal" (§2 file map: "per-chart contact joins live in
     `ka_kshetra` stage 1"). This writer stores the TIMING; the visibility-
     to-a-specific-birth-place join is `ka_kshetra`'s job, later.
  4. DOUBLE-TRANSIT GEOMETRY — conjunction events between two slow-moving
     grahas. At minimum, Jupiter-Saturn ("Guru-Śani double-transit" — the
     brief's own paradigm case, cited by name in SHAD_DARSHANA_BRIEF_v2_0.md
     §2). `DOUBLE_TRANSIT_PAIRS` below is the extensible registry of pairs;
     Jupiter-Saturn is the only pair populated at this build (the classical
     "great conjunction" cycle, ~20 years) — additional slow-mover pairs can
     be added to that list in a future rebuild without a schema change.

WHAT THIS WRITER DOES NOT BUILD:
  - RETURNS (solar return, etc.) — a "return" is inherently chart-specific
    (it needs a NATAL degree to return to). SHAD_DARSHANA_BRIEF_v2_0.md §2's
    own file map is explicit: chart-independent stock lives here; "per-chart
    contact joins live in `ka_kshetra` stage 1." Computing returns against a
    natal position has no meaning in a chart-independent table, so this is a
    scope boundary drawn from the brief's own words, not an omission.
  - Eclipse-to-natal / ingress-to-natal-house joins — same reasoning: any
    "this event touches THIS chart's houses/points" computation is a
    per-chart join, `ka_kshetra`'s job (brief §2), not this writer's.

REUSE — the existing ephemeris/event-search layer (per task instruction: do
NOT reimplement astronomical math):
  `pipeline.transit_search` (built for `ka_gochara`, L3) already implements
  real pyswisseph-backed event search over Lahiri sidereal longitudes:
    - `find_ingress_events(swe, planet, target_sign, start_jd, end_jd)` —
      reused AS-IS, once per (planet, sign) pair. The underlying position
      lookup (`_get_planet_pos`) is `functools.lru_cache`-memoized on the
      exact (swe, jd, planet_id, flags) tuple, so calling this 12x per
      planet (once per target sign) over the SAME start/end/step is cheap —
      the 2nd..12th calls are overwhelmingly cache hits, not recomputation
      (measured: 9 planets x 12 signs x 5-year window = 1055 events in
      ~0.47s locally; the algorithm is linear in horizon length).
    - `find_station_events(swe, planet, start_jd, end_jd)` — reused AS-IS
      for the 5 classical stationing planets (already excludes Rahu/Ketu/
      Sun/Moon internally — see the Rahu/Ketu note above).
    - `find_conjunction_events(swe, planet_a, planet_b, orb_deg, start_jd,
      end_jd)` — reused AS-IS for double-transit geometry.
    - `_jd_to_ist_iso`, `SIGNS` reused for display/parsing.
  Only the eclipse family has no existing wrapper in `transit_search` (that
  module's `find_eclipse_proximity_events` is the proxy discussed above, not
  the real thing) — `_scan_eclipses()` below calls pyswisseph's own
  `sol_eclipse_when_glob` / `lun_eclipse_when` directly, which IS the
  existing (native swisseph) astronomical-math layer for eclipses; nothing
  here re-derives eclipse geometry from first principles.

HORIZON (rolling; re-runnable to extend — brief §2.5.6):
  HISTORY_START = 1900-01-01 (fixed). Chosen to match `bg_ephemeris`'s own
  build start exactly — this writer's real-time swisseph computation is not
  actually bounded by `ephemeris_daily`'s stored range (it calls swisseph
  live, which supports any DE441-covered date), but matching the existing
  almanac's start gives one consistent "how far back does this instrument's
  reference astronomy go" answer across both L0 sky assets, and comfortably
  covers retrodiction for both canonical charts (1984, pre-1984 ancestor
  generation context) with wide margin.
  FORWARD_HORIZON_YEARS = 10, computed as `today + 10y` AT RUN TIME (not a
  fixed end date baked in). This is deliberately NOT the brief's own "~5y
  forward, rolling" figure cited elsewhere for lattice-type L0 assets
  (`bg_muhurta_lattice`) — a sky calendar is reused for RETRODICTION
  (period-echo mining, EXPLAIN counterfactuals over the native's full life)
  at least as much as for forward election windows, so a shallow 5-year
  forward edge would undersell it. 10 years forward is a defensible middle
  ground: long enough that a rebuild cadence of a few times a year keeps the
  forward edge comfortably ahead of "now" without the writer needing to
  recompute a 250-year span on every rebuild. Per brief §2.5.6, this asset's
  forward edge ages and is refreshed via an explicit super-admin L0 refresh
  trigger on a cadence recorded in the campaign state ledger; the envelope's
  freshness attestation (a later-wave concern, not this writer's) is what
  serves the staleness flag honestly if that cadence lapses. Because the
  forward bound is computed from `date.today()` at every run and idempotency
  is ON CONFLICT DO NOTHING (natural-key: event_type + bodies + rounded jd),
  a later re-run naturally extends the calendar forward without duplicating
  or mutating previously-computed events — this is the "re-runnable to
  extend the horizon, not a one-shot" property the brief requires.

RETURNS SCOPE DECISION (explicit, for the PR record): registry item 3 lists
  "returns" among the sky-event families, but per the brief's own §2 file
  map quote above, chart-independent stock lives here and "per-chart contact
  joins live in `ka_kshetra` stage 1" — a return event is defined relative
  to a natal degree, which does not exist in a chart-independent context.
  This writer deliberately does NOT compute returns; that is `ka_kshetra`'s
  job (a future wave), not a gap in this one.

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
§2):
- uses ctx.db_conn exclusively (never opens, commits, or closes it)
- returns WriterResult with actual rows_inserted
- honours ctx.dry_run
- LIGHT writer (single `run(ctx)`) — the full-horizon compute is seconds,
  not the ">~10 min or > a few hundred k rows" heavy threshold (§5 of the
  convergence-close doc); this mirrors `bg_ephemeris`'s and `bg_cohort`'s own
  choice of the light-writer shape for similarly large deterministic L0
  builds (both do their whole multi-hundred-thousand-row / multi-decade
  compute inside one `run()`, batching INSERTs, with no sub-step plan).

L0 idempotency (CLAUDE.md §N.3): global reference table, `ON CONFLICT
(natural key) DO NOTHING` — safe to upsert; deterministic recomputation
of an already-covered window reproduces the same events (see natural-key
note in the migration), so a re-run only WIDENS coverage, never duplicates.

ZERO LLM use. Pure deterministic pyswisseph computation via the existing
`pipeline.transit_search` event-search layer (+ pyswisseph's native eclipse
functions for the one family that layer doesn't already wrap).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    WriterBase,
    WriterResult,
    register,
)

logger = logging.getLogger(__name__)

# ── Horizon (documented in full in the module docstring above) ───────────────

HISTORY_START = date(1900, 1, 1)
FORWARD_HORIZON_YEARS = 10
SAMPLING_METHOD_VERSION = "sky_calendar_ingress_station_eclipse_doubletransit_v1"
SOURCE_CITATION = (
    "pyswisseph DE441 (Swiss Ephemeris) via pipeline.transit_search + "
    "sol_eclipse_when_glob/lun_eclipse_when; Lahiri ayanamsha"
)
AYANAMSHA_KEY = "lahiri"

# The 9 grahas tracked for ingress events.
INGRESS_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

# The 5 classical planets that station. Sun/Moon never station; Rahu/Ketu are
# deliberately excluded from station events per the module docstring's
# "Rahu/Ketu decision" note (an inherited convention, not a new omission).
STATION_PLANETS: tuple[str, ...] = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Double-transit pairs. Jupiter-Saturn is the brief's own paradigm case
# ("Guru-Śani double-transit"); the list is intentionally extensible for a
# future rebuild without a schema change.
DOUBLE_TRANSIT_PAIRS: tuple[tuple[str, str], ...] = (
    ("Jupiter", "Saturn"),
)
DOUBLE_TRANSIT_ORB_DEG = 1.0

SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def compute_horizon(today: date | None = None) -> tuple[date, date]:
    """
    Pure function: (history_start, forward_end) for a given `today`.

    Forward end is `today + FORWARD_HORIZON_YEARS` years — computed fresh
    every call, which is what makes the writer's horizon "rolling" across
    re-runs (see module docstring HORIZON section). No DB/swisseph
    dependency — independently unit-testable.
    """
    if today is None:
        today = date.today()
    try:
        forward_end = today.replace(year=today.year + FORWARD_HORIZON_YEARS)
    except ValueError:
        # Feb 29 on a non-leap target year -- fall back to Feb 28.
        forward_end = today.replace(year=today.year + FORWARD_HORIZON_YEARS, day=28)
    return HISTORY_START, forward_end


@dataclass
class _Row:
    event_type: str
    primary_body: str
    secondary_body: str | None
    event_jd: float
    event_datetime_utc: Any
    sign: str | None
    nakshatra: str | None
    longitude_deg: float | None
    speed_dps: float | None
    detail: dict[str, Any]


def _event_jd_to_utc(swe: Any, jd: float):
    """Convert a Julian day (UT) to a Python datetime (UTC, naive)."""
    from datetime import datetime

    y, m, d, hour_dec = swe.revjul(jd)
    h = int(hour_dec)
    mn = int((hour_dec - h) * 60)
    s = int(((hour_dec - h) * 60 - mn) * 60)
    s = max(0, min(59, s))
    try:
        return datetime(int(y), int(m), int(d), h, mn, s)
    except ValueError:
        return datetime(int(y), int(m), int(d), 0, 0, 0)


# ── Family 1: ingresses ───────────────────────────────────────────────────────

def scan_ingresses(swe: Any, start_jd: float, end_jd: float) -> list[_Row]:
    """
    All sign-ingress events for the 9 tracked grahas over [start_jd, end_jd].

    Reuses `pipeline.transit_search.find_ingress_events` as-is (see module
    docstring REUSE note for the cache-efficiency rationale of the 12-call
    per-planet pattern).

    KNOWN FLOATING-POINT BOUNDARY ARTIFACT in the reused function (found
    while testing this writer, NOT introduced by it): `find_ingress_events`
    bisects to the exact crossing instant, then re-derives the `sign` field
    from the bisected `exact_longitude_deg` via `_sign_nak(lon)`. At the
    converged boundary, `lon` can land a hair (~1e-7 deg, sub-millisecond of
    time) on EITHER side of the cusp -- e.g. observed `299.9999997938...`
    instead of `300.0` when searching for a Capricorn->Aquarius crossing --
    so `_sign_nak` occasionally reports the PRIOR sign even though the
    search correctly found the crossing into `target_sign` and the timing
    itself is accurate to the bisection's tolerance. This is a pre-existing
    property of `pipeline.transit_search` (shared with `ka_gochara`/L3 and
    any other caller doing a target-sign search near a cusp) -- NOT fixed
    here, since that module is owned by a different asset (ka_gochara) and
    a shared-utility change is out of this writer's scope. It is worth
    flagging for whoever next builds on `find_ingress_events` near a sign
    cusp: the returned `.sign` field is occasionally off-by-one-sign at
    the exact boundary; `.event_jd` (the timing) is not affected.
    This writer sidesteps it entirely by storing the LOOP'S OWN
    `target_sign` as the authoritative `sign` value rather than re-trusting
    the re-derived `ev.sign` -- the loop already knows, unambiguously,
    which sign it searched for; there is no need to re-derive it from a
    longitude that is by construction adjacent to a discontinuity.
    """
    from pipeline.transit_search import find_ingress_events

    rows: list[_Row] = []
    for planet in INGRESS_PLANETS:
        for target_sign in SIGN_NAMES:
            events = find_ingress_events(swe, planet, target_sign, start_jd, end_jd)
            for ev in events:
                rows.append(_Row(
                    event_type="ingress",
                    primary_body=planet,
                    secondary_body=None,
                    event_jd=ev.event_jd,
                    event_datetime_utc=_event_jd_to_utc(swe, ev.event_jd),
                    sign=target_sign,  # authoritative -- see docstring note above
                    nakshatra=ev.nakshatra,
                    longitude_deg=ev.exact_longitude_deg,
                    speed_dps=ev.speed_at_event_dps,
                    detail={"target_sign": target_sign},
                ))
    return rows


# ── Family 2: stations ────────────────────────────────────────────────────────

def scan_stations(swe: Any, start_jd: float, end_jd: float) -> list[_Row]:
    """
    Retrograde/direct station events for the 5 classical stationing planets.

    Reuses `pipeline.transit_search.find_station_events` as-is.
    """
    from pipeline.transit_search import find_station_events

    rows: list[_Row] = []
    for planet in STATION_PLANETS:
        events = find_station_events(swe, planet, start_jd, end_jd)
        for ev in events:
            rows.append(_Row(
                event_type="station",
                primary_body=planet,
                secondary_body=None,
                event_jd=ev.event_jd,
                event_datetime_utc=_event_jd_to_utc(swe, ev.event_jd),
                sign=ev.sign,
                nakshatra=ev.nakshatra,
                longitude_deg=ev.exact_longitude_deg,
                speed_dps=ev.speed_at_event_dps,
                detail={"station_type": ev.extra.get("station_type")},
            ))
    return rows


# ── Family 3: eclipses (real swisseph eclipse-finding, not the orb proxy) ────

def scan_eclipses(swe: Any, start_jd: float, end_jd: float) -> list[_Row]:
    """
    Solar + lunar eclipse TIMING events over [start_jd, end_jd].

    Calls pyswisseph's own global eclipse-finding functions directly
    (`sol_eclipse_when_glob`, `lun_eclipse_when`) -- see module docstring
    for why this is used instead of transit_search's node-conjunction proxy.
    Per-location visibility/magnitude is out of scope here (see docstring).
    """
    rows: list[_Row] = []
    rows.extend(_scan_solar_eclipses(swe, start_jd, end_jd))
    rows.extend(_scan_lunar_eclipses(swe, start_jd, end_jd))
    return rows


_SOLAR_TYPE_BITS = (
    ("total", "ECL_TOTAL"),
    ("annular", "ECL_ANNULAR"),
    ("annular_total", "ECL_ANNULAR_TOTAL"),
    ("partial", "ECL_PARTIAL"),
)
_LUNAR_TYPE_BITS = (
    ("total", "ECL_TOTAL"),
    ("partial", "ECL_PARTIAL"),
    ("penumbral", "ECL_PENUMBRAL"),
)


def _decode_eclipse_type(swe: Any, retflag: int, bits: tuple[tuple[str, str], ...]) -> str:
    for label, const_name in bits:
        const = getattr(swe, const_name, None)
        if const is not None and (retflag & const):
            return label
    return "unknown"


def _scan_solar_eclipses(swe: Any, start_jd: float, end_jd: float) -> list[_Row]:
    rows: list[_Row] = []
    jd = start_jd
    guard = 0
    # Solar eclipses recur roughly every ~173 days at minimum; a horizon of
    # decades is at most a few hundred iterations -- the guard is a defensive
    # cap against any pathological infinite loop, not a real limit.
    max_iterations = 2000
    while jd < end_jd and guard < max_iterations:
        guard += 1
        try:
            retflag, tret = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
        except Exception as exc:  # pragma: no cover -- swisseph search exhaustion at range edges
            logger.warning("[bg_sky_calendar] sol_eclipse_when_glob halted at jd=%s: %s", jd, exc)
            break
        max_jd = tret[0]
        if max_jd > end_jd:
            break
        begin_jd, end_jd_ev = tret[2], tret[3]
        is_central = bool(retflag & getattr(swe, "ECL_CENTRAL", 0))
        eclipse_type = _decode_eclipse_type(swe, retflag, _SOLAR_TYPE_BITS)
        lon, speed = _sun_position(swe, max_jd)
        sign = SIGN_NAMES[int(lon // 30.0) % 12]
        rows.append(_Row(
            event_type="eclipse_solar",
            primary_body="Sun",
            secondary_body="Moon",
            event_jd=max_jd,
            event_datetime_utc=_event_jd_to_utc(swe, max_jd),
            sign=sign,
            nakshatra=None,
            longitude_deg=round(lon, 4),
            speed_dps=round(speed, 6),
            detail={
                "eclipse_type": eclipse_type,
                "is_central": is_central,
                "begin_jd": round(begin_jd, 6) if begin_jd else None,
                "end_jd": round(end_jd_ev, 6) if end_jd_ev else None,
            },
        ))
        jd = max_jd + 1.0  # advance past this event before searching the next
    return rows


def _scan_lunar_eclipses(swe: Any, start_jd: float, end_jd: float) -> list[_Row]:
    rows: list[_Row] = []
    jd = start_jd
    guard = 0
    max_iterations = 2000
    while jd < end_jd and guard < max_iterations:
        guard += 1
        try:
            retflag, tret = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0, False)
        except Exception as exc:  # pragma: no cover
            logger.warning("[bg_sky_calendar] lun_eclipse_when halted at jd=%s: %s", jd, exc)
            break
        max_jd = tret[0]
        if max_jd > end_jd:
            break
        begin_jd, end_jd_ev = tret[2], tret[3]
        eclipse_type = _decode_eclipse_type(swe, retflag, _LUNAR_TYPE_BITS)
        lon, speed = _moon_position(swe, max_jd)
        sign = SIGN_NAMES[int(lon // 30.0) % 12]
        rows.append(_Row(
            event_type="eclipse_lunar",
            primary_body="Moon",
            secondary_body="Sun",
            event_jd=max_jd,
            event_datetime_utc=_event_jd_to_utc(swe, max_jd),
            sign=sign,
            nakshatra=None,
            longitude_deg=round(lon, 4),
            speed_dps=round(speed, 6),
            detail={
                "eclipse_type": eclipse_type,
                "begin_jd": round(begin_jd, 6) if begin_jd else None,
                "end_jd": round(end_jd_ev, 6) if end_jd_ev else None,
            },
        ))
        jd = max_jd + 1.0
    return rows


def _sun_position(swe: Any, jd: float) -> tuple[float, float]:
    from pipeline.transit_search import _get_planet_pos
    return _get_planet_pos(swe, "Sun", jd)


def _moon_position(swe: Any, jd: float) -> tuple[float, float]:
    from pipeline.transit_search import _get_planet_pos
    return _get_planet_pos(swe, "Moon", jd)


# ── Family 4: double-transit geometry ─────────────────────────────────────────

def scan_double_transits(swe: Any, start_jd: float, end_jd: float) -> list[_Row]:
    """
    Conjunction events for each configured slow-mover pair (§DOUBLE_TRANSIT_PAIRS).

    Reuses `pipeline.transit_search.find_conjunction_events` as-is.
    """
    from pipeline.transit_search import find_conjunction_events

    rows: list[_Row] = []
    for planet_a, planet_b in DOUBLE_TRANSIT_PAIRS:
        events = find_conjunction_events(
            swe, planet_a, planet_b, DOUBLE_TRANSIT_ORB_DEG, start_jd, end_jd,
        )
        for ev in events:
            rows.append(_Row(
                event_type="double_transit",
                primary_body=planet_a,
                secondary_body=planet_b,
                event_jd=ev.event_jd,
                event_datetime_utc=_event_jd_to_utc(swe, ev.event_jd),
                sign=ev.sign,
                nakshatra=ev.nakshatra,
                longitude_deg=ev.exact_longitude_deg,
                speed_dps=ev.speed_at_event_dps,
                detail={
                    "orb_deg": ev.orb_at_event_deg,
                    "planet_b_lon": ev.extra.get("planet_b_lon"),
                },
            ))
    return rows


# ── Writer ─────────────────────────────────────────────────────────────────────

@register("bg_sky_calendar")
class BgSkyCalendarWriter(WriterBase):
    """
    Seeds bg_sky_events — a chart-independent global sky-event diary (ingresses,
    stations, eclipses, double-transit geometry). See module docstring for the
    full methodology, horizon reasoning, and scope boundaries (no returns, no
    per-chart joins -- those are `ka_kshetra`'s job).

    L0 writer -- chart-agnostic, global scope. Idempotency: ON CONFLICT on the
    natural key (event_type, primary_body, secondary_body, event_jd_rounded)
    DO NOTHING -- see migration 473's comment for the exact constraint.
    """

    asset_id = "bg_sky_calendar"

    _BATCH_SIZE = 500

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_sky_calendar] dry_run=True — skipping INSERT")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        try:
            import swisseph as swe  # type: ignore[import]
        except ImportError:
            logger.warning("[bg_sky_calendar] swisseph not available — skipping computation.")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="skipped: swisseph unavailable",
                duration_seconds=round(time.time() - t0, 2),
            )

        try:
            from brahmagyan.l0_ephemeris import _resolve_ephe_path
            ephe_path = _resolve_ephe_path()
            if ephe_path:
                swe.set_ephe_path(ephe_path)
        except Exception:  # pragma: no cover -- optional; Moshier fallback still works
            pass

        swe.set_sid_mode(swe.SIDM_LAHIRI)

        history_start, forward_end = compute_horizon()
        start_jd = swe.julday(history_start.year, history_start.month, history_start.day, 0.0)
        end_jd = swe.julday(forward_end.year, forward_end.month, forward_end.day, 0.0)

        logger.info(
            "[bg_sky_calendar] horizon %s -> %s (jd %.1f -> %.1f)",
            history_start, forward_end, start_jd, end_jd,
        )

        all_rows: list[_Row] = []
        try:
            all_rows.extend(scan_ingresses(swe, start_jd, end_jd))
            logger.info("[bg_sky_calendar] ingress scan complete: %d events", len(all_rows))
            n_before = len(all_rows)
            all_rows.extend(scan_stations(swe, start_jd, end_jd))
            logger.info("[bg_sky_calendar] station scan complete: %d events", len(all_rows) - n_before)
            n_before = len(all_rows)
            all_rows.extend(scan_eclipses(swe, start_jd, end_jd))
            logger.info("[bg_sky_calendar] eclipse scan complete: %d events", len(all_rows) - n_before)
            n_before = len(all_rows)
            all_rows.extend(scan_double_transits(swe, start_jd, end_jd))
            logger.info("[bg_sky_calendar] double-transit scan complete: %d events", len(all_rows) - n_before)
        except Exception as exc:
            logger.error("[bg_sky_calendar] computation failed: %s", exc)
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"failed: {exc}",
                duration_seconds=round(time.time() - t0, 2),
            )

        conn = ctx.db_conn
        rows_written = 0
        try:
            with conn.cursor() as cur:
                batch: list[dict[str, Any]] = []
                for row in all_rows:
                    batch.append(self._to_insert_dict(row, ctx.build_id))
                    if len(batch) >= self._BATCH_SIZE:
                        rows_written += self._flush_batch(cur, batch)
                        batch = []
                if batch:
                    rows_written += self._flush_batch(cur, batch)
        except Exception as exc:
            logger.error("[bg_sky_calendar] insert failed after %d rows: %s", rows_written, exc)
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=rows_written,
                notes=f"partial: {exc}",
                duration_seconds=round(time.time() - t0, 2),
            )

        elapsed = round(time.time() - t0, 2)
        logger.info(
            "[bg_sky_calendar] complete — %d/%d rows written in %.1fs",
            rows_written, len(all_rows), elapsed,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_written,
            duration_seconds=elapsed,
            notes=(
                f"horizon={history_start.isoformat()}..{forward_end.isoformat()}; "
                f"scanned={len(all_rows)}; families=ingress,station,eclipse_solar,"
                f"eclipse_lunar,double_transit"
            ),
        )

    @staticmethod
    def _to_insert_dict(row: _Row, build_id: str) -> dict[str, Any]:
        import json
        return {
            "event_type": row.event_type,
            "primary_body": row.primary_body,
            "secondary_body": row.secondary_body,
            "event_jd": round(row.event_jd, 5),
            "event_datetime_utc": row.event_datetime_utc,
            "sign": row.sign,
            "nakshatra": row.nakshatra,
            "longitude_deg": row.longitude_deg,
            "speed_dps": row.speed_dps,
            "detail": json.dumps(row.detail),
            "ayanamsha_key": AYANAMSHA_KEY,
            "sampling_method": SAMPLING_METHOD_VERSION,
            "source_citation": SOURCE_CITATION,
            "build_id": build_id,
        }

    @staticmethod
    def _flush_batch(cur: Any, batch: list[dict[str, Any]]) -> int:
        cur.executemany(
            """
            INSERT INTO bg_sky_events
              (event_type, primary_body, secondary_body, event_jd,
               event_datetime_utc, sign, nakshatra, longitude_deg, speed_dps,
               detail, ayanamsha_key, sampling_method, source_citation,
               build_id, computed_at)
            VALUES
              (%(event_type)s, %(primary_body)s, %(secondary_body)s, %(event_jd)s,
               %(event_datetime_utc)s, %(sign)s, %(nakshatra)s, %(longitude_deg)s,
               %(speed_dps)s, %(detail)s::jsonb, %(ayanamsha_key)s,
               %(sampling_method)s, %(source_citation)s, %(build_id)s, NOW())
            ON CONFLICT (event_type, primary_body, secondary_body_key, event_jd)
            DO NOTHING
            """,
            batch,
        )
        return cur.rowcount
