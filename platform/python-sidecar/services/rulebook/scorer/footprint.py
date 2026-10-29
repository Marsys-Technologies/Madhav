"""Rule Book scorer - footprint gate (v1.0 4.4 as changed by v1.1 D8), testability (v1.1 D7), descriptive hits (C4).

All of it is computed from charts and rules (and, for testability and the descriptive hits, from episode
counts and windows). Nothing here feeds a p-value.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .core import FamilyContext, _place
from .model import ChartTimeline, Episode, UnitSpec


def _union_true(t: ChartTimeline, rids: Sequence[str]) -> np.ndarray:
    u = np.zeros(t.n_days, dtype=bool)
    for r in rids:
        a = t.states.get(r)
        if a is not None:
            u |= a == 1
    return u


def _touch_3d(true_days: np.ndarray) -> Optional[float]:
    n = true_days.size
    if n < C.G1_WINDOW_DAYS:
        return None
    cs = np.concatenate([[0], np.cumsum(true_days.astype(np.int64))])
    w = cs[C.G1_WINDOW_DAYS:] - cs[:-C.G1_WINDOW_DAYS]
    return float(np.count_nonzero(w > 0) / w.size)


def _touch_month(true_days: np.ndarray, h_start: int) -> Optional[float]:
    n = true_days.size
    cs = np.concatenate([[0], np.cumsum(true_days.astype(np.int64))])
    hit = tot = 0
    d0 = date.fromordinal(h_start)
    y, m = d0.year, d0.month
    if d0.day != 1:
        m += 1
        if m == 13:
            y, m = y + 1, 1
    while True:
        first = date(y, m, 1).toordinal()
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        last = date(ny, nm, 1).toordinal() - 1
        if last - h_start > n - 1:
            break
        a, b = first - h_start, last - h_start
        tot += 1
        hit += int(cs[b + 1] - cs[a] > 0)
        y, m = ny, nm
    return hit / tot if tot else None


def touch_rates(timelines: Sequence[ChartTimeline], units: Sequence[UnitSpec]) -> Dict[str, Dict[str, Optional[float]]]:
    """Per unit and window class ('3d', 'month'): the mean over charts of the share of windows that contain at
    least one TRUE day of any evaluable member of the unit (v1.1 D8)."""
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for u in units:
        rids = [m.rid for m in u.members()]
        r3: List[float] = []
        rm: List[float] = []
        for t in timelines:
            tr = _union_true(t, rids)
            a = _touch_3d(tr)
            b = _touch_month(tr, t.h_start)
            if a is not None:
                r3.append(a)
            if b is not None:
                rm.append(b)
        out[u.unit_id] = {
            "3d": float(np.mean(r3)) if r3 else None,
            "month": float(np.mean(rm)) if rm else None,
        }
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
    ctx: FamilyContext, scored: Sequence[Episode], min_episodes: int = C.TESTABLE_MIN_EPISODES, min_charts: int = C.TESTABLE_MIN_CHARTS
) -> Dict[str, Any]:
    """v1.1 D7.2: at least 250 scored primary episodes in at least 15 charts, and at least half the family's
    evaluable units surviving the footprint gate in at least one used window class."""
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
    reasons = []
    if not ok_ep:
        reasons.append(f"episodes {len(scored)} (need {min_episodes}) in {charts} charts (need {min_charts})")
    if not ok_units:
        reasons.append(f"units surviving the gate {survivors} of {n_units} (need at least half)")
    return {"testable": bool(ok_ep and ok_units), "episodes": len(scored), "charts": charts, "units": n_units, "units_surviving": survivors, "reasons": reasons}


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
