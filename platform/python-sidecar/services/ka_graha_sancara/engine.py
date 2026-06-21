"""
engine.py — Core ephemeris-at-T engine for ka_graha_sancara.

Two read paths:
  PATH-A (cheap): date is within bg_ephemeris range (1900-01-01 to 2150-12-31)
      → read tropical_longitude + speed_dps from ephemeris_daily,
        apply ayanamsha derivation via brahmagyan.l0_ephemeris.derive_sidereal.
        NO swisseph call.

  PATH-B (live): date is out of range, OR db_conn=None, OR intra-day precision flag set
      → delegate to platform/scripts/temporal/compute_transits.get_transit_states
        (pyswisseph + Moshier ephemeris).

Ephemeris cache (I-9):
    Per-call memo keyed on (T_rounded_to_day, ayanamsha) → computed state dict.
    Cache lifetime = one get_ephemeris() call (instance-level, not module-level).
    Tests assert single-compute across repeated queries for the same (T, ayanamsha).

TRUE_NODE everywhere:
    Rahu = swe.TRUE_NODE (swe_id=11).  Ketu = Rahu + 180.

Per CLAUDE.md §I B.10: no fabricated computation. All numeric values come from
pyswisseph or from the bg_ephemeris table (which was itself computed by pyswisseph).
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "PurvaPhalguni", "UttaraPhalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "PurvaAshadha", "UttaraAshadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "PurvaBhadrapada", "UttaraBhadrapada", "Revati",
)

NAK_SIZE_DEG = 360.0 / 27.0
SIGN_SIZE_DEG = 30.0

# bg_ephemeris covers 1900-01-01 → 2150-12-31
BG_EPHEMERIS_START = date(1900, 1, 1)
BG_EPHEMERIS_END = date(2150, 12, 31)

# 9 grahas in canonical order
ALL_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# Ayanamshas supported by bg_ephemeris + derive_sidereal
SUPPORTED_AYANAMSHAS = {"lahiri", "raman", "kp", "krishnamurti", "yukteshwar", "surya_siddhanta"}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class GrahaState:
    """Full state for one graha at an instant T."""
    name: str
    sidereal_lon_deg: float
    sign: str
    sign_idx: int           # 0-based (0=Aries … 11=Pisces)
    nakshatra: str
    nakshatra_idx: int      # 0-based
    degrees_in_sign: float
    degrees_in_nakshatra: float
    speed_dps: float        # degrees per day; negative = retrograde direction
    is_retrograde: bool
    source: str             # 'bg_ephemeris' | 'swisseph_live'

    def applying_or_separating(self, target_lon_deg: float) -> str:
        """
        Determine whether this graha is APPLYING toward or SEPARATING from
        a target ecliptic longitude.

        Convention: angular separation = (target - graha) mod 360.
        If the graha's speed_dps > 0 (direct motion):
            - If separation is decreasing (graha moving toward target): APPLYING
            - Else: SEPARATING
        If speed_dps < 0 (retrograde):
            The graha moves backward; separation w.r.t. forward-signed distance
            is increasing in the forward direction, so it is SEPARATING from targets
            it has already passed, and APPLYING to targets behind it.

        Formal rule:  d(separation)/dt = -speed_dps (sign of d/dt for forward angle)
        If d(separation)/dt < 0  → gap is closing → APPLYING
        If d(separation)/dt > 0  → gap is widening → SEPARATING

        separation = (target - graha) mod 360 — always in [0, 360)
        d(separation)/dt = -speed_dps  (because separation decreases as graha advances)

        If speed_dps > 0 and separation > 0  → graha moving toward target → APPLYING
        If speed_dps < 0 (retro) → graha moving away from forward target → SEPARATING

        The sign of -speed_dps gives us d(separation)/dt:
            negative → APPLYING
            positive → SEPARATING
            zero     → EXACT
        """
        sep = (target_lon_deg - self.sidereal_lon_deg) % 360.0
        if abs(self.speed_dps) < 1e-9:
            return "stationary"
        # d(sep)/dt = -speed_dps
        d_sep_dt = -self.speed_dps
        if abs(d_sep_dt) < 1e-9:
            return "stationary"
        # "APPLYING" = separation is shrinking = d_sep_dt < 0
        # BUT: if sep > 180 the graha is actually past the target in retro sense
        # We use the shortest-arc approach:
        if sep > 180.0:
            # Measure from other side
            d_sep_dt = self.speed_dps
        return "applying" if d_sep_dt < 0 else "separating"


@dataclass
class EphemerisResult:
    """Full ephemeris for all 9 grahas at an instant T."""
    query_dt: datetime
    ayanamsha: str
    source: str             # 'bg_ephemeris' | 'swisseph_live' | 'mixed'
    grahas: dict[str, GrahaState] = field(default_factory=dict)

    def get(self, graha_name: str) -> GrahaState:
        return self.grahas[graha_name]


# ── Cache (per-call, keyed on (date, ayanamsha)) ──────────────────────────────

class _EphemerisCache:
    """Memo cache for one get_ephemeris() call. Keyed on (date_str, ayanamsha)."""

    def __init__(self):
        self._store: dict[tuple[str, str], dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def key(self, d: date, ayanamsha: str) -> tuple[str, str]:
        return (d.isoformat(), ayanamsha)

    def get(self, d: date, ayanamsha: str) -> dict[str, Any] | None:
        k = self.key(d, ayanamsha)
        val = self._store.get(k)
        if val is not None:
            self._hits += 1
        else:
            self._misses += 1
        return val

    def put(self, d: date, ayanamsha: str, value: dict[str, Any]) -> None:
        self._store[self.key(d, ayanamsha)] = value

    @property
    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._store)}


# ── Path-A: bg_ephemeris read ─────────────────────────────────────────────────

def _read_from_bg_ephemeris(
    d: date,
    ayanamsha: str,
    db_conn: Any,
) -> dict[str, GrahaState] | None:
    """
    Read tropical longitudes from ephemeris_daily for the given date,
    apply ayanamsha derivation, return dict of GrahaState objects.

    Returns None if the table is unavailable or no rows found.
    """
    try:
        from brahmagyan.l0_ephemeris import derive_sidereal, _tropical_to_jd
    except ImportError as exc:
        logger.warning("brahmagyan.l0_ephemeris not available: %s", exc)
        return None

    try:
        jd = _tropical_to_jd(d)
    except RuntimeError:
        # pyswisseph not available for ayanamsha derivation even for stored rows
        return None

    try:
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT body, tropical_longitude, speed_dps, is_retrograde
                FROM ephemeris_daily
                WHERE date = %s AND ayanamsha_id = 'tropical'
                ORDER BY body
                """,
                (d,),
            )
            rows = cur.fetchall()
    except Exception as exc:
        logger.warning("bg_ephemeris read failed for %s: %s", d, exc)
        return None

    if not rows:
        logger.debug("bg_ephemeris: no rows for %s", d)
        return None

    # Build a body→row map
    body_map: dict[str, tuple[float, float, bool]] = {}
    for row in rows:
        body, trop_lon, speed, is_retro = row[0], float(row[1]), float(row[2]), bool(row[3])
        body_map[body] = (trop_lon, speed, is_retro)

    grahas: dict[str, GrahaState] = {}

    for graha in ALL_GRAHAS:
        if graha not in body_map:
            logger.debug("bg_ephemeris missing body %s for %s", graha, d)
            return None  # incomplete — fall through to live compute

        trop_lon, speed_dps, is_retro_stored = body_map[graha]

        try:
            sid = derive_sidereal(trop_lon, jd, ayanamsha)
        except (ValueError, RuntimeError) as exc:
            logger.warning("derive_sidereal failed for %s/%s: %s", graha, ayanamsha, exc)
            return None

        sid_lon = sid["sidereal_longitude"]
        sign_idx = int(sid_lon // SIGN_SIZE_DEG)
        nak_idx = int(sid_lon // NAK_SIZE_DEG)

        # Retrograde: use stored flag for planets (Sun/Moon/Rahu/Ketu never retrograde)
        is_retro = is_retro_stored if graha not in ("Sun", "Moon", "Rahu", "Ketu") else False

        grahas[graha] = GrahaState(
            name=graha,
            sidereal_lon_deg=sid_lon,
            sign=SIGNS[sign_idx % 12],
            sign_idx=sign_idx % 12,
            nakshatra=NAKSHATRAS[nak_idx % 27],
            nakshatra_idx=nak_idx % 27,
            degrees_in_sign=sid_lon % SIGN_SIZE_DEG,
            degrees_in_nakshatra=sid_lon % NAK_SIZE_DEG,
            speed_dps=speed_dps,
            is_retrograde=is_retro,
            source="bg_ephemeris",
        )

    return grahas


# ── Path-B: live swisseph compute ─────────────────────────────────────────────

def _compute_live(
    query_dt: datetime,
    ayanamsha: str,
) -> dict[str, GrahaState]:
    """
    Compute ephemeris positions live via compute_transits.get_transit_states.
    Supports only 'lahiri' ayanamsha (engine constraint); raises for others.
    """
    # Add platform/scripts to sys.path if needed
    scripts_path = str(
        Path(__file__).parent.parent.parent.parent / "scripts"
    )
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)

    try:
        from temporal.compute_transits import get_transit_states
    except ImportError as exc:
        raise RuntimeError(
            f"compute_transits not importable from {scripts_path}: {exc}"
        ) from exc

    if ayanamsha != "lahiri":
        raise NotImplementedError(
            f"Live swisseph path only supports 'lahiri' ayanamsha; got {ayanamsha!r}. "
            "Use a date within bg_ephemeris range (1900-2150) for multi-ayanamsha support."
        )

    q_date = query_dt.date() if hasattr(query_dt, "date") else query_dt
    raw = get_transit_states(query_dt, q_date, ayanamsha=ayanamsha)
    planets = raw["planets"]

    grahas: dict[str, GrahaState] = {}
    for graha in ALL_GRAHAS:
        p = planets[graha]
        lon = float(p["sidereal_lon_deg"])
        sign_idx = int(lon // SIGN_SIZE_DEG)
        nak_idx = int(lon // NAK_SIZE_DEG)
        speed = float(p["speed_deg_per_day"])
        is_retro = bool(p["is_retrograde"])

        grahas[graha] = GrahaState(
            name=graha,
            sidereal_lon_deg=lon,
            sign=SIGNS[sign_idx % 12],
            sign_idx=sign_idx % 12,
            nakshatra=NAKSHATRAS[nak_idx % 27],
            nakshatra_idx=nak_idx % 27,
            degrees_in_sign=lon % SIGN_SIZE_DEG,
            degrees_in_nakshatra=lon % NAK_SIZE_DEG,
            speed_dps=speed,
            is_retrograde=is_retro,
            source="swisseph_live",
        )

    return grahas


# ── Public API ────────────────────────────────────────────────────────────────

def get_ephemeris(
    dt: datetime,
    ayanamsha: str = "lahiri",
    db_conn: Any = None,
    *,
    force_live: bool = False,
    _cache: _EphemerisCache | None = None,
) -> EphemerisResult:
    """
    Compute or retrieve ephemeris for all 9 grahas at datetime dt.

    Parameters
    ----------
    dt : datetime
        The instant of interest (timezone-aware preferred; naive treated as IST).
    ayanamsha : str
        Ayanamsha to use.  Default: 'lahiri'.
        Multi-ayanamsha (raman/kp/yukteshwar/surya_siddhanta) requires PATH-A
        (bg_ephemeris) — live path only supports lahiri.
    db_conn : psycopg connection | None
        If provided, PATH-A (bg_ephemeris read) is attempted first for dates
        within 1900-2150.  If None or PATH-A fails, PATH-B (live compute) is used.
    force_live : bool
        Skip PATH-A and always use PATH-B (swisseph live compute).
    _cache : _EphemerisCache | None
        Optional caller-supplied cache (used internally and in tests to verify
        single-compute behaviour).  If None, a fresh cache is created per call.

    Returns
    -------
    EphemerisResult with all 9 GrahaState objects.
    """
    if ayanamsha not in SUPPORTED_AYANAMSHAS:
        raise ValueError(
            f"Unknown ayanamsha '{ayanamsha}'. Supported: {sorted(SUPPORTED_AYANAMSHAS)}"
        )

    # Ensure dt is timezone-aware (assume IST if naive)
    if dt.tzinfo is None:
        from datetime import timezone as _tz
        import zoneinfo
        try:
            ist = zoneinfo.ZoneInfo("Asia/Kolkata")
            dt = dt.replace(tzinfo=ist)
        except Exception:
            # Fallback: offset-based IST
            from datetime import timedelta
            dt = dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))

    q_date = dt.date()

    # Use caller-supplied cache or fresh per-call cache
    cache = _cache if _cache is not None else _EphemerisCache()

    # Check cache
    cached = cache.get(q_date, ayanamsha)
    if cached is not None:
        logger.debug("ephemeris cache hit for (%s, %s)", q_date, ayanamsha)
        return EphemerisResult(
            query_dt=dt,
            ayanamsha=ayanamsha,
            source=cached["_source"],
            grahas=cached["grahas"],
        )

    # ── PATH-A: bg_ephemeris (cheap read) ──
    grahas: dict[str, GrahaState] | None = None
    source = "swisseph_live"

    if (
        not force_live
        and db_conn is not None
        and BG_EPHEMERIS_START <= q_date <= BG_EPHEMERIS_END
    ):
        logger.debug("ephemeris PATH-A: bg_ephemeris for %s/%s", q_date, ayanamsha)
        grahas = _read_from_bg_ephemeris(q_date, ayanamsha, db_conn)
        if grahas is not None:
            source = "bg_ephemeris"
            logger.debug("ephemeris PATH-A: success — %d grahas", len(grahas))

    # ── PATH-B: live swisseph ──
    if grahas is None:
        logger.debug("ephemeris PATH-B: live swisseph for %s/%s", q_date, ayanamsha)
        grahas = _compute_live(dt, ayanamsha)
        source = "swisseph_live"

    # Store in cache
    cache.put(q_date, ayanamsha, {"grahas": grahas, "_source": source})

    return EphemerisResult(
        query_dt=dt,
        ayanamsha=ayanamsha,
        source=source,
        grahas=grahas,
    )
