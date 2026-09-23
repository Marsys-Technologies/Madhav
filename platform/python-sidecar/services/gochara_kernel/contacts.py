"""Contact solving: bracket every root from the arc index, refine by direct
Swiss bisection at the instant (plan §4.2).

Relations (plan §4.2, WP1_CONTRACTS.md §2.2 N-14, §7):
  conjunction      — separation root, target longitude, orb per orb_conj_*
  drishti_contact  — directed special dṛṣṭi: body at target + angle for each
                     angle in the per-graha table; nodes cast NONE (N-14)
  return           — separation root like conjunction, orb per orb_return_*
  sign_ingress / nakshatra_ingress / kakshya_cell_crossing — boundary roots at
                     30° / 13°20′ / 3°75′ grid edges (boundary-exact, no orb —
                     WP1 §7 orb_ingress; episodes rooted at the span edge)

Two-stage discipline (plan §4.2): the arc index brackets the root from the
spline; the root is then REFINED by direct Swiss bisection at the instant
(FLG_SIDEREAL, FLG_SWIEPH), with retflag asserted on every call (F-14). The
spline value seeds the unwrapped branch for the Swiss bisection so the
objective is continuous over a bracket of at most a few hours.

ADOPTED from services/w2g/crossings.py (the bracket-then-bisect contact
solver); the E8 fixes live in arcs.py (no station merge) and episodes.py
(no-exact episodes, horizon truncation), and relation semantics (dṛṣṭi table,
nodes) come from WP1_CONTRACTS.md rather than the legacy SPECIAL_DRISHTI_DEG.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .arcs import ARCSEC_PER_DEG, ArcIndex, MonotoneArc
from .convention import (
    KAKSHYA_CELL_DEG,
    NAKSHATRA_DEG,
    SIGN_DEG,
    drishti_angles,
)
from .knots import EphemerisBackendError, calc_sidereal_lon

MAX_BISECTION_ITERATIONS = 80

EXACT_SEPARATION_RELATIONS = ("conjunction", "return", "drishti_contact")
BOUNDARY_RELATIONS = ("sign_ingress", "nakshatra_ingress", "kakshya_cell_crossing")


@dataclass(frozen=True)
class ContactRoot:
    """One bracketed and Swiss-refined root for a (body, target, relation)."""

    body: str
    relation: str
    target_deg: float        # the target longitude the relation is measured on
    aspect_deg: float        # dṛṣṭi angle for drishti_contact, else 0.0
    level_deg: float         # the effective longitude reached (= (target+aspect) % 360)
    spline_exact_jd: float   # root of the spline (arc index stage)
    exact_jd: float          # refined by direct Swiss bisection at the instant
    bracket: tuple[float, float]
    arc: MonotoneArc         # the arc that produced the root (branch source)


def _bisect_arc(arc: MonotoneArc, level_unwrapped: float, tol_deg: float) -> float:
    """Bisect one monotone arc for `level_unwrapped` (spline stage).

    Adopted from services/w2g/crossings.py:_bisect_for_level, with the stored
    endpoint accepted when the interpolant disagrees by less than the
    tolerance (a wrap boundary endpoint is recorded as exactly 360k while the
    spline re-evaluates 360k ± a fraction of an arcsecond — inherited from
    w2g, kept).
    """
    lo, hi = arc.start_jd, arc.end_jd
    f_lo = arc.unwrapped_longitude_at(lo) - level_unwrapped
    f_hi = arc.unwrapped_longitude_at(hi) - level_unwrapped
    if f_lo == 0.0:
        return lo
    if f_hi == 0.0:
        return hi
    if f_lo * f_hi > 0.0:
        nearest = lo if abs(f_lo) <= abs(f_hi) else hi
        if min(abs(f_lo), abs(f_hi)) <= max(tol_deg, 0.01):
            return nearest
        raise ValueError(
            f"level {level_unwrapped}° is not bracketed by arc "
            f"{arc.body}#{arc.arc_index}"
        )
    for _ in range(MAX_BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)
        f_mid = arc.unwrapped_longitude_at(mid) - level_unwrapped
        if abs(f_mid) <= tol_deg or (hi - lo) < 1e-9:
            return mid
        if f_lo * f_mid <= 0.0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)


def swiss_bisect(
    body: str,
    jd_lo: float,
    jd_hi: float,
    level_wrapped_deg: float,
    ephe_path: str | None,
    tol_days: float = 1e-9,
) -> tuple[float, int]:
    """Refine a root by DIRECT Swiss bisection at the instant.

    Objective: wrapped angular separation of the body's sidereal longitude
    from `level_wrapped_deg`, ((lon - level + 180) % 360) - 180, continuous
    over a sub-day bracket for every body (the Moon moves < 14°/day and the
    arc-index bracket is at most an arc or two long). Every calc_ut asserts
    the SWIEPH backend via the returned retflag (F-14); retflag & 4 raises
    EphemerisBackendError (the caller reports NOT_RUN, never PASS).

    Returns (refined_jd, retflag).
    """
    level = float(level_wrapped_deg) % 360.0

    def sep(jd: float) -> float:
        lon, retflag = calc_sidereal_lon(body, jd, ephe_path)
        if not (retflag & 2) or (retflag & 4):
            raise EphemerisBackendError(body, retflag)
        return ((lon - level + 180.0) % 360.0) - 180.0

    f_lo, f_hi = sep(jd_lo), sep(jd_hi)
    if f_lo == 0.0:
        return jd_lo, 2
    if f_hi == 0.0:
        return jd_hi, 2
    if f_lo * f_hi > 0.0:
        # Bracket lost between spline and Swiss (spline error near a
        # station): widen once by a quarter day each side before failing.
        span = jd_hi - jd_lo
        jd_lo2, jd_hi2 = jd_lo - 0.25 * span - 0.01, jd_hi + 0.25 * span + 0.01
        f_lo, f_hi = sep(jd_lo2), sep(jd_hi2)
        if f_lo * f_hi > 0.0:
            raise ValueError(
                f"{body}: separation root at {level:.4f}° lost its bracket "
                f"under direct Swiss ({jd_lo}..{jd_hi})"
            )
        jd_lo, jd_hi = jd_lo2, jd_hi2
    lo, hi = jd_lo, jd_hi
    for _ in range(MAX_BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)
        if hi - lo < tol_days:
            return mid, 2
        f_mid = sep(mid)
        if f_lo * f_mid <= 0.0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi), 2


def _levels_for_relation(body: str, relation: str, target_deg: float) -> list[tuple[float, float]]:
    """[(aspect_deg, effective_level_deg)] for (body, relation, target)."""
    t = float(target_deg) % 360.0
    if relation in ("conjunction", "return"):
        return [(0.0, t)]
    if relation == "drishti_contact":
        # N-14: nodes cast no dṛṣṭi at all — an empty angle list means the
        # relation simply has no roots for this body (never an error state).
        return [(a, (t + a) % 360.0) for a in drishti_angles(body)]
    raise ValueError(f"relation {relation!r} has no exact-separation levels")


def find_roots(
    index: ArcIndex,
    body: str,
    relation: str,
    target_deg: float,
    ephe_path: str | None = None,
    refine: bool = True,
) -> list[ContactRoot]:
    """Every exact-separation root of (body, target, relation) in the index.

    Candidate roots are enumerated from the arc index (a range predicate —
    the candidate set is auditable), each bracketed on its arc, then refined
    by direct Swiss bisection at the instant when `refine` is true.
    """
    tol_deg = index.tolerance_arcsec / ARCSEC_PER_DEG
    roots: list[ContactRoot] = []
    for aspect_deg, level in _levels_for_relation(body, relation, target_deg):
        for arc in index.arcs_covering_degree(level):
            level_u = float(level) % 360.0 + 360.0 * arc.wrap_index
            spline_jd = _bisect_arc(arc, level_u, tol_deg)
            exact_jd = spline_jd
            if refine:
                exact_jd, _ = swiss_bisect(
                    body, arc.start_jd, arc.end_jd, level, ephe_path
                )
            roots.append(
                ContactRoot(
                    body=body,
                    relation=relation,
                    target_deg=float(target_deg) % 360.0,
                    aspect_deg=float(aspect_deg),
                    level_deg=float(level),
                    spline_exact_jd=float(spline_jd),
                    exact_jd=float(exact_jd),
                    bracket=(float(arc.start_jd), float(arc.end_jd)),
                    arc=arc,
                )
            )
    roots.sort(key=lambda r: r.exact_jd)
    return roots


def boundary_degrees(relation: str) -> list[float]:
    """The fixed grid degrees (in [0,360)) at which `relation` has roots —
    boundary-exact, no orb (WP1 §7 orb_ingress)."""
    if relation == "sign_ingress":
        return [SIGN_DEG * k for k in range(1, 12)]
    if relation == "nakshatra_ingress":
        return [NAKSHATRA_DEG * k for k in range(1, 27)]
    if relation == "kakshya_cell_crossing":
        # Equal-eighths cells: internal boundaries at 3.75° steps within each
        # sign (0° and 30° are sign cusps — sign_ingress owns those). Lords
        # per WP1_CONTRACTS.md §8 (cell k of a sign → KAKSHYA_LORD_ORDER[k]).
        out: list[float] = []
        for sign in range(12):
            for cell in range(1, 8):
                out.append(sign * SIGN_DEG + KAKSHYA_CELL_DEG * cell)
        return out
    raise ValueError(f"relation {relation!r} is not a boundary relation")


def find_boundary_roots(
    index: ArcIndex,
    body: str,
    relation: str,
    ephe_path: str | None = None,
    refine: bool = True,
) -> list[ContactRoot]:
    """Every boundary root of `relation` for `body` in the index.

    Sign- / nakṣatra- / kakṣyā-ingress relations are span-edge rooted; their
    episode objects are boundary-exact (no orb). The target of a boundary
    root is the degree itself.
    """
    tol_deg = index.tolerance_arcsec / ARCSEC_PER_DEG
    roots: list[ContactRoot] = []
    for level in boundary_degrees(relation):
        for arc in index.arcs_covering_degree(level):
            level_u = float(level) % 360.0 + 360.0 * arc.wrap_index
            spline_jd = _bisect_arc(arc, level_u, tol_deg)
            exact_jd = spline_jd
            if refine:
                exact_jd, _ = swiss_bisect(
                    body, arc.start_jd, arc.end_jd, level, ephe_path
                )
            roots.append(
                ContactRoot(
                    body=body,
                    relation=relation,
                    target_deg=float(level),
                    aspect_deg=0.0,
                    level_deg=float(level),
                    spline_exact_jd=float(spline_jd),
                    exact_jd=float(exact_jd),
                    bracket=(float(arc.start_jd), float(arc.end_jd)),
                    arc=arc,
                )
            )
    roots.sort(key=lambda r: r.exact_jd)
    return roots


__all__ = [
    "BOUNDARY_RELATIONS",
    "ContactRoot",
    "EXACT_SEPARATION_RELATIONS",
    "boundary_degrees",
    "find_boundary_roots",
    "find_roots",
    "swiss_bisect",
]
