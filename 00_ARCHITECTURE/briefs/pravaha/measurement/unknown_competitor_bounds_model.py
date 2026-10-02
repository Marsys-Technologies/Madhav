"""Reference MODEL (Stream B), v2 — SI addendum v1.3/v1.4 §4: attainable rank percentiles and plateau fractions when some competing
candidates have an UNKNOWN intensity. Not production: it states the arithmetic the candidate adapter must reproduce and holds the
Codex round-7/8/9 cases as asserts. Stdlib only. `python unknown_competitor_bounds_model.py` runs them.

Protocol rules (EVALUATION_PROTOCOL_v2_3 §4): rank by intensity DESCENDING; ties take the AVERAGE rank; two values are the same
value iff their difference is < TAU = 1e-9 and tie groups are formed by the ADJACENT-GAP rule (a chain whose adjacent differences are
all < TAU is one group, so an unknown can BRIDGE two groups); percentile = 100*(avg_rank - 1)/N with N = ALL admitted candidates;
§8.3: the largest tie group's fraction of the set. An unknown intensity is any finite real >= 0.

v2 replaces the v1 placement GRID (0.75·TAU steps, a BIG = 1000 sentinel), which Codex round 9 (R9-7) disproved: it missed
unknown–unknown bridges across a gap of up to (m+1)·TAU and a sentinel that sat below a known 1e10.

THE OUTCOME SET IS COMPUTED EXACTLY, BY BRUTE FORCE, ON A LATTICE THAT PROVABLY CONTAINS A WITNESS FOR EVERY ATTAINABLE STRUCTURE.
Lemma. Sort the known values; an unknown lies in a slot LOW=[0,v_1], MID_j=[v_j,v_{j+1}] or HIGH=[v_n,inf). The outcome depends only on
the sorted order and on which adjacent differences are cuts (>= TAU). A chain of m unknowns in MID_j with span g has an attainable
pattern of c cuts iff (c = 0 and g < (m+1)·TAU) or (c >= 1 and g >= c·TAU); in LOW iff c·TAU <= v_1; in HIGH always. Sufficiency is
by construction, and the construction only ever places values at  v_j + t·TAU  (t an integer, |t| <= m)  or at  v_j + i·g/(m+1)
(equal spacing, c = 0).  The lattice below contains exactly those points, so enumerating every assignment on it reaches every
attainable structure; every lattice assignment is a real assignment, so nothing unattainable is reported.
"""
from fractions import Fraction
from itertools import combinations_with_replacement, product

TAU = Fraction(1, 10**9)            # exact; the float 1e-9 differs from this in the 17th digit and the model says so rather than hide it


def _groups(values):
    order = sorted(range(len(values)), key=lambda i: -values[i])
    out, cur = [], [order[0]]
    for a, b in zip(order, order[1:]):
        if values[a] - values[b] < TAU:
            cur.append(b)
        else:
            out.append(cur)
            cur = [b]
    out.append(cur)
    return out


def percentile_of(values, idx):
    pos = 0
    for g in _groups(values):
        if idx in g:
            return Fraction(100) * (pos + Fraction(len(g) + 1, 2) - 1) / len(values)
        pos += len(g)
    raise AssertionError


def plateau_fraction(values):
    return Fraction(max(len(g) for g in _groups(values)), len(values))


def lattice(known, k):
    """Placement points: every v_j + t·TAU (|t| <= k), 0 + t·TAU, and equal-spacing points v_j + i·g/(m+1) (1 <= m <= k)."""
    ks = sorted({Fraction(x) for x in known})
    pts = {Fraction(0)}
    for t in range(0, k + 1):
        pts.add(t * TAU)
    for v in ks:
        for t in range(-k, k + 1):
            if v + t * TAU >= 0:
                pts.add(v + t * TAU)
    for a, b in zip(ks, ks[1:]):
        g = b - a
        for m in range(1, k + 1):
            for i in range(1, m + 1):
                pts.add(a + i * g / (m + 1))
    return sorted(pts)


def attainable(known, k_unknown, f):
    """{f(full vector)} over EVERY assignment of the unknowns on the lattice (unknowns are interchangeable here)."""
    kn = [Fraction(x) for x in known]
    return {f(kn + list(c)) for c in combinations_with_replacement(lattice(known, k_unknown), k_unknown)}


def percentile_range(known, matched_idx, k_unknown):
    s = attainable(known, k_unknown, lambda v: percentile_of(v, matched_idx))
    return float(min(s)), float(max(s)), sorted(float(x) for x in s)


def plateau_fractions(known, k_unknown):
    return sorted(float(x) for x in attainable(known, k_unknown, plateau_fraction))


if __name__ == "__main__":
    # (1) round 7: matched 2; known others 1, 0; two unknown => N=5, percentile in [0, 40]
    lo, hi, _ = percentile_range([2, 1, 0], 0, 2)
    assert (lo, hi) == (0.0, 40.0), (lo, hi)
    # (2) round 8 R8-8(1): matched 0; known others 2, 1; two unknown — unknowns cannot be strictly BELOW 0
    lo, hi, vals = percentile_range([0, 2, 1], 0, 2)
    assert (lo, hi) == (60.0, 80.0), (lo, hi, vals)
    # (3) round 8 R8-8(2): known 0,0,1.5e-9,1.5e-9,1,2,3 + ONE unknown => plateau fraction takes 3/8, 2/8 AND 5/8 (void)
    fr = plateau_fractions([0, 0, Fraction(3, 2) / 10**9, Fraction(3, 2) / 10**9, 1, 2, 3], 1)
    assert 0.375 in fr and 0.25 in fr and 0.625 in fr, fr
    assert max(fr) >= 0.5 > min(fr)
    # (4) no unknown => a single percentile
    lo, hi, _ = percentile_range([2, 1, 0], 0, 0)
    assert lo == hi == 0.0
    # (5) round 9 R9-7 (a): known [0, 2.9e-9, 1, 2, 3, 4] + 2 unknowns: two unknowns bridge the 2.9·TAU gap => a tie group of 4 of 8
    fr = plateau_fractions([0, Fraction(29, 10) / 10**9, 1, 2, 3, 4], 2)
    assert 0.5 in fr and max(fr) == 0.5, fr
    # (6) round 9 R9-7 (b): known [1e10, 0], matched 1e10, one unknown at 1e10+1 => percentile 33.33 (a sentinel BIG=1000 said 16.67)
    lo, hi, vals = percentile_range([10**10, 0], 0, 1)
    assert hi > 33.3 and lo == 0.0, (lo, hi, vals)
    print("OK: worked cases and both round-9 counterexamples reproduced "
          "(ranges [0,40], [60,80]; plateau", [round(x, 3) for x in plateau_fractions([0, 0, Fraction(3, 2) / 10**9, Fraction(3, 2) / 10**9, 1, 2, 3], 1)], ")")
