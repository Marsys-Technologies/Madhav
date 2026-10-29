"""Rule Book scorer - the statistics: percentile scores, check (a), checks (b) and (c), direction check.

Conventions fixed here, each tied to a clause of the yardstick (v1.0 as amended by v1.1):

* Episode score (v1.0 3.2, v1.1 C3). For a member: coverage of the window = share of ASSESSED days
  that are TRUE (a window with fewer than half its days assessed is not scored). Its percentile is the
  mid-rank of that coverage among the coverages of all scorable windows of the same length lying wholly
  inside the same block (no wrap; a window clipped at a block edge is ranked against windows of the
  clipped length). A member whose coverage is identical in every such window is dropped for the
  episode. Unit score = mean of its members' percentiles; episode score = mean of its units'.
* T = mean over charts of (mean over that chart's episodes of the episode score).
* Check (a) (v1.1 D1): per chart and block, ONE shift drawn uniformly among the integers that keep every
  episode window of the block inside the block (and, added here for NOT_ASSESSED, on which every episode
  of the block is still scorable). 5-year blocks; F-D also 15-year blocks, in the same draws.
* Z25 (v1.1 D2): the mean of the top quartile of unit z-scores among units with at least 10 applicable
  episodes; a unit's score is the mean percentile over its applicable episodes (pooled over charts); z is
  standardised by the mean and sd of that score across the draws.
* p1 of a family: single-step min-p over the family's statistics, all ranked in the same draws.
* Check (b)/(c) (v1.1 D3, D4): per-chart independent donor draw, including self; donor mean fixed.
* Direction check (v1.1 D5): own-polarity score minus opposite-polarity score, from the (a) draws.

Every p-value counts the observed placement as one of the pool: p = (1 + #{draws >= observed}) / (draws + 1).
The observed value and the draws pass through the same arithmetic, so ties are exact.
"""

from __future__ import annotations

import math
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .model import ChartTimeline, CompKey, Episode, ScorerError, UnitSpec, Variant

Klass = Tuple[str, str, str]  # (polarity, area, grade)


# ── small pure helpers (unit-tested on their own) ───────────────────────────
def make_blocks(n_days: int, block_days: int, merge_below: int) -> List[Tuple[int, int]]:
    """Consecutive blocks over days 0..n_days-1 as inclusive (lo, hi); a final block shorter than
    ``merge_below`` merges into the previous one (v1.0 4.1 / v1.1 D1)."""
    if n_days <= 0:
        return []
    full = n_days // block_days
    rem = n_days - full * block_days
    blocks = [(i * block_days, (i + 1) * block_days - 1) for i in range(full)]
    if rem:
        if rem < merge_below and blocks:
            blocks[-1] = (blocks[-1][0], n_days - 1)
        else:
            blocks.append((full * block_days, n_days - 1))
    return blocks


def percentile_curve(T: np.ndarray, A: np.ndarray, bl: int, bh: int, L: int) -> np.ndarray:
    """Mid-rank percentile of the window coverage for every window start of length L inside [bl, bh].

    ``T``/``A`` are prefix sums (length n+1) of TRUE and of assessed days. NaN where the window is not
    scorable (fewer than half its days assessed) and everywhere when every scorable window has the same
    coverage (the member carries no information).
    """
    nst = bh - bl - L + 2
    if nst <= 0:
        return np.zeros(0, dtype=np.float32)
    s = np.arange(bl, bl + nst)
    num = T[s + L] - T[s]
    den = A[s + L] - A[s]
    ok = den * 2 >= L
    out = np.full(nst, np.nan, dtype=np.float32)
    if not ok.any():
        return out
    cov = np.round(num[ok] / den[ok], 10)
    if cov.min() == cov.max():
        return out
    srt = np.sort(cov)
    lo = np.searchsorted(srt, cov, side="left")
    hi = np.searchsorted(srt, cov, side="right")
    out[ok] = ((lo + hi) / (2.0 * cov.size)).astype(np.float32)
    return out


def or_values(member_vals: Sequence[Sequence[np.ndarray]]) -> np.ndarray:
    """Daily value of a multi-group unit variant. ``member_vals[g][i]`` is member i of group g as a float
    array (1 TRUE, 0 FALSE, NaN not assessed). A group's value is the share of its assessed members that are
    TRUE (members of a group are rival readings); groups are disjoint claims, OR-ed as 1 - prod(1 - value),
    which is the plain Kleene OR when every group has one member. NaN when nothing is TRUE and some group is
    not assessed (Kleene)."""
    n = member_vals[0][0].shape[0]
    none_true_prod = np.ones(n)
    any_pos = np.zeros(n, dtype=bool)
    any_na = np.zeros(n, dtype=bool)
    for grp in member_vals:
        stack = np.vstack([m[None, :] for m in grp])
        assessed = ~np.isnan(stack)
        cnt = assessed.sum(axis=0)
        tot = np.where(assessed, stack, 0.0).sum(axis=0)
        f = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)
        na = cnt == 0
        any_na |= na
        fz = np.where(na, 0.0, f)
        any_pos |= fz > 0
        none_true_prod *= 1.0 - fz
    out = 1.0 - none_true_prod
    out[~any_pos & any_na] = np.nan
    return out


def pool_p(pool: np.ndarray) -> float:
    """p of the observed value (index 0) among the pool: (1 + #{draws >= observed}) / (n_draws + 1)."""
    return float((np.count_nonzero(pool[1:] >= pool[0]) + 1) / pool.size)


def pool_p_all(pool: np.ndarray) -> np.ndarray:
    """p of every pool element: #{pool >= value} / pool.size (the observed is one of the pool)."""
    srt = np.sort(pool)
    return (pool.size - np.searchsorted(srt, pool, side="left")) / float(pool.size)


def min_p_adjusted(pools: Mapping[str, np.ndarray]) -> Tuple[float, Dict[str, float]]:
    """Single-step min-p over statistics ranked in the same draws. Returns (adjusted p, per-statistic p)."""
    names = sorted(pools)
    size = pools[names[0]].size
    minp = np.ones(size)
    per: Dict[str, float] = {}
    for nm in names:
        p = pool_p_all(pools[nm])
        per[nm] = float(p[0])
        minp = np.minimum(minp, p)
    return float(np.count_nonzero(minp <= minp[0]) / size), per


# ── the family context: timelines + units + caches ──────────────────────────
class FamilyContext:
    """Everything about one family that does not depend on the episodes.

    Built once per family and reused across studies (calibration) or used once (the real run). All caches
    are keyed so that re-use cannot mix different inputs.
    """

    def __init__(
        self,
        family: str,
        timelines: Sequence[ChartTimeline],
        units: Sequence[UnitSpec],
        gate_drop: Optional[Mapping[str, FrozenSet[str]]] = None,
    ):
        if family not in C.FAMILIES:
            raise ScorerError(f"unknown family {family!r}")
        self.family = family
        self.tl = list(timelines)
        for t in self.tl:
            t.validate()
        self.units = [u for u in units if u.plane == family]
        self.unit_by_id = {u.unit_id: u for u in self.units}
        # grades for which a unit is dropped by the footprint gate (v1.1 D8)
        self.gate_drop: Dict[str, FrozenSet[str]] = {k: frozenset(v) for k, v in (gate_drop or {}).items()}
        self.schemes = C.SCHEMES[family]
        self._blocks: Dict[Tuple[str, int], List[Tuple[int, int]]] = {}
        self._cpre: Dict[Tuple[int, CompKey], Tuple[np.ndarray, np.ndarray]] = {}
        self._ucurve: Dict[Tuple[Any, ...], np.ndarray] = {}
        self._kcurve: Dict[Tuple[Any, ...], np.ndarray] = {}
        self._kvars: Dict[Klass, List[Variant]] = {}
        self._cls_pre: Dict[Klass, Tuple[np.ndarray, np.ndarray, float]] = {}
        self.g0 = min(t.h_start for t in self.tl) if self.tl else 0
        self.g1 = max(t.h_end for t in self.tl) if self.tl else 0
        # flat layout of the per-chart prefix arrays: chart c occupies n_days + 1 entries from flat_off[c]
        self.flat_off = np.concatenate([[0], np.cumsum([t.n_days + 1 for t in self.tl])]).astype(np.int64)

    # structure ------------------------------------------------------------
    def blocks(self, scheme: str, chart: int) -> List[Tuple[int, int]]:
        k = (scheme, chart)
        if k not in self._blocks:
            for nm, bd, mb in self.schemes:
                if nm == scheme:
                    self._blocks[k] = make_blocks(self.tl[chart].n_days, bd, mb)
                    break
            else:
                raise ScorerError(f"scheme {scheme!r} not defined for {self.family}")
        return self._blocks[k]

    def klass_variants(self, klass: Klass) -> List[Variant]:
        """Unit variants an episode of this class brings: polarity matches, the footprint gate has not
        dropped the unit for the grade, and at least one member's own tags match the area (or GENERAL)."""
        if klass not in self._kvars:
            pol, area, grade = klass
            out: List[Variant] = []
            for u in self.units:
                if u.polarity != pol or grade in self.gate_drop.get(u.unit_id, frozenset()):
                    continue
                v = u.variant(area, moon_ok=(grade == C.G1))
                if v is not None:
                    out.append(v)
            self._kvars[klass] = out
        return self._kvars[klass]

    # component series -------------------------------------------------------
    def _member_vals(self, chart: int, rid: str) -> np.ndarray:
        t = self.tl[chart]
        a = t.states.get(rid)
        if a is None:
            return np.full(t.n_days, np.nan)
        v = a.astype(np.float64)
        v[a < 0] = np.nan
        return v

    def comp_vals(self, chart: int, comp: CompKey) -> np.ndarray:
        """Daily value of a component (1 TRUE, 0 FALSE, NaN not assessed; fractions for a multi-group OR). Not cached."""
        if comp[0] == "m":
            return self._member_vals(chart, comp[1])
        return or_values([[self._member_vals(chart, r) for r in g] for g in comp[1]])

    def comp_prefix(self, chart: int, comp: CompKey) -> Tuple[np.ndarray, np.ndarray]:
        """Prefix sums (length n+1) of TRUE and of assessed days. Members: exact integer counts, computed on
        demand from the int8 states (nothing cached: curves are). OR components: cached float prefix sums."""
        if comp[0] == "m":
            a = self.tl[chart].states.get(comp[1])
            n = self.tl[chart].n_days
            if a is None:
                return np.zeros(n + 1, dtype=np.int64), np.zeros(n + 1, dtype=np.int64)
            T = np.concatenate([[0], np.cumsum(a == 1, dtype=np.int64)])
            A = np.concatenate([[0], np.cumsum(a >= 0, dtype=np.int64)])
            return T, A
        k = (chart, comp)
        if k not in self._cpre:
            v = self.comp_vals(chart, comp)
            ok = ~np.isnan(v)
            self._cpre[k] = (
                np.concatenate([[0.0], np.cumsum(np.where(ok, v, 0.0))]),
                np.concatenate([[0], np.cumsum(ok, dtype=np.int64)]),
            )
        return self._cpre[k]

    # curves -----------------------------------------------------------------
    def comp_curve(self, scheme: str, chart: int, blk: int, L: int, comp: CompKey) -> np.ndarray:
        """Percentile curve of one component in one block (not cached: unit curves are, and they dominate memory)."""
        bl, bh = self.blocks(scheme, chart)[blk]
        T, A = self.comp_prefix(chart, comp)
        return percentile_curve(T, A, bl, bh, L)

    def unit_curve(self, scheme: str, chart: int, blk: int, L: int, var: Variant) -> np.ndarray:
        k = (scheme, chart, blk, L, var.key)
        c = self._ucurve.get(k)
        if c is None:
            c = _nanmean_stack([self.comp_curve(scheme, chart, blk, L, comp) for comp in var.components()])
            self._ucurve[k] = c
        return c

    def klass_curve(self, scheme: str, chart: int, blk: int, L: int, klass: Klass) -> np.ndarray:
        k = (scheme, chart, blk, L, klass)
        c = self._kcurve.get(k)
        if c is None:
            vs = self.klass_variants(klass)
            nst = self.blocks(scheme, chart)[blk]
            nst = nst[1] - nst[0] - L + 2
            if not vs:
                c = np.full(max(nst, 0), np.nan, dtype=np.float32)
            else:
                c = _nanmean_stack([self.unit_curve(scheme, chart, blk, L, v) for v in vs])
            self._kcurve[k] = c
        return c

    # class coverage prefix arrays, global day frame (checks (b) and (c)) -----
    def klass_prefix(self, klass: Klass) -> Tuple[np.ndarray, np.ndarray, float]:
        """(CT, CA, W): prefix sums of the weighted TRUE and weighted assessed component-days of the class, all
        charts concatenated in one flat array. Chart c's prefix at k days after its horizon start sits at flat
        index ``self.flat_off[c] + k`` (k = 0..n_days). W = total weight: every unit counts once, the components
        of one unit variant sharing its weight equally."""
        if klass in self._cls_pre:
            return self._cls_pre[klass]
        vs = self.klass_variants(klass)
        W = float(len(vs))
        CT = np.zeros(int(self.flat_off[-1]))
        CA = np.zeros(int(self.flat_off[-1]))
        for ci, t in enumerate(self.tl):
            dT = np.zeros(t.n_days)
            dA = np.zeros(t.n_days)
            for v in vs:
                comps = v.components()
                w = 1.0 / len(comps)
                for comp in comps:
                    val = self.comp_vals(ci, comp)
                    ok = ~np.isnan(val)
                    dT += w * np.where(ok, val, 0.0)
                    dA += w * ok
            o = int(self.flat_off[ci])
            CT[o + 1 : o + 1 + t.n_days] = np.cumsum(dT)
            CA[o + 1 : o + 1 + t.n_days] = np.cumsum(dA)
        self._cls_pre[klass] = (CT, CA, W)
        return self._cls_pre[klass]


def _nanmean_stack(curves: Sequence[np.ndarray]) -> np.ndarray:
    if len(curves) == 1:
        return curves[0]
    st = np.vstack(curves).astype(np.float64)
    ok = ~np.isnan(st)
    cnt = ok.sum(axis=0)
    tot = np.where(ok, st, 0.0).sum(axis=0)
    out = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)
    return out.astype(np.float32)


# ── assembling an episode set under one block scheme ─────────────────────────
class _Ep:
    __slots__ = ("idx", "chart", "klass", "okl", "blk", "a", "b", "L", "off", "K", "O", "sched", "w", "wd", "wn")

    def __init__(self) -> None:
        self.O = None


def _place(ctx: FamilyContext, scheme: str, ep: Episode, idx: int) -> _Ep:
    t = ctx.tl[ep.chart]
    lo, hi = ep.lo - t.h_start, ep.hi - t.h_start
    if lo < 0 or hi >= t.n_days:
        raise ScorerError(f"episode {idx}: window outside the chart's family horizon")
    blks = ctx.blocks(scheme, ep.chart)
    mid = (lo + hi) // 2
    bi = next(i for i, (bl, bh) in enumerate(blks) if bl <= mid <= bh)
    bl, bh = blks[bi]
    e = _Ep()
    e.idx, e.chart, e.blk = idx, ep.chart, bi
    e.a, e.b = max(lo, bl), min(hi, bh)
    e.L = e.b - e.a + 1
    e.off = e.a - bl
    pol = C.POLARITY_OF_DIRECTION[ep.direction]
    opp = C.POLARITY_OF_DIRECTION[C.OPPOSITE_DIRECTION[ep.direction]]
    e.klass = (pol, ep.area, ep.grade)
    e.okl = (opp, ep.area, ep.grade)
    e.K = ctx.klass_curve(scheme, ep.chart, bi, e.L, e.klass)
    e.O = ctx.klass_curve(scheme, ep.chart, bi, e.L, e.okl)
    e.sched = ep.schedulable
    return e


class SchemeResult:
    """Pools of the (a) statistics for one block scheme."""

    def __init__(self) -> None:
        self.pools: Dict[str, np.ndarray] = {}
        self.n_scored = 0
        self.n_unit_eligible = 0
        self.fallback_pool: Optional[np.ndarray] = None


def applicable_mask(ctx: FamilyContext, episodes: Sequence[Episode]) -> List[bool]:
    """v1.2 K2 / v1.3 L1: "scored-applicable". The episode has at least one applicable unit (footprint gate,
    member-area filter, Moon members on day grade only) with a member whose window is at least half assessed.
    Uses only which days are assessed (NOT_ASSESSED masks), never a TRUE/FALSE state, so it is what the blind
    counting script can compute. Admission (exclusion 5), testability (D7) and the A7 minimum are decided on
    THIS count; the percentile-informative set used by the statistics is ``scorable_mask``."""
    out = []
    for ep in episodes:
        t = ctx.tl[ep.chart]
        lo, hi = ep.lo - t.h_start, ep.hi - t.h_start
        if lo < 0 or hi >= t.n_days:
            out.append(False)
            continue
        L = hi - lo + 1
        ok = False
        for v in ctx.klass_variants((C.POLARITY_OF_DIRECTION[ep.direction], ep.area, ep.grade)):
            for g in v.groups:
                for rid in g:
                    a = t.states.get(rid)
                    if a is not None and int((a[lo : hi + 1] >= 0).sum()) * 2 >= L:
                        ok = True
                        break
                if ok:
                    break
            if ok:
                break
        out.append(ok)
    return out


def scorable_mask(ctx: FamilyContext, episodes: Sequence[Episode], scheme: Optional[str] = None) -> List[bool]:
    """An episode is scored under a block scheme iff its own-polarity class score at the observed placement is
    defined there (at least one applicable unit has an informative member in the episode's block).

    The set is decided PER SCHEME (default: the family's primary, 5-year scheme). Deciding it on the
    intersection of the schemes would select episodes by their 5-year block's activity and then rank them in
    15-year blocks, where such episodes score above the shifted placements (found in the Part F calibration:
    T over 15-year blocks rejected the N0 null in 92% of studies).
    """
    scheme = scheme or ctx.schemes[0][0]
    ok = []
    for i, ep in enumerate(episodes):
        e = _place(ctx, scheme, ep, i)
        ok.append(bool(np.isfinite(e.K[e.off])))
    return ok


class _Assembly:
    """Per-block tables of one episode set under one scheme: for every valid shift, the block's contribution
    to T (BT), to the direction statistic (BD) and to the fallback statistic (BN), and per-unit sums."""

    def __init__(self) -> None:
        self.recs: List[Dict[str, Any]] = []
        self.unit_ids: List[str] = []
        self.n_obs_unit: np.ndarray = np.zeros(0, dtype=np.int64)
        self.has_dir = False
        self.has_ns = False
        self.n_scored = 0


def assemble(ctx: FamilyContext, scheme: str, episodes: Sequence[Episode], want_dir: bool, want_fallback: bool) -> _Assembly:
    """Place the (scored) episodes in the blocks of ``scheme`` and tabulate every valid shift. No random numbers."""
    asm = _Assembly()
    placed = [_place(ctx, scheme, ep, i) for i, ep in enumerate(episodes)]
    asm.n_scored = len(placed)
    if not placed:
        return asm
    by_chart: Dict[int, List[_Ep]] = {}
    for e in placed:
        by_chart.setdefault(e.chart, []).append(e)
    n_charts = len(by_chart)
    # direction set: episodes whose opposite-polarity score exists at the observed placement
    dir_by_chart: Dict[int, int] = {}
    ns_by_chart: Dict[int, int] = {}
    for c, es in by_chart.items():
        nd_ = sum(1 for e in es if np.isfinite(e.O[e.off]))
        if nd_:
            dir_by_chart[c] = nd_
        nn_ = sum(1 for e in es if e.sched is False)
        if nn_:
            ns_by_chart[c] = nn_
    for e in placed:
        e.w = 1.0 / (n_charts * len(by_chart[e.chart]))
        e.wd = 1.0 / (len(dir_by_chart) * dir_by_chart[e.chart]) if (e.chart in dir_by_chart and np.isfinite(e.O[e.off])) else 0.0
        e.wn = 1.0 / (len(ns_by_chart) * ns_by_chart[e.chart]) if (e.chart in ns_by_chart and e.sched is False) else 0.0
    asm.has_dir = bool(want_dir and dir_by_chart)
    asm.has_ns = bool(want_fallback and ns_by_chart)

    unit_ids = sorted(ctx.unit_by_id)
    upos = {u: i for i, u in enumerate(unit_ids)}
    n_obs_unit = np.zeros(len(unit_ids), dtype=np.int64)
    blocks: Dict[Tuple[int, int], List[_Ep]] = {}
    for e in placed:
        blocks.setdefault((e.chart, e.blk), []).append(e)

    for (c, bi), es in sorted(blocks.items()):
        bl, bh = ctx.blocks(scheme, c)[bi]
        smin = max(bl - e.a for e in es)
        smax = min(bh - e.b for e in es)
        W = smax - smin + 1
        mask = np.ones(W, dtype=bool)
        sl = []
        for e in es:
            k = e.K[e.off + smin : e.off + smax + 1]
            sl.append(k)
            mask &= np.isfinite(k)
            if e.wd > 0:
                mask &= np.isfinite(e.O[e.off + smin : e.off + smax + 1])
        vi = np.nonzero(mask)[0]
        i0 = int(np.nonzero(vi == -smin)[0][0])  # position of shift 0 in the valid list
        BT = np.zeros(vi.size)
        BD = np.zeros(vi.size)
        BN = np.zeros(vi.size)
        us: Dict[int, List[np.ndarray]] = {}
        for e, k in zip(es, sl):
            kv = k[vi].astype(np.float64)
            BT += e.w * kv
            if e.wd > 0:
                BD += e.wd * (kv - e.O[e.off + smin : e.off + smax + 1][vi].astype(np.float64))
            if e.wn > 0:
                BN += e.wn * kv
            for v in ctx.klass_variants(e.klass):
                uc = ctx.unit_curve(scheme, c, bi, e.L, v)
                us_slice = uc[e.off + smin : e.off + smax + 1][vi]
                p = upos[v.unit_id]
                n_obs_unit[p] += 1  # applicable episodes (v1.3 L1 item 2: applicability only, informative or not)
                fin = np.isfinite(us_slice)
                ent = us.get(p)
                if ent is None:
                    us[p] = [np.where(fin, us_slice, 0.0).astype(np.float64), fin.astype(np.float64)]
                else:
                    ent[0] += np.where(fin, us_slice, 0.0)
                    ent[1] += fin
        asm.recs.append({"chart": c, "blk": bi, "shifts": smin + vi, "i0": i0, "BT": BT, "BD": BD, "BN": BN, "us": us})
    asm.unit_ids = unit_ids
    asm.n_obs_unit = n_obs_unit
    return asm


def run_scheme(
    ctx: FamilyContext,
    scheme: str,
    episodes: Sequence[Episode],
    draws: int,
    rng: np.random.Generator,
    want_dir: bool,
    want_fallback: bool,
    z25_units: Optional[Iterable[str]] = None,
) -> SchemeResult:
    """Check (a) under one block scheme. ``episodes`` are the scored ones."""
    res = SchemeResult()
    asm = assemble(ctx, scheme, episodes, want_dir, want_fallback)
    res.n_scored = asm.n_scored
    if not asm.recs:
        return res
    nb = len(asm.recs)
    pool = draws + 1
    TP = np.zeros(pool)
    DP = np.zeros(pool) if asm.has_dir else None
    NP = np.zeros(pool) if asm.has_ns else None
    # Z25 units (v1.2 K5): those with at least 10 applicable episodes; D7 may fix the list from the K2 counts (v1.3)
    allowed = None if z25_units is None else set(z25_units)
    elig = [
        p
        for p in range(len(asm.unit_ids))
        if (asm.n_obs_unit[p] >= C.Z25_MIN_UNIT_EPISODES if allowed is None else asm.unit_ids[p] in allowed)
    ]
    epos = {p: i for i, p in enumerate(elig)}
    SS = np.zeros((len(elig), pool))
    CC = np.zeros((len(elig), pool))
    # draws are made in fixed-size chunks (DRAW_CHUNK) to bound memory; the observed placement is pool entry 0
    for c0 in range(0, draws, C.DRAW_CHUNK):
        c1 = min(draws, c0 + C.DRAW_CHUNK)
        U = rng.random((nb, c1 - c0))
        for r, rec in enumerate(asm.recs):
            V = rec["shifts"].size
            idx = np.minimum((U[r] * V).astype(np.int64), V - 1)
            TP[1 + c0 : 1 + c1] += rec["BT"][idx]
            if DP is not None:
                DP[1 + c0 : 1 + c1] += rec["BD"][idx]
            if NP is not None:
                NP[1 + c0 : 1 + c1] += rec["BN"][idx]
            for p, (s_arr, c_arr) in rec["us"].items():
                j = epos.get(p)
                if j is not None:
                    SS[j, 1 + c0 : 1 + c1] += s_arr[idx]
                    CC[j, 1 + c0 : 1 + c1] += c_arr[idx]
    for rec in asm.recs:  # the observed placement: shift 0, the same arithmetic as a draw
        i0 = rec["i0"]
        TP[0] += rec["BT"][i0]
        if DP is not None:
            DP[0] += rec["BD"][i0]
        if NP is not None:
            NP[0] += rec["BN"][i0]
        for p, (s_arr, c_arr) in rec["us"].items():
            j = epos.get(p)
            if j is not None:
                SS[j, 0] += s_arr[i0]
                CC[j, 0] += c_arr[i0]
    res.pools["T"] = TP
    if DP is not None:
        res.pools["_dir"] = DP
    if NP is not None:
        res.fallback_pool = NP
    if len(elig) >= C.Z25_MIN_UNITS:
        with np.errstate(invalid="ignore", divide="ignore"):
            score = np.where(CC > 0, SS / np.maximum(CC, 1.0), np.nan)
            mu = np.nanmean(score[:, 1:], axis=1, keepdims=True)
            sd = np.nanstd(score[:, 1:], axis=1, keepdims=True)
            z = np.where(sd > 0, (score - mu) / np.where(sd > 0, sd, 1.0), 0.0)
        z = np.where(np.isnan(z), 0.0, z)
        k = max(1, int(math.ceil(C.Z25_TOP_FRACTION * len(elig))))
        top = np.sort(z, axis=0)[-k:, :]
        res.pools["Z25"] = top.mean(axis=0)
        res.n_unit_eligible = len(elig)
    return res


# ── checks (b) and (c): donor timelines ──────────────────────────────────────
def _donor_geometry(ctx: FamilyContext, eps: Sequence[Episode], c: int, age_matched: bool):
    """Window positions of chart c's episodes on every timeline: calendar-matched (same dates) or age-matched
    (same days since birth). Returns (dlo, dhi, inside) with shapes (episodes, charts)."""
    births = np.array([t.birth for t in ctx.tl], dtype=np.int64)
    hs = np.array([t.h_start for t in ctx.tl], dtype=np.int64)
    he = np.array([t.h_end for t in ctx.tl], dtype=np.int64)
    lo = np.array([e.lo for e in eps], dtype=np.int64)
    hi = np.array([e.hi for e in eps], dtype=np.int64)
    delta = (births - births[c]) if age_matched else np.zeros(len(ctx.tl), dtype=np.int64)
    dlo = lo[:, None] + delta[None, :]
    dhi = hi[:, None] + delta[None, :]
    inside = (dlo >= hs[None, :]) & (dhi <= he[None, :])
    return dlo, dhi, inside, hs, he


def _admitted_mask(ctx: FamilyContext, admitted: Optional[Iterable[int]]) -> np.ndarray:
    m = np.zeros(len(ctx.tl), dtype=bool)
    if admitted is None:
        m[:] = True
    else:
        m[list(admitted)] = True
    return m


def donor_eligibility_counts(ctx: FamilyContext, episodes: Sequence[Episode], admitted: Optional[Iterable[int]] = None) -> Dict[str, int]:
    """v1.2 K11 / K2: how many charts have at least MIN_ELIGIBLE_DONORS eligible donors for check (b) and for check
    (c). A donor is eligible when it is an admitted chart of the family whose horizon covers all of the chart's
    episode windows (calendar dates for (b), the same ages for (c)). Horizons only: no state, no statistic."""
    adm = _admitted_mask(ctx, admitted)
    by_chart: Dict[int, List[Episode]] = {}
    for ep in episodes:
        by_chart.setdefault(ep.chart, []).append(ep)
    out = {"b": 0, "c": 0}
    for c, eps in by_chart.items():
        if not adm[c]:
            continue
        for key, age in (("b", False), ("c", True)):
            _lo, _hi, inside, _hs, _he = _donor_geometry(ctx, eps, c, age)
            ok = inside.all(axis=0) & adm
            ok[c] = False
            if int(ok.sum()) >= C.MIN_ELIGIBLE_DONORS:
                out[key] += 1
    return out


def direction_counts(ctx: FamilyContext, episodes: Sequence[Episode]) -> Dict[str, int]:
    """v1.2 K4: episodes with at least one applicable opposite-polarity unit, and the charts they sit in."""
    n = 0
    charts = set()
    for ep in episodes:
        okl = (C.POLARITY_OF_DIRECTION[C.OPPOSITE_DIRECTION[ep.direction]], ep.area, ep.grade)
        if ctx.klass_variants(okl):
            n += 1
            charts.add(ep.chart)
    return {"episodes": n, "charts": len(charts), "testable": bool(n >= C.DIR_MIN_EPISODES and len(charts) >= C.DIR_MIN_CHARTS)}


def run_donor_check(
    ctx: FamilyContext,
    episodes: Sequence[Episode],
    draws: int,
    rng: np.random.Generator,
    age_matched: bool,
    admitted: Optional[Iterable[int]] = None,
) -> Dict[str, Any]:
    """T2 (calendar-matched, ``age_matched`` False) or T3 (age-matched, True), its pool and p.

    Episode coverage on a timeline = weighted share of assessed class-days that are TRUE in the window. T =
    mean over included charts of mean over its episodes of (coverage on the drawn timeline - mean coverage over
    the chart's eligible donors, own chart excluded). Observed: the chart's own timeline. Donors are the
    ADMITTED charts of the family only (v1.2 K6).

    EPISODE SET. ``episodes`` are ALL episodes of the family with an applicable unit; an episode counts for a
    chart if its coverage is defined on the chart's own timeline (at least half the weighted class-days
    assessed). The check-(a) rule "drop a member that is identical in every window of the block" is a
    percentile device and is NOT applied here: it conditions on the own timeline being active in the episode's
    block, and a coverage statistic computed on episodes selected that way is higher on the own timeline than on
    any donor's at the same dates (found in the Part F calibration, where it made p2 and p3 about 0.001 under
    every null model).
    """
    nch = len(ctx.tl)
    adm = _admitted_mask(ctx, admitted)
    by_chart: Dict[int, List[int]] = {}
    for i, ep in enumerate(episodes):
        if adm[ep.chart]:
            by_chart.setdefault(ep.chart, []).append(i)
    included: List[int] = []
    excluded: List[int] = []
    V: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}  # chart -> (donor ids incl. self first, values)
    for c, ids in sorted(by_chart.items()):
        eps = [episodes[i] for i in ids]
        dlo, dhi, inside, hs, he = _donor_geometry(ctx, eps, c, age_matched)
        M = np.full((len(eps), nch), np.nan)
        for j, e in enumerate(eps):
            klass = (C.POLARITY_OF_DIRECTION[e.direction], e.area, e.grade)
            CT, CA, W = ctx.klass_prefix(klass)
            if W <= 0:
                continue
            # prefix index of a date inside donor d's horizon: flat_off[d] + (date - h_start[d])
            k0 = np.clip(dlo[j] - hs, 0, he - hs + 1)
            k1 = np.clip(dhi[j] + 1 - hs, 0, he - hs + 1)
            num = CT[ctx.flat_off[:-1] + k1] - CT[ctx.flat_off[:-1] + k0]
            den = CA[ctx.flat_off[:-1] + k1] - CA[ctx.flat_off[:-1] + k0]
            L = e.hi - e.lo + 1
            okc = inside[j] & (den * 2.0 >= W * L) & (den > 0)
            M[j, okc] = num[okc] / den[okc]
        keep = np.isfinite(M[:, c])  # defined on the own timeline
        if not keep.any():
            continue
        M, inside = M[keep], inside[keep]
        elig_mask = inside.all(axis=0) & adm
        elig_mask[c] = False
        elig = np.nonzero(elig_mask)[0]
        if elig.size < C.MIN_ELIGIBLE_DONORS:
            excluded.append(c)
            continue
        m_e = np.nanmean(M[:, elig], axis=1)
        dev = np.where(np.isnan(M), 0.0, M - m_e[:, None])  # a donor with the window not assessed contributes no deviation
        choices = np.concatenate([[c], elig])  # first entry = self = observed
        V[c] = (choices, dev[:, choices].mean(axis=0))
        included.append(c)
    out: Dict[str, Any] = {"included_charts": included, "excluded_charts": excluded}
    if not included:
        out.update(T=None, p=None, pool=None)
        return out
    pool = np.zeros((draws + 1,))
    for c in included:
        choices, vals = V[c]
        k = np.empty(draws + 1, dtype=np.int64)
        k[0] = 0
        k[1:] = np.minimum((rng.random(draws) * choices.size).astype(np.int64), choices.size - 1)
        pool += vals[k]
    pool /= len(included)
    out.update(T=float(pool[0]), p=pool_p(pool), pool=pool)
    return out


# ── one family, end to end ────────────────────────────────────────────────────
FAMILY_STREAM = {C.FAMILY_DASHA: 1, C.FAMILY_TRANSIT: 2}


def score_family(
    ctx: FamilyContext,
    episodes: Sequence[Episode],
    cfg: C.ScoreConfig,
    admitted: Optional[Iterable[int]] = None,
    d7: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """All statistics and p-values of one family for one episode set. Pure given (ctx, episodes, cfg)."""
    for ep in episodes:
        ep.validate()
        if not 0 <= ep.chart < len(ctx.tl):
            raise ScorerError("episode refers to a chart outside the family")
    mask = scorable_mask(ctx, episodes)  # primary scheme
    scored = [e for e, ok in zip(episodes, mask) if ok]
    out: Dict[str, Any] = {
        "family": ctx.family,
        "episodes_given": len(episodes),
        "episodes_scored": len(scored),
        "episodes_unscorable": len(episodes) - len(scored),
        "charts_scored": len({e.chart for e in scored}),
        "draws": cfg.draws,
    }
    if not scored:
        out.update(status="no_scored_episodes", p1=None, p2=None, p3=None, p_dir=None)
        return out
    stream = FAMILY_STREAM[ctx.family]
    dircount = direction_counts(ctx, scored)  # v1.2 K4: decided from counts, before any p-value
    z25_units = None
    if d7 is not None:  # v1.3: the D7 decisions made from the sealed count_blind aggregates override the recount
        if "dir_testable" in d7:
            dircount = dict(dircount, testable=bool(d7["dir_testable"]))
        z25_units = d7.get("z25_units")
    out["dir_testable"] = dircount["testable"]
    out["dir_episodes"] = dircount["episodes"]
    out["dir_charts"] = dircount["charts"]
    pools: Dict[str, np.ndarray] = {}
    primary: Optional[SchemeResult] = None
    for si, (scheme, _bd, _mb) in enumerate(ctx.schemes):
        rng = np.random.default_rng([cfg.seed, stream, si])
        sc = scored if si == 0 else [e for e, ok in zip(episodes, scorable_mask(ctx, episodes, scheme)) if ok]
        if not sc:
            continue
        res = run_scheme(ctx, scheme, sc, cfg.draws, rng, want_dir=(si == 0 and dircount["testable"]), want_fallback=(si == 0 and cfg.fallback_primary_set), z25_units=z25_units)
        if si == 0:
            primary = res
        pools["T-" + scheme] = res.pools["T"]
        if "Z25" in res.pools:
            pools["Z25-" + scheme] = res.pools["Z25"]
    p1, per = min_p_adjusted(pools)
    out.update(
        status="scored",
        stats={k: float(v[0]) for k, v in sorted(pools.items())},
        null_mean={k: float(v[1:].mean()) for k, v in sorted(pools.items())},
        p_stat=per,
        p1=p1,
        T=float(pools["T-" + ctx.schemes[0][0]][0]),
        z25_units=primary.n_unit_eligible if primary else 0,
    )
    assert primary is not None
    dpool = primary.pools.get("_dir")
    out["T_dir"] = float(dpool[0]) if dpool is not None else None
    out["p_dir"] = pool_p(dpool) if dpool is not None else None
    if cfg.fallback_primary_set:
        npool = primary.fallback_pool
        out["T_nonschedulable"] = float(npool[0]) if npool is not None else None
        out["nonschedulable_above_null_mean"] = bool(npool is not None and npool[0] > npool[1:].mean())
    adm = None if admitted is None else list(admitted)
    rb = run_donor_check(ctx, list(episodes), cfg.draws, np.random.default_rng([cfg.seed, stream, 90]), age_matched=False, admitted=adm)
    rc = run_donor_check(ctx, list(episodes), cfg.draws, np.random.default_rng([cfg.seed, stream, 91]), age_matched=True, admitted=adm)
    out.update(
        T2=rb["T"], p2=rb["p"], b_charts=len(rb["included_charts"]), b_excluded=len(rb["excluded_charts"]),
        T3=rc["T"], p3=rc["p"], c_charts=len(rc["included_charts"]), c_excluded=len(rc["excluded_charts"]),
        donor_floor_ok=bool(len(rb["included_charts"]) >= C.DONOR_FLOOR_CHARTS and len(rc["included_charts"]) >= C.DONOR_FLOOR_CHARTS),
        b_excluded_codes=[ctx.tl[i].code for i in rb["excluded_charts"]],
        c_excluded_codes=[ctx.tl[i].code for i in rc["excluded_charts"]],
    )
    return out
