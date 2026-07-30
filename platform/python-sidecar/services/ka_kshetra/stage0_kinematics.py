"""
services.ka_kshetra.stage0_kinematics — ṢAḌ-DARŚANA W2 Lane A, Stage 0.

Spec: KALA_W2_FIELD_DESIGN_v1_0.md §3.1. Builds the exact position model (cubic
Hermite spline over `ephemeris_daily`'s daily knots), roots every "when exactly"
event via Brent's method, and computes the dwell-time weight + trapezoidal
within-episode kernel that replaces the "stations act with full force" special
case. Writes `kala_field_kinematics` (migration 474).

Design principles this module is built to (KALA_W2_FIELD_DESIGN_v1_0.md §1):
  - §N.5 / B.10: natal target longitudes are REFERENCED from `chart_facts`
    (L1), never recomputed; sidereal derivation reuses the existing product
    convention (`brahmagyan.l0_ephemeris.AYANAMSHA_MAP` + pyswisseph
    `set_sid_mode`/`get_ayanamsa_ut`), not a re-derived formula.
  - Velocity is ALWAYS the spline derivative, never `speed_dps` read directly
    and never mean motion (the "true lunar velocity" requirement).
  - Root-finding is Brent's method (`scipy.optimize.brentq`), bracketed by
    sign change on the daily grid, `xtol=1e-6 days`, `maxiter=100`. A root
    inside a single day-pair with no sign change is NOT detected at W2 (the
    day-grade regime — exactly what W2G buys).
  - Everything here writes `precision_regime='day_grade'`.

The pure math (unwrap, spline, root-finding, dwell weight, kernel) takes plain
float sequences and has zero DB/swisseph dependency, so it is fully unit-
testable on small synthetic fixtures. The DB/ephemeris-reading layer at the
bottom of this module is the only part that needs a live connection (or
pyswisseph for sidereal derivation) — those functions are exercised by the
"live" test tier only (see tests/test_stage0_kinematics.py).
"""
from __future__ import annotations

import bisect
import hashlib
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Optional, Sequence

from scipy.optimize import brentq

# ── Constants ─────────────────────────────────────────────────────────────────

J2000_EPOCH = date(2000, 1, 1)

# The 9 daily-ephemeris bodies (brahmagyan.l0_ephemeris.DAILY_BODIES names).
DAILY_BODIES: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

# The project's pinned/canonical ayanamsha (matches ka_dasha_kala, ka_gochara_resonance,
# ka_avadhi — CANONICAL_AYANAMSHA convention repo-wide). Sidereal longitude is derived
# at read time by subtracting this ayanamsha's offset from the stored tropical value
# (§N.5 — do not re-derive the conversion itself, reuse the existing convention).
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

# natal fact_subject codes (chart_facts), matching ga_transit_anchors._SUBJECT_TO_GRAHA
# and bo_karanajala's shared map exactly (§N.5 — reused, not re-declared with new codes).
GRAHA_FACT_SUBJECTS: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
}
LAGNA_FACT_SUBJECT = "LAGNA"

# Default orb when bg_transit_rules has no per-(body,target_class) entry — the
# design's own honest fallback (§3.1: "if absent, ω = 3.0°, orb_source='default_3deg'").
DEFAULT_ORB_DEG = 3.0

# Horizon: birth -> birth + 36525 days (~100y), matching the existing sweep horizon.
HORIZON_DAYS = 36525.0

# Root-finding tolerances (§3.1 "Root finding", exact).
BRENT_XTOL_DAYS = 1e-6
BRENT_MAXITER = 100

# V0-1 build-time velocity-range assert (§3.1).
MOON_VELOCITY_RANGE_DPS = (11.60, 15.50)


class KinematicsVelocityOutOfRange(RuntimeError):
    """V0-1 halting assert: |lambda_dot_Moon(t)| outside [11.60, 15.50] deg/day."""


# ── Angle helpers ─────────────────────────────────────────────────────────────

def wrap180(x: float) -> float:
    """wrap180(x) = ((x + 180) mod 360) - 180 — the ONE re-wrap point (§3.1)."""
    return ((x + 180.0) % 360.0) - 180.0


def unwrap_series(values: Sequence[float]) -> list[float]:
    """Unwrap a longitude series so consecutive knots never jump > 180 deg.

    Mandatory before splining (§3.1's "#1 source of silent bugs"): add +360 to
    every subsequent knot whenever the raw step < -180, and -360 whenever the
    raw step > +180. Uses the +-180 test ONLY — never `is_retrograde` — so a
    genuinely retrograde (decreasing) body is unwrapped correctly too.
    """
    if not values:
        return []
    out = [float(values[0])]
    offset = 0.0
    for i in range(1, len(values)):
        raw_prev = float(values[i - 1])
        raw_cur = float(values[i])
        step = raw_cur - raw_prev
        if step < -180.0:
            offset += 360.0
        elif step > 180.0:
            offset -= 360.0
        out.append(raw_cur + offset)
    return out


# ── Cubic Hermite spline (exact formula, §3.1) ────────────────────────────────

def _hermite_basis(u: float) -> tuple[float, float, float, float]:
    u2 = u * u
    u3 = u2 * u
    h00 = 2.0 * u3 - 3.0 * u2 + 1.0
    h10 = u3 - 2.0 * u2 + u
    h01 = -2.0 * u3 + 3.0 * u2
    h11 = u3 - u2
    return h00, h10, h01, h11


def _hermite_basis_d1(u: float) -> tuple[float, float, float, float]:
    """d/du of the four basis functions."""
    u2 = u * u
    return (6.0 * u2 - 6.0 * u, 3.0 * u2 - 4.0 * u + 1.0, -6.0 * u2 + 6.0 * u, 3.0 * u2 - 2.0 * u)


def _hermite_basis_d2(u: float) -> tuple[float, float, float, float]:
    """d2/du2 of the four basis functions."""
    return (12.0 * u - 6.0, 6.0 * u - 4.0, -12.0 * u + 6.0, 6.0 * u - 2.0)


@dataclass(frozen=True)
class HermiteSpline:
    """Cubic Hermite spline over daily knots (t_i, lambda_i unwrapped, lambda_dot_i).

    `.value(t)`, `.velocity(t)`, `.acceleration(t)` evaluate the SAME segment
    representation the design specifies exactly (§3.1) — this is a definition
    of the stored position model, not an approximation.
    """

    t: tuple[float, ...]        # ascending, days since J2000
    lam: tuple[float, ...]      # unwrapped degrees
    lamdot: tuple[float, ...]   # deg/day (the Hermite tangent = speed_dps)

    def __post_init__(self) -> None:
        if len(self.t) != len(self.lam) or len(self.t) != len(self.lamdot):
            raise ValueError("HermiteSpline: t/lam/lamdot must be equal length")
        if len(self.t) < 2:
            raise ValueError("HermiteSpline: need >= 2 knots")
        for i in range(1, len(self.t)):
            if self.t[i] <= self.t[i - 1]:
                raise ValueError("HermiteSpline: t must be strictly ascending")

    @property
    def t_min(self) -> float:
        return self.t[0]

    @property
    def t_max(self) -> float:
        return self.t[-1]

    def _segment(self, tq: float) -> tuple[int, float, float]:
        """Return (i, h, u) for the knot interval [t_i, t_{i+1}] containing tq."""
        n = len(self.t)
        if tq <= self.t[0]:
            i = 0
        elif tq >= self.t[-1]:
            i = n - 2
        else:
            i = bisect.bisect_right(self.t, tq) - 1
            i = max(0, min(i, n - 2))
        h = self.t[i + 1] - self.t[i]
        u = (tq - self.t[i]) / h
        return i, h, u

    def value(self, tq: float) -> float:
        i, h, u = self._segment(tq)
        h00, h10, h01, h11 = _hermite_basis(u)
        return (
            h00 * self.lam[i] + h10 * h * self.lamdot[i]
            + h01 * self.lam[i + 1] + h11 * h * self.lamdot[i + 1]
        )

    def velocity(self, tq: float) -> float:
        i, h, u = self._segment(tq)
        d00, d10, d01, d11 = _hermite_basis_d1(u)
        return (
            d00 * self.lam[i] + d10 * h * self.lamdot[i]
            + d01 * self.lam[i + 1] + d11 * h * self.lamdot[i + 1]
        ) / h

    def acceleration(self, tq: float) -> float:
        i, h, u = self._segment(tq)
        dd00, dd10, dd01, dd11 = _hermite_basis_d2(u)
        return (
            dd00 * self.lam[i] + dd10 * h * self.lamdot[i]
            + dd01 * self.lam[i + 1] + dd11 * h * self.lamdot[i + 1]
        ) / (h * h)


def build_spline(t_days: Sequence[float], tropical_or_sidereal_lon: Sequence[float],
                  speed_dps: Sequence[float]) -> HermiteSpline:
    """Build a HermiteSpline from daily knots. Caller supplies already-sidereal
    (or any consistently-wrapped) longitude; this function unwraps it."""
    lam_unwrapped = unwrap_series(tropical_or_sidereal_lon)
    return HermiteSpline(tuple(t_days), tuple(lam_unwrapped), tuple(speed_dps))


def assert_moon_velocity_in_range(spline: HermiteSpline, sample_stride_days: float = 1.0) -> None:
    """V0-1 build-time assert (§3.1): |lambda_dot_Moon(t)| in [11.60, 15.50] deg/day
    at every evaluated t. Halts with KinematicsVelocityOutOfRange on violation."""
    lo, hi = MOON_VELOCITY_RANGE_DPS
    t = spline.t_min
    while t <= spline.t_max:
        v = abs(spline.velocity(t))
        if not (lo <= v <= hi):
            raise KinematicsVelocityOutOfRange(
                f"kinematics_velocity_out_of_range: |lambda_dot_Moon({t})|={v:.4f} "
                f"outside [{lo}, {hi}] deg/day"
            )
        t += sample_stride_days


# ── Root finding (Brent's method, exact per §3.1) ─────────────────────────────

def _brent_root(g: Callable[[float], float], a: float, b: float) -> Optional[float]:
    """One Brent root in [a, b] if g(a) and g(b) have opposite signs (or either
    is exactly zero); else None. xtol/maxiter per §3.1."""
    ga, gb = g(a), g(b)
    if ga == 0.0:
        return a
    if gb == 0.0:
        return b
    if (ga > 0) == (gb > 0):
        return None
    return brentq(g, a, b, xtol=BRENT_XTOL_DAYS, maxiter=BRENT_MAXITER)


def find_roots_on_grid(g: Callable[[float], float], t_grid: Sequence[float]) -> list[float]:
    """All roots of g bracketed by a sign change between consecutive grid points.
    A double root inside one bracket is NOT detected (day-grade regime, §3.1)."""
    roots: list[float] = []
    for i in range(len(t_grid) - 1):
        a, b = t_grid[i], t_grid[i + 1]
        r = _brent_root(g, a, b)
        if r is not None:
            roots.append(r)
    return roots


def find_modulus_boundary_roots(spline: HermiteSpline, t_grid: Sequence[float],
                                 width: float) -> list[float]:
    """Roots of `spline.value(t) mod width == 0` (sign_ingress width=30,
    nakshatra_ingress width=360/27). Handles a fast body (e.g. Moon,
    nakshatra width < daily motion) crossing more than one boundary within a
    single day-pair by iterating every integer multiple of `width` spanned by
    [lam(t_i), lam(t_{i+1})], not just the nearest one. Uses `_brent_root`'s own
    sign/equality handling (not a manual strict-inequality pre-filter) so a
    root that lands exactly on a grid knot's value is not silently skipped."""
    roots: list[float] = []
    seen: set[float] = set()
    for i in range(len(t_grid) - 1):
        a, b = t_grid[i], t_grid[i + 1]
        lo_v, hi_v = spline.value(a), spline.value(b)
        v_min, v_max = (lo_v, hi_v) if lo_v <= hi_v else (hi_v, lo_v)
        k_lo = math.floor(v_min / width)
        k_hi = math.ceil(v_max / width)
        for k in range(k_lo, k_hi + 1):
            boundary = k * width
            g = lambda t, _b=boundary: spline.value(t) - _b
            r = _brent_root(g, a, b)
            if r is not None:
                key = round(r, 6)
                if key not in seen:
                    seen.add(key)
                    roots.append(r)
    return sorted(roots)


def find_station_roots(spline: HermiteSpline, t_grid: Sequence[float]) -> list[tuple[float, str]]:
    """Roots of lambda_dot(t) = 0, direction from sign of lambda_ddot at the root."""
    out: list[tuple[float, str]] = []
    for t in find_roots_on_grid(spline.velocity, t_grid):
        accel = spline.acceleration(t)
        direction = "direct_onset" if accel > 0 else "retro_onset"
        out.append((t, direction))
    return out


def find_syzygy_roots(moon: HermiteSpline, sun: HermiteSpline,
                       t_grid: Sequence[float]) -> list[tuple[float, str]]:
    """Roots of wrap180(lam_Moon - lam_Sun) = 0 (new) or = 180 (full)."""
    out: list[tuple[float, str]] = []
    g_new = lambda t: wrap180(moon.value(t) - sun.value(t))
    for t in find_roots_on_grid(g_new, t_grid):
        out.append((t, "new"))
    g_full = lambda t: wrap180(moon.value(t) - sun.value(t) - 180.0)
    for t in find_roots_on_grid(g_full, t_grid):
        out.append((t, "full"))
    out.sort(key=lambda x: x[0])
    return out


@dataclass
class ContactEpisode:
    body: str
    target_ref: str
    t_in: float
    t_out: float
    t_peak: float
    orb_deg: float
    orb_source: str
    ok_core_in: Optional[float] = None
    ok_core_out: Optional[float] = None


def _signed_sep(spline: HermiteSpline, natal_lon: float) -> Callable[[float], float]:
    return lambda t: wrap180(spline.value(t) - natal_lon)


def find_contact_episodes(spline: HermiteSpline, natal_lon: float, body: str,
                           target_ref: str, t_grid: Sequence[float],
                           orb_deg: float, orb_source: str) -> list[ContactEpisode]:
    """Every contact episode of `body` on natal point `target_ref` within
    `orb_deg`, as a (t_in, t_out, t_peak) triple, plus the ohm_core crossings
    (§3.1's "within-episode envelope" knots)."""
    s = _signed_sep(spline, natal_lon)
    boundary_crossings = _threshold_crossings_state_machine(s, t_grid, orb_deg)
    episodes: list[ContactEpisode] = []
    i = 0
    n = len(boundary_crossings)
    while i < n:
        t_in, entering = boundary_crossings[i]
        if not entering:
            i += 1
            continue
        # find the matching exit
        j = i + 1
        while j < n and boundary_crossings[j][1]:
            j += 1
        if j < n:
            t_out, _exiting = boundary_crossings[j]
        else:
            # never exits within horizon — clip at horizon end
            t_out = t_grid[-1]
        t_peak = _episode_peak(spline, s, t_in, t_out)
        omega_core = 0.25 * orb_deg
        core_in, core_out = _core_crossings(s, t_in, t_out, omega_core)
        episodes.append(ContactEpisode(
            body=body, target_ref=target_ref, t_in=t_in, t_out=t_out, t_peak=t_peak,
            orb_deg=orb_deg, orb_source=orb_source,
            ok_core_in=core_in, ok_core_out=core_out,
        ))
        i = j + 1
    return episodes


def _threshold_crossings_state_machine(s: Callable[[float], float], t_grid: Sequence[float],
                                        threshold: float) -> list[tuple[float, bool]]:
    """All times |s(t)| crosses `threshold`, tagged True=entering (going below
    threshold), False=exiting (going above), in chronological order. A single
    forward pass over the daily grid: at most one boundary crossing per grid
    step is assumed (valid whenever orb << the body's daily motion, true for
    every body-orb pair W2 uses; a faster crossing is the day-grade limit)."""
    out: list[tuple[float, bool]] = []
    inside_prev = abs(s(t_grid[0])) < threshold
    for i in range(len(t_grid) - 1):
        a, b = t_grid[i], t_grid[i + 1]
        inside_b = abs(s(b)) < threshold
        if inside_b != inside_prev:
            # exactly one boundary (+threshold or -threshold) is crossed in a
            # well-behaved day (orb << daily motion for every body but Moon,
            # and Moon's orb-crossing rate is still << 1/day); root against
            # whichever threshold sign matches the direction of the crossing.
            sa = s(a)
            candidates = []
            for target in (threshold, -threshold):
                ga, gb = sa - target, s(b) - target
                if ga == 0.0 or gb == 0.0 or (ga > 0) != (gb > 0):
                    r = _brent_root(lambda t, _tg=target: s(t) - _tg, a, b)
                    if r is not None:
                        candidates.append(r)
            if candidates:
                r = min(candidates)
                out.append((r, inside_b))
        inside_prev = inside_b
    return out


def _episode_peak(spline: HermiteSpline, s: Callable[[float], float],
                   t_in: float, t_out: float) -> float:
    """t_peak = argmin |s(t)| over [t_in, t_out] (§3.1: "always a breakpoint"
    analogue for kinematics — the exact conjunction, or the station if the
    body never reaches exact conjunction inside the window)."""
    s_in, s_out = s(t_in), s(t_out)
    if (s_in > 0) != (s_out > 0) or s_in == 0.0 or s_out == 0.0:
        r = _brent_root(s, t_in, t_out)
        if r is not None:
            return r
    # No exact conjunction in-window: the peak is a station (velocity=0) if
    # one exists inside, else fall back to a fine-grid argmin (day-grade).
    v = lambda t: spline.velocity(t)
    v_in, v_out = v(t_in), v(t_out)
    if (v_in > 0) != (v_out > 0):
        r = _brent_root(v, t_in, t_out)
        if r is not None:
            return r
    n_grid = max(2, int(math.ceil((t_out - t_in))) + 1)
    ts = [t_in + (t_out - t_in) * k / (n_grid - 1) for k in range(n_grid)]
    return min(ts, key=lambda t: abs(s(t)))


def _core_crossings(s: Callable[[float], float], t_in: float, t_out: float,
                     omega_core: float) -> tuple[Optional[float], Optional[float]]:
    """The two omega_core crossings inside [t_in, t_out], if the episode
    actually saturates the kernel (comes within omega_core of exact)."""
    n_grid = max(2, int(math.ceil((t_out - t_in))) + 1)
    ts = [t_in + (t_out - t_in) * k / (n_grid - 1) for k in range(n_grid)]
    crossings = _threshold_crossings_state_machine(s, ts, omega_core)
    if not crossings:
        return None, None
    core_in = min(t for t, _ in crossings)
    core_out = max(t for t, _ in crossings)
    return core_in, core_out


# ── Dwell time / weight (§3.1, exact formula) ─────────────────────────────────

def dwell_days(t_in: float, t_out: float) -> float:
    return t_out - t_in


def dwell_nominal_days(orb_deg: float, mean_daily_motion_dps: float) -> float:
    """D_nom = 2*omega / v_bar_b (days). v_bar_b must be the body's MEAN
    (unsigned) sidereal daily motion — callers pass abs(mean_motion)."""
    v_bar = abs(mean_daily_motion_dps)
    if v_bar <= 0.0:
        raise ValueError("mean_daily_motion_dps must be nonzero")
    return 2.0 * orb_deg / v_bar


def dwell_weight(d_days: float, d_nom_days: float) -> float:
    """w_dwell = D / (D + D_nom) in (0, 1). 0.5 at mean speed; -> 1 stationary."""
    return d_days / (d_days + d_nom_days)


# ── Within-episode envelope kernel (§3.1, exact formula) ──────────────────────

def contact_kernel(t: float, t_peak: float, spline: HermiteSpline, natal_lon: float,
                    orb_deg: float, w_dwell: float) -> float:
    """x_contact(t) = w_dwell * clamp01((omega - |sep|) / (omega - omega_core))."""
    omega_core = 0.25 * orb_deg
    sep = abs(wrap180(spline.value(t) - natal_lon))
    raw = (orb_deg - sep) / (orb_deg - omega_core)
    return w_dwell * min(1.0, max(0.0, raw))


# ── Eclipse geometry (honest W2 limit, §3.1) ──────────────────────────────────

NEW_MOON_ECLIPSE_BETA_MAX = 1.50
FULL_MOON_ECLIPSE_BETA_MAX = 1.00


def eclipse_candidate(syzygy_kind: str, beta_deg: float) -> bool:
    threshold = NEW_MOON_ECLIPSE_BETA_MAX if syzygy_kind == "new" else FULL_MOON_ECLIPSE_BETA_MAX
    return abs(beta_deg) <= threshold


# ── kala_field_kinematics row shape ───────────────────────────────────────────

@dataclass
class KinematicsRow:
    chart_id: str
    event_kind: str
    body: str
    t_days: float
    target_kind: Optional[str] = None
    target_ref: Optional[str] = None
    longitude_deg: Optional[float] = None
    velocity_dps: Optional[float] = None
    latitude_deg: Optional[float] = None
    episode_id: Optional[str] = None
    dwell_days: Optional[float] = None
    dwell_weight: Optional[float] = None
    orb_deg: Optional[float] = None
    orb_source: Optional[str] = None
    eclipse_candidate: bool = False
    gamma_proxy: Optional[float] = None
    ayanamsha_id: str = CANONICAL_AYANAMSHA
    precision_regime: str = "day_grade"


def t_days_to_datetime(t_days: float) -> datetime:
    """t_days is days since J2000 epoch (2000-01-01), UTC."""
    return datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(days=t_days)


def make_episode_id(chart_id: str, body: str, target_ref: str, t_in: float) -> str:
    """Stable, deterministic episode id grouping the 5 knots of one contact
    episode (hash-replayable, matching §5.2's window_id convention)."""
    raw = f"{chart_id}|{body}|{target_ref}|{round(t_in, 6)}"
    return "kep_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


# ── Row emission: turn events/episodes into persistable KinematicsRow(s) ─────

def ingress_rows(chart_id: str, body: str, spline: HermiteSpline, event_kind: str,
                  roots: Sequence[float], ayanamsha_id: str = CANONICAL_AYANAMSHA
                  ) -> list[KinematicsRow]:
    """sign_ingress / nakshatra_ingress rows (one per root)."""
    rows = []
    for t in roots:
        rows.append(KinematicsRow(
            chart_id=chart_id, event_kind=event_kind, body=body, t_days=t,
            longitude_deg=spline.value(t) % 360.0, velocity_dps=spline.velocity(t),
            ayanamsha_id=ayanamsha_id,
        ))
    return rows


def station_rows(chart_id: str, body: str, spline: HermiteSpline,
                  roots: Sequence[tuple[float, str]], ayanamsha_id: str = CANONICAL_AYANAMSHA
                  ) -> list[KinematicsRow]:
    """station rows (direction carried as class-free metadata is not a column
    on this table per §3.1's schema — the direction is recoverable from the
    sign of velocity either side of t_days by any downstream reader, so it is
    not persisted as a separate field; kept in-memory by callers that need it
    at symbolization time, e.g. for station_band construction)."""
    rows = []
    for t, _direction in roots:
        rows.append(KinematicsRow(
            chart_id=chart_id, event_kind="station", body=body, t_days=t,
            longitude_deg=spline.value(t) % 360.0, velocity_dps=spline.velocity(t),
            ayanamsha_id=ayanamsha_id,
        ))
    return rows


def syzygy_rows(chart_id: str, moon: HermiteSpline, sun: HermiteSpline,
                 latitude_spline: HermiteSpline, roots: Sequence[tuple[float, str]],
                 ayanamsha_id: str = CANONICAL_AYANAMSHA) -> list[KinematicsRow]:
    """syzygy rows, with eclipse_candidate + gamma_proxy from the Moon's
    latitude spline at the same root (§3.1's "honest W2 limit")."""
    rows = []
    for t, kind in roots:
        beta = latitude_spline.value(t)
        rows.append(KinematicsRow(
            chart_id=chart_id, event_kind="syzygy", body="Moon", target_ref=kind,
            t_days=t, longitude_deg=moon.value(t) % 360.0, velocity_dps=moon.velocity(t),
            latitude_deg=beta, eclipse_candidate=eclipse_candidate(kind, beta),
            gamma_proxy=beta, ayanamsha_id=ayanamsha_id,
        ))
    return rows


def contact_episode_rows(chart_id: str, spline: HermiteSpline, episode: ContactEpisode,
                          target_kind: str, natal_lon: float,
                          ayanamsha_id: str = CANONICAL_AYANAMSHA) -> list[KinematicsRow]:
    """The up-to-5 knot rows for one contact episode (contact_in, the two
    contact_core_in/out if the episode saturates omega_core, contact_peak,
    contact_out) — episode_id groups them (§3.1's "episode_id groups the 5
    knots of one contact episode")."""
    d = dwell_days(episode.t_in, episode.t_out)
    epi_id = make_episode_id(chart_id, episode.body, episode.target_ref, episode.t_in)

    def _row(event_kind: str, t: float) -> KinematicsRow:
        return KinematicsRow(
            chart_id=chart_id, event_kind=event_kind, body=episode.body,
            target_kind=target_kind, target_ref=episode.target_ref, t_days=t,
            longitude_deg=spline.value(t) % 360.0, velocity_dps=spline.velocity(t),
            episode_id=epi_id, dwell_days=d, orb_deg=episode.orb_deg,
            orb_source=episode.orb_source, ayanamsha_id=ayanamsha_id,
        )

    rows = [_row("contact_in", episode.t_in)]
    if episode.ok_core_in is not None:
        rows.append(_row("contact_core_in", episode.ok_core_in))
    rows.append(_row("contact_peak", episode.t_peak))
    if episode.ok_core_out is not None:
        rows.append(_row("contact_core_out", episode.ok_core_out))
    rows.append(_row("contact_out", episode.t_out))
    return rows


def attach_dwell_weight(rows: Sequence[KinematicsRow], w_dwell: float) -> None:
    """Mutates dwell_weight in place on every row of a contact episode's
    5-knot group (kept as a separate step so callers can compute w_dwell from
    the body's mean daily motion once, then apply it uniformly)."""
    for r in rows:
        r.dwell_weight = w_dwell


# ═════════════════════════════════════════════════════════════════════════════
# DB / ephemeris I/O layer — needs a live connection (and pyswisseph for the
# sidereal derivation). Exercised only by the "live" test tier.
# ═════════════════════════════════════════════════════════════════════════════

def _sidereal_offset_series(jds: Sequence[float], ayanamsha: str) -> list[float]:
    """The ayanamsha offset at each Julian Day, via the SAME pyswisseph call
    sequence as brahmagyan.l0_ephemeris.derive_sidereal (§N.5 — reusing the
    existing product convention's AYANAMSHA_MAP + set_sid_mode/get_ayanamsa_ut,
    inlined here only to avoid derive_sidereal's per-call sign/nakshatra
    bucketing overhead, which stage 0 doesn't need — the continuous longitude
    is what gets splined; bucketing happens downstream via root-finding)."""
    from brahmagyan.l0_ephemeris import AYANAMSHA_MAP, _SWE_AVAILABLE  # noqa: PLC0415

    if not _SWE_AVAILABLE:
        raise RuntimeError("pyswisseph not available; cannot derive sidereal positions")
    import swisseph as swe  # noqa: PLC0415

    sidm_id = AYANAMSHA_MAP.get(ayanamsha)
    if sidm_id is None:
        raise ValueError(f"Unknown ayanamsha '{ayanamsha}'")
    swe.set_sid_mode(sidm_id)
    return [swe.get_ayanamsa_ut(jd) for jd in jds]


def fetch_ephemeris_series(conn, body: str, date_start: date, date_end: date,
                            ayanamsha: str = CANONICAL_AYANAMSHA) -> dict:
    """Read `ephemeris_daily` (stored tropical) for `body` over
    [date_start, date_end] and derive sidereal longitude at read time.

    Returns {"t_days": [...], "longitude_deg": [...] (sidereal), "speed_dps": [...],
             "latitude_deg": [...]}, all ascending by date.
    """
    rows = conn.execute(
        """
        SELECT date, tropical_longitude, latitude, speed_dps
        FROM ephemeris_daily
        WHERE body = %s AND ayanamsha_id = 'tropical'
          AND date BETWEEN %s AND %s
        ORDER BY date ASC
        """,
        [body, date_start, date_end],
    ).fetchall()
    if not rows:
        raise RuntimeError(
            f"stage0_kinematics: no ephemeris_daily rows for body={body} "
            f"[{date_start}, {date_end}]"
        )

    def _get(r, key, idx):
        return r[key] if isinstance(r, dict) else r[idx]

    dates = [_get(r, "date", 0) for r in rows]
    tropical = [float(_get(r, "tropical_longitude", 1)) for r in rows]
    latitude = [float(_get(r, "latitude", 2)) for r in rows]
    speed = [float(_get(r, "speed_dps", 3)) for r in rows]

    t_days = [(d - J2000_EPOCH).days for d in dates]
    import swisseph as swe  # noqa: PLC0415
    jds = [swe.julday(d.year, d.month, d.day, 12.0) for d in dates]
    offsets = _sidereal_offset_series(jds, ayanamsha)
    sidereal = [(trop - off) % 360.0 for trop, off in zip(tropical, offsets)]

    return {
        "t_days": [float(t) for t in t_days],
        "longitude_deg": sidereal,
        "speed_dps": speed,
        "latitude_deg": latitude,
    }


def fetch_natal_longitude(conn, chart_id: str, target_kind: str, target_ref: str,
                           ayanamsha: str = CANONICAL_AYANAMSHA) -> float:
    """Reference (never recompute, §N.5) the natal longitude of a graha or
    Lagna from `chart_facts` (L1)."""
    if target_kind == "natal_lagna":
        subject = LAGNA_FACT_SUBJECT
        row = conn.execute(
            """SELECT fact_value_num FROM chart_facts
               WHERE chart_id = %s AND fact_subject = %s
                 AND fact_key = 'longitude' AND ayanamsha_id = %s
               LIMIT 1""",
            [chart_id, subject, ayanamsha],
        ).fetchone()
    else:
        subject = GRAHA_FACT_SUBJECTS[target_ref]
        row = conn.execute(
            """SELECT fact_value_num FROM chart_facts
               WHERE chart_id = %s AND ayanamsha_id = %s
                 AND fact_category = 'graha_position' AND fact_subject = %s
                 AND fact_key = 'longitude_sidereal'
               LIMIT 1""",
            [chart_id, ayanamsha, subject],
        ).fetchone()
    if row is None:
        raise RuntimeError(
            f"stage0_kinematics: no natal longitude for chart={chart_id} "
            f"target_kind={target_kind} target_ref={target_ref}"
        )
    val = row["fact_value_num"] if isinstance(row, dict) else row[0]
    return float(val) % 360.0


def fetch_orb_deg(conn, body: str, target_class: str) -> tuple[float, str]:
    """omega from bg_transit_rules per (body, target_class); default 3.0 deg,
    orb_source='default_3deg' if absent (§3.1's own honest fallback — served,
    never silently). bg_transit_rules does not carry a per-target orb_deg
    column in the live schema as of this writer (its columns are rule_type /
    graha / primary_house / vedha_house / phala — see migration 397), so this
    currently always falls back; the lookup is still attempted so a future
    schema addition is picked up automatically without a code change here."""
    try:
        row = conn.execute(
            """SELECT orb_deg FROM bg_transit_rules
               WHERE graha = %s AND rule_type = %s LIMIT 1""",
            [body, target_class],
        ).fetchone()
    except Exception:
        row = None
    if row is not None:
        val = row["orb_deg"] if isinstance(row, dict) else row[0]
        if val is not None:
            return float(val), "bg_transit_rules"
    return DEFAULT_ORB_DEG, "default_3deg"


# Mean sidereal daily motion (deg/day, unsigned) — reused from the existing
# canonical constant table (pipeline.transit_search.MEAN_MOTIONS, §N.5: do
# not re-declare a second copy that could drift), used ONLY as v_bar_b in the
# dwell-time normalization D_nom = 2*omega/v_bar_b — never as the velocity
# itself (the "true velocity" rule forbids that; velocity is always the
# spline derivative).
def _mean_daily_motion(body: str) -> float:
    from pipeline.transit_search import MEAN_MOTIONS  # noqa: PLC0415
    return abs(MEAN_MOTIONS[body])


def compute_contacts_for_body(chart_id: str, spline: HermiteSpline, body: str,
                               natal_targets: Sequence[tuple[str, str, float]],
                               t_grid: Sequence[float], orb_lookup: Callable[[str, str], tuple[float, str]],
                               ayanamsha_id: str = CANONICAL_AYANAMSHA
                               ) -> list[KinematicsRow]:
    """The per-body Stage 0 contact pipeline: for every natal target
    `(target_kind, target_ref, natal_lon)`, find contact episodes, compute
    dwell weight, and emit the up-to-5 knot rows per episode. `orb_lookup`
    is `(body, target_class) -> (orb_deg, orb_source)` — see `fetch_orb_deg`."""
    v_bar = _mean_daily_motion(body)
    rows: list[KinematicsRow] = []
    for target_kind, target_ref, natal_lon in natal_targets:
        target_class = target_ref  # bg_transit_rules keys per (graha, target/rule class)
        orb_deg, orb_source = orb_lookup(body, target_class)
        episodes = find_contact_episodes(
            spline, natal_lon, body, target_ref, t_grid, orb_deg, orb_source,
        )
        d_nom = dwell_nominal_days(orb_deg, v_bar)
        for ep in episodes:
            w = dwell_weight(dwell_days(ep.t_in, ep.t_out), d_nom)
            ep_rows = contact_episode_rows(chart_id, spline, ep, target_kind, natal_lon, ayanamsha_id)
            attach_dwell_weight(ep_rows, w)
            rows.extend(ep_rows)
    return rows


REPLACE_PRIOR_SQL = "DELETE FROM kala_field_kinematics WHERE chart_id = %s"

UPSERT_SQL = """
INSERT INTO kala_field_kinematics (
    chart_id, event_kind, body, target_kind, target_ref, t_days, event_ts,
    longitude_deg, velocity_dps, latitude_deg, episode_id, dwell_days,
    dwell_weight, orb_deg, orb_source, eclipse_candidate, gamma_proxy,
    precision_regime, ayanamsha_id, source_table
) VALUES (
    %(chart_id)s, %(event_kind)s, %(body)s, %(target_kind)s, %(target_ref)s,
    %(t_days)s, %(event_ts)s, %(longitude_deg)s, %(velocity_dps)s,
    %(latitude_deg)s, %(episode_id)s, %(dwell_days)s, %(dwell_weight)s,
    %(orb_deg)s, %(orb_source)s, %(eclipse_candidate)s, %(gamma_proxy)s,
    %(precision_regime)s, %(ayanamsha_id)s, 'ephemeris_daily'
)
ON CONFLICT (chart_id, event_kind, body, COALESCE(target_ref, ''), t_days)
DO UPDATE SET
    longitude_deg = EXCLUDED.longitude_deg,
    velocity_dps = EXCLUDED.velocity_dps,
    latitude_deg = EXCLUDED.latitude_deg,
    dwell_days = EXCLUDED.dwell_days,
    dwell_weight = EXCLUDED.dwell_weight,
    orb_deg = EXCLUDED.orb_deg,
    orb_source = EXCLUDED.orb_source,
    eclipse_candidate = EXCLUDED.eclipse_candidate,
    gamma_proxy = EXCLUDED.gamma_proxy,
    computed_at = now()
"""


def row_to_params(row: KinematicsRow) -> dict:
    return {
        "chart_id": row.chart_id,
        "event_kind": row.event_kind,
        "body": row.body,
        "target_kind": row.target_kind,
        "target_ref": row.target_ref,
        "t_days": row.t_days,
        "event_ts": t_days_to_datetime(row.t_days),
        "longitude_deg": row.longitude_deg,
        "velocity_dps": row.velocity_dps,
        "latitude_deg": row.latitude_deg,
        "episode_id": row.episode_id,
        "dwell_days": row.dwell_days,
        "dwell_weight": row.dwell_weight,
        "orb_deg": row.orb_deg,
        "orb_source": row.orb_source,
        "eclipse_candidate": row.eclipse_candidate,
        "gamma_proxy": row.gamma_proxy,
        "precision_regime": row.precision_regime,
        "ayanamsha_id": row.ayanamsha_id,
    }


def write_kinematics_rows(conn, rows: Sequence[KinematicsRow]) -> int:
    """Idempotent per-row upsert (natural key = chart_id, event_kind, body,
    target_ref, t_days) — row-level idempotency; the coarser once-per-chart
    delete-then-insert (§N.3) is orchestrated once in `ka_kshetra.plan_substeps`
    (Lane C), never here (§1 rail 4)."""
    n = 0
    for r in rows:
        conn.execute(UPSERT_SQL, row_to_params(r))
        n += 1
    return n
