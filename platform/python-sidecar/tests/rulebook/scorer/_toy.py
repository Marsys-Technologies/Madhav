"""Toy worlds for the scorer tests: random persistent on/off timelines, small units, planted effects."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from services.rulebook.scorer import config as C
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec

BASE = date(1990, 1, 1).toordinal()


def runs_series(rng: np.random.Generator, n: int, duty: float, mean_run: float, na_frac: float = 0.0) -> np.ndarray:
    """int8 states from alternating exponential runs; ``duty`` = long-run share TRUE."""
    out = np.zeros(n, dtype=np.int8)
    i = 0
    state = 1 if rng.random() < duty else 0
    while i < n:
        mean = mean_run * (duty / (1 - duty) if state == 1 else 1.0) if 0 < duty < 1 else mean_run
        ln = max(1, int(rng.exponential(mean)))
        out[i : i + ln] = state
        i += ln
        state = 1 - state
    if na_frac:
        k = max(1, int(na_frac * n))
        s = int(rng.integers(0, max(1, n - k)))
        out[s : s + k] = -1
    return out


def make_units(spec: Sequence[Tuple[str, str, Sequence[Sequence[Tuple[str, Sequence[str]]]]]]) -> List[UnitSpec]:
    """spec: (unit_id, polarity, groups) with groups = [[(rid, area_tags), ...], ...]."""
    out = []
    for uid, pol, groups in spec:
        gs = tuple(tuple(MemberSpec(r, frozenset(tags)) for r, tags in g) for g in groups)
        out.append(UnitSpec(uid, C.FAMILY_DASHA, pol, "cluster" if len(gs) > 1 or len(gs[0]) > 1 else "conflict_free", gs))
    return out


def toy_world(
    seed: int,
    n_charts: int = 12,
    years: int = 30,
    n_units: int = 6,
    duty: float = 0.15,
    mean_run: float = 20.0,
    areas: Sequence[str] = ("career_adv_change_entry", "illness_chronic_surgery"),
    na_frac: float = 0.0,
) -> Tuple[List[ChartTimeline], List[UnitSpec]]:
    rng = np.random.default_rng(seed)
    units = []
    for k in range(n_units):
        pol = "promotive" if k % 2 == 0 else "obstructive"
        tag = areas[k % len(areas)] if k % 3 else C.GENERAL
        units.append(make_units([(f"U{k}", pol, [[(f"M{k}", [tag])]])])[0])
    tls = []
    for c in range(n_charts):
        n = years * 365 + int(rng.integers(0, 200))
        t = ChartTimeline(code=f"c{c}", birth=BASE - 12 * 365, h_start=BASE + int(rng.integers(0, 30)), h_end=0)
        t.h_end = t.h_start + n - 1
        for u in units:
            for m in u.members():
                t.states[m.rid] = runs_series(rng, n, duty, mean_run, na_frac)
        tls.append(t)
    return tls, units


def month_window(y: int, m: int) -> Tuple[int, int]:
    a = date(y, m, 1).toordinal()
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return a, date(ny, nm, 1).toordinal() - 1


def random_episodes(rng: np.random.Generator, tls: Sequence[ChartTimeline], per_chart: int, areas: Sequence[str], g1_share: float = 0.4) -> List[Episode]:
    eps: List[Episode] = []
    for c, t in enumerate(tls):
        for _ in range(per_chart):
            area = areas[int(rng.integers(0, len(areas)))]
            direction = C.FAVOURABLE if rng.random() < 0.5 else C.UNFAVOURABLE
            if rng.random() < g1_share:
                d = int(rng.integers(t.h_start + 1, t.h_end - 1))
                eps.append(Episode(c, area, direction, C.G1, d - 1, d + 1))
            else:
                while True:
                    d = date.fromordinal(int(rng.integers(t.h_start, t.h_end)))
                    lo, hi = month_window(d.year, d.month)
                    if lo >= t.h_start and hi <= t.h_end:
                        break
                eps.append(Episode(c, area, direction, C.G2, lo, hi))
    return eps


def planted_episodes(
    rng: np.random.Generator,
    tls: Sequence[ChartTimeline],
    units: Sequence[UnitSpec],
    per_chart: int,
    q: float,
    areas: Sequence[str],
    only_units: Optional[Sequence[str]] = None,
    g1_share: float = 0.4,
    schedulable_effect: Optional[bool] = None,
) -> List[Episode]:
    """Like ``random_episodes`` but a share ``q`` of the episodes sits on a TRUE day of a unit that applies to it."""
    eps = random_episodes(rng, tls, per_chart, areas, g1_share)
    out: List[Episode] = []
    for e in eps:
        if rng.random() >= q:
            out.append(Episode(e.chart, e.area, e.direction, e.grade, e.lo, e.hi, schedulable=bool(schedulable_effect) if schedulable_effect is not None else False))
            continue
        t = tls[e.chart]
        pol = C.POLARITY_OF_DIRECTION[e.direction]
        cand = [u for u in units if u.polarity == pol and (only_units is None or u.unit_id in only_units) and u.variant(e.area, True) is not None]
        if not cand:
            out.append(e)
            continue
        u = cand[int(rng.integers(0, len(cand)))]
        rid = u.variant(e.area, True).groups[0][0]
        days = np.nonzero(t.states[rid] == 1)[0]
        for _ in range(50):
            d = t.h_start + int(days[int(rng.integers(0, days.size))])
            if e.grade == C.G1 and t.h_start < d < t.h_end:
                out.append(Episode(e.chart, e.area, e.direction, C.G1, d - 1, d + 1, schedulable=bool(schedulable_effect) if schedulable_effect is not None else False))
                break
            if e.grade == C.G2:
                from datetime import date as _d

                dd = _d.fromordinal(d)
                lo, hi = month_window(dd.year, dd.month)
                if lo >= t.h_start and hi <= t.h_end:
                    out.append(Episode(e.chart, e.area, e.direction, C.G2, lo, hi, schedulable=bool(schedulable_effect) if schedulable_effect is not None else False))
                    break
        else:
            out.append(e)
    return out


# ── ledgers (SUR-RB-45/46): every ledger-touching test uses a temporary directory (see conftest.py) ─────────────
REAL_LEDGER_DIR = C.LEDGER_DIR  # captured at import, before the autouse fixture redirects the constants
REAL_LOCK_LEDGER_PATH = C.LOCK_LEDGER_PATH
REAL_QUARANTINE_DIR = C.LEDGER_QUARANTINE_DIR
FAKE_COUNT_BLIND_SHA = "c0" * 32  # the toy count_blind V3 script hash logged in each test's own decisions ledger
FAKE_COUNT_BLIND_TESTS_SHA = "c1" * 32
FAKE_LOCK_OCC = "1" * 64
FAKE_LOCK_BIRTH = "2" * 64


def ledger_lines(occ: str = FAKE_LOCK_OCC, birth: str = FAKE_LOCK_BIRTH, cutoff_occ: Optional[str] = None, cutoff_birth: Optional[str] = None) -> List[Dict]:
    """The decisions-ledger entries the scorer reads, in their logged formats, with toy hashes."""
    return [
        {"id": "SOMETHING-ELSE", "files_sha256": {}},
        {"id": "CUTOFF-AND-FILE-HASHES-V5-20261030", "files_sha256": {"sample_events_v5_slim.csv": cutoff_occ or occ, "BIRTH_DATA_v5.csv": cutoff_birth or birth, "sample_events_v5.csv": "f" * 64}},
        {"id": "YARDSTICK-LOCK-STEP4", "hashes_verified_by_surrogate": {"sample_events_v5_slim.csv": occ, "BIRTH_DATA_v5.csv": birth, "sample_events_v5.csv (full)": "f" * 64}},
        {"id": "COUNT-BLIND-V3-HASHES", "supersedes": "COUNT-BLIND-V2-HASHES", "sha256": FAKE_COUNT_BLIND_SHA, "tests": {"sha256": FAKE_COUNT_BLIND_TESTS_SHA}},
    ]
