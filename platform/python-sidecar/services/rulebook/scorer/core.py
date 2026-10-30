"""Rule Book scorer - the statistics: percentile scores, check (a), checks (b) and (c), direction check.

Conventions fixed here, each tied to a clause of the yardstick (v1.0 as amended by v1.1 to v1.5):

* Episode score (v1.0 3.2, v1.1 C3). For a member: coverage of the window = share of ASSESSED days
  that are TRUE (a window with fewer than half its days assessed is not scored). Its percentile is the
  mid-rank of that coverage among the coverages of all scorable windows of the same length lying wholly
  inside the same block (no wrap; a window clipped at a block edge is ranked against windows of the
  clipped length). A member whose coverage is identical in every such window is dropped for the
  episode. Unit score = mean over its readings' percentiles (SUR-RB-39: a reading applies when a member is at least
  half assessed; masks only); episode score = mean of its units'.
* T = mean over charts of (mean over that chart's episodes of the episode score).
* Check (a) (v1.1 D1): per chart and block, ONE shift drawn uniformly among the integers that keep every
  episode window of the block inside the block (and, added here for NOT_ASSESSED, on which every episode
  of the block is still scorable). 5-year blocks; F-D also 15-year blocks, each scheme in its OWN draws (v1.4 M1).
* Z25 (v1.1 D2): the mean of the top quartile of unit z-scores among units with at least 10 applicable
  episodes; a unit's score is the mean percentile over its applicable episodes (pooled over charts); z is
  standardised by the mean and sd of that score across the draws.
* p1 of a family: within each scheme, single-step min-p over that scheme's statistics in its draws (K5); F-T has one
  scheme; F-D combines its two schemes by Simes, min(1, 2 min, max) (v1.4 M1; Bonferroni is the logged fallback).
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


def reading_coverage(arrays: Sequence[Optional[np.ndarray]], starts: np.ndarray, L: int) -> np.ndarray:
    """Window coverage of one reading (a member, or an OR reading of several members) for windows
    [s, s + L - 1], s in ``starts`` (SUR-RB-39 (1)):

    * a member PASSES a window when it is at least half assessed there (masks only, K2/L1); with no member passing,
      the reading does not apply and the coverage is NaN;
    * the window's day set is the union of the passing members' assessed days; a day is TRUE when any passing
      member assessed that day is TRUE (a NOT_ASSESSED member adds nothing: TRUE/N reads TRUE, FALSE/N reads FALSE);
    * coverage = TRUE days / days in that set (rounded to 1e-10 so equal rationals tie exactly).

    ``arrays`` are int8 member states (1, 0, -1), None for a member with no states."""
    k = len(arrays)
    n_out = starts.size
    cov = np.full(n_out, np.nan)
    if n_out == 0 or k == 0:
        return cov
    arrs = [a for a in arrays]
    As, Ts = [], []
    for a in arrs:
        if a is None:
            As.append(None)
            Ts.append(None)
        else:
            As.append(np.concatenate([[0], np.cumsum(a >= 0, dtype=np.int64)]))
            Ts.append(np.concatenate([[0], np.cumsum(a == 1, dtype=np.int64)]))
    code = np.zeros(n_out, dtype=np.int64)
    for i, A in enumerate(As):
        if A is None:
            continue
        code |= ((A[starts + L] - A[starts]) * 2 >= L).astype(np.int64) << i
    for c in np.unique(code):
        if c == 0:
            continue
        sel = code == c
        members = [i for i in range(k) if (c >> i) & 1]
        s0 = starts[sel]
        if len(members) == 1:
            i = members[0]
            num, den = Ts[i][s0 + L] - Ts[i][s0], As[i][s0 + L] - As[i][s0]
        else:
            au = np.zeros(arrs[members[0]].size, dtype=bool)
            tu = np.zeros_like(au)
            for i in members:
                au |= arrs[i] >= 0
                tu |= arrs[i] == 1
            AU = np.concatenate([[0], np.cumsum(au, dtype=np.int64)])
            TU = np.concatenate([[0], np.cumsum(tu, dtype=np.int64)])
            num, den = TU[s0 + L] - TU[s0], AU[s0 + L] - AU[s0]
        cov[sel] = np.round(num / den, 10)
    return cov


def constant_coverage(cov: np.ndarray) -> bool:
    """CARVE-OUT 3 (SUR-RB-36; v1.0 3.2 step 3): True when every applicable window of the block has the same
    coverage (or none applies): the component carries no information there and is dropped. It depends on the
    block's state pattern only, never on where an episode falls."""
    c = cov[np.isfinite(cov)]
    return bool(c.size == 0 or c.min() == c.max())


def percentile_from_coverage(cov: np.ndarray) -> np.ndarray:
    """Mid-rank percentile of each applicable window's coverage among all applicable windows of the block; NaN for
    windows where the component does not apply, and everywhere when the component is constant in the block."""
    out = np.full(cov.size, np.nan, dtype=np.float32)
    if constant_coverage(cov):
        return out
    ok = np.isfinite(cov)
    c = cov[ok]
    srt = np.sort(c)
    lo = np.searchsorted(srt, c, side="left")
    hi = np.searchsorted(srt, c, side="right")
    out[ok] = ((lo + hi) / (2.0 * c.size)).astype(np.float32)
    return out


def percentile_curve(T: np.ndarray, A: np.ndarray, bl: int, bh: int, L: int) -> np.ndarray:
    """Single-member form on prefix sums (kept for the primitive tests): the member passes a window when at least
    half assessed; percentile as ``percentile_from_coverage``."""
    nst = bh - bl - L + 2
    if nst <= 0:
        return np.zeros(0, dtype=np.float32)
    s = np.arange(bl, bl + nst)
    num = T[s + L] - T[s]
    den = A[s + L] - A[s]
    ok = den * 2 >= L
    cov = np.full(nst, np.nan)
    cov[ok] = np.round(num[ok] / den[ok], 10)
    return percentile_from_coverage(cov)


TIE_TOL = 1e-12  # review M3: statistics equal within this are ties (and ties count against the observed)


def pool_p(pool: np.ndarray) -> float:
    """p of the observed value (index 0) among the pool: (1 + #{draws >= observed}) / (n_draws + 1)."""
    return float((np.count_nonzero(pool[1:] >= pool[0] - TIE_TOL) + 1) / pool.size)


def pool_p_all(pool: np.ndarray) -> np.ndarray:
    """p of every pool element: #{pool >= value - TIE_TOL} / pool.size (the observed is one of the pool)."""
    srt = np.sort(pool)
    return (pool.size - np.searchsorted(srt, pool - TIE_TOL, side="left")) / float(pool.size)


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
    return float(np.count_nonzero(minp <= minp[0] + TIE_TOL) / size), per


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
        self._ucurve: Dict[Tuple[Any, ...], np.ndarray] = {}
        self._kcurve: Dict[Tuple[Any, ...], np.ndarray] = {}
        self._kvars: Dict[Klass, List[Variant]] = {}
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
        """Float states of a member (1, 0, NaN). Statistics only (the planted-effect simulator, descriptive hits)."""
        t = self.tl[chart]
        a = t.values(rid)
        if a is None:
            return np.full(t.n_days, np.nan)
        v = a.astype(np.float64)
        v[a < 0] = np.nan
        return v

    def _reading_arrays(self, chart: int, comp: CompKey) -> List[Optional[np.ndarray]]:
        """The member state arrays of a component (carve-outs 1 and 3: statistics and the constant-member rule)."""
        t = self.tl[chart]
        rids = (comp[1],) if comp[0] == "m" else tuple(comp[1])
        out: List[Optional[np.ndarray]] = []
        for r in rids:  # a plain loop: the state read is attributed to this function on every Python version
            out.append(t.values(r))
        return out

    def comp_prefix(self, chart: int, comp: CompKey) -> Tuple[np.ndarray, np.ndarray]:
        """Prefix sums (length n+1) of TRUE and of assessed days of a single member (descriptive hits)."""
        a = self.tl[chart].values(comp[1])
        n = self.tl[chart].n_days
        if a is None:
            return np.zeros(n + 1, dtype=np.int64), np.zeros(n + 1, dtype=np.int64)
        return np.concatenate([[0], np.cumsum(a == 1, dtype=np.int64)]), np.concatenate([[0], np.cumsum(a >= 0, dtype=np.int64)])

    # curves -----------------------------------------------------------------
    def comp_coverage(self, scheme: str, chart: int, blk: int, L: int, comp: CompKey) -> np.ndarray:
        """Coverage of every window of length L wholly inside the block (``reading_coverage``)."""
        bl, bh = self.blocks(scheme, chart)[blk]
        nst = bh - bl - L + 2
        if nst <= 0:
            return np.zeros(0)
        return reading_coverage(self._reading_arrays(chart, comp), np.arange(bl, bl + nst), L)

    def comp_curve(self, scheme: str, chart: int, blk: int, L: int, comp: CompKey) -> np.ndarray:
        """Percentile curve of one component in one block (not cached: unit curves are, and they dominate memory)."""
        return percentile_from_coverage(self.comp_coverage(scheme, chart, blk, L, comp))

    def unit_curve(self, scheme: str, chart: int, blk: int, L: int, var: Variant) -> np.ndarray:
        """Unit percentile = mean over the readings that apply in the window (R units: the members that pass)."""
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

    def member_assessed_flat(self, rid: str) -> Optional[np.ndarray]:
        """Flat prefix counts of member ``rid``'s ASSESSED days, all charts (chart c from ``flat_off[c]``); None when
        the member is assessed on every day of every chart (every window then fully assessed). Masks only."""
        if not hasattr(self, "_mflat"):
            self._mflat: Dict[str, Optional[np.ndarray]] = {}
        if rid not in self._mflat:
            parts = []
            any_na = False
            for t in self.tl:
                a = t.assessed(rid)
                if a is None:
                    a = np.zeros(t.n_days, dtype=bool)
                any_na |= not bool(a.all())
                parts.append(np.concatenate([[0], np.cumsum(a, dtype=np.int32)]))
            self._mflat[rid] = np.concatenate(parts).astype(np.int32) if any_na else None
        return self._mflat[rid]

    def _reading_flat(self, rids: Tuple[str, ...]) -> Tuple[np.ndarray, np.ndarray]:
        """Flat prefix counts (TRUE, assessed) of the union of ``rids``, all charts: the reading's day set when every
        listed member passes (checks (b) and (c), statistics: carve-out 1)."""
        if not hasattr(self, "_rflat"):
            self._rflat: Dict[Tuple[str, ...], Tuple[np.ndarray, np.ndarray]] = {}
        if rids not in self._rflat:
            pt, pa = [], []
            for ci, t in enumerate(self.tl):
                arrs = self._reading_arrays(ci, ("or", rids))
                au = np.zeros(t.n_days, dtype=bool)
                tu = np.zeros(t.n_days, dtype=bool)
                for a in arrs:
                    if a is not None:
                        au |= a >= 0
                        tu |= a == 1
                pt.append(np.concatenate([[0], np.cumsum(tu, dtype=np.int32)]))
                pa.append(np.concatenate([[0], np.cumsum(au, dtype=np.int32)]))
            self._rflat[rids] = (np.concatenate(pt), np.concatenate(pa))
        return self._rflat[rids]

    def episode_coverage(self, units: Sequence[Variant], lo: np.ndarray, hi: np.ndarray, charts: np.ndarray) -> np.ndarray:
        """Mean over the units of ``unit_coverages`` (NaN where a unit does not apply)."""
        return self.unit_coverages(units, lo, hi, charts).mean(axis=0)

    def block_base_rate(self, chart: int, var: Variant, L: int, mid: int) -> float:
        """v1.5 P2 imputation: the unit's mean coverage over all windows of length L lying wholly inside the 5-year
        block of ``chart``'s own timeline that contains day ``mid`` (date ordinal), over the windows where the unit
        applies (SUR-RB-39 rule). From that timeline alone; cached."""
        if not hasattr(self, "_base"):
            self._base: Dict[Tuple[Any, ...], float] = {}
        t = self.tl[chart]
        rel = min(max(mid - t.h_start, 0), t.n_days - 1)
        scheme = self.schemes[0][0]
        blk = next(i for i, (bl, bh) in enumerate(self.blocks(scheme, chart)) if bl <= rel <= bh)
        k = (chart, blk, L, var.key)
        if k not in self._base:
            rc = [self.comp_coverage(scheme, chart, blk, L, comp) for comp in var.components()]
            st = np.vstack(rc)
            ok = np.isfinite(st)
            ucov = np.where(ok.any(axis=0), np.where(ok, st, 0.0).sum(axis=0) / np.maximum(ok.sum(axis=0), 1), np.nan)
            f = ucov[np.isfinite(ucov)]
            self._base[k] = float(f.mean()) if f.size else float("nan")
        return self._base[k]

    def unit_coverages(self, units: Sequence[Variant], lo: np.ndarray, hi: np.ndarray, charts: np.ndarray) -> np.ndarray:
        """Coverage of one episode's unit set on several timelines (checks (b) and (c), SUR-RB-39 (2)): for timeline
        ``charts[i]`` and window [lo[i], hi[i]] (date ordinals inside its horizon): unit coverage = mean over its
        readings that apply (``reading_coverage`` rule); episode coverage = mean over the units. NaN where a unit
        does not apply (the caller only passes eligible timelines)."""
        L = int(hi[0] - lo[0] + 1)
        hs = np.array([self.tl[c].h_start for c in charts], dtype=np.int64)
        k0 = lo - hs
        k1 = hi + 1 - hs
        off = self.flat_off[:-1][charts]
        unit_cov = []
        for v in units:
            rc = []
            for reading in v.readings():
                passing = np.zeros((len(reading), charts.size), dtype=bool)
                for j, rid in enumerate(reading):
                    fa = self.member_assessed_flat(rid)
                    passing[j] = True if fa is None else ((fa[off + k1] - fa[off + k0]) * 2 >= L)
                cov = np.full(charts.size, np.nan)
                allp = passing.all(axis=0)
                if allp.any():
                    FT, FA = self._reading_flat(tuple(reading))
                    num = FT[off + k1] - FT[off + k0]
                    den = FA[off + k1] - FA[off + k0]
                    cov[allp] = np.round(num[allp] / den[allp], 10)
                some = passing.any(axis=0) & ~allp
                for i in np.nonzero(some)[0]:  # only some members pass: the union of those that do
                    sub = tuple(r for r, p in zip(reading, passing[:, i]) if p)
                    t_arr = self._reading_arrays(int(charts[i]), ("or", sub))
                    cov[i] = reading_coverage(t_arr, np.array([k0[i]]), L)[0]
                rc.append(cov)
            st = np.vstack(rc)
            ok = np.isfinite(st)
            unit_cov.append(np.where(ok.any(axis=0), np.where(ok, st, 0.0).sum(axis=0) / np.maximum(ok.sum(axis=0), 1), np.nan))
        return np.vstack(unit_cov)


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
    __slots__ = ("idx", "chart", "klass", "okl", "blk", "a", "b", "L", "off", "K", "O", "w", "wd", "dir_ok")

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
    return e


class SchemeResult:
    """Pools of the (a) statistics for one block scheme."""

    def __init__(self) -> None:
        self.pools: Dict[str, np.ndarray] = {}
        self.n_scored = 0
        self.n_unit_eligible = 0


def _unit_applies(t: ChartTimeline, v: Variant, lo: int, hi: int) -> bool:
    """At least one applicable member of the variant has its window [lo, hi] (indices from h_start) at least half
    assessed. Assessed masks only (v1.2 K2, v1.3 L1, v1.4 M3)."""
    L = hi - lo + 1
    for g in v.groups:
        for rid in g:
            n = t.assessed_count(rid, lo, hi)
            if n is not None and n * 2 >= L:
                return True
    return False


def _polarity_applicable(ctx: FamilyContext, ep: Episode, polarity: str) -> List[Variant]:
    t = ctx.tl[ep.chart]
    lo, hi = ep.lo - t.h_start, ep.hi - t.h_start
    if lo < 0 or hi >= t.n_days:
        return []
    return [v for v in ctx.klass_variants((polarity, ep.area, ep.grade)) if _unit_applies(t, v, lo, hi)]


def applicable_mask(ctx: FamilyContext, episodes: Sequence[Episode]) -> List[bool]:
    """v1.2 K2 / v1.3 L1: "scored-applicable". The episode has at least one applicable unit (footprint gate,
    member-area filter, Moon members on day grade only) with a member whose (clipped) window is at least half
    assessed. Assessed masks only, never a TRUE/FALSE state: what the blind counting script computes. Admission
    (exclusion 5), testability (D7) and the A7 minimum are decided on THIS count; the percentile-informative set
    used by the statistics is ``scorable_mask`` (carve-out 3)."""
    return [bool(_polarity_applicable(ctx, ep, C.POLARITY_OF_DIRECTION[ep.direction])) for ep in episodes]


def opposite_applicable_mask(ctx: FamilyContext, episodes: Sequence[Episode]) -> List[bool]:
    """v1.3 L1 item 1: the episode also has an applicable opposite-polarity unit (same applicability rules)."""
    return [bool(_polarity_applicable(ctx, ep, C.POLARITY_OF_DIRECTION[C.OPPOSITE_DIRECTION[ep.direction]])) for ep in episodes]


def unit_applicable_counts(ctx: FamilyContext, episodes: Sequence[Episode]) -> Dict[str, int]:
    """v1.3 L1 item 2: per unit, the number of scored-applicable episodes it applies to (an applicable member whose
    window is at least half assessed). Assessed masks only."""
    out: Dict[str, int] = {u.unit_id: 0 for u in ctx.units}
    for ep in episodes:
        for v in _polarity_applicable(ctx, ep, C.POLARITY_OF_DIRECTION[ep.direction]):
            out[v.unit_id] += 1
    return out


def d7_from_counts(ctx: FamilyContext, episodes: Sequence[Episode]) -> Dict[str, Any]:
    """The D7 decisions the scorer needs, from applicability counts only (what count_blind emits, v1.2 K2 / v1.3):
    p_dir testability (K4) and the Z25 unit set (K5). Used when no sealed counts are supplied."""
    app = [e for e, ok in zip(episodes, applicable_mask(ctx, episodes)) if ok]
    uc = unit_applicable_counts(ctx, app)
    return {
        "dir_testable": direction_counts(ctx, app)["testable"],
        "z25_units": sorted(u for u, n in uc.items() if n >= C.Z25_MIN_UNIT_EPISODES),
    }


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
    to T (BT), to the direction statistic (BD), and per-unit sums."""

    def __init__(self) -> None:
        self.recs: List[Dict[str, Any]] = []
        self.unit_ids: List[str] = []
        self.n_obs_unit: np.ndarray = np.zeros(0, dtype=np.int64)
        self.has_dir = False
        self.n_scored = 0


def assemble(
    ctx: FamilyContext,
    scheme: str,
    episodes: Sequence[Episode],
    want_dir: bool,
    dir_eligible: Optional[Sequence[bool]] = None,
) -> _Assembly:
    """Place the (scored) episodes in the blocks of ``scheme`` and tabulate every valid shift. No random numbers:
    every eligibility decision of check (a) is made here, once, before any draw (SUR-RB-36 (ii)).

    ``dir_eligible``: per episode, whether it has an applicable opposite-polarity unit (v1.2 K4 / v1.3 L1; the
    direction set). The direction statistic uses those episodes whose opposite-polarity score is defined at the
    observed placement (v1.0 3.2 step 5); the opposite-polarity mask narrows the shift set only when the direction
    statistic is computed (review M1)."""
    asm = _Assembly()
    placed = [_place(ctx, scheme, ep, i) for i, ep in enumerate(episodes)]
    if dir_eligible is None:
        dir_eligible = [True] * len(placed)
    asm.n_scored = len(placed)
    if not placed:
        return asm
    by_chart: Dict[int, List[_Ep]] = {}
    for e in placed:
        by_chart.setdefault(e.chart, []).append(e)
    n_charts = len(by_chart)
    # direction set: episodes whose opposite-polarity score exists at the observed placement
    dir_by_chart: Dict[int, int] = {}
    for e in placed:
        e.dir_ok = bool(want_dir and dir_eligible[e.idx] and np.isfinite(e.O[e.off]))
    for c, es in by_chart.items():
        nd_ = sum(1 for e in es if e.dir_ok)
        if nd_:
            dir_by_chart[c] = nd_
    for e in placed:
        e.w = 1.0 / (n_charts * len(by_chart[e.chart]))
        e.wd = 1.0 / (len(dir_by_chart) * dir_by_chart[e.chart]) if (e.chart in dir_by_chart and e.dir_ok) else 0.0
    asm.has_dir = bool(want_dir and dir_by_chart)

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
        us: Dict[int, List[np.ndarray]] = {}
        for e, k in zip(es, sl):
            kv = k[vi].astype(np.float64)
            BT += e.w * kv
            if e.wd > 0:
                BD += e.wd * (kv - e.O[e.off + smin : e.off + smax + 1][vi].astype(np.float64))
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
        asm.recs.append({"chart": c, "blk": bi, "shifts": smin + vi, "i0": i0, "BT": BT, "BD": BD, "us": us})
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
    z25_units: Optional[Iterable[str]] = None,
    dir_eligible: Optional[Sequence[bool]] = None,
) -> SchemeResult:
    """Check (a) under one block scheme. ``episodes`` are the scored ones."""
    res = SchemeResult()
    asm = assemble(ctx, scheme, episodes, want_dir, dir_eligible)
    res.n_scored = asm.n_scored
    if not asm.recs:
        return res
    nb = len(asm.recs)
    pool = draws + 1
    TP = np.zeros(pool)
    DP = np.zeros(pool) if asm.has_dir else None
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
        for p, (s_arr, c_arr) in rec["us"].items():
            j = epos.get(p)
            if j is not None:
                SS[j, 0] += s_arr[i0]
                CC[j, 0] += c_arr[i0]
    res.pools["T"] = TP
    if DP is not None:
        res.pools["_dir"] = DP
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


DONOR_RULES = {"m3": None, "p2_90": 0.90, "p2_95": 0.95}  # v1.4 M3; v1.5 P2 at the 90% bar and its 95% escalation


def donor_sets(
    ctx: FamilyContext,
    episodes: Sequence[Episode],
    age_matched: bool,
    admitted: Optional[Iterable[int]] = None,
    rule: str = "m3",
) -> Dict[int, Dict[str, Any]]:
    """Checks (b)/(c) eligibility, computed ONCE before any draw (SUR-RB-36 (ii)), from horizons and assessed masks
    only:
    * a chart's check set = its scored-applicable episodes (K2), each with the units that apply to it on the chart's
      own timeline (its (episode, unit) cells);
    * ``rule == "m3"`` (v1.4 M3): a donor is eligible if it is an admitted chart of the family (K6), its horizon covers
      every episode window (same dates for (b), same ages for (c)), and EVERY cell is defined on it (the unit has at
      least one member at least half assessed in the donor's window);
    * ``rule == "p2_90"`` / ``"p2_95"`` (v1.5 P2): the same horizon condition, and at least 90% (95%) of the cells
      defined; undefined cells are imputed later (``block_base_rate``).
    Returns chart -> {"eps", "units", "elig", "defined" (per episode: units x charts bool), "dlo", "dhi", "inside"}."""
    if rule not in DONOR_RULES:
        raise ScorerError(f"unknown donor rule {rule!r}")
    bar = DONOR_RULES[rule]
    adm = _admitted_mask(ctx, admitted)
    hs = np.array([t.h_start for t in ctx.tl], dtype=np.int64)
    he = np.array([t.h_end for t in ctx.tl], dtype=np.int64)
    by_chart: Dict[int, List[int]] = {}
    for i, ep in enumerate(episodes):
        if adm[ep.chart]:
            by_chart.setdefault(ep.chart, []).append(i)
    out: Dict[int, Dict[str, Any]] = {}
    for c, ids in sorted(by_chart.items()):
        units_of: List[List[Variant]] = []
        keep: List[int] = []
        for i in ids:
            vs = _polarity_applicable(ctx, episodes[i], C.POLARITY_OF_DIRECTION[episodes[i].direction])
            if vs:
                keep.append(i)
                units_of.append(vs)
        if not keep:
            continue
        eps = [episodes[i] for i in keep]
        dlo, dhi, inside, _hs, _he = _donor_geometry(ctx, eps, c, age_matched)
        horizon_ok = inside.all(axis=0) & adm
        k0 = np.clip(dlo - hs[None, :], 0, (he - hs + 1)[None, :])
        k1 = np.clip(dhi + 1 - hs[None, :], 0, (he - hs + 1)[None, :])
        off = ctx.flat_off[:-1][None, :]
        defined: List[np.ndarray] = []
        n_cells = 0
        n_def = np.zeros(len(ctx.tl), dtype=np.int64)
        for j, vs in enumerate(units_of):
            L = eps[j].hi - eps[j].lo + 1
            dm = np.zeros((len(vs), len(ctx.tl)), dtype=bool)
            for ui, v in enumerate(vs):
                unit_ok = np.zeros(len(ctx.tl), dtype=bool)
                for g in v.groups:
                    for rid in g:
                        fa = ctx.member_assessed_flat(rid)
                        if fa is None:
                            unit_ok[:] = True
                            break
                        n = fa[off[0] + k1[j]] - fa[off[0] + k0[j]]
                        unit_ok |= n * 2 >= L
                    if unit_ok.all():
                        break
                dm[ui] = unit_ok
            defined.append(dm)
            n_cells += len(vs)
            n_def += dm.sum(axis=0)
        if bar is None:
            ok = horizon_ok & (n_def == n_cells)
        else:
            ok = horizon_ok & (n_def >= bar * n_cells - 1e-9)
        ok[c] = False
        out[c] = {"eps": keep, "units": units_of, "elig": np.nonzero(ok)[0], "defined": defined, "dlo": dlo, "dhi": dhi, "inside": inside, "cells": n_cells}
    return out


def donor_eligibility_counts(ctx: FamilyContext, episodes: Sequence[Episode], admitted: Optional[Iterable[int]] = None, rules: Optional[Mapping[str, str]] = None) -> Dict[str, int]:
    """v1.2 K11: charts with at least MIN_ELIGIBLE_DONORS eligible donors for check (b) and for (c), under each
    check's donor rule (v1.4 M3 unless v1.5 P2 is active for it)."""
    rules = rules or {}
    out = {"b": 0, "c": 0}
    for key, age in (("b", False), ("c", True)):
        for c, d in donor_sets(ctx, episodes, age, admitted, rules.get(key, "m3")).items():
            if d["elig"].size >= C.MIN_ELIGIBLE_DONORS:
                out[key] += 1
    return out


def donor_recount(ctx: FamilyContext, episodes: Sequence[Episode], admitted: Optional[Iterable[int]] = None) -> Dict[str, Any]:
    """The scorer's own recount of count_blind V3's donor outputs (masks only), for the pre-claim equality check:
    per pool chart (by code) own_cells, donors_{b,c}_m3, donors_{b,c}_p2, imputed_cells_{b,c}_p2, donors_{b,c}_p95,
    imputed_cells_{b,c}_p95; per check pool_charts, charts_ge5_donors_{m3,p2,p95}, k11_floor_met_{m3,p2,p95},
    imputed_cell_share_{p2,p95} (6 decimals; '' when the rule has no donor cell, never '0.000000')."""
    adm = _admitted_mask(ctx, admitted)
    pool = [c for c in range(len(ctx.tl)) if adm[c]]
    rows: Dict[str, Dict[str, int]] = {}
    agg = {k: [0, 0, 0, 0, 0, 0, 0] for k in ("b", "c")}  # >=5 m3, >=5 p2, imputed p2, p2 cells, >=5 p95, imputed p95, p95 cells
    zero = ("own_cells", "donors_b_m3", "donors_c_m3", "donors_b_p2", "donors_c_p2", "imputed_cells_b_p2", "imputed_cells_c_p2",
            "donors_b_p95", "donors_c_p95", "imputed_cells_b_p95", "imputed_cells_c_p95")
    for key, age in (("b", False), ("c", True)):
        m3 = donor_sets(ctx, episodes, age, admitted, "m3")
        p2 = donor_sets(ctx, episodes, age, admitted, "p2_90")
        p95 = donor_sets(ctx, episodes, age, admitted, "p2_95")
        for c in pool:
            code = ctx.tl[c].code
            row = rows.setdefault(code, {k: 0 for k in zero})
            if c not in p2:
                continue
            row["own_cells"] = p2[c]["cells"]
            n_m3 = int(m3[c]["elig"].size) if c in m3 else 0
            a = agg[key]
            a[0] += n_m3 >= C.MIN_ELIGIBLE_DONORS
            row[f"donors_{key}_m3"] = n_m3
            for tag, sets, base in (("p2", p2, 1), ("p95", p95, 4)):
                d = sets.get(c)
                n = int(d["elig"].size) if d is not None else 0
                imp = sum(int(d["cells"] - sum(int(dm[:, donor].sum()) for dm in d["defined"])) for donor in d["elig"]) if d is not None else 0
                row[f"donors_{key}_{tag}"] = n
                row[f"imputed_cells_{key}_{tag}"] = imp
                a[base] += n >= C.MIN_ELIGIBLE_DONORS
                a[base + 1] += imp
                a[base + 2] += n * (d["cells"] if d is not None else 0)
    summary = {}
    for key in ("b", "c"):
        a = agg[key]
        summary[key] = {"pool_charts": len(pool), "charts_ge5_donors_m3": a[0], "k11_floor_met_m3": int(a[0] >= C.DONOR_FLOOR_CHARTS),
                        "charts_ge5_donors_p2": a[1], "k11_floor_met_p2": int(a[1] >= C.DONOR_FLOOR_CHARTS),
                        "imputed_cell_share_p2": f"{(a[2] / a[3]):.6f}" if a[3] else "",
                        "charts_ge5_donors_p95": a[4], "k11_floor_met_p95": int(a[4] >= C.DONOR_FLOOR_CHARTS),
                        "imputed_cell_share_p95": f"{(a[5] / a[6]):.6f}" if a[6] else ""}
    return {"charts": rows, "checks": summary}


def donor_diagnostic(ctx: FamilyContext, episodes: Sequence[Episode], admitted: Optional[Iterable[int]] = None) -> Dict[str, Any]:
    """Review N2 / v1.5 P1: per check, the charts keeping at least 5 donors under v1.4 M3, the K11 floor status, and
    the P1 trigger (P2 applies to a check if and only if its M3 count is below the floor). Counts only; to be logged
    before any p-value. It needs the charts' episode windows, so on real data it runs inside the count_blind boundary."""
    m3 = donor_eligibility_counts(ctx, episodes, admitted)
    out: Dict[str, Any] = {"family": ctx.family, "rule": "v1.4 M3", "floor": C.DONOR_FLOOR_CHARTS}
    for key in ("b", "c"):
        out[key] = {"charts_with_5_donors": m3[key], "floor_ok": m3[key] >= C.DONOR_FLOOR_CHARTS, "p2_trigger": m3[key] < C.DONOR_FLOOR_CHARTS}
    out["donor_rules"] = {k: ("p2_90" if out[k]["p2_trigger"] else "m3") for k in ("b", "c")}
    return out


def direction_counts(ctx: FamilyContext, episodes: Sequence[Episode]) -> Dict[str, int]:
    """v1.2 K4 / v1.3 L1: scored-applicable episodes that also have an applicable opposite-polarity unit (window at
    least half assessed), and the charts they sit in. Assessed masks only."""
    app = applicable_mask(ctx, episodes)
    opp = opposite_applicable_mask(ctx, episodes)
    sel = [e for e, a, o in zip(episodes, app, opp) if a and o]
    charts = {e.chart for e in sel}
    return {"episodes": len(sel), "charts": len(charts), "testable": bool(len(sel) >= C.DIR_MIN_EPISODES and len(charts) >= C.DIR_MIN_CHARTS)}


def run_donor_check(
    ctx: FamilyContext,
    episodes: Sequence[Episode],
    draws: int,
    rng: np.random.Generator,
    age_matched: bool,
    admitted: Optional[Iterable[int]] = None,
    rule: str = "m3",
) -> Dict[str, Any]:
    """T2 (calendar-matched) or T3 (age-matched), its pool and p.

    Eligibility (episode set, its own-chart applicable unit set, donors) comes from ``donor_sets``, fixed before any
    draw. Episode coverage on a timeline = mean over that unit set of the unit coverage (SUR-RB-39). T = mean over
    included charts of mean over its episodes of (coverage on the drawn timeline - mean coverage over the chart's
    eligible donors, own chart excluded). Observed: the chart's own timeline. Under v1.4 M3 every eligible donor has
    every cell defined; under v1.5 P2 a donor's undefined cell takes the donor's own block base rate for that unit and
    window length, in the donor mean and whenever it is drawn (never a zero deviation); the imputed share is reported.
    """
    sets = donor_sets(ctx, episodes, age_matched, admitted, rule)
    included: List[int] = []
    excluded: List[int] = []
    V: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}
    cells_total = 0
    cells_imputed = 0
    for c, d in sets.items():
        elig = d["elig"]
        if elig.size < C.MIN_ELIGIBLE_DONORS:
            excluded.append(c)
            continue
        choices = np.concatenate([[c], elig])  # first entry = self = observed
        M = np.empty((len(d["eps"]), choices.size))
        for j in range(len(d["eps"])):
            # SUR-RB-39 (2): the episode's own-chart applicable unit set, fixed before the draws
            lo, hi = d["dlo"][j][choices], d["dhi"][j][choices]
            U = ctx.unit_coverages(d["units"][j], lo, hi, choices)
            if rule != "m3":
                L = int(hi[0] - lo[0] + 1)
                for ui, v in enumerate(d["units"][j]):
                    for ci in range(1, choices.size):  # donors only: the own chart's cells are all defined
                        cells_total += 1
                        if not np.isfinite(U[ui, ci]):
                            U[ui, ci] = ctx.block_base_rate(int(choices[ci]), v, L, int((lo[ci] + hi[ci]) // 2))
                            cells_imputed += 1
            M[j] = U.mean(axis=0)
        if not np.isfinite(M).all():
            raise ScorerError("check (b)/(c): an eligible timeline has an undefined coverage")
        m_e = M[:, 1:].mean(axis=1)  # donor mean: eligible donors only, own chart excluded
        V[c] = (choices, (M - m_e[:, None]).mean(axis=0))
        included.append(c)
    out: Dict[str, Any] = {"included_charts": included, "excluded_charts": excluded, "donor_rule": rule,
                           "imputed_share": (cells_imputed / cells_total) if cells_total else 0.0}
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


def simes_two(p_a: float, p_b: float) -> float:
    """v1.4 M1: Simes combination of two p-values, min(1, 2 * min, max)."""
    return float(min(1.0, 2.0 * min(p_a, p_b), max(p_a, p_b)))


def nonschedulable_statistic(
    ctx: FamilyContext, ns_episodes: Optional[Sequence[Episode]], cfg: C.ScoreConfig, admitted: Optional[Sequence[int]] = None
) -> Dict[str, Any]:
    """SUR-RB-55 (d): the fallback direction-consistency statistic = T (v1.0 section 3.2, chart-weighted mean of the
    episode percentiles under the primary block scheme) on the separately formed non-schedulable list, its episodes
    fixed by the same scorable rule before any draw; the condition is T above its null mean, exactly 0.5 (section 3.2
    step 4). No scored episode (or no list) = the condition is NOT met (fail closed)."""
    eps = list(ns_episodes or [])
    for ep in eps:
        ep.validate()
        if not 0 <= ep.chart < len(ctx.tl):
            raise ScorerError("a non-schedulable episode refers to a chart outside the family")
    if admitted is not None:
        keep = set(admitted)
        eps = [e for e in eps if e.chart in keep]
    sc = [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok] if eps else []
    if not sc:
        return {"T_nonschedulable": None, "nonschedulable_episodes_scored": 0, "nonschedulable_above_null_mean": False}
    scheme = ctx.schemes[0][0]
    # the observed T sits at index 0 and does not depend on the draws (one draw is run only to use the same code path)
    res = run_scheme(ctx, scheme, sc, 1, np.random.default_rng([cfg.seed, FAMILY_STREAM[ctx.family], 95]), want_dir=False)
    t = float(res.pools["T"][0])
    return {"T_nonschedulable": t, "nonschedulable_episodes_scored": len(sc), "nonschedulable_above_null_mean": bool(t > C.NONSCHEDULABLE_NULL_MEAN)}


def score_family(
    ctx: FamilyContext,
    episodes: Sequence[Episode],
    cfg: C.ScoreConfig,
    admitted: Optional[Iterable[int]] = None,
    d7: Optional[Mapping[str, Any]] = None,
    ns_episodes: Optional[Sequence[Episode]] = None,
) -> Dict[str, Any]:
    """All statistics and p-values of one family for one episode set. Pure given (ctx, episodes, cfg, d7, ns_episodes).

    ``ns_episodes`` (SUR-RB-55): the SEPARATELY formed non-schedulable list (count_blind's primary_nonschedulable:
    schedulable occurrences dropped before the horizon trim and the merge). With ``cfg.fallback_primary_set`` it gives
    the fallback's direction-consistency statistic and nothing else (never T, Z25, (b), (c), p_dir or eligibility).

    ``d7``: the sealed D7 decisions (dir_testable, z25_units). When absent (calibration), they are recounted from
    applicability only, as count_blind would (v1.2 K4/K5, v1.3 L1; SUR-RB-36 (a)).
    p1: F-T = min-p over {T5, Z25-5}; F-D = Simes over the two within-scheme min-p values, each scheme in its own
    draws (v1.4 M1), or Bonferroni across schemes when ``cfg.scheme_combination == "bonferroni"`` (the v1.4 M1
    fallback)."""
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
    own = d7_from_counts(ctx, episodes)
    dir_testable, z25_units = own["dir_testable"], own["z25_units"]
    if d7 is not None:
        if "dir_testable" in d7:
            dir_testable = bool(d7["dir_testable"])
        if "z25_units" in d7:
            z25_units = list(d7["z25_units"])
    dircount = direction_counts(ctx, episodes)
    out["dir_testable"] = dir_testable
    out["dir_episodes"] = dircount["episodes"]
    out["dir_charts"] = dircount["charts"]
    out["z25_unit_list"] = sorted(z25_units)
    pools: Dict[str, np.ndarray] = {}
    scheme_p: Dict[str, float] = {}
    per_all: Dict[str, float] = {}
    primary: Optional[SchemeResult] = None
    for si, (scheme, _bd, _mb) in enumerate(ctx.schemes):
        rng = np.random.default_rng([cfg.seed, stream, si])
        sc = scored if si == 0 else [e for e, ok in zip(episodes, scorable_mask(ctx, episodes, scheme)) if ok]
        if not sc:
            continue
        dir_el = opposite_applicable_mask(ctx, sc) if si == 0 else None
        res = run_scheme(
            ctx, scheme, sc, cfg.draws, rng,
            want_dir=(si == 0 and dir_testable),
            z25_units=z25_units, dir_eligible=dir_el,
        )
        if si == 0:
            primary = res
        sp = {"T-" + scheme: res.pools["T"]}
        if "Z25" in res.pools:
            sp["Z25-" + scheme] = res.pools["Z25"]
        p_s, per = min_p_adjusted(sp)  # within-scheme min-p, the scheme's own draws (K5, v1.4 M1)
        scheme_p[scheme] = p_s
        per_all.update(per)
        pools.update(sp)
    if len(scheme_p) == 1:
        p1 = next(iter(scheme_p.values()))
    elif cfg.scheme_combination == "bonferroni":
        p1 = float(min(1.0, 2.0 * min(scheme_p.values())))
    else:
        a_, b_ = list(scheme_p.values())
        p1 = simes_two(a_, b_)
    out.update(
        status="scored",
        stats={k: float(v[0]) for k, v in sorted(pools.items())},
        null_mean={k: float(v[1:].mean()) for k, v in sorted(pools.items())},
        p_stat=per_all,
        p_scheme=scheme_p,
        scheme_combination=cfg.scheme_combination if len(scheme_p) > 1 else "single",
        p1=p1,
        T=float(pools["T-" + ctx.schemes[0][0]][0]),
        z25_units=primary.n_unit_eligible if primary else 0,
    )
    assert primary is not None
    dpool = primary.pools.get("_dir")
    out["T_dir"] = float(dpool[0]) if dpool is not None else None
    out["p_dir"] = pool_p(dpool) if dpool is not None else None
    adm = None if admitted is None else list(admitted)
    if cfg.fallback_primary_set:
        out.update(nonschedulable_statistic(ctx, ns_episodes, cfg, adm))
    rules = {"b": (d7 or {}).get("donor_rule_b", "m3"), "c": (d7 or {}).get("donor_rule_c", "m3")}  # v1.5 P1, sealed at D7
    rb = run_donor_check(ctx, list(episodes), cfg.draws, np.random.default_rng([cfg.seed, stream, 90]), age_matched=False, admitted=adm, rule=rules["b"])
    rc = run_donor_check(ctx, list(episodes), cfg.draws, np.random.default_rng([cfg.seed, stream, 91]), age_matched=True, admitted=adm, rule=rules["c"])
    out.update(
        T2=rb["T"], p2=rb["p"], b_charts=len(rb["included_charts"]), b_excluded=len(rb["excluded_charts"]),
        T3=rc["T"], p3=rc["p"], c_charts=len(rc["included_charts"]), c_excluded=len(rc["excluded_charts"]),
        donor_floor_ok=bool(len(rb["included_charts"]) >= C.DONOR_FLOOR_CHARTS and len(rc["included_charts"]) >= C.DONOR_FLOOR_CHARTS),
        donor_rules=rules, imputed_share_b=rb.get("imputed_share"), imputed_share_c=rc.get("imputed_share"),
        b_excluded_codes=[ctx.tl[i].code for i in rb["excluded_charts"]],
        c_excluded_codes=[ctx.tl[i].code for i in rc["excluded_charts"]],
    )
    return out
