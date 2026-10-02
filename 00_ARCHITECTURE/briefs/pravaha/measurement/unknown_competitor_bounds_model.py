"""Reference MODEL (Stream B) for SI addendum v1.3 §4 — attainable rank percentiles and plateau fractions when some
competing candidates have an UNKNOWN intensity. Not production: it states the arithmetic the candidate adapter must reproduce,
and holds Codex's round-8 worked cases as asserts. Stdlib only. `python unknown_competitor_bounds_model.py` runs them.

Protocol rules reproduced (EVALUATION_PROTOCOL_v2_3 §4): rank by signed intensity DESCENDING; ties take the AVERAGE rank; two
values are the same value iff |a-b| < TOL (1e-9), and tie groups are formed by the ADJACENT-GAP rule (a chain of values each
within TOL of its neighbour is one group — so an unknown value can BRIDGE two groups); percentile = 100*(r-1)/N with N = ALL
admitted candidates (unknown ones included); the §8.3 plateau test is on the largest tie-group fraction of the candidate set.
An unknown intensity is any finite real >= 0 (the schema bound on evidence_for): the boundary 0 is admissible, nothing
below it, nothing above is excluded."""
from itertools import product

TOL = 1e-9
BIG = 1e6                       # stands for "any value above every known value"


def groups(values):
    """Adjacent-gap tie groups over sorted-descending values: list of lists of indices into `values`."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    out, cur = [], [order[0]]
    for a, b in zip(order, order[1:]):
        if values[a] - values[b] < TOL:
            cur.append(b)
        else:
            out.append(cur); cur = [b]
    out.append(cur)
    return out


def percentile_of(values, idx):
    """100*(avg_rank-1)/N of candidate `idx` (ties average, adjacent-gap groups)."""
    pos = 0
    for g in groups(values):
        if idx in g:
            avg_rank = pos + (len(g) + 1) / 2.0
            return 100.0 * (avg_rank - 1) / len(values)
        pos += len(g)
    raise AssertionError


def placements(known):
    """A finite, sufficient set of placement classes for ONE unknown: the boundary 0, 'above everything', every known value, points
    half a tolerance and 1.5 tolerances either side of each known value (ties and BRIDGES), and the midpoint of every gap."""
    pts = {0.0, BIG}
    ks = sorted(set(known))
    for v in ks:
        for d in (0.0, 0.5 * TOL, 1.5 * TOL, -0.5 * TOL, -1.5 * TOL):
            if v + d >= 0.0:
                pts.add(v + d)
    for a, b in zip(ks, ks[1:]):
        pts.add((a + b) / 2.0)
    pts.add(ks[0] / 2.0)
    return sorted(pts)


def attainable(known, k_unknown, f):
    """The set of values f(full_vector) over ALL placement-class assignments of k unknowns (k small)."""
    pl = placements(known)
    return {f(list(known) + list(combo)) for combo in product(pl, repeat=k_unknown)}


def percentile_range(known, matched_idx, k_unknown):
    s = attainable(known, k_unknown, lambda v: round(percentile_of(v, matched_idx), 9))
    return min(s), max(s), sorted(s)


def plateau_fractions(known, k_unknown):
    s = attainable(known, k_unknown, lambda v: round(max(len(g) for g in groups(v)) / len(v), 9))
    return sorted(s)


if __name__ == "__main__":
    # (1) round 7 / v1.2 §4: matched 2; known others 1, 0; two unknown => N=5, percentile in [0, 40]
    lo, hi, _ = percentile_range([2.0, 1.0, 0.0], 0, 2)
    assert (lo, hi) == (0.0, 40.0), (lo, hi)
    # (2) round 8 R8-8(1): matched 0; known others 2, 1; two unknown — unknowns cannot be strictly BELOW 0
    lo, hi, vals = percentile_range([0.0, 2.0, 1.0], 0, 2)
    assert (lo, hi) == (60.0, 80.0), (lo, hi, vals)
    # (3) round 8 R8-8(2): known 0,0,1.5e-9,1.5e-9,1,2,3 + ONE unknown => N=8; plateau fraction takes 3/8, 2/8 AND 5/8 (void)
    fr = plateau_fractions([0.0, 0.0, 1.5e-9, 1.5e-9, 1.0, 2.0, 3.0], 1)
    assert 0.375 in fr and 0.25 in fr and 0.625 in fr, fr
    assert max(fr) >= 0.5 > min(fr)          # the §8.3 verdict (>= 50% void) is NOT invariant over admissible values => unqualified
    # (4) a candidate with no unknown competitor has a single percentile
    lo, hi, _ = percentile_range([2.0, 1.0, 0.0], 0, 0)
    assert lo == hi == 0.0
    print("OK: worked cases reproduced (ranges [0,40], [60,80]; plateau fractions", [round(x, 3) for x in fr], ")")
