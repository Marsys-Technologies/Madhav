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
from ..scorer.core import FamilyContext, applicable_mask, score_family
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
        self.eff = {f: O.ChartTimelineSet(self.ctx[f]) for f in FAMS}
        # D7.2 second half: at least half the family's units survive the footprint gate in at least one window class
        self.units_ok = {
            f: bool(self.ctx[f].units) and 2 * sum(1 for u in self.ctx[f].units if len(self.ctx[f].gate_drop.get(u.unit_id, frozenset())) < 2) >= len(self.ctx[f].units)
            for f in FAMS
        }

    def warm(self, n: int = 150) -> None:
        """Run ``n`` throwaway studies so the curve caches are filled BEFORE the worker pool forks (pages are then
        shared copy-on-write). Their results are discarded; study indices start at 10**7 and are never reused."""
        for i in range(n):
            self.run_study("N4", 10_000_000 + i)

    def admit(self, eps_by_family: Mapping[str, Sequence[Any]], min_usable: int) -> Tuple[Dict[str, List[Any]], Dict[str, Optional[List[int]]]]:
        """v1.2 K8: exclusion 5 per family. A chart with fewer than ``min_usable`` usable (scored, primary-scheme)
        episodes in a family is excluded from that family only: its episodes are dropped there and it is not a donor
        there. ``min_usable`` 0 admits every chart."""
        from ..scorer.core import applicable_mask

        out: Dict[str, List[Any]] = {}
        adm: Dict[str, Optional[List[int]]] = {}
        for f in FAMS:
            eps = list(eps_by_family[f])
            if not min_usable:
                out[f], adm[f] = eps, None
                continue
            usable: Dict[int, int] = {}
            for e, ok in zip(eps, applicable_mask(self.ctx[f], eps)):  # scored-APPLICABLE (K2), not informative
                if ok:
                    usable[e.chart] = usable.get(e.chart, 0) + 1
            keep = sorted(c for c, n in usable.items() if n >= min_usable)
            ks = set(keep)
            out[f], adm[f] = [e for e in eps if e.chart in ks], keep
        return out, adm

    def run_study(self, model: str, index: int, q: float = 0.0, target: str = C.FAMILY_DASHA, sparse: bool = False, min_usable: int = 0) -> Dict[str, Any]:
        mi = O.MODELS.index(model)
        rng = np.random.default_rng([self.seed, 100 + mi, index, int(round(q * 1000)), int(sparse), FAMS.index(target)])
        occ = O.place_study(rng, self.profile, self.tls[C.FAMILY_TRANSIT], self.pmfs, model)
        if q > 0:
            occ = O.apply_effect(rng, occ, q, self.eff[target], sparse)
        cfg = C.ScoreConfig(draws=self.draws, seed=int(rng.integers(1, 2**31 - 1)))
        eps_f, adm = self.admit({f: O.to_episodes(occ, self.tls[f]) for f in FAMS}, min_usable)
        res: Dict[str, Dict[str, Any]] = {}
        testable: Dict[str, bool] = {}
        app_counts: Dict[str, Tuple[int, int]] = {}
        for f in FAMS:
            res[f] = score_family(self.ctx[f], eps_f[f], cfg, admitted=adm[f])
            app = [e for e, ok in zip(eps_f[f], applicable_mask(self.ctx[f], eps_f[f])) if ok]
            app_counts[f] = (len(app), len({e.chart for e in app}))
            # this study's D7, as production would decide it (review S6): counts, units surviving the gate, K11 floors
            testable[f] = bool(
                app_counts[f][0] >= C.TESTABLE_MIN_EPISODES
                and app_counts[f][1] >= C.TESTABLE_MIN_CHARTS
                and self.units_ok[f]
                and res[f].get("donor_floor_ok")
                and res[f].get("p1") is not None
            )
        p1 = {f: res[f]["p1"] for f in FAMS if testable[f]}
        adj = holm_adjust(p1) if p1 else {}
        out: Dict[str, Any] = {"model": model, "i": index, "q": q, "target": target, "sparse": sparse, "min_usable": min_usable}
        for f in FAMS:
            r = res[f]
            m2 = holm_adjust({g: res[g]["p1"] for g in FAMS if res[g].get("p1") is not None})
            out[f] = {
                "n": r["episodes_scored"],
                "n_applicable": app_counts[f][0],
                "charts_applicable": app_counts[f][1],
                "charts": r["charts_scored"],
                "testable": testable[f],
                "p1": r.get("p1"),
                "adj": adj.get(f),
                "p2": r.get("p2"),
                "p3": r.get("p3"),
                "pd": r.get("p_dir"),
                "dir_ok": r.get("dir_testable"),
                "floor_ok": r.get("donor_floor_ok"),
                "T": r.get("T"),
                "flags": flags(adj.get(f), r),  # the production rule: Holm over this study's testable families
                "flags_m1": flags(r.get("p1"), r),  # one family testable: adjusted p1 = p1
                "flags_m2": flags(m2.get(f), r),  # both families in Holm
            }
        for key in ("flags", "flags_m1", "flags_m2"):
            out["any" if key == "flags" else "any_" + key[6:]] = {v: any(out[f][key][v] for f in FAMS) for v in VARIANTS}
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
    if out_path:  # review M9: identical content -> identical bytes, whatever the worker count
        lines = sorted(open(out_path, encoding="utf-8").read().splitlines())
        with open(out_path, "w", encoding="utf-8") as fo:
            fo.write("".join(x + "\n" for x in lines))
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


def rates(results: Sequence[Mapping[str, Any]], key: str = "flags") -> Dict[str, Any]:
    n = len(results)
    anykey = "any" if key == "flags" else "any_" + key[6:]
    out: Dict[str, Any] = {"n": n, "rule": key}
    for f in FAMS:
        out[f] = {v: sum(1 for r in results if r[f][key][v]) / n if n else None for v in VARIANTS}
        out[f]["full_k"] = sum(1 for r in results if r[f][key]["full"])
        out[f]["full_upper95"] = wilson_upper(out[f]["full_k"], n)
    out["any"] = {v: sum(1 for r in results if r[anykey][v]) / n if n else None for v in VARIANTS}
    out["any"]["full_k"] = sum(1 for r in results if r[anykey]["full"])
    out["any"]["full_upper95"] = wilson_upper(out["any"]["full_k"], n)
    return out


def sanity_ok(rates: Mapping[str, float], testable: Sequence[str]) -> bool:
    """SUR-RB-39 (4): for EACH family D7 makes testable, with the effect planted in that family, STRONG >= 0.80 at
    q = 30% under N0."""
    return bool(testable) and all(f in rates and rates[f] >= C.GATE_SANITY_POWER for f in testable)


def sanity_report(rates: Mapping[str, float], testable: Sequence[str], q_curves: Mapping[str, Mapping[str, float]], unit_tests: Mapping[str, int]) -> Dict[str, Any]:
    """On a shortfall: DO NOT FREEZE; print the q-curve (10/20/30/40%) and the unit-test status so low power can be
    told apart from a defect (SUR-RB-39 (4))."""
    ok = sanity_ok(rates, testable)
    if ok:
        reading = "met"
    elif unit_tests.get("failed", 1) > 0:
        reading = "possible scorer defect: unit tests are not all passing"
    else:
        rising = all(
            all(b >= a - 0.02 for a, b in zip([c[k] for k in sorted(c, key=float)], [c[k] for k in sorted(c, key=float)][1:]))
            and c[sorted(c, key=float)[-1]] > c[sorted(c, key=float)[0]]
            for f, c in q_curves.items()
        )
        reading = "low power: the STRONG rate rises with q but is below 0.80 at q = 30%" if rising else "possible scorer defect: the STRONG rate does not rise with q"
    return {"ok": ok, "freeze": "may proceed" if ok else "DO NOT FREEZE", "rates_q30": dict(rates), "testable": list(testable),
            "q_curve": {f: dict(c) for f, c in q_curves.items()}, "unit_tests": dict(unit_tests), "reading": reading}


def f2_gate(
    by_model: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    draws: int,
    scorer_sha256: str,
    frozen_scorer_sha256: Optional[str],
    d7_known: bool = False,
    sanity: Optional[Mapping[str, float]] = None,
    testable: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """v1.1 F2 with SUR-RB-37 S6/S7. GATE only if: all five models N0-N4, each with at least 5,000 studies, at least
    2,000 draws per check, the scorer byte-identical to the frozen one, and the q = 30% sanity check (STRONG >= 0.80
    under N0, each target family) supplied and met; otherwise status NOT_GATE. Criterion: the point estimate,
    per family <= 0.02 and overall <= 0.03 (Wilson upper bounds printed). Under D7's m when ``d7_known``; otherwise
    the m = 1 and m = 2 readings must BOTH pass."""
    rules = ["flags"] if d7_known else ["flags_m1", "flags_m2"]
    rows: Dict[str, Any] = {}
    ok_all = True
    for m in O.MODELS:
        res = by_model.get(m) or []
        row: Dict[str, Any] = {"n": len(res)}
        for key in rules:
            r = rates(res, key) if res else None
            fam_ok = bool(r) and all(r[f]["full"] <= C.GATE_PER_FAMILY for f in FAMS)
            over_ok = bool(r) and r["any"]["full"] <= C.GATE_OVERALL
            row[key] = {"rates": r, "per_family_ok": fam_ok, "overall_ok": over_ok}
            ok_all &= fam_ok and over_ok
        rows[m] = row
    conditions = {
        "all_five_models": all(m in by_model for m in O.MODELS),
        "studies_at_least_5000": all(len(by_model.get(m) or []) >= C.GATE_MIN_STUDIES for m in O.MODELS),
        "draws_at_least_2000": draws >= C.MIN_DRAWS_CALIBRATION,
        "scorer_is_the_frozen_one": bool(frozen_scorer_sha256) and frozen_scorer_sha256 == scorer_sha256,
        "sanity_q30_met": sanity_ok(sanity or {}, list(testable) if testable is not None else list(FAMS)),
    }
    status = "GATE" if all(conditions.values()) else "NOT_GATE"
    return {"status": status, "pass": bool(status == "GATE" and ok_all), "rates_pass": bool(ok_all), "conditions": conditions,
            "criterion": "point estimate: per family <= 0.02, overall <= 0.03 (Wilson 95% upper bounds printed)",
            "rules": rules, "sanity_q30": dict(sanity or {}), "models": rows}


# ── v1.2 K12: remedies triggered by check (a) alone ───────────────────────────────────────────────────────
K12_LIMIT = 0.035
K12_STEP = 0.025


def k12_check(by_model: Mapping[str, Sequence[Mapping[str, Any]]]) -> Dict[str, Any]:
    """Rate of p1 <= 0.025 for (a) alone, per family and model (nominal 0.025). Trigger: under N1 or N4 in any
    family -> F3 step 1 (age-adjusted coverage), then step 2; under N2 in the transit family -> F3 step 3."""
    rows: Dict[str, Any] = {}
    triggers: List[str] = []
    for m, res in by_model.items():
        rows[m] = {}
        for f in FAMS:
            v = [r[f]["p1"] for r in res if r[f]["p1"] is not None]
            rate = (sum(1 for x in v if x <= K12_STEP) / len(v)) if v else None
            rows[m][f] = {"rate_p1_le_0.025": rate, "n": len(v)}
            if rate is not None and rate > K12_LIMIT:
                if m in ("N1", "N4"):
                    triggers.append(f"{m}/{f}: F3 step 1 (age adjustment) then step 2")
                if m == "N2" and f == C.FAMILY_TRANSIT:
                    triggers.append(f"{m}/{f}: F3 step 3 (whole-year shifts in 10-year blocks)")
    return {"limit": K12_LIMIT, "nominal": K12_STEP, "rows": rows, "triggers": triggers, "triggered": bool(triggers)}
