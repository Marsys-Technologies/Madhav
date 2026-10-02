"""Unknown-competitor bounds (SI addendum v1.3 §4) — a PROVEN enumeration of the attainable tie partitions.

A candidate whose ranking intensity `si` is UNKNOWN (stored NULL = unqualified) stays in the frozen candidate set and in N. Its
admissible values are every finite real >= 0 (including the boundary 0 and every value that ties with or bridges known values
under the protocol's tolerance TAU = 1e-9, ADJACENT-GAP grouping: values sorted, a group is a maximal run whose adjacent
differences are all < TAU). Rank percentile and the §8.3 plateau fraction depend on the assignment ONLY through the sorted
sequence and which adjacent differences are cuts (>= TAU). The enumeration below ranges over exactly those structures.

Why it is complete (the lemma every line below follows). Sort the known values v_1 <= ... <= v_n. An unknown lies in exactly one
SLOT: LOW = [0, v_1], MID_j = [v_j, v_{j+1}], HIGH = [v_n, inf) (closed: equality with a known value is a tie, difference 0).
Inside a slot, m unknowns sorted ascending give a chain of consecutive differences; each difference is either a CUT (>= TAU) or
UNCUT (in [0, TAU)); any CUT/UNCUT pattern with c cuts is attainable iff the chain's total span allows it:
  * MID_j, span g = v_{j+1} - v_j, m+1 differences:  c = 0 needs g < (m+1)·TAU;  c >= 1 needs g >= c·TAU
    (cuts absorb any excess; uncut differences may be 0).
  * LOW, m differences (the last one ends at v_1), the leftmost value must stay >= 0:  c·TAU <= v_1.
  * HIGH, m differences: any c.
  * no known value at all: m-1 differences among the unknowns: any c.
Necessity: a cut contributes >= TAU and an uncut < TAU to the span, so c cuts need span >= c·TAU and zero cuts need span <
(m+1)·TAU. Sufficiency: construct the chain explicitly (cuts TAU, the first cut taking the excess; uncut 0; for c = 0 equal
spacing g/(m+1)) — `tests/l3/gochara_eval/test_unknowns.py` builds that witness for EVERY enumerated structure with exact rational
arithmetic and re-derives the outcome from the numbers. Which unknowns are in which slot, in which order, and which of them are
members of the event's overlapping set ("contained") are enumerated exhaustively; nothing is sampled, no sentinel value or step
size is used (the earlier grid of 0.75·TAU steps and the BIG = 1000 sentinel were unsound: unknown–unknown bridges across a gap
of up to (m+1)·TAU, and an "above everything" placement that sat below a known value of 1e10).

The enumeration is finite; when its size exceeds the budget the caller receives `BudgetExceeded` and reports the endpoint
UNQUALIFIED — never a partial range.
"""
from __future__ import annotations

import math
from fractions import Fraction
from itertools import combinations
from typing import Iterator, Sequence

from .registry import TIE_TOL

TAU_EXACT = Fraction(TIE_TOL)          # the exact value of the float tolerance, for the real-valued unknowns
DEFAULT_BUDGET = 400_000               # structures evaluated per query before the answer is declared BudgetExceeded


class BudgetExceeded(RuntimeError):
    """The attainable-structure enumeration is larger than the budget; the endpoint is unqualified."""


# ---- concrete (all values known) arithmetic: unchanged protocol definitions ----------------------------------------------
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


# ---- the structural enumeration ------------------------------------------------------------------------------------------
def _compositions(total: int, parts: int) -> Iterator[tuple[int, ...]]:
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first, *rest)


def _feasible(kind: str, c: int, m: int, span: Fraction | None) -> bool:
    """Is a chain of m unknowns with c cuts attainable in a slot of this kind? (the lemma in the module docstring)"""
    if kind == "mid":
        return span < (m + 1) * TAU_EXACT if c == 0 else span >= c * TAU_EXACT
    if kind == "low":
        return c == 0 or c * TAU_EXACT <= span          # span = v_1 here: the leftmost unknown stays >= 0
    return True                                          # "high" and "only"


def _slot_options(kind: str, span: Fraction | None, a: int, b: int):
    """Every (labels, cuts) of the m = a+b unknowns in one slot: which positions are A (contained) and which differences are cuts."""
    m = a + b
    if m == 0:
        yield (), ()
        return
    n_diff = m - 1 if kind == "only" else m + (1 if kind == "mid" else 0)
    for a_pos in combinations(range(m), a):
        labels = tuple("A" if i in a_pos else "B" for i in range(m))
        for mask in range(1 << n_diff):
            cuts = tuple(bool(mask >> i & 1) for i in range(n_diff))
            if _feasible(kind, sum(cuts), m, span):
                yield labels, cuts


def enumerate_structures(known: Sequence[float], known_cont: Sequence[bool], k_a: int, k_b: int,
                         budget: int = DEFAULT_BUDGET) -> Iterator[dict]:
    """Yield every attainable structure: {'pct': Fraction|None, 'plateau': Fraction, 'slots': [...]}.

    `known` — the known intensities; `known_cont[i]` — whether known candidate i is CONTAINED (overlaps the event's span);
    `k_a` unknowns are contained, `k_b` are not. `pct` is the matched (highest contained) candidate's rank percentile, None when
    nothing is contained."""
    n = len(known)
    order = sorted(range(n), key=lambda i: known[i])
    ks = [known[i] for i in order]
    kc = [bool(known_cont[i]) for i in order]
    kcut = [ks[j + 1] - ks[j] >= TIE_TOL for j in range(n - 1)]                    # the protocol's own float predicate
    if n == 0:
        slots = [("only", None)]
    else:
        slots = ([("low", Fraction(ks[0]))]
                 + [("mid", Fraction(ks[j + 1]) - Fraction(ks[j])) for j in range(n - 1)]
                 + [("high", None)])
    n_dist = math.comb(len(slots) + k_a - 1, k_a) * math.comb(len(slots) + k_b - 1, k_b)
    if n_dist > budget:
        raise BudgetExceeded(f"{n_dist} slot distributions > budget {budget}")
    count = 0
    for da in _compositions(k_a, len(slots)):
        for db in _compositions(k_b, len(slots)):
            opts = [list(_slot_options(kind, span, a, b)) for (kind, span), a, b in zip(slots, da, db)]
            if any(not o for o in opts):
                continue
            idx = [0] * len(opts)
            while True:
                count += 1
                if count > budget:
                    raise BudgetExceeded(f"more than {budget} structures")
                yield _outcome(slots, ks, kc, kcut, [opts[s][idx[s]] for s in range(len(opts))])
                s = len(opts) - 1
                while s >= 0:
                    idx[s] += 1
                    if idx[s] < len(opts[s]):
                        break
                    idx[s] = 0
                    s -= 1
                if s < 0:
                    break


def _outcome(slots, ks, kc, kcut, chosen) -> dict:
    """Assemble the ascending item sequence with its cut flags and read off the matched percentile and the plateau fraction."""
    n = len(ks)
    items: list[bool] = []         # contained?
    cut_after: list[bool] = []     # cut between item i and i+1
    plan = []

    if n == 0:
        labels, cuts = chosen[0]
        for lab in labels:
            items.append(lab == "A")
        cut_after.extend(cuts)
        plan.append(("only", None, labels, cuts))
    else:
        labels, cuts = chosen[0]                                   # LOW: u_1..u_m then v_1
        for lab in labels:
            items.append(lab == "A")
        cut_after.extend(cuts)                                     # m diffs, the last ends at v_1
        plan.append(("low", slots[0][1], labels, cuts))
        for j in range(n):
            items.append(kc[j])
            if j < n - 1:
                labels, cuts = chosen[1 + j]                       # MID_j: v_j, u..., v_{j+1}
                if not labels:
                    cut_after.append(kcut[j])
                else:
                    for lab in labels:
                        items.append(lab == "A")
                    cut_after.extend(cuts)                         # m+1 diffs
                plan.append(("mid", slots[1 + j][1], labels, cuts))
        labels, cuts = chosen[-1]                                  # HIGH: v_n, u_1..u_m
        if labels:
            for lab in labels:
                items.append(lab == "A")
            cut_after.extend(cuts)
        plan.append(("high", None, labels, cuts))
    total = len(items)
    assert len(cut_after) == total - 1, (len(cut_after), total)
    # groups ascending
    sizes: list[int] = []
    owner: list[int] = []
    cur = 0
    for i in range(total):
        cur += 1
        owner.append(len(sizes))
        if i == total - 1 or cut_after[i]:
            sizes.append(cur)
            cur = 0
    plateau = Fraction(max(sizes), total)
    pct = None
    contained = [i for i, c in enumerate(items) if c]
    if contained:
        g = owner[contained[-1]]                                   # the highest contained item (ascending order)
        above = sum(sizes[g + 1:])
        pct = Fraction(100 * (2 * above + sizes[g] - 1), 2 * total)    # 100*(above + (s+1)/2 - 1)/N
    return {"pct": pct, "plateau": plateau, "plan": plan, "items": items, "cut_after": cut_after}


def event_percentiles(known: Sequence[float], known_cont: Sequence[bool], k_a: int, k_b: int,
                      budget: int = DEFAULT_BUDGET) -> tuple[list[float], int]:
    """All attainable matched-candidate rank percentiles, and the number of structures enumerated."""
    out: set[Fraction] = set()
    n = 0
    for st in enumerate_structures(known, known_cont, k_a, k_b, budget):
        n += 1
        if st["pct"] is not None:
            out.add(st["pct"])
    return sorted(float(x) for x in out), n


def percentile_range(known: Sequence[float], matched_idx: int, k_unknown: int, budget: int = DEFAULT_BUDGET):
    """(min, max, sorted values) of the matched KNOWN candidate's percentile over every assignment of `k_unknown` unknowns."""
    cont = [i == matched_idx for i in range(len(known))]
    vals, _ = event_percentiles(known, cont, 0, k_unknown, budget)
    return min(vals), max(vals), vals


def plateau_fractions(known: Sequence[float], k_unknown: int, budget: int = DEFAULT_BUDGET) -> list[float]:
    """Every attainable largest-tie-group fraction of the candidate set."""
    cont = [False] * len(known)
    return sorted({float(st["plateau"]) for st in enumerate_structures(known, cont, 0, k_unknown, budget)})
