"""Rule Book scorer - footprint gate (v1.0 4.4 as changed by v1.1 D8), testability (v1.1 D7), descriptive hits (C4).

All of it is computed from charts and rules (and, for testability and the descriptive hits, from episode
counts and windows). Nothing here feeds a p-value.
"""

from __future__ import annotations

import itertools
from datetime import date
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .core import FamilyContext, _place
from .model import ChartTimeline, Episode, UnitSpec


def _windows(t: ChartTimeline, window: str) -> Tuple[np.ndarray, np.ndarray]:
    """Window starts and lengths wholly inside the horizon: '3d' every 3-day window starting on each day; 'month'
    the calendar months (SUR-RB-27 Q3)."""
    n = t.n_days
    if window == "3d":
        s = np.arange(0, max(0, n - C.G1_WINDOW_DAYS + 1))
        return s, np.full(s.size, C.G1_WINDOW_DAYS)
    lo, ln = [], []
    d0 = date.fromordinal(t.h_start)
    y, m = (d0.year, d0.month) if d0.day == 1 else ((d0.year + (d0.month == 12)), d0.month % 12 + 1)
    while True:
        first = date(y, m, 1).toordinal()
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        last = date(ny, nm, 1).toordinal() - 1
        if last - t.h_start > n - 1:
            break
        lo.append(first - t.h_start)
        ln.append(last - first + 1)
        y, m = ny, nm
    return np.array(lo, dtype=np.int64), np.array(ln, dtype=np.int64)


def _reading_touch(t: ChartTimeline, rids: Sequence[str], window: str) -> Optional[float]:
    """CARVE-OUT 2 (SUR-RB-36): the D8 touch rate of one reading, from the timeline alone. The same rule as the
    scorer's coverage (SUR-RB-39 (1)): a window counts when at least one member is at least half assessed in it
    (otherwise it is skipped: NOT_ASSESSED is never FALSE); it is touched when a passing member is TRUE on a day."""
    from .core import reading_coverage

    starts, lens = _windows(t, window)
    if starts.size == 0:
        return None
    arrs = []
    for r in rids:  # a plain loop: the state read is attributed to this function on every Python version
        arrs.append(t.values(r))
    cov = np.full(starts.size, np.nan)
    for L in np.unique(lens):
        sel = lens == L
        cov[sel] = reading_coverage(arrs, starts[sel], int(L))
    ok = np.isfinite(cov)
    if not ok.any():
        return None
    return float(np.count_nonzero(cov[ok] > 0) / np.count_nonzero(ok))


def unit_touch(t: ChartTimeline, u: UnitSpec, window: str) -> Optional[float]:
    """SUR-RB-27 Q3, on the unit's FULL evaluable member set: E, single and conflict-free units -> touch rate of the
    OR of members; R units -> mean of member touch rates; MIXED units -> mean over all one-member-per-group readings
    of the touch rate of the OR across groups. (All three are the mean over readings, v1.4 M2.)"""
    rates = []
    for reading in itertools.product(*[[m.rid for m in g] for g in u.groups]):
        r = _reading_touch(t, reading, window)
        if r is not None:
            rates.append(r)
    return float(np.mean(rates)) if rates else None


def touch_rates(timelines: Sequence[ChartTimeline], units: Sequence[UnitSpec]) -> Dict[str, Dict[str, Optional[float]]]:
    """Per unit and window class ('3d', 'month'): the mean over charts of ``unit_touch`` (v1.1 D8, SUR-RB-27 Q3)."""
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for u in units:
        per = {"3d": [], "month": []}
        for t in timelines:
            for w in per:
                r = unit_touch(t, u, w)
                if r is not None:
                    per[w].append(r)
        out[u.unit_id] = {w: (float(np.mean(v)) if v else None) for w, v in per.items()}
    return out


def gate_from_touch(touch: Mapping[str, Mapping[str, Optional[float]]]) -> Dict[str, FrozenSet[str]]:
    """unit_id -> the grades for which the unit is dropped (touch rate above 0.60 in that window class)."""
    drop: Dict[str, FrozenSet[str]] = {}
    inv = {v: k for k, v in C.WINDOW_CLASS_OF_GRADE.items()}
    for uid, rates in touch.items():
        gs = frozenset(inv[w] for w, r in rates.items() if r is not None and r > C.TOUCH_RATE_GATE)
        if gs:
            drop[uid] = gs
    return drop


def pooled_touch(touch: Mapping[str, Mapping[str, Optional[float]]]) -> Dict[str, Optional[float]]:
    """Reported, not gated (v1.1 D8): the mean touch rate over units, per window class."""
    out: Dict[str, Optional[float]] = {}
    for w in ("3d", "month"):
        v = [r[w] for r in touch.values() if r.get(w) is not None]
        out[w] = float(np.mean(v)) if v else None
    return out


def family_testable(
    ctx: FamilyContext,
    scored: Sequence[Episode],
    min_episodes: int = C.TESTABLE_MIN_EPISODES,
    min_charts: int = C.TESTABLE_MIN_CHARTS,
    admitted: Optional[Sequence[int]] = None,
    donor_rules: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """v1.1 D7.2 with v1.2 K4 and K11, from counts and horizons only (no state, no p-value):
    at least 250 scored primary episodes in at least 15 charts; at least half the family's evaluable units
    surviving the footprint gate in at least one used window class; at least 15 charts with at least 5 eligible
    donors for check (b) AND for check (c). Direction testability (K4) and Z25 availability (K5) are reported
    here as well: they decide STRONG's reachability and the min-p set, not the family's testability."""
    from .core import applicable_mask, direction_counts, donor_eligibility_counts

    scored = [e for e, ok in zip(scored, applicable_mask(ctx, scored)) if ok]  # K2: counts are of scored-APPLICABLE episodes
    charts = len({e.chart for e in scored})
    used = {e.grade for e in scored}
    survivors = 0
    for u in ctx.units:
        dropped = ctx.gate_drop.get(u.unit_id, frozenset())
        if any(g not in dropped for g in used):
            survivors += 1
    n_units = len(ctx.units)
    ok_ep = len(scored) >= min_episodes and charts >= min_charts
    ok_units = n_units > 0 and survivors * 2 >= n_units * 1  # survivors >= half of the units
    donors = donor_eligibility_counts(ctx, scored, admitted, donor_rules)
    ok_donors = donors["b"] >= C.DONOR_FLOOR_CHARTS and donors["c"] >= C.DONOR_FLOOR_CHARTS
    dirc = direction_counts(ctx, scored)
    reasons = []
    if not ok_donors:
        reasons.append(f"charts with at least {C.MIN_ELIGIBLE_DONORS} eligible donors: (b) {donors['b']}, (c) {donors['c']} (need {C.DONOR_FLOOR_CHARTS} each)")
    if not ok_ep:
        reasons.append(f"episodes {len(scored)} (need {min_episodes}) in {charts} charts (need {min_charts})")
    if not ok_units:
        reasons.append(f"units surviving the gate {survivors} of {n_units} (need at least half)")
    return {
        "testable": bool(ok_ep and ok_units and ok_donors),
        "episodes": len(scored),
        "charts": charts,
        "units": n_units,
        "units_surviving": survivors,
        "donor_charts_b": donors["b"],
        "donor_charts_c": donors["c"],
        "direction": dirc,
        "reasons": reasons,
    }


def descriptive_hits(ctx: FamilyContext, scored: Sequence[Episode], scheme: Optional[str] = None) -> Dict[str, Any]:
    """v1.0 3.2 / v1.1 C4, descriptive only. For each scored episode and each member of its applicable units:
    O = the member is TRUE on at least one day of the window; E = share of same-length windows of the block
    (the clipped window's length) that contain at least one TRUE day of the member. O/E is not a test."""
    scheme = scheme or ctx.schemes[0][0]
    O = 0
    E = 0.0
    n = 0
    for i, ep in enumerate(scored):
        e = _place(ctx, scheme, ep, i)
        bl, bh = ctx.blocks(scheme, ep.chart)[e.blk]
        for v in ctx.klass_variants(e.klass):
            for g in v.groups:
                for rid in g:
                    T, A = ctx.comp_prefix(ep.chart, ("m", rid))
                    nst = bh - bl - e.L + 2
                    s = np.arange(bl, bl + nst)
                    touch = (T[s + e.L] - T[s]) > 0
                    O += int(T[e.b + 1] - T[e.a] > 0)
                    E += float(touch.mean())
                    n += 1
    return {"member_episodes": n, "O": O, "E": E, "O_over_E": (O / E) if E > 0 else None}


def build_family_context(family: str, timelines: Sequence[ChartTimeline], units: Sequence[UnitSpec]) -> Tuple[FamilyContext, Dict[str, Any]]:
    """The family context with the v1.1 D8 footprint gate applied, and the footprint report (hash it before opening)."""
    fam_units = [u for u in units if u.plane == family]
    touch = touch_rates(timelines, fam_units)
    drop = gate_from_touch(touch)
    ctx = FamilyContext(family, timelines, fam_units, drop)
    report = {
        "family": family,
        "units": len(fam_units),
        "touch_rates": {k: dict(v) for k, v in sorted(touch.items())},
        "pooled_touch_rate": pooled_touch(touch),
        "dropped": {k: sorted(v) for k, v in sorted(drop.items())},
    }
    return ctx, report


def sealed_gate_from_s7(s7: Mapping[str, Any], family: str) -> Dict[str, FrozenSet[str]]:
    """The sealed footprint gate (admission out/s7_footprint.json): unit -> grades dropped, from
    ``summary.<family>.<3day|month>.dropped_units``."""
    inv = {"3day": C.G1, "month": C.G2}
    drop: Dict[str, set] = {}
    for wc, grade in inv.items():
        for uid in ((s7.get("summary") or {}).get(family) or {}).get(wc, {}).get("dropped_units") or []:
            drop.setdefault(uid, set()).add(grade)
    return {k: frozenset(v) for k, v in drop.items()}
