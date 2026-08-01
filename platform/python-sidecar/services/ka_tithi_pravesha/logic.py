"""
services/ka_tithi_pravesha/logic.py — pure, engine/DB-free computation for
item 13 (Tithi-Praveśa, lunar-return annual chart). SHAD_DARSHANA_BRIEF_v2_0.md
§1 item 13: "Tithi-Praveśa (lunar-return annual)." Wave W3. Registered as
writer id `ka_tithi_pravesha` (layer kala).

── WHAT TITHI-PRAVEŚA IS (disclosed derivation — B.10 / no deeper spec doc) ──
No spec doc beyond the one-line registry item exists for this technique (per
SHAD_DARSHANA_BRIEF_v2_0.md's own authority-order note); this module implements
it from established Jyotiṣa doctrine per the CLAUDECODE task brief's explicit
framing and KALA_TRANSFORMATION_HANDOFF_v1_0.md's own glossary entry
("Tithi-Praveśa (annual lunar-return chart)"), using `ga_tajaka` (L1 Tājika
Vārṣaphala, the SOLAR-return annual chart) as the closest codebase precedent:
Tithi-Praveśa is the LUNAR-return counterpart — the praveśa ("entry") year
begins at the instant the transiting Moon returns to its EXACT natal sidereal
longitude nearest each solar-birthday anniversary, and the annual chart
(Praveśa Lagna + graha positions) is cast for that instant. Same "annual-return
chart" pattern as `ga_tajaka`, anchored on the Moon instead of the Sun — see
writer.py's module docstring for the ephemeris-engine wiring and §N.5 data-
source discipline (natal Moon longitude is read verbatim from chart_facts,
never re-derived).

── SCOPE (disclosed, not an oversight) ───────────────────────────────────────
Return-instant + annual-chart-cast ONLY. The fuller Tājika-specific apparatus
(Muntha, Vārṣeśa candidate scoring, the five Tajik yogas) is Vārṣaphala-only
machinery `ga_tajaka` already owns; no codebase-attested classical source
treats that apparatus as part of Tithi-Praveśa specifically, so it is not
re-derived here (matches the project's own disclosed-scope convention, e.g.
ka_sudarshana_varsha's year-wheel-only scope).

── THE BRACKET-STRATEGY DESIGN (why this is NOT ga_tajaka's bisection verbatim) ─
`ga_tajaka._solar_return` brackets a ±2-day (widening to ±6) window around the
anniversary and bisects directly — safe because the Sun moves ~1 deg/day, so a
±2-day bracket can never contain more than one `ang_diff()` zero-crossing. The
Moon moves ~13.2 deg/day (a full 360° cycle every ~27.3 days), so the SAME
wide-bracket-around-anniversary strategy is unsafe here: a ±15-to-20-day
bracket (wide enough to guarantee catching the nearest return, since the
closest occurrence can be up to ~13.66 days from the anniversary) can just as
easily straddle `ang_diff()`'s -180/+180 WRAP DISCONTINUITY as it can the true
zero-crossing — both look identical to a bisection sign-change test, and
bisecting into the discontinuity converges to a false "root" ~180° off target
(confirmed empirically during design: a naive ±15-day bracket produced
diff_deg values of -179.997, +179.999 etc. on real chart data instead of
~0.001). The fix is a two-stage strategy: (1) a LINEAR ESTIMATE of the nearest
return, using the Moon's actual longitude at the anniversary plus its mean
daily speed — this estimate is always within one lunar sidereal month of the
true root by construction; (2) bisection within a NARROW (±1.5, widening to
±4) day bracket centered on that estimate, which is far too narrow to ever
contain the discontinuity (the Moon travels ~20-53° across the full widened
bracket span, nowhere near the ~180° needed to reach the wrap point starting
from a converged estimate). Re-verified on both canonical charts across 8
praveśa years each (1/2/5/10/20/30/40[/42]): every row converged with
diff_deg < 0.002° and the annual chart's own recomputed Moon longitude matched
natal to the same tolerance — see the writer's two-pass verification.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Optional, TypedDict

from dateutil.relativedelta import relativedelta

# Mean daily motion of the Moon (deg/day) — matches ga_tajaka_writer.py's own
# MEAN_SPEED["Moon"] = 13.176 (Tajik faster/slower convention), reused here
# rather than re-derived, per the project's one-source-of-truth-per-constant
# discipline.
MEAN_MOON_SPEED_DEG_PER_DAY = 13.176

# Convergence tolerance (deg) — matches ga_tajaka_writer.SOLAR_RETURN_TOL_DEG's
# convention exactly (0.01 deg). At the Moon's mean speed this is ≈1.1 minutes
# of wall-clock precision, comfortably tighter than the bisection's own
# 30-second time-tolerance stop condition below.
LUNAR_RETURN_TOL_DEG = 0.01

# Full-life horizon (ka_sudarshana_varsha / ka_avadhi / ka_jivana_parva
# convention) rather than ga_tajaka's bounded hybrid window: benchmarked at
# ~3.4ms/praveśa-year (root-find + full annual-chart cast) during design, so
# the FULL 120-year table is cheap here — no reason to under-serve relative to
# the codebase's other full-lifespan Kāla writers (disclosed choice; ga_tajaka's
# narrower window was driven by its much heavier 5-ayanamsha x Tajik-yoga
# computation, which doesn't apply to this writer's narrower scope).
DEFAULT_MAX_PRAVESHA_YEAR = 120

# Bisection bracket policy — see module docstring for why this is narrow
# (centered on a linear estimate), not wide-around-anniversary.
INITIAL_BRACKET_DAYS = 1.5
MAX_BRACKET_DAYS = 4.0
BRACKET_GROWTH_DAYS = 0.5
MAX_BRACKET_WIDEN_TRIES = 4
BISECTION_TIME_TOL = timedelta(seconds=30)
MAX_BISECTION_ITERS = 64


def ang_diff(a: float, b: float) -> float:
    """Signed shortest angular difference a-b in (-180, 180]. Matches
    ga_tajaka_writer.py's `_ang_diff` exactly (same convention, independently
    defined here to keep this module engine/DB-free and importable without
    the L1 writer's dependencies)."""
    return ((a - b + 180.0) % 360.0) - 180.0


def pravesha_anniversary(birth_dt: datetime, pravesha_year: int) -> datetime:
    """The Nth solar-birthday-anniversary wall-clock instant (pravesha_year=1
    -> birth_dt itself; pravesha_year=2 -> first birthday; ...), matching
    ga_tajaka's own varsha-year indexing convention exactly (1-indexed, N=1
    covers [birth, first anniversary))."""
    if pravesha_year < 1:
        raise ValueError(f"pravesha_year must be >= 1, got {pravesha_year}")
    return birth_dt + relativedelta(years=pravesha_year - 1)


class LunarReturnAudit(TypedDict):
    converged: bool
    diff_deg: Optional[float]
    bracket_days: float
    iterations: int
    estimate_offset_days: Optional[float]
    unconverged_reason: Optional[str]


def lunar_return(
    anniversary: datetime,
    natal_moon_long: float,
    moon_longitude_fn: Callable[[datetime], Optional[float]],
) -> tuple[datetime, LunarReturnAudit]:
    """Root-find the instant NEAREST `anniversary` where the Moon (as reported
    by `moon_longitude_fn`) returns to `natal_moon_long`. See module docstring
    for the two-stage (linear-estimate + narrow-bisection) strategy and why it
    differs from ga_tajaka's wide-bracket solar-return approach.

    `moon_longitude_fn(dt) -> float | None`: returns the sidereal Moon
    longitude (deg, 0..360) at wall-clock instant `dt`, or None if the
    underlying position engine cannot compute it (mirrors ga_tajaka's
    `_safe_f`/"no information" honesty discipline — B.10, never fabricate). May
    also raise; any exception is caught and treated identically to a None
    return, so a single unresolvable instant degrades this search to
    `converged: False` rather than propagating a crash.

    Always returns a (datetime, audit) pair — never raises. On failure to
    converge, the returned instant is `anniversary` itself (the same honest
    fallback ga_tajaka's `_unconverged` uses) and `audit["converged"]` is
    False with a named `unconverged_reason`.
    """

    def _safe_long(dt: datetime) -> Optional[float]:
        try:
            return moon_longitude_fn(dt)
        except Exception:  # noqa: BLE001 — engine-level failure, not a logic bug
            return None

    def _f(dt: datetime) -> Optional[float]:
        v = _safe_long(dt)
        return None if v is None else ang_diff(v, natal_moon_long)

    def _unconverged(reason: str, bracket_days_: float,
                     estimate_offset_days: Optional[float] = None) -> tuple[datetime, LunarReturnAudit]:
        diff = _f(anniversary)
        return anniversary, {
            "converged": False,
            "diff_deg": round(diff, 6) if diff is not None else None,
            "bracket_days": bracket_days_,
            "iterations": 0,
            "estimate_offset_days": estimate_offset_days,
            "unconverged_reason": reason,
        }

    # ── Stage 1: linear estimate ─────────────────────────────────────────────
    m0 = _safe_long(anniversary)
    if m0 is None:
        return _unconverged("position_engine_error_at_anniversary", 0.0)
    diff0 = ang_diff(natal_moon_long, m0)
    days_est = diff0 / MEAN_MOON_SPEED_DEG_PER_DAY
    guess = anniversary + timedelta(days=days_est)

    # ── Stage 2: narrow bisection around the estimate ────────────────────────
    bracket_days = INITIAL_BRACKET_DAYS
    lo = guess - timedelta(days=bracket_days)
    hi = guess + timedelta(days=bracket_days)
    f_lo, f_hi = _f(lo), _f(hi)
    tries = 0
    while ((f_lo is None or f_hi is None or f_lo * f_hi > 0)
           and bracket_days < MAX_BRACKET_DAYS and tries < MAX_BRACKET_WIDEN_TRIES):
        bracket_days += BRACKET_GROWTH_DAYS
        lo = guess - timedelta(days=bracket_days)
        hi = guess + timedelta(days=bracket_days)
        f_lo, f_hi = _f(lo), _f(hi)
        tries += 1
    if f_lo is None or f_hi is None:
        return _unconverged("position_engine_error", bracket_days, round(days_est, 4))
    if f_lo * f_hi > 0:
        return _unconverged("no_sign_change", bracket_days, round(days_est, 4))

    iters = 0
    while (hi - lo) > BISECTION_TIME_TOL and iters < MAX_BISECTION_ITERS:
        mid = lo + (hi - lo) / 2
        f_mid = _f(mid)
        if f_mid is None:
            # Unresolvable midpoint — stop bisecting here rather than crash;
            # [lo, hi] still brackets a real root, just not narrowed further.
            break
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
        iters += 1
    instant = lo + (hi - lo) / 2
    diff = _f(instant)
    if diff is None:
        return _unconverged("position_engine_error_at_final_instant", bracket_days, round(days_est, 4))
    return instant, {
        "converged": True,
        "diff_deg": round(diff, 6),
        "bracket_days": bracket_days,
        "iterations": iters,
        "estimate_offset_days": round(days_est, 4),
        "unconverged_reason": None,
    }


__all__ = [
    "MEAN_MOON_SPEED_DEG_PER_DAY",
    "LUNAR_RETURN_TOL_DEG",
    "DEFAULT_MAX_PRAVESHA_YEAR",
    "ang_diff",
    "pravesha_anniversary",
    "LunarReturnAudit",
    "lunar_return",
]
