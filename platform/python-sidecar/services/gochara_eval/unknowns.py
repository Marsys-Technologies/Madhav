"""Unknown-competitor bounds (SI addendum v1.3 §4) — the production form of
measurement/unknown_competitor_bounds_model.py.

A candidate whose ranking intensity `si` is UNKNOWN (stored NULL = unqualified) stays in the frozen candidate set and in N
(addendum §4 item 1). Its admissible values are every finite real >= 0, INCLUDING the boundary 0 and every value that ties with
or bridges known values under the protocol's tolerance (|a-b| < 1e-9, ADJACENT-GAP grouping: a chain of values each within
tolerance of its neighbour is one group, so an unknown can bridge two groups). Bounds range over ALL admissible assignments with
average ranks for ties and percentile = 100*(r-1)/N. An endpoint is qualified only if its verdict is identical for every
attainable assignment (item 4).

Enumeration is over a finite, sufficient set of PLACEMENT CLASSES per unknown: the boundary 0, "above everything", every known
value, points within and just outside tolerance of each known value, every gap midpoint — and, because unknowns can also chain
with EACH OTHER (not only with known values), chain offsets of 0.75*tolerance up to the number of unknowns around each anchor.
When the number of assignments exceeds the budget the result is `BUDGET_EXCEEDED` — reported as unqualified, never guessed.
"""
from __future__ import annotations

import math
from itertools import combinations_with_replacement, product
from typing import Callable, Iterable, Sequence

from .registry import TIE_TOL

BIG = 1e3                      # stands for "any value above every known value" (ulp ~1e-13, far below TIE_TOL)
STEP = 0.75 * TIE_TOL          # a chain step strictly inside the tolerance
DEFAULT_BUDGET = 400_000       # assignment evaluations per query before the answer is declared BUDGET_EXCEEDED


class BudgetExceeded(RuntimeError):
    """The attainable-assignment enumeration is larger than the budget; the endpoint is unqualified."""


def groups(values: Sequence[float]) -> list[list[int]]:
    """Adjacent-gap tie groups over values sorted DESCENDING: lists of indices into `values`."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    out, cur = [], [order[0]]
    for a, b in zip(order, order[1:]):
        if values[a] - values[b] < TIE_TOL:
            cur.append(b)
        else:
            out.append(cur)
            cur = [b]
    out.append(cur)
    return out


def percentile_of(values: Sequence[float], idx: int) -> float:
    """100*(avg_rank-1)/N of candidate `idx`; ties (adjacent-gap groups) take the average rank."""
    pos = 0
    for g in groups(values):
        if idx in g:
            avg_rank = pos + (len(g) + 1) / 2.0
            return 100.0 * (avg_rank - 1) / len(values)
        pos += len(g)
    raise AssertionError("index not in any group")


def plateau_fraction(values: Sequence[float]) -> float:
    """Largest adjacent-gap tie group as a fraction of the candidate set (the §8.3 plateau test)."""
    return max(len(g) for g in groups(values)) / len(values)


def placements(known: Iterable[float], k_unknown: int) -> list[float]:
    """Placement classes for ONE unknown among `k_unknown` unknowns (finite, sufficient; see module docstring)."""
    ks = sorted(set(known))
    pts = {0.0, BIG}
    for j in range(0, k_unknown + 1):
        pts.add(j * STEP)                      # unknown-unknown chains from the boundary 0
        pts.add(BIG + j * STEP)                # ... and above everything
    for v in ks:
        for d in (0.0, 0.5 * TIE_TOL, 1.5 * TIE_TOL, -0.5 * TIE_TOL, -1.5 * TIE_TOL):
            if v + d >= 0.0:
                pts.add(v + d)
        for j in range(1, k_unknown + 1):
            for sgn in (1, -1):
                if v + sgn * j * STEP >= 0.0:
                    pts.add(v + sgn * j * STEP)
    for a, b in zip(ks, ks[1:]):
        pts.add((a + b) / 2.0)
    if ks:
        pts.add(ks[0] / 2.0)
    return sorted(pts)


def _n_multisets(n_places: int, k: int) -> int:
    return math.comb(n_places + k - 1, k) if k else 1


def assignments(known: Sequence[float], group_sizes: Sequence[int], budget: int = DEFAULT_BUDGET):
    """Yield one tuple of per-group value-multisets per attainable assignment. Unknowns inside one group are
    interchangeable (combinations with replacement); distinct groups are enumerated independently.
    Raises BudgetExceeded BEFORE enumerating if the count exceeds `budget`."""
    k = sum(group_sizes)
    pl = placements(known, k)
    total = 1
    for gsz in group_sizes:
        total *= _n_multisets(len(pl), gsz)
    if total > budget:
        raise BudgetExceeded(f"{total} assignments > budget {budget} (k_unknown={k}, placements={len(pl)})")
    parts = [list(combinations_with_replacement(pl, gsz)) for gsz in group_sizes]
    for combo in product(*parts):
        yield combo


def attainable(known: Sequence[float], k_unknown: int, f: Callable[[list[float]], object], budget: int = DEFAULT_BUDGET) -> set:
    """The set of values f(full_vector) over ALL placement-class assignments of k interchangeable unknowns."""
    out = set()
    for (combo,) in assignments(known, [k_unknown], budget):
        out.add(f(list(known) + list(combo)))
    return out


def percentile_range(known: Sequence[float], matched_idx: int, k_unknown: int, budget: int = DEFAULT_BUDGET):
    s = attainable(known, k_unknown, lambda v: round(percentile_of(v, matched_idx), 9), budget)
    return min(s), max(s), sorted(s)


def plateau_fractions(known: Sequence[float], k_unknown: int, budget: int = DEFAULT_BUDGET) -> list[float]:
    return sorted(attainable(known, k_unknown, lambda v: round(plateau_fraction(v), 9), budget))
