"""Part F calibration - command line.

  python -m services.rulebook.scorer_calib.cli build-timelines --births surrogate|FILE --people CSV --manifest M --bundle B --sky S --out DIR
  python -m services.rulebook.scorer_calib.cli gate  --timelines DIR --manifest M --clusters T --out OUT [--studies 5000] [--draws 2000] [--workers N] [--mean-per-chart 24]
  python -m services.rulebook.scorer_calib.cli power --timelines DIR --manifest M --clusters T --out OUT [--studies 400] ...

Every output file is written 0600 and listed with its sha256 in ``OUT/HASHES.json`` together with the scorer and
simulator source hashes. Results depend on (seed, study index) only, never on the worker count.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from ..scorer import config as C
from ..scorer.footprint import build_family_context
from ..scorer.model import units_from_manifest
from ..scorer.outcome import mde_report
from . import harness as H
from . import occurrences as O
from . import source_sha256 as sim_sha


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(args) -> H.Calibration:
    from .timelines import load_timelines

    man = json.loads(Path(args.manifest).read_text())
    tab = json.loads(Path(args.clusters).read_text())
    tl = load_timelines(args.timelines)
    units = {f: units_from_manifest(man, tab, f) for f in C.FAMILIES}
    gate: Dict[str, Any] = {}
    for f in C.FAMILIES:
        ctx, rep = build_family_context(f, tl[f], units[f])
        gate[f] = ctx.gate_drop
    prof = O.declared_profile(len(tl[C.FAMILY_DASHA]), mean=args.mean_per_chart)
    if getattr(args, "counts_file", None):
        prof = O.profile_from_counts_file(args.counts_file, [t.code for t in tl[C.FAMILY_TRANSIT]])
    cal = H.Calibration(tl, units, gate, prof, draws=args.draws, seed=args.seed)
    cal.warm(args.warm)
    return cal


def _write(path: Path, obj: Any) -> None:
    data = (json.dumps(obj, sort_keys=True, indent=1, default=float) + "\n").encode()
    path.write_bytes(data)
    os.chmod(path, 0o600)


def _hashes(out: Path, extra: Dict[str, Any]) -> None:
    files = {p.name: _sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "HASHES.json"}
    _write(out / "HASHES.json", {"scorer_source_sha256": C.source_sha256(), "simulator_source_sha256": sim_sha(), "files": files, **extra})


def cmd_gate(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    cal = _load(a)
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    t0 = time.time()
    for m in a.models.split(","):
        p = out / f"studies_{m}_q0.jsonl"
        if p.exists():
            p.unlink()
        by_model[m] = H.run_many(cal, [(m, i, 0.0, C.FAMILY_DASHA, False, a.threshold) for i in range(a.studies)], a.workers, str(p))
        os.chmod(p, 0o600)
        print(m, "done", round(time.time() - t0), "s", flush=True)
    res = H.f2_gate(by_model, min_studies=min(a.studies, C.GATE_MIN_STUDIES) if a.allow_fewer else C.GATE_MIN_STUDIES)
    k12 = H.k12_check(by_model)
    status = "FINAL_INPUTS" if a.step5_hash else "PROVISIONAL_NOT_STEP5_INPUTS"
    _write(out / "F2_GATE.json", {"status": status, "step5_hash": a.step5_hash, "threshold": a.threshold, "draws": a.draws, "studies_per_model": a.studies, "mean_per_chart": a.mean_per_chart, "gate": res, "k12": k12})
    _hashes(out, {"draws": a.draws, "studies": a.studies, "seed": a.seed, "status": status, "threshold": a.threshold})
    print("K12 remedies:", k12["triggers"] or "not triggered")
    print(json.dumps({m: {k: v for k, v in r["rates"].items() if k != "n"} for m, r in res["models"].items()}, indent=1, default=float))
    print("F2 GATE", "PASS" if res["pass"] else "FAIL")
    return 0 if res["pass"] else 2


def cmd_power(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    cal = _load(a)
    qs = [float(x) for x in a.qs.split(",")]
    table: Dict[str, Any] = {}
    for sparse in (False, True):
        for target in C.FAMILIES:
            key = f"{target}{'_sparse' if sparse else ''}"
            tasks = [(a.model, i, q, target, sparse) for q in qs for i in range(a.studies)]
            p = out / f"power_{key}.jsonl"
            if p.exists():
                p.unlink()
            res = H.run_many(cal, tasks, a.workers, str(p))
            os.chmod(p, 0o600)
            row = {}
            for q in qs:
                rr = [r for r in res if r["q"] == q]
                rt = H.rates(rr)
                row[str(q)] = {"n": len(rr), "target_full": rt[target]["full"], "target_a": rt[target]["a"], "other_full": rt[[f for f in C.FAMILIES if f != target][0]]["full"], "any_full": rt["any"]["full"]}
            curve = {"q": qs, "power": [row[str(q)]["target_full"] for q in qs]}
            table[key] = {"by_q": row, "mde": mde_report(curve["q"], curve["power"])}
            print(key, json.dumps(table[key]["mde"]), flush=True)
    _write(out / "F4_POWER.json", {"model": a.model, "draws": a.draws, "mean_per_chart": a.mean_per_chart, "table": table})
    _hashes(out, {"draws": a.draws, "studies_per_cell": a.studies, "seed": a.seed})
    return 0


def cmd_a6(a) -> int:
    """v1.1 A6: the exclusion-5 threshold (3, 5 or 8) with the highest daśā STRONG rate at q = 10% (N4), among the
    thresholds whose primary set meets A7 (20 charts, 400 scored daśā episodes); ties go to the higher threshold.
    PROVISIONAL while the per-chart counts are the declared stand-in: the real choice is made from real counts."""
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    cal = _load(a)
    rows: Dict[str, Any] = {}
    for t in (3, 5, 8):
        res = H.run_many(cal, [("N4", i, 0.10, C.FAMILY_DASHA, False, t) for i in range(a.studies)], a.workers, None)
        n_d = float(np.mean([r[C.FAMILY_DASHA]["n"] for r in res]))
        ch = float(np.mean([r[C.FAMILY_DASHA]["charts"] for r in res]))
        rate = H.rates(res)[C.FAMILY_DASHA]["full"]
        rows[str(t)] = {"dasha_strong_rate_q10": rate, "mean_scored_dasha_episodes": n_d, "mean_charts": ch, "meets_A7": bool(n_d >= C.MIN_DASHA_EPISODES_FOR_VERDICT and ch >= C.MIN_CHARTS_FOR_VERDICT)}
        print(t, rows[str(t)], flush=True)
    ok = [t for t in (3, 5, 8) if rows[str(t)]["meets_A7"]]
    best = max(ok, key=lambda t: (round(rows[str(t)]["dasha_strong_rate_q10"], 12), t)) if ok else None
    _write(out / "A6_THRESHOLD.json", {"provisional": not a.step5_hash, "counts": "K2 aggregates" if a.counts_file else "declared stand-in profile", "q_definition": "v1.2 K9 (top 20% coverage windows)", "studies": a.studies, "rows": rows, "chosen": best})
    _hashes(out, {"draws": a.draws, "studies": a.studies, "seed": a.seed})
    print("A6 threshold:", best)
    return 0


def cmd_build(a) -> int:
    from .births import births_from_file, births_sha256, read_permitted_columns, surrogate_births
    from .timelines import InputsBundle, build_one, save_chart

    births = surrogate_births(read_permitted_columns(a.people)) if a.births == "surrogate" else births_from_file(a.births)
    inp = InputsBundle(a.manifest, a.bundle, a.sky)
    tally: Dict[str, int] = {}
    for b in births:
        r = build_one(b, inp)
        k = r.get("excluded", "admitted")
        tally[k] = tally.get(k, 0) + 1
        if "excluded" not in r:
            save_chart(r, a.out)
    print(json.dumps({"births_sha256": births_sha256(births), "surrogate": a.births == "surrogate", "tally": tally}, sort_keys=True))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rulebook-scorer-calib")
    sub = ap.add_subparsers(dest="cmd", required=True)
    def common(p, studies):
        p.add_argument("--timelines", required=True)
        p.add_argument("--manifest", required=True)
        p.add_argument("--clusters", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--studies", type=int, default=studies)
        p.add_argument("--draws", type=int, default=C.MIN_DRAWS_CALIBRATION)
        p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
        p.add_argument("--mean-per-chart", type=float, default=O.DECLARED_MEAN_PER_CHART)
        p.add_argument("--seed", type=int, default=20261030)
        p.add_argument("--warm", type=int, default=150)
        p.add_argument("--counts-file", default=None, help="K2 aggregate counts (chart_code,area,direction,grade,count); else the declared stand-in")
        p.add_argument("--step5-hash", default=None, help="hash of the step-5 admission artefacts; without it every output is labelled PROVISIONAL")
        p.add_argument("--threshold", type=int, default=0, help="exclusion-5 threshold (3, 5, 8) applied per family; 0 = none")
    g = sub.add_parser("gate"); common(g, C.GATE_MIN_STUDIES)
    g.add_argument("--models", default=",".join(O.MODELS)); g.add_argument("--allow-fewer", action="store_true"); g.set_defaults(fn=cmd_gate)
    p = sub.add_parser("power"); common(p, 400)
    p.add_argument("--qs", default="0.05,0.10,0.15,0.20,0.30"); p.add_argument("--model", default="N4"); p.set_defaults(fn=cmd_power)
    a6 = sub.add_parser("a6"); common(a6, 300); a6.set_defaults(fn=cmd_a6)
    b = sub.add_parser("build-timelines")
    b.add_argument("--births", required=True); b.add_argument("--people", required=True); b.add_argument("--manifest", required=True)
    b.add_argument("--bundle", required=True); b.add_argument("--sky", required=True); b.add_argument("--out", required=True); b.set_defaults(fn=cmd_build)
    a = ap.parse_args(argv)
    return int(a.fn(a))


if __name__ == "__main__":
    sys.exit(main())
