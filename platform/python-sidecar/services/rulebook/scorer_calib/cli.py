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
    if getattr(args, "admission", None):  # the step-5 artefacts, every file hash-checked against TIMELINES_MANIFEST.json
        from ..scorer.inputs import AdmissionInputs

        adm = AdmissionInputs(args.admission)
        tl = {f: adm.timelines(f) for f in C.FAMILIES}
    else:
        tl = load_timelines(args.timelines)
    units = {f: units_from_manifest(man, tab, f) for f in C.FAMILIES}
    gate: Dict[str, Any] = {}
    for f in C.FAMILIES:
        ctx, rep = build_family_context(f, tl[f], units[f])
        gate[f] = ctx.gate_drop
    prof = O.declared_profile(len(tl[C.FAMILY_DASHA]), mean=args.mean_per_chart)
    if getattr(args, "count_blind", None):  # sealed counts, hash-checked against COUNT_BLIND_RUN.json
        from ..scorer.inputs import read_count_blind

        prof = O.profile_from_count_blind(read_count_blind(args.count_blind), [t.code for t in tl[C.FAMILY_TRANSIT]])
    cal = H.Calibration(tl, units, gate, prof, draws=args.draws, seed=args.seed)
    cal.warm(args.warm)
    return cal


def _write(path: Path, obj: Any) -> None:
    data = (json.dumps(obj, sort_keys=True, indent=1, default=float) + "\n").encode()
    path.write_bytes(data)
    os.chmod(path, 0o600)


def _hashes(out: Path, extra: Dict[str, Any]) -> None:
    files = {p.name: _sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "HASHES.json"}
    import platform

    _write(out / "HASHES.json", {"scorer_source_sha256": C.source_sha256(), "simulator_source_sha256": sim_sha(), "files": files,
                                 "python": platform.python_version(), "numpy": np.__version__, **extra})


def cmd_gate(a) -> int:
    """F2 gate (v1.1 F2, v1.2 K12, SUR-RB-35/37): N0-N4 null studies plus the q = 30% sanity check under N0."""
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    cal = _load(a)
    if a.d7_known:  # review N6: the single m that D7 fixed applies to every study
        cal.fixed_testable = {f: f in a.testable.split(",") for f in C.FAMILIES}
    for spec in filter(None, (a.donor_rules or "").split(";")):  # e.g. "dasha:b=p2_90,c=m3" (sealed at D7, v1.5 P1)
        fam, kv = spec.split(":")
        for item in kv.split(","):
            chk, rule = item.split("=")
            cal.donor_rules[fam][chk] = rule

    def run_models(tag: str) -> Dict[str, List[Dict[str, Any]]]:
        bym: Dict[str, List[Dict[str, Any]]] = {}
        t0 = time.time()
        for m in a.models.split(","):
            p = out / f"studies_{m}_q0{tag}.jsonl"
            if p.exists():
                p.unlink()
            bym[m] = H.run_many(cal, [(m, i, 0.0, C.FAMILY_DASHA, False, a.threshold) for i in range(a.studies)], a.workers, str(p))
            os.chmod(p, 0o600)
            print(m, tag or "base", "done", round(time.time() - t0), "s", flush=True)
        return bym

    by_model = run_models("")
    p3 = H.p3_check(by_model, cal.donor_rules)
    p3_history = [p3]
    untestable: List[str] = []
    if not p3["ok"]:  # v1.5 P3: raise the bar to 95% for the failing P2 checks and re-run once
        for f, chk in p3["failing"]:
            cal.donor_rules[f][chk] = "p2_95"
        by_model = run_models("_p2_95")
        p3 = H.p3_check(by_model, cal.donor_rules)
        p3_history.append(p3)
        untestable = sorted({f for f, _chk in p3["failing"]})  # still failing: the family is untestable (K11)
    testable = [f for f in a.testable.split(",") if f]
    key = "flags" if a.d7_known else "flags_m2"
    sanity: Dict[str, float] = {}
    for target in testable:  # SUR-RB-39 (4): each D7-testable family, effect planted in it, q = 30%, N0
        p = out / f"sanity_N0_q30_{target}.jsonl"
        if p.exists():
            p.unlink()
        res = H.run_many(cal, [("N0", i, 0.30, target, False, a.threshold) for i in range(a.sanity_studies)], a.workers, str(p))
        os.chmod(p, 0o600)
        sanity[target] = H.rates(res, key)[target]["full"]
    q_curves: Dict[str, Dict[str, float]] = {}
    for target in testable:
        if sanity[target] < C.GATE_SANITY_POWER:  # shortfall: the q-curve, to tell low power from a defect
            q_curves[target] = {}
            for q in (0.10, 0.20, 0.30, 0.40):
                rq = H.run_many(cal, [("N0", i, q, target, False, a.threshold) for i in range(a.sanity_studies)], a.workers, None)
                q_curves[target][str(q)] = H.rates(rq, key)[target]["full"]
    unit_tests = json.loads(Path(a.unit_test_report).read_text()) if a.unit_test_report else {"failed": None}
    rep = H.sanity_report(sanity, testable, q_curves, unit_tests)
    _write(out / "SANITY_Q30.json", rep)
    res = H.f2_gate(by_model, draws=a.draws, scorer_sha256=C.source_sha256(), frozen_scorer_sha256=a.frozen_scorer_sha, d7_known=a.d7_known, sanity=sanity, testable=[f for f in testable if f not in untestable], untestable=untestable)
    res["p3"] = p3_history
    k12 = H.k12_check(by_model)
    status = res["status"] if a.step5_hash else "PROVISIONAL_NOT_STEP5_INPUTS"
    _write(out / "F2_GATE.json", {"status": status, "step5_hash": a.step5_hash, "threshold": a.threshold, "draws": a.draws, "studies_per_model": a.studies, "gate": res, "k12": k12})
    _hashes(out, {"draws": a.draws, "studies": a.studies, "seed": a.seed, "status": status, "threshold": a.threshold})
    print("K12 remedies:", k12["triggers"] or "not triggered")
    print("F2", status, "rates", "PASS" if res["rates_pass"] else "FAIL", "conditions", res["conditions"])
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
            tasks = [(a.model, i, q, target, sparse, a.threshold) for q in qs for i in range(a.studies)]
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
    _write(out / "F4_POWER.json", {"status": "FINAL_INPUTS" if a.step5_hash else "PROVISIONAL_NOT_STEP5_INPUTS", "threshold": a.threshold, "q_definition": "v1.2 K9", "model": a.model, "draws": a.draws, "mean_per_chart": a.mean_per_chart, "table": table})
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
    cb = None
    if a.count_blind:
        from ..scorer.inputs import read_count_blind

        cb = read_count_blind(a.count_blind)
    for t in (3, 5, 8):
        res = H.run_many(cal, [("N4", i, 0.10, C.FAMILY_DASHA, False, t) for i in range(a.studies)], a.workers, None)
        rate = H.rates(res)[C.FAMILY_DASHA]["full"]
        if cb is not None:  # the real choice: A7 from the sealed counts of this threshold's pool (v1.2 K8, review M7)
            from ..scorer.inputs import d7_decisions

            meets = bool(d7_decisions(cb, t, C.FAMILY_DASHA)["a7_ok"])
            share = None
        else:  # synthetic counts: A7 on scored-APPLICABLE daśā counts, judged per sample, all samples must meet it
            per = [r[C.FAMILY_DASHA]["n_applicable"] >= C.MIN_DASHA_EPISODES_FOR_VERDICT and r[C.FAMILY_DASHA]["charts_applicable"] >= C.MIN_CHARTS_FOR_VERDICT for r in res]
            share = float(np.mean(per))
            meets = bool(all(per))
        rows[str(t)] = {"dasha_strong_rate_q10": rate, "meets_A7": meets, "share_of_samples_meeting_A7": share}
        print(t, rows[str(t)], flush=True)
    ok = [t for t in (3, 5, 8) if rows[str(t)]["meets_A7"]]
    best = max(ok, key=lambda t: (round(rows[str(t)]["dasha_strong_rate_q10"], 12), t)) if ok else None
    _write(out / "A6_THRESHOLD.json", {"provisional": not a.step5_hash, "counts": "count_blind aggregates" if a.count_blind else "declared stand-in profile", "q_definition": "v1.2 K9 (top 20% coverage windows)", "studies": a.studies, "rows": rows, "chosen": best})
    _hashes(out, {"draws": a.draws, "studies": a.studies, "seed": a.seed})
    print("A6 threshold:", best)
    return 0


def cmd_donor_diagnostic(a) -> int:
    """Review N2 / v1.5 P1: per family, the charts keeping at least 5 donors under (b) and (c) (v1.4 M3), the K11 floor
    status and the P2 trigger. Reads the step-5 timelines (hash-checked) and an episodes file of windows
    [{chart_id, family, area, direction, grade: day|month, lo: ISO date, hi: ISO date}]; that file is built from the
    occurrences, so this runs ONLY inside the count_blind boundary. Emits counts and decisions, nothing else."""
    from datetime import date as _date

    from ..scorer.core import donor_diagnostic
    from ..scorer.inputs import AdmissionInputs
    from ..scorer.model import Episode

    adm = AdmissionInputs(a.admission)
    man = json.loads(Path(a.manifest).read_text())
    tab = json.loads(Path(a.clusters).read_text())
    rows = json.loads(Path(a.episodes).read_text())
    out: Dict[str, Any] = {"timelines_manifest_sha256": adm.manifest_sha256, "episodes_file_sha256": _sha(Path(a.episodes))}
    for fam in C.FAMILIES:
        ids = adm.admitted()
        tls = adm.timelines(fam, ids)
        ctx, _rep = build_family_context(fam, tls, units_from_manifest(man, tab, fam))
        pos = {c: i for i, c in enumerate(ids)}
        eps = []
        for r in rows:
            if r["family"] == fam and r["chart_id"] in pos and r["direction"] in C.POLARITY_OF_DIRECTION:
                eps.append(Episode(pos[r["chart_id"]], r["area"], r["direction"], {"day": C.G1, "month": C.G2}[r["grade"]],
                                   _date.fromisoformat(r["lo"]).toordinal(), _date.fromisoformat(r["hi"]).toordinal()))
        out[fam] = donor_diagnostic(ctx, eps)
    p = Path(a.out)
    _write(p, out)
    print(json.dumps({f: {k: out[f][k] for k in ("b", "c", "donor_rules")} for f in C.FAMILIES}, sort_keys=True))
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
        p.add_argument("--timelines", default=None, help="saved calibration timelines (surrogate or provisional)")
        p.add_argument("--admission", default=None, help="step-5 admission directory (admission-v1_1); overrides --timelines")
        p.add_argument("--count-blind", default=None, help="count_blind output directory (sealed aggregates)")
        p.add_argument("--manifest", required=True)
        p.add_argument("--clusters", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--studies", type=int, default=studies)
        p.add_argument("--draws", type=int, default=C.MIN_DRAWS_CALIBRATION)
        p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
        p.add_argument("--mean-per-chart", type=float, default=O.DECLARED_MEAN_PER_CHART)
        p.add_argument("--seed", type=int, default=20261030)
        p.add_argument("--warm", type=int, default=150)
        p.add_argument("--step5-hash", default=None, help="hash of the step-5 admission artefacts; without it every output is labelled PROVISIONAL")
        p.add_argument("--threshold", type=int, default=0, help="exclusion-5 threshold (3, 5, 8) applied per family; 0 = none")
    g = sub.add_parser("gate"); common(g, C.GATE_MIN_STUDIES)
    g.add_argument("--models", default=",".join(O.MODELS))
    g.add_argument("--sanity-studies", type=int, default=500)
    g.add_argument("--frozen-scorer-sha", default=None, help="sha256 of the frozen scorer; without it the status is NOT_GATE")
    g.add_argument("--d7-known", action="store_true", help="D7 has fixed m; otherwise m = 1 and m = 2 must both pass")
    g.add_argument("--testable", default=",".join(C.FAMILIES), help="the families D7 makes testable (comma list)")
    g.add_argument("--donor-rules", default="", help='v1.5 P1 decisions from D7, e.g. "dasha:b=p2_90,c=m3;transit:b=m3,c=m3"')
    g.add_argument("--unit-test-report", default=None, help='JSON {"passed": n, "failed": n} of the scorer test run')
    g.set_defaults(fn=cmd_gate)
    p = sub.add_parser("power"); common(p, 400)
    p.add_argument("--qs", default="0.05,0.10,0.15,0.20,0.30"); p.add_argument("--model", default="N4"); p.set_defaults(fn=cmd_power)
    a6 = sub.add_parser("a6"); common(a6, 300); a6.set_defaults(fn=cmd_a6)
    dd = sub.add_parser("donor-diagnostic")
    dd.add_argument("--admission", required=True)
    dd.add_argument("--manifest", required=True)
    dd.add_argument("--clusters", required=True)
    dd.add_argument("--episodes", required=True)
    dd.add_argument("--out", required=True)
    dd.set_defaults(fn=cmd_donor_diagnostic)
    b = sub.add_parser("build-timelines")
    b.add_argument("--births", required=True); b.add_argument("--people", required=True); b.add_argument("--manifest", required=True)
    b.add_argument("--bundle", required=True); b.add_argument("--sky", required=True); b.add_argument("--out", required=True); b.set_defaults(fn=cmd_build)
    a = ap.parse_args(argv)
    return int(a.fn(a))


if __name__ == "__main__":
    sys.exit(main())
