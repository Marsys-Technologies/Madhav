"""Contact solving: bracket every root from the arc index, refine by direct
Swiss bisection at the instant (plan §4.2).

Relations (plan §4.2, WP1_CONTRACTS.md §2.2 N-14, §7):
  conjunction      — separation root, target longitude, orb per orb_conj_*
  drishti_contact  — directed special dṛṣṭi: body at target − angle for each
                     angle in the per-graha table (forward count: the aspect
                     from body b falls at (λ_b + angle) mod 360, so the aspect
                     lands on the target when λ_b = (target − angle) mod 360 —
                     GOCHARA_DESIGN_SPECS §6.2 inv 6); nodes cast NONE (N-14)
  return           — separation root like conjunction, orb per orb_return_*
  sign_ingress / nakshatra_ingress / kakshya_cell_crossing — boundary roots at
                     30° / 13°20′ / 3°75′ grid edges (boundary-exact, no orb —
                     WP1 §7 orb_ingress; episodes rooted at the span edge). All
                     three grids include the 0°/360° seam (spec §6.2: "0° seam
                     root exists", #14) — one root per seam crossing: an interior
                     wrap crossing is owned by the arc that REACHES the boundary,
                     and a domain endpoint sitting exactly on the seam (direct
                     start at 0°, retrograde end at 0°) keeps its endpoint root
                     (R6; see arcs.MonotoneArc.covers_degree and
                     contacts._append_root_deduped).

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
    level_deg: float         # the effective longitude reached (= (target−aspect) % 360)
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
    from `level_wrapped_deg`, ((lon - level + 180) % 360) - 180. That
    objective is continuous only while the body's travel over the bracket
    stays under 180° from the level — the caller MUST pass a bracket that
    satisfies this (`_refine_root` does so by construction: a narrow window
    around the spline root, clamped inside the arc, capped at well under
    180° of travel). Bracketing a whole arc is NOT valid: a wrap-band arc
    can span up to a year of travel (Sun), and the objective then crosses
    its ±180° branch cut mid-arc, leaving both endpoints with the same
    sign (the ADK-0019 defect: "lost its bracket" on real 2029 curves).
    Every calc_ut asserts the SWIEPH backend via the returned retflag
    (F-14); retflag & 4 raises EphemerisBackendError (the caller reports
    NOT_RUN, never PASS).

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


# Refinement window around the spline root (ADK-0019). The wrapped objective
# in swiss_bisect is continuous only under <180° of travel from the level, so
# the refinement bracket is a narrow window around the already-computed
# spline root — never the whole arc. The initial half-window is one day
# (spline error on daily knots is far below that even near a station); on a
# lost bracket (spline/Swiss disagreement near a station) the window is
# expanded by ×4, capped so the arc's average travel over the half-window
# stays at or under _REFINE_MAX_TRAVEL_DEG — comfortably short of the 180°
# branch cut. If the capped window still does not bracket, that is a real
# spline/Swiss divergence and swiss_bisect's ValueError propagates.
_REFINE_INITIAL_HALF_WINDOW_DAYS = 1.0
_REFINE_WINDOW_GROWTH = 4.0
_REFINE_MAX_TRAVEL_DEG = 90.0


def _refine_root(
    body: str,
    arc: MonotoneArc,
    spline_jd: float,
    level_wrapped_deg: float,
    ephe_path: str | None,
) -> tuple[float, int]:
    """Swiss-refine one spline root inside a narrow, branch-cut-safe window."""
    arc_span = arc.end_jd - arc.start_jd
    travel = abs(arc.end_lon_unwrapped - arc.start_lon_unwrapped)
    rate = travel / arc_span if arc_span > 0.0 else 0.0  # mean deg/day
    max_half = (
        min(arc_span / 2.0, _REFINE_MAX_TRAVEL_DEG / rate)
        if rate > 0.0
        else arc_span / 2.0
    )
    half = min(_REFINE_INITIAL_HALF_WINDOW_DAYS, max_half)
    while True:
        jd_lo = max(arc.start_jd, spline_jd - half)
        jd_hi = min(arc.end_jd, spline_jd + half)
        try:
            return swiss_bisect(body, jd_lo, jd_hi, level_wrapped_deg, ephe_path)
        except ValueError:
            if jd_lo <= arc.start_jd and jd_hi >= arc.end_jd:
                raise  # the whole arc is already the bracket: real failure
            if half >= max_half:
                raise  # widening further risks the ±180° cut: real failure
            half = min(half * _REFINE_WINDOW_GROWTH, max_half)


def _levels_for_relation(body: str, relation: str, target_deg: float) -> list[tuple[float, float]]:
    """[(aspect_deg, effective_level_deg)] for (body, relation, target)."""
    t = float(target_deg) % 360.0
    if relation in ("conjunction", "return"):
        return [(0.0, t)]
    if relation == "drishti_contact":
        # N-14: nodes cast no dṛṣṭi at all — an empty angle list means the
        # relation simply has no roots for this body (never an error state).
        # Direction (GOCHARA_DESIGN_SPECS §6.2 inv 6 — computed, never
        # mirrored): a special aspect from body b falls at (λ_b + angle)
        # mod 360 (Mars 4th/8th +90/+210, Saturn 3rd/10th +60/+270, Jupiter
        # 5th/9th +120/+240), so the aspect lands on the target when the body
        # sits at (target − angle) mod 360.
        return [(a, (t - a) % 360.0) for a in drishti_angles(body)]
    raise ValueError(f"relation {relation!r} has no exact-separation levels")


def _levels_unwrapped_for_arc(level: float, arc: MonotoneArc) -> list[float]:
    """The unwrapped representatives of `level` inside `arc`'s band.

    Non-seam levels have exactly one representative per band. The 0°/360°
    seam has TWO — 0 at a band's start, 360 at the previous band's end — and
    an arc can legitimately own BOTH: an arc whose endpoints are both seams
    (a full-revolution piece, e.g. [360k, 360(k+1)]) carries a crossing at
    each end, and they are DISTINCT physical events (one revolution apart).
    Both in-range representatives are returned, each solved separately; the
    shared-cut duplicates between adjacent arcs are collapsed in
    _append_root_deduped (R6 + A2.2 amendment 3).
    """
    w = float(level) % 360.0
    lo = min(arc.start_lon_unwrapped, arc.end_lon_unwrapped)
    hi = max(arc.start_lon_unwrapped, arc.end_lon_unwrapped)
    candidates = (360.0, 0.0) if w == 0.0 else (w,)
    out: list[float] = []
    for c in candidates:
        level_u = c + 360.0 * arc.wrap_index
        if lo - 1e-9 <= level_u <= hi + 1e-9:
            out.append(level_u)
    return out


def _append_root_deduped(
    roots: list[ContactRoot],
    *,
    body: str,
    relation: str,
    target_deg: float,
    aspect_deg: float,
    level: float,
    arc: MonotoneArc,
    level_u: float,
    tol_deg: float,
    ephe_path: str | None,
    refine: bool,
) -> None:
    """Bracket, (optionally) Swiss-refine and append one root — dropping the
    duplicate candidate when an interior seam crossing is covered by BOTH the
    arc that reaches 360 and the next band's arc that starts at 0 (R6
    ownership): both bisections land on the shared cut instant, so the second
    candidate of the same (level, instant) is the same physical event and is
    dropped. The kept root is the arc that REACHES the boundary (its end is
    the seam instant), preserving the pre-R6 attribution; a genuine endpoint
    root (domain start/end exactly on the seam) has no twin and is kept.
    """
    spline_jd = _bisect_arc(arc, level_u, tol_deg)
    seam_level = float(level) % 360.0 == 0.0
    if seam_level:
        # Anchor the candidate to the arc endpoint THE SOLVED ROOT SITS ON:
        # wrap-cut arcs share the identical cut float, so the two candidates
        # of one physical crossing anchor to the same instant even when the
        # two bisections land a tolerance apart (the pre-anchor 1e-6-day join
        # missed exactly this on real ephemerides — Venus at the seam gave two
        # roots 0.02 s apart). The anchor follows the ROOT's position, never
        # blindly the arc's start: an arc whose both endpoints are seams
        # carries a distinct crossing at each end (A2.2 amendment 3 — the
        # start-only anchor merged 710d into 350d and duplicated 1430d).
        def _anchor(a: MonotoneArc, jd: float) -> float:
            seam_ends = []
            s = a.start_lon_unwrapped % 360.0
            e = a.end_lon_unwrapped % 360.0
            if s <= 1e-9 or s >= 360.0 - 1e-9:
                seam_ends.append(a.start_jd)
            if e <= 1e-9 or e >= 360.0 - 1e-9:
                seam_ends.append(a.end_jd)
            if not seam_ends:
                return jd
            return min(seam_ends, key=lambda e_jd: abs(e_jd - jd))

        anchor = _anchor(arc, spline_jd)
        for existing in roots:
            if (
                existing.relation == relation
                and existing.target_deg == float(target_deg) % 360.0
                and existing.aspect_deg == float(aspect_deg)
                and existing.level_deg == float(level)
                and _anchor(existing.arc, existing.spline_exact_jd) == anchor
            ):
                # Same physical seam crossing found twice. Keep the arc that
                # REACHES the seam (the root at its end); if neither does,
                # keep the first candidate deterministically.
                this_at_end = abs(spline_jd - arc.end_jd) < abs(
                    spline_jd - arc.start_jd)
                existing_at_end = abs(
                    existing.spline_exact_jd - existing.arc.end_jd) < abs(
                    existing.spline_exact_jd - existing.arc.start_jd)
                if this_at_end and not existing_at_end:
                    roots.remove(existing)
                    break
                return
    exact_jd = spline_jd
    if refine:
        exact_jd, _ = _refine_root(body, arc, spline_jd, level, ephe_path)
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
            for level_u in _levels_unwrapped_for_arc(level, arc):
                _append_root_deduped(
                    roots, body=body, relation=relation, target_deg=target_deg,
                    aspect_deg=aspect_deg, level=level, arc=arc, level_u=level_u,
                    tol_deg=tol_deg, ephe_path=ephe_path, refine=refine,
                )
    roots.sort(key=lambda r: r.exact_jd)
    return roots


def boundary_degrees(relation: str) -> list[float]:
    """The fixed grid degrees (in [0,360)) at which `relation` has roots —
    boundary-exact, no orb (WP1 §7 orb_ingress)."""
    if relation == "sign_ingress":
        # 12 cusps per revolution, 0° (the Aries seam) included (spec §6.2,
        # #14) — O-SS-1 pins Sun = 12 sign crossings/yr.
        return [SIGN_DEG * k for k in range(12)]
    if relation == "nakshatra_ingress":
        # 27 boundaries per revolution, 0° included — O-SS-1 pins 27/yr.
        return [NAKSHATRA_DEG * k for k in range(27)]
    if relation == "kakshya_cell_crossing":
        # Equal-eighths cells (WP1_CONTRACTS.md §8): re-derived against O-SS-1
        # (Sun = 96 kakṣyā crossings/yr), NOT the earlier "sign_ingress owns
        # 0°/30°" carve-out — sign_ingress did not own 0° (the #14 seam was
        # owned by nobody) and the 84-boundary internal-only grid cannot
        # reach the pinned 96. Every 3.75° step is a cell crossing, including
        # the sign cusps (30s = 3.75·8s) and the 0° seam; sign_ingress
        # reports the cusp crossings too (a separate relation's event).
        return [KAKSHYA_CELL_DEG * k for k in range(96)]
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
            for level_u in _levels_unwrapped_for_arc(level, arc):
                _append_root_deduped(
                    roots, body=body, relation=relation, target_deg=level,
                    aspect_deg=0.0, level=level, arc=arc, level_u=level_u,
                    tol_deg=tol_deg, ephe_path=ephe_path, refine=refine,
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
