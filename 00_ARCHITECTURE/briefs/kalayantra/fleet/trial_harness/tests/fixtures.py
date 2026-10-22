"""A fully-passing synthetic world for the gate evaluator tests: 12 classes, per-path shares above every floor, a complete verification / cross-check,
a second identical run, equal head digests.  Each test breaks exactly ONE claim."""
import copy
import json
from datetime import datetime
from pathlib import Path

import gates

HARNESS = Path(__file__).resolve().parents[1]
CLASSES = list(gates.TRIAL_CLASSES_12)
PATH_WINDOWS = {"P1": 600, "P2": 700, "P3": 100, "P4": 400}      # per 12 classes (sums to 1,800 windows)
PATH_NUMBERED = {"P1": 300, "P2": 500, "P3": 98, "P4": 396}      # shares .50 / .714 / .98 / .99


def profile(**over):
    p = json.loads((HARNESS / "gate_profile.plan_defaults.json").read_text())
    p.update(over)
    if p.get("final"):                               # a final profile must state the century horizon (G-5)
        p["runtime"]["century_horizon"] = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
    return p


def baseline():
    return {"schema": "ky.trial_baseline/2", "classes": {c: {"windows_total": 150, "blank": 150} for c in CLASSES}, "totals": {"windows_total": 1800}}


QUIET_LOAD = 0.2         # 1-minute load average per core during every writer stage of the synthetic trial (HARNESS-3.2, D-10: the G-5 validity detector reads it)


def report():
    classes = {c: {"windows_total": 150} for c in CLASSES}
    paths = {p: {"windows": PATH_WINDOWS[p], "numbered": PATH_NUMBERED[p]} for p in PATH_WINDOWS}
    blank_total = sum(PATH_WINDOWS.values()) - sum(PATH_NUMBERED.values())          # 1800 - 1294 = 506
    primary = {"state_boundaries_incomplete": 6, "agent_nature_node_undecided": 300, "node_obstruction_undecided": 200}
    assert sum(primary.values()) == blank_total
    return {
        "schema": "ky.trial_report/2",
        "config": {"classes": CLASSES, "requested_result_policy": "window_qualification/1"},
        "classes": classes,
        "totals": {"windows_total": 1800, "with_peak": sum(PATH_NUMBERED.values()), "blank": blank_total, "blank_reasons": dict(primary),
                   "unresolved_factors_in_blank_windows": {k: {"windows": v, "members": v} for k, v in primary.items()}},
        "anomalies": {k: 0 for k in gates.ANOMALY_FIELDS},
        "policy_effect": {"took_effect": True},
        "build": {"defects": [], "aborted": None, "dead_classes": []},
        "paths": paths,
        "reason_windows_any": dict(primary),
        "horizon": {"start": "1998-01-01T00:00:00+00:00", "end": "2084-02-05T00:00:00+00:00", "days": (datetime(2084, 2, 5) - datetime(1998, 1, 1)).total_seconds() / 86400.0},
        "runtime_s": {"by_step_kind": {"rules": 5.0, "convention": 3.0, "body": 330.0, "manifest": 2.0, "snapshot": 3.0, "inventory": 6.0, "record": 800.0,
                                       "window": 50.0, "verify": 1.0}},
        "effective_wall": {"schema": "ky.effective_wall/1", "stages": {f"build:{k}": {"wall_s": 1.0, "lock_wait_s": 0.0, "compute_s": 1.0, "max_load_per_core": QUIET_LOAD}
                                                                     for k in ("rules", "body", "record", "window")}},
        "code": {"head": "a" * 40, "implementation_modules": {"services.gochara_kernel.window_sweep": "1" * 64, "services.gochara_kernel.window_verifier": "2" * 64}},
        "window_rows_digest": {"sha256": "d" * 64, "windows": 1800},
        "verification": {"ran": True, "source": "synthetic",
                         "generation_verdict": {"status": "PASSED", "numbered_windows": 1294, "judgment_flags": [], "problems": []},
                         "attestation_recount": {"attested": {"windows": 1800, "numbered": 1294}, "live": {"windows": 1800, "numbered": 1294}},
                         "unverified_windows": 0,
                         "classes": {c: {"status": "VERIFIED", "window_check_s": 20.0} for c in CLASSES}},
        "crosscheck": {"status": "COMPLETE", "seed": 7, "numbered_windows": 1294, "sampled": 39, "top_mixed_requested": 4, "top_mixed_checked": 4,
                       "sampler_violations": [], "dense_violations": [], "dense": {"windows": 12}, "recompute_inconsistent": []},
    }


def good():
    return report(), baseline(), profile()


def second():
    return copy.deepcopy(report())


def dispatch_modules():
    return dict(report()["code"]["implementation_modules"])


# ── the A10.1 world: the same synthetic trial, now satisfying the G-3 decision table and carrying every A10.1 section ────────────────────────────────
A10_PATH_NUMBERED = {"P1": 560, "P2": 620, "P3": 95, "P4": 390}          # shares .933 / .886 / .95 / .975; P3+P4 .97; ALL .925  (table floors .90/.85/.92/.95/.90/.88)
A10_BLANK = {"state_boundaries_incomplete": 60, "obstructor_residence_unknown": 45, "node_residence_unknown": 30}      # 135 = 1800 - 1665, every reason allowed
TABLE_PATH = HARNESS / "g3_decision_table.json"


def decision_table():
    return gates.load_decision_table(json.loads(TABLE_PATH.read_text()))


def snapshot(geometry="g" * 64, versions=None, tweak=None):
    """A noninterference snapshot built by the harness's own pure function from a tiny synthetic key set."""
    import trial_eval as te
    keys = {"windows": [("bereavement|P1", "1.2.0", '["bereavement","P1","1998-01-01T00:00:00.000000","1998-02-01T00:00:00.000000"]'),
                        ("bereavement|P2", "1.2.0", '["bereavement","P2","1999-01-01T00:00:00.000000","1999-02-01T00:00:00.000000"]')],
            "supports": [("bereavement|P1", "1.2.0", '["bereavement","self","h","a","Sun","conj","o1","karaka","c1","P1","t","admitted","scored","{}"]')],
            "contacts": [("contacts|-", "-", '["c1","1998-01-01T00:00:00.000000",null,null,"0.5"]')],
            "membership": [("bereavement|P1", "1.2.0", '[["w"],["r"]]')]}
    if tweak:
        tweak(keys)
    snap = te.snapshot_from_rows(keys, geometry)
    if versions is not None:
        snap["rule_versions"] = versions
    return snap


def digests(**over):
    import trial_eval as te
    vec = {"registry": "r" * 64, "l0": {"bg_transit_rules": "l" * 64}, "ephemeris": {"backend": "swiss", "swe_version": "2.10", "library_sha256": "s" * 64, "platform": "linux/amd64",
                                                                                   "files": {"sepl_18.se1": "f" * 64}, "probe_digest": "p" * 64},
           "sky_convention": {"id": "kala_v1"}, "node": {"model": "mean"}, "orb_policy": {"admission_digest": "o" * 64, "activity": {"1.3.0": "1.0"}},
           "rulings_digest": "u" * 64, "result_policy": "window_qualification/1", "in_build_verify": False}
    vec.update(over)
    return te.digests_record(vec)


def a10_report():
    r = report()
    n = A10_PATH_NUMBERED
    r["paths"] = {p: {"windows": PATH_WINDOWS[p], "numbered": n[p]} for p in PATH_WINDOWS}
    r["totals"]["with_peak"] = sum(n.values())
    r["totals"]["blank"] = 1800 - sum(n.values())
    r["totals"]["blank_reasons"] = dict(A10_BLANK)
    r["totals"]["unresolved_factors_in_blank_windows"] = {k: {"windows": v, "members": v} for k, v in A10_BLANK.items()}
    r["reason_windows_any"] = dict(A10_BLANK)
    peak = sum(n.values())
    r["verification"]["generation_verdict"]["numbered_windows"] = peak
    r["verification"]["attestation_recount"] = {"attested": {"windows": 1800, "numbered": peak}, "live": {"windows": 1800, "numbered": peak}}
    r["crosscheck"].update({"numbered_windows": peak, "sampled": 50})
    r["digests_record"] = digests()
    r["noninterference"] = snapshot()
    kinds = r["runtime_s"]["by_step_kind"]
    stages = {f"build:{k}": {"wall_s": v, "lock_wait_s": round(v * 0.1, 3), "compute_s": round(v - round(v * 0.1, 3), 3), "max_load_per_core": QUIET_LOAD}
              for k, v in kinds.items() if k != "verify"}
    r["effective_wall"] = {"schema": "ky.effective_wall/1", "stages": stages}
    r["trial_ready"] = trial_ready()
    return r


def trial_ready(head="a" * 40, **over):
    doc = {"predicate": "TRIAL_READY/1", "head_sha": head, "evaluated_at": "2026-10-22T00:00:00Z",
           "checks": [{"id": i, "claim": "c", "value": True, "evidence_ref": "e", "sha256": "0" * 64} for i in gates.TRIAL_READY_IDS], "ready": True}
    doc.update(over)
    return doc


def a10_baseline():
    b = baseline()
    b["noninterference"] = snapshot()
    return b


def dispatch_digests():
    return digests()


def a10_good():
    return a10_report(), a10_baseline(), profile()
