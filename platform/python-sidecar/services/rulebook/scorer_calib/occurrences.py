"""Synthetic occurrences for the calibration (v1.1 Part F1): the null models N0-N4 and the planted effect.

No real occurrence is read. A ``CountsProfile`` says, per chart, how many episodes of which (area, direction,
grade) a study has; it is DECLARED here (fixed seed, weights written below) unless a counts-only file of real
per-chart counts is supplied through ``profile_from_counts_file``. The models place those episodes:

N0  uniform within the horizon.
N1  age-clustered, with the fixed age densities of v1.1 F1 (truncated to the horizon).
N2  seasonal: N0 with month weights 1 + 0.3 sin(2 pi (month - 1) / 12).
N3  bursty: half the episodes within 15 days after a previous one of the same chart.
N4  N1 + N2 + N3 together.

The effect q > 0 (power): with probability q an episode is placed on a day on which a randomly chosen unit that
applies to it is TRUE (member state TRUE), a typical-rule effect; ``sparse`` limits the choice to a random 20% of
the units (v1.1 F4). Episodes are created over the transit horizon (the longer one) and each family keeps those
inside its own horizon, so the two families see the same occurrences.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..scorer import config as C
from ..scorer.model import ChartTimeline, Episode, UnitSpec

MODELS = ("N0", "N1", "N2", "N3", "N4")

# (area, direction): weight. The areas and directions are those of the collector table (COLLECTOR_DEFINITIONS A).
# "other"/favourable = marriage, adoption; "other"/unfavourable = accident, legal trial. DECLARED weights.
DECLARED_MIX: Tuple[Tuple[str, str, float], ...] = (
    ("separation_relationship_end", C.UNFAVOURABLE, 0.06),
    ("childbirth_progeny", C.FAVOURABLE, 0.12),
    ("bereavement_parent", C.UNFAVOURABLE, 0.08),
    ("bereavement_other", C.UNFAVOURABLE, 0.05),
    ("illness_chronic_surgery", C.UNFAVOURABLE, 0.10),
    ("career_adv_change_entry", C.FAVOURABLE, 0.20),
    ("achievement_recognition", C.FAVOURABLE, 0.18),
    ("education_learning", C.FAVOURABLE, 0.04),
    ("other", C.FAVOURABLE, 0.09),
    ("other", C.UNFAVOURABLE, 0.08),
)
DECLARED_G1_SHARE = 0.35
DECLARED_MEAN_PER_CHART = 24.0
SEASONAL_AMPLITUDE = 0.3
BURST_SHARE = 0.5
BURST_DAYS = 15

# age densities (years): kind, params. v1.1 F1.
AGE_DENSITY: Dict[Tuple[str, str], Tuple[str, Tuple[float, ...]]] = {
    ("other", C.FAVOURABLE): ("normal", (29.0, 5.0)),  # partnership start (marriage, adoption)
    ("separation_relationship_end", C.UNFAVOURABLE): ("normal", (38.0, 8.0)),  # partnership end
    ("childbirth_progeny", C.FAVOURABLE): ("normal", (31.0, 5.0)),
    ("bereavement_parent", C.UNFAVOURABLE): ("normal", (52.0, 12.0)),
    ("bereavement_other", C.UNFAVOURABLE): ("normal", (55.0, 15.0)),
    ("career_adv_change_entry", C.FAVOURABLE): ("career", ()),
    ("achievement_recognition", C.FAVOURABLE): ("career", ()),
    ("illness_chronic_surgery", C.UNFAVOURABLE): ("normal", (55.0, 15.0)),
}


@dataclass(frozen=True)
class CountsProfile:
    """Per chart (by index): the (area, direction, grade) of every episode of a study."""

    per_chart: Tuple[Tuple[Tuple[str, str, str], ...], ...]

    def total(self) -> int:
        return sum(len(x) for x in self.per_chart)


def declared_profile(n_charts: int, seed: int = 7, mean: float = DECLARED_MEAN_PER_CHART) -> CountsProfile:
    """A declared stand-in for the real per-chart counts: heterogeneous counts (lognormal around ``mean``)."""
    rng = np.random.default_rng([seed, 1])
    w = np.array([m[2] for m in DECLARED_MIX])
    w = w / w.sum()
    out = []
    for _ in range(n_charts):
        lam = mean * math.exp(rng.normal(-0.18, 0.6))  # lognormal with mean ~ `mean`
        n = int(rng.poisson(lam))
        eps = []
        for _k in range(n):
            a, d, _w = DECLARED_MIX[int(rng.choice(len(DECLARED_MIX), p=w))]
            g = C.G1 if rng.random() < DECLARED_G1_SHARE else C.G2
            eps.append((a, d, g))
        out.append(tuple(eps))
    return CountsProfile(tuple(out))


def profile_from_counts_file(path: str, codes: Sequence[str]) -> CountsProfile:
    """Real counts only: CSV with columns chart_code, area, direction, grade, count (no names, no dates)."""
    per: Dict[str, List[Tuple[str, str, str]]] = {c: [] for c in codes}
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["chart_code"] in per:
                per[r["chart_code"]].extend([(r["area"], r["direction"], r["grade"])] * int(r["count"]))
    return CountsProfile(tuple(tuple(per[c]) for c in codes))


# ── day-probability vectors ──────────────────────────────────────────────────────────────
def _age_density(kind: Tuple[str, Tuple[float, ...]], age: np.ndarray) -> np.ndarray:
    name, p = kind
    if name == "normal":
        mu, sd = p
        return np.exp(-0.5 * ((age - mu) / sd) ** 2)
    # career and recognition: uniform on 20-65 with a x2 weight on 25-40
    d = np.where((age >= 20.0) & (age <= 65.0), 1.0, 0.0)
    return d * np.where((age >= 25.0) & (age <= 40.0), 2.0, 1.0)


def _month_weights_for_days(h_start: int, n: int) -> np.ndarray:
    months = np.array([date.fromordinal(h_start + i).month for i in range(n)])
    return 1.0 + SEASONAL_AMPLITUDE * np.sin(2.0 * math.pi * (months - 1) / 12.0)


class _DayPmf:
    """Per-chart caches of the day weights (age densities, seasonal) over the transit horizon."""

    def __init__(self, tl: ChartTimeline):
        self.tl = tl
        self.n = tl.n_days
        self.age_years = (np.arange(self.n) + (tl.h_start - tl.birth)) / 365.25
        self._season: Optional[np.ndarray] = None
        self._age: Dict[Tuple[str, str], np.ndarray] = {}
        self._cdf: Dict[Tuple[Any, ...], np.ndarray] = {}

    def season(self) -> np.ndarray:
        if self._season is None:
            self._season = _month_weights_for_days(self.tl.h_start, self.n)
        return self._season

    def age(self, area: str, direction: str) -> np.ndarray:
        k = (area, direction)
        if k not in self._age:
            kind = AGE_DENSITY.get(k)
            self._age[k] = _age_density(kind, self.age_years) if kind else np.ones(self.n)
        return self._age[k]

    def cdf(self, area: str, direction: str, aged: bool, seasonal: bool) -> np.ndarray:
        """Cumulative day probabilities (cached); sampling is ``searchsorted(cdf, u)``."""
        k = (area if aged else "", direction if aged else "", aged, seasonal)
        c = self._cdf.get(k)
        if c is None:
            w = np.ones(self.n)
            if aged:
                w = w * self.age(area, direction)
            if seasonal:
                w = w * self.season()
            s = w.sum()
            w = w / s if s > 1e-12 else np.full(self.n, 1.0 / self.n)
            c = np.cumsum(w)
            c /= c[-1]
            self._cdf[k] = c
        return c


def month_of(d: int) -> Tuple[int, int]:
    x = date.fromordinal(d)
    a = date(x.year, x.month, 1).toordinal()
    ny, nm = (x.year + 1, 1) if x.month == 12 else (x.year, x.month + 1)
    return a, date(ny, nm, 1).toordinal() - 1


def _window(day: int, grade: str) -> Tuple[int, int]:
    return (day - 1, day + 1) if grade == C.G1 else month_of(day)


def _inside(win: Tuple[int, int], tl: ChartTimeline) -> bool:
    return win[0] >= tl.h_start and win[1] <= tl.h_end


@dataclass(frozen=True)
class Occurrence:
    chart: int
    area: str
    direction: str
    grade: str
    lo: int
    hi: int


def place_study(
    rng: np.random.Generator,
    profile: CountsProfile,
    tls: Sequence[ChartTimeline],
    pmfs: Sequence[_DayPmf],
    model: str,
) -> List[Occurrence]:
    """Occurrences of one null study under ``model`` (over the longer, transit, horizon of each chart)."""
    if model not in MODELS:
        raise ValueError(model)
    aged = model in ("N1", "N4")
    seasonal = model in ("N2", "N4")
    bursty = model in ("N3", "N4")
    out: List[Occurrence] = []
    for ci, eps in enumerate(profile.per_chart):
        tl = tls[ci]
        placed: List[Occurrence] = []
        n_burst = int(round(BURST_SHARE * len(eps))) if bursty else 0
        order = list(range(len(eps)))
        burst_set = set(rng.permutation(len(eps))[:n_burst].tolist()) if bursty else set()
        # the first episode can never follow a previous one
        for k in order:
            area, direction, grade = eps[k]
            win = None
            if k in burst_set and placed:
                for _try in range(40):
                    prev = placed[int(rng.integers(0, len(placed)))]
                    base = (prev.lo + prev.hi) // 2 if prev.grade == C.G1 else prev.lo
                    day = base + int(rng.integers(1, BURST_DAYS + 1))
                    w = _window(day, grade)
                    if _inside(w, tl):
                        win = w
                        break
            if win is None:
                cdf = pmfs[ci].cdf(area, direction, aged, seasonal)
                for _try in range(200):
                    day = tl.h_start + min(int(np.searchsorted(cdf, rng.random(), side="right")), tl.n_days - 1)
                    w = _window(day, grade)
                    if _inside(w, tl):
                        win = w
                        break
                if win is None:
                    continue
            placed.append(Occurrence(ci, area, direction, grade, win[0], win[1]))
        out.extend(placed)
    return out


def apply_effect(
    rng: np.random.Generator,
    occ: Sequence[Occurrence],
    q: float,
    target: ChartTimelineSet,
    sparse: bool = False,
) -> List[Occurrence]:
    """Move a share ``q`` of the occurrences onto TRUE days of the target family's rules (see module text)."""
    if q <= 0:
        return list(occ)
    ctx_units = target.units
    active = list(ctx_units)
    if sparse:
        k = max(1, int(round(0.2 * len(ctx_units))))
        idx = rng.permutation(len(ctx_units))[:k]
        active = [ctx_units[i] for i in sorted(idx.tolist())]
    out: List[Occurrence] = []
    for o in occ:
        if rng.random() >= q:
            out.append(o)
            continue
        tl = target.tls[o.chart]
        pol = C.POLARITY_OF_DIRECTION[o.direction]
        cand = []
        for u in active:
            if u.polarity != pol:
                continue
            v = u.variant(o.area, moon_ok=(o.grade == C.G1))
            if v is not None and o.grade not in target.gate_drop.get(u.unit_id, frozenset()):
                cand.append(v)
        moved = None
        for _try in range(30):
            if not cand:
                break
            v = cand[int(rng.integers(0, len(cand)))]
            rid = v.groups[int(rng.integers(0, len(v.groups)))]
            rid = rid[int(rng.integers(0, len(rid)))]
            days = target.true_days(o.chart, rid)
            if days.size == 0:
                cand = [c for c in cand if c is not v]
                continue
            day = tl.h_start + int(days[int(rng.integers(0, days.size))])
            w = _window(day, o.grade)
            if _inside(w, tl):
                moved = Occurrence(o.chart, o.area, o.direction, o.grade, w[0], w[1])
                break
        out.append(moved or o)
    return out


class ChartTimelineSet:
    """The target family's timelines and units for effect placement; caches each member's TRUE-day list."""

    def __init__(self, tls: Sequence[ChartTimeline], units: Sequence[UnitSpec], gate_drop: Mapping[str, Any]):
        self.tls = list(tls)
        self.units = list(units)
        self.gate_drop = dict(gate_drop)
        self._days: Dict[Tuple[int, str], np.ndarray] = {}

    def true_days(self, chart: int, rid: str) -> np.ndarray:
        k = (chart, rid)
        if k not in self._days:
            a = self.tls[chart].states.get(rid)
            self._days[k] = np.nonzero(a == 1)[0] if a is not None else np.zeros(0, dtype=np.int64)
        return self._days[k]


def to_episodes(occ: Sequence[Occurrence], tls: Sequence[ChartTimeline]) -> List[Episode]:
    """The occurrences that fall inside a family's horizon, as scorer episodes (all primary / non-schedulable)."""
    out = []
    for o in occ:
        t = tls[o.chart]
        if o.lo >= t.h_start and o.hi <= t.h_end:
            out.append(Episode(o.chart, o.area, o.direction, o.grade, o.lo, o.hi, schedulable=False))
    return out
