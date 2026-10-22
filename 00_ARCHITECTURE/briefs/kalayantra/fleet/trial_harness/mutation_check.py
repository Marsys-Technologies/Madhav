"""Planted-reversion check for the harness's own claims (D-OWNER-TESTS-20261016: ONE reversion per distinct claim, each must make the suite FAIL).
Each mutation is applied to a COPY of the harness under the job folder; the repository and the harness itself are never touched.  Usage:
  python -I mutation_check.py <copies_dir> [mutation_report.json] [id-prefix ...]    (id prefixes select a subset, e.g. A3 N W)"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PY = "/Users/Dev/kalayantra/venv/bin/python"

# (id, claim, file, old, new) — `old` must occur exactly once in `file`
M = [
 ("G1-a", "G-1 windows_total per class must equal the baseline", "gates.py", 'if b is not None and r != b:', 'if b is not None and r != r:'),
 ("G1-b", "G-1 anomalies must all be zero", "gates.py", 'check("anomalies are all zero", not nonzero, nonzero or 0, 0)', 'check("anomalies are all zero", True, nonzero or 0, 0)'),
 ("G1-c", "G-1 the trial ran exactly the 12 classes", "gates.py", 'sorted(want) == list(got)', 'True'),
 ("G1-d", "G-1 a missing anomaly detector is not a zero", "gates.py", 'if missing:\n        checks.append(check("anomalies are all zero", None', 'if False:\n        checks.append(check("anomalies are all zero", None'),
 ("G2-a", "G-2 each wiring code must have zero blank windows", "gates.py", 'any_.get(code, 0) == 0', 'True'),
 ("G2-b", "G-2 primary reasons inside the closed set", "gates.py", 'check("every primary blank reason is inside the closed allowed set", not outside_p', 'check("every primary blank reason is inside the closed allowed set", True'),
 ("G2-c", "G-2 secondary reasons inside the closed set", "gates.py", 'not outside_s,\n', 'True,\n'),
 ("G2-d", "G-2 the allowed set follows the owner's answers", "gates.py", 'all(q in answers and answers[q] in opts for q, opts in when.items())', 'all(q in answers for q, opts in when.items())'),
 ("G3-a", "G-3 share floors", "gates.py", 'n / w >= floor', 'True'),
 ("G3-b", "G-3 solver_budget_exhausted cap", "gates.py", 'n_budget / total <= cap', 'True'),
 ("G3-c", "G-3 the floor follows the owner's answer", "gates.py", 'ans = answers_of(profile).get(spec["by"])', 'ans = "a"'),
 ("G4-a", "G-4 verdict must be PASSED", "gates.py", 'None if not st else st == "PASSED"', 'None if not st else True'),
 ("G4-b", "G-4 numbered_windows > 0", "gates.py", 'None if nb is None else nb > 0', 'None if nb is None else True'),
 ("G4-c", "G-4 no blocking judgment flag", "gates.py", 'ATTESTATION_BLOCKING_FLAG not in flags, flags', 'True, flags'),
 ("G4-d", "G-4 attested counts equal the live recount", "gates.py", 'att.get("windows") == live.get("windows") and att.get("numbered") == live.get("numbered")', 'True'),
 ("G4-e", "G-4 UNVERIFIED windows = 0", "gates.py", 'None if un is None else un == 0', 'None if un is None else True'),
 ("G4-f", "G-4 every class VERIFIED", "gates.py", 'None if not cls else not not_verified', 'None if not cls else True'),
 ("G5-a", "G-5 projection scales the 12-class trial to 26 classes", "gates.py", '(base_s + solver_s) * scale * r * speed', '(base_s + solver_s) * r * speed'),
 ("G5-b", "G-5 writer time must be under the limit", "gates.py", 'proj["projected_writer_s"] <= proj["limit_s"]', 'True'),
 ("G5-c", "G-5 r = century horizon / trial horizon", "gates.py", 'r = (days_cent / days_trial) if days_trial and days_cent else None', 'r = 1.0'),
 ("G5-d", "G-5 verifier solver check under 600 s per class", "gates.py", 'projected <= per_class_cap', 'True'),
 ("G5-e", "G-5 solver seconds are the window phase, base is the rest", "gates.py", 'sum(v for k, v in kinds.items() if k != "window")', 'sum(v for k, v in kinds.items())'),
 ("G6-a", "G-6 sample >= 3 % of numbered windows", "gates.py", '(crosscheck.get("sampled") or 0) >= need', 'True'),
 ("G6-b", "G-6 solver >= legacy sampler", "gates.py", 'check("solver value ≥ legacy sampler value on every window", not sv', 'check("solver value ≥ legacy sampler value on every window", True'),
 ("G6-c", "G-6 brute force equals stored", "gates.py", 'check("brute force (1 s) equals the stored value on the dense subset", not dv', 'check("brute force (1 s) equals the stored value on the dense subset", True'),
 ("G6-d", "G-6 value at the stored peak", "gates.py", 'check("the recomputed objective at the stored peak equals the stored value", not ri', 'check("the recomputed objective at the stored peak equals the stored value", True'),
 ("G6-e", "G-6 every top-mixed window checked", "gates.py", 'None if req is None or got is None else got == req', 'None if req is None or got is None else True'),
 ("G6-f", "G-6 sample drawn from this trial's numbered windows", "gates.py", 'crosscheck.get("numbered_windows") == n_num,', 'True,'),
 ("G6-g", "G-6 zero numbered windows is not a vacuous pass", "gates.py", '    if not n_num:\n        checks.append(check("there are numbered windows', '    if False:\n        checks.append(check("there are numbered windows'),
 ("G6-h", "G-6 an incomplete cross-check is not a pass", "gates.py", 'crosscheck.get("status") == "COMPLETE", crosscheck.get("status")', 'True, crosscheck.get("status")'),
 ("G7-a", "G-7 window rows byte-identical", "gates.py", 'bool(a.get("sha256")) and a.get("sha256") == b.get("sha256")', 'True'),
 ("G7-b", "G-7 both runs at the same head", "gates.py", '_get(report, "code", "head") == _get(second, "code", "head") and bool(_get(report, "code", "head"))', 'True'),
 ("G8-a", "G-8 module digests equal", "gates.py", 'check("every module file digest is equal", not differ', 'check("every module file digest is equal", True'),
 ("G8-b", "G-8 same set of modules", "gates.py", 'not only_t and not only_d', 'True'),
 ("V-a", "a placeholder profile is never dispatchable", "gates.py", '    elif not final:\n        overall = "ALL_GATES_PASS_PROFILE_NOT_FINAL"', '    elif False:\n        overall = "ALL_GATES_PASS_PROFILE_NOT_FINAL"'),
 ("V-b", "an unevaluated gate is never a pass overall", "gates.py", '    elif unevaluated:\n        overall = "NO_DISPATCH_NOT_EVALUATED"', '    elif False:\n        overall = "NO_DISPATCH_NOT_EVALUATED"'),
 ("V-c", "NOT_EVALUATED does not roll up to PASS", "gates.py", '    if NOT_EVALUATED in statuses:\n        return NOT_EVALUATED', '    if False:\n        return NOT_EVALUATED'),
 ("V-d", "a trial whose policy did not take effect is invalid", "gates.py", '_get(report, "policy_effect", "took_effect") is True,', 'True,'),
 ("X-a", "cross-check: a higher value exists (stored < brute force)", "crosscheck.py", 'if stored_value < dm["max"] - tol:', 'if False:'),
 ("X-b", "cross-check: a value that does not exist (stored > brute force)", "crosscheck.py", 'if stored_value > dm["max"] + tol:', 'if False:'),
 ("X-c", "cross-check: stored >= legacy sampler", "crosscheck.py", 'elif stored_value < sm["max"] - tol:', 'elif False:'),
 ("X-d", "cross-check: F(stored peak) = stored value", "crosscheck.py", 'elif abs(fp - stored_value) > tol:', 'elif False:'),
 ("X-e", "cross-check: unknown is never agreement", "crosscheck.py", 'if dm["max"] is None or dm["unknown"]:', 'if False:'),
 ("X-f", "cross-check: sample size is the ceiling of the rate", "crosscheck.py", 'math.ceil(rate * n)', 'math.floor(rate * n)'),
 ("X-g", "cross-check: a timed-out scan is a violation, not a pass", "crosscheck.py", '            rec["violations"].append({"kind": "timeout"', '            pass; rec["x"] = ({"kind": "timeout"'),
 ("X-h", "cross-check: mixed-piece detection", "crosscheck.py", 'return 2 in dirs or {1, -1} <= dirs', 'return False'),
 ("X-i", "cross-check: narrow crests are refined between grid points", "crosscheck.py", 'if vals[i] < top - REFINE_MARGIN:\n                continue', 'continue'),
 ("X-j", "cross-check: legacy-sampler leg runs on every sampled window", "crosscheck.py", '    sm = sampler_max(ws, pieces)\n', '    sm = {"max": stored_value, "instant": None, "unknown": 0}\n'),
]

from mutants_a10 import M10                                  # noqa: E402  the A10.1 (T1B) claims
M = M + M10


def main():
    copies = Path(sys.argv[1])
    report = []
    only = tuple(a for a in sys.argv[3:])                    # optional id prefixes
    for mid, claim, fname, old, new in M:
        if only and not mid.startswith(only):
            continue
        dst = copies / mid
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(HERE, dst, ignore=shutil.ignore_patterns("__pycache__", "mutants", "*.part"))
        src = (dst / fname).read_text()
        if src.count(old) != 1:
            report.append({"id": mid, "claim": claim, "result": "BAD_MUTATION", "occurrences": src.count(old)})
            continue
        (dst / fname).write_text(src.replace(old, new))
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "KY_TEST_CHECKOUT": os.environ.get("KY_TEST_CHECKOUT", str(HERE.parent / "code_od1"))}
        r = subprocess.run([PY, "-I", "-m", "pytest", "-p", "no:cacheprovider", f"--basetemp={copies}/_bt_{mid}", "-q", "-x", "tests"], cwd=dst, capture_output=True, text=True, env=env, timeout=600)
        failed = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
        report.append({"id": mid, "claim": claim, "result": "KILLED" if r.returncode != 0 else "SURVIVED", "pytest_exit": r.returncode, "first_failure": failed[0][:140] if failed else None})
        print(f"{report[-1]['result']:<9}{mid:<7}{claim}", flush=True)
    if len(sys.argv) > 2 and sys.argv[2] != "-":
        Path(sys.argv[2]).write_text(json.dumps(report, indent=1) + "\n")
    bad = [x for x in report if x["result"] != "KILLED"]
    print(f"{len(report) - len(bad)} of {len(report)} planted reversions killed; {len(bad)} not")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
