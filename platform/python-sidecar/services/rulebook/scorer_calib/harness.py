"""The Part F calibration harness: studies on real timelines with synthetic occurrences, rates, the F2 gate.

One study = one synthetic occurrence set (model, optional planted effect) scored by the production scorer
(``score_family`` for both families, Holm over the two) at a declared number of draws. The harness records the
raw p-values of every study, so every decision variant is a re-reading of the same studies:

  a        Holm-adjusted p1 <= 0.05                                  (check (a) alone)
  a+b      and p2 <= 0.05
  a+c      and p3 <= 0.05
  full     and p2 <= 0.05 and p3 <= 0.05 and p_dir <= 0.05           (the v1.1 STRONG rule)

False-STRONG is counted per family (a family passes) and overall (either family passes).
"""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import os
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..scorer import config as C
from ..scorer.core import FamilyContext, score_family
from ..scorer.outcome import holm_adjust
from . import occurrences as O

VARIANTS = ("a", "a+b", "a+c", "a+b+c", "full")
FAMS = C.FAMILIES


def flags(adj: Optional[float], r: Mapping[str, Any]) -> Dict[str, bool]:
    def le(x: Optional[float]) -> bool:
        return x is not None and x <= C.ALPHA_STRONG

    a = le(adj)
    b = a and le(r.get("p2"))
    c = a and le(r.get("p3"))
    bc = b and le(r.get("p3"))
    full = bc and le(r.get("p_dir"))
    return {"a": a, "a+b": b, "a+c": c, "a+b+c": bc, "full": full}


class Calibration:
    """Contexts for both families and the study generator. Build once, then ``run_study`` many times."""

    def __init__(
        self,
        timelines: Mapping[str, Sequence[Any]],
        units: Mapping[str, Sequence[Any]],
        gate_drop: Mapping[str, Mapping[str, Any]],
        profile: O.CountsProfile,
        draws: int = C.MIN_DRAWS_CALIBRATION,
        seed: int = 20261030,
    ):
        self.draws = draws
        self.seed = seed
        self.profile = profile
        self.ctx = {f: FamilyContext(f, timelines[f], units[f], gate_drop.get(f)) for f in FAMS}
        self.tls = {f: list(timelines[f]) for f in FAMS}
        # the longer (transit) horizon carries the placement; the daśā horizon is inside it for every chart
        for a, b in zip(self.tls[C.FAMILY_DASHA], self.tls[C.FAMILY_TRANSIT]):
            assert a.code == b.code and a.h_start >= b.h_start and a.h_end == b.h_end
        self.pmfs = [O._DayPmf(t) for t in self.tls[C.FAMILY_TRANSIT]]
        self.eff = {f: O.ChartTimelineSet(self.tls[f], self.ctx[f].units, self.ctx[f].gate_drop) for f in FAMS}

    def warm(self, n: int = 150) -> None:
        """Run ``n`` throwaway studies so the curve caches are filled BEFORE the worker pool forks (pages are then
        shared copy-on-write). Their results are discarded; study indices start at 10**7 and are never reused."""
        for i in range(n):
            self.run_study("N4", 10_000_000 + i)

    def usable_filter(self, occ: Sequence[O.Occurrence], min_usable: int) -> List[O.Occurrence]:
        """v1.0 7.4 item 5 / v1.1 A6: drop every chart with fewer than ``min_usable`` usable episodes, an episode
        being usable when it is scored in the primary set of at least one family."""
        from ..scorer.core import scorable_mask

        usable: Dict[int, set] = {}
        for f in FAMS:
            eps = O.to_episodes(occ, self.tls[f])
            for e, ok in zip(eps, scorable_mask(self.ctx[f], eps)):
                if ok:
                    usable.setdefault(e.chart, set()).add((e.lo, e.hi, e.area, e.direction))
        keep = {c for c, s in usable.items() if len(s) >= min_usable}
        return [o for o in occ if o.chart in keep]

    def run_study(self, model: str, index: int, q: float = 0.0, target: str = C.FAMILY_DASHA, sparse: bool = False, min_usable: int = 0) -> Dict[str, Any]:
        mi = O.MODELS.index(model)
        rng = np.random.default_rng([self.seed, 100 + mi, index, int(round(q * 1000)), int(sparse), FAMS.index(target)])
        occ = O.place_study(rng, self.profile, self.tls[C.FAMILY_TRANSIT], self.pmfs, model)
        if q > 0:
            occ = O.apply_effect(rng, occ, q, self.eff[target], sparse)
        if min_usable:
            occ = self.usable_filter(occ, min_usable)
        cfg = C.ScoreConfig(draws=self.draws, seed=int(rng.integers(1, 2**31 - 1)))
        res: Dict[str, Dict[str, Any]] = {}
        for f in FAMS:
            res[f] = score_family(self.ctx[f], O.to_episodes(occ, self.tls[f]), cfg)
        p1 = {f: res[f]["p1"] for f in FAMS if res[f].get("p1") is not None}
        adj = holm_adjust(p1) if p1 else {}
        out: Dict[str, Any] = {"model": model, "i": index, "q": q, "target": target, "sparse": sparse, "min_usable": min_usable}
        for f in FAMS:
            r = res[f]
            out[f] = {
                "n": r["episodes_scored"],
                "charts": r["charts_scored"],
                "p1": r.get("p1"),
                "adj": adj.get(f),
                "p2": r.get("p2"),
                "p3": r.get("p3"),
                "pd": r.get("p_dir"),
                "T": r.get("T"),
                "flags": flags(adj.get(f), r),
            }
        out["any"] = {v: any(out[f]["flags"][v] for f in FAMS) for v in VARIANTS}
        return out


# ── parallel driver ───────────────────────────────────────────────────────────────────────────
_CAL: Optional[Calibration] = None


def _work(task: Tuple[Any, ...]) -> Dict[str, Any]:
    assert _CAL is not None
    model, i, q, target, sparse = task[:5]
    return _CAL.run_study(model, i, q, target, sparse, task[5] if len(task) > 5 else 0)


def run_many(cal: Calibration, tasks: Sequence[Tuple[str, int, float, str, bool]], workers: int, out_path: Optional[str] = None, log_every: int = 200) -> List[Dict[str, Any]]:
    """Run studies (fork pool sharing ``cal`` read-only), appending each result to ``out_path`` as a JSON line."""
    global _CAL
    _CAL = cal
    results: List[Dict[str, Any]] = []
    t0 = time.time()
    fh = open(out_path, "a", encoding="utf-8") if out_path else None
    try:
        if workers <= 1:
            it: Iterable[Dict[str, Any]] = map(_work, tasks)
            pool = None
        else:
            pool = mp.get_context("fork").Pool(workers)
            it = pool.imap_unordered(_work, tasks, chunksize=4)
        for k, r in enumerate(it, 1):
            results.append(r)
            if fh:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
                fh.flush()
            if k % log_every == 0:
                print("  %d/%d studies, %.0fs" % (k, len(tasks), time.time() - t0), flush=True)
        if pool:
            pool.close()
            pool.join()
    finally:
        if fh:
            fh.close()
    return results


# ── reading the results ─────────────────────────────────────────────────────────────────────────
def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c + r) / d


def rates(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    n = len(results)
    out: Dict[str, Any] = {"n": n}
    for f in FAMS:
        out[f] = {v: sum(1 for r in results if r[f]["flags"][v]) / n if n else None for v in VARIANTS}
        out[f]["full_k"] = sum(1 for r in results if r[f]["flags"]["full"])
        out[f]["full_upper95"] = wilson_upper(out[f]["full_k"], n)
    out["any"] = {v: sum(1 for r in results if r["any"][v]) / n if n else None for v in VARIANTS}
    out["any"]["full_k"] = sum(1 for r in results if r["any"]["full"])
    out["any"]["full_upper95"] = wilson_upper(out["any"]["full_k"], n)
    return out


def f2_gate(by_model: Mapping[str, Sequence[Mapping[str, Any]]], min_studies: int = C.GATE_MIN_STUDIES) -> Dict[str, Any]:
    """v1.1 F2: under EACH model, per-family false-STRONG <= 0.02 and overall <= 0.03, over >= 5,000 studies."""
    rows: Dict[str, Any] = {}
    ok_all = True
    for m, res in by_model.items():
        r = rates(res)
        fam_ok = all(r[f]["full"] <= C.GATE_PER_FAMILY for f in FAMS)
        over_ok = r["any"]["full"] <= C.GATE_OVERALL
        enough = r["n"] >= min_studies
        rows[m] = {"rates": r, "per_family_ok": fam_ok, "overall_ok": over_ok, "enough_studies": enough, "pass": bool(fam_ok and over_ok and enough)}
        ok_all &= rows[m]["pass"]
    return {"pass": bool(ok_all and rows), "models": rows}
