"""TR-26 (SR-J4E-CENTURY-FAIL-1 (4): "the trial universe must equal the century universe"; SR-TR26-PLAN: a writer fix means 26 classes, no 14-class path) — the harness reads a 26-class run.  One oracle per distinct claim; the single
planted reversion that fails each is named in its docstring.  No database: the baseline writer is fed a synthetic all-null report; the class universe is read from the verifier's own source.
Class table: EVALUATION_PROTOCOL v2.3 §2 (27 classes) minus the unscored annotation `birth_anchor` (input_vector_verifier.SCORED_CLASS_UNIVERSE)."""
import argparse
import json
import re
from pathlib import Path

import pytest

import gates
import trial_slice as ts

REPO = Path(__file__).resolve().parents[6]
VERIFIER = REPO / "platform" / "python-sidecar" / "services" / "gochara_kernel" / "input_vector_verifier.py"


def report(classes, windows=10):
    """The slice of a passed all-null default-policy report that cmd_baseline reads."""
    by = {c: {"windows_total": windows, "blank": windows, "valence": {"unqualified": windows}, "blank_reasons": {"all_null_candidate_policy": windows},
              "by_path": {"P1": {"windows": windows}}} for c in classes}
    n = windows * len(classes)
    return {"oracle": {"passed": True}, "config": {"classes": list(classes), "baseline_mode": True}, "classes": by,
            "totals": {"windows_total": n, "blank": n}, "paths": {"P1": {"windows": n}}, "code": {"head": "0" * 40}, "lane": {},
            "runtime_s": {"by_step_kind": {}, "build_substeps_sum": 1.0, "load_average_at_report": [0, 0, 0]}, "window_rows_digest": {"sha256": "ab" * 32}, "noninterference": None}


def baseline(tmp_path, classes, *, ran=None):
    rp, out = tmp_path / "r.json", tmp_path / "b.json"
    rp.write_text(json.dumps(report(ran or classes)))
    ns = argparse.Namespace(report=str(rp), out=str(out), prior_4class=None, from_prior_only=False, note=None, classes=",".join(classes))
    rc = ts.cmd_baseline(ns)
    return rc, json.loads(out.read_text())


def test_26_is_the_verifiers_scored_universe_and_14_is_the_remainder():
    """The trial universe equals the century universe: gates.TRIAL_CLASSES_26 == SCORED_CLASS_UNIVERSE of the verifier's own source; NEW_14 = it minus the 12.  Reversion: drop one class from NEW_14."""
    src = VERIFIER.read_text()
    universe = set(re.findall(r'"([a-z_]+)"', re.search(r"SCORED_CLASS_UNIVERSE = \((.*?)\)", src, re.S).group(1)))
    assert len(universe) == 26
    assert set(gates.TRIAL_CLASSES_26) == universe and len(gates.TRIAL_CLASSES_26) == 26
    assert set(gates.TRIAL_CLASSES_NEW_14) == universe - set(gates.TRIAL_CLASSES_12) and len(gates.TRIAL_CLASSES_NEW_14) == 14


def test_a_26_class_baseline_groups_each_class_once(tmp_path):
    """The 26-class baseline carries 4 prior_4class + 8 new_8 + 14 new_14 and the group sums add up.  Reversion: label every non-prior class new_8."""
    rc, b = baseline(tmp_path, list(gates.TRIAL_CLASSES_26))
    groups = [v["group"] for v in b["classes"].values()]
    assert (groups.count("prior_4class"), groups.count("new_8"), groups.count("new_14")) == (4, 8, 14)
    t = b["totals"]
    assert t["prior_4class_windows"] + t["new_8_windows"] + t["new_14_windows"] == t["windows_total"] == 260


def test_the_baseline_refuses_a_report_that_ran_other_classes_than_asked_and_any_14_class_path(tmp_path):
    """A baseline is never written from a run of a different class list (its geometry_config would not match the trial's), and there is no 14-class baseline (SR-TR26-PLAN: 26 only).
    Reversion: compare against CLASSES again / accept any subset of the 26."""
    with pytest.raises(ts.Refused):
        baseline(tmp_path, list(gates.TRIAL_CLASSES_26), ran=list(gates.TRIAL_CLASSES_12))
    with pytest.raises(ts.Refused):
        baseline(tmp_path, ["bereavement", "not_a_class"])
    with pytest.raises(ts.Refused):
        baseline(tmp_path, list(gates.TRIAL_CLASSES_NEW_14))


def test_g1_names_the_required_class_count_and_reads_a_missing_new_class_baseline_as_not_evaluated():
    """G-1 with the 26-class profile: the claim text names 26; a baseline without a measured count for a new class is NOT_EVALUATED, never equal.  Reversion: hard-code '12' in the claim text."""
    prof = {"trial_classes": list(gates.TRIAL_CLASSES_26)}
    cls = list(gates.TRIAL_CLASSES_26)
    rep = {"config": {"classes": cls}, "classes": {c: {"windows_total": 5} for c in cls}, "anomalies": {k: 0 for k in gates.ANOMALY_FIELDS}}
    base = {"classes": {c: {"windows_total": 5} for c in cls if c != "surgery"}}
    g = gates.g1_integrity(rep, base, prof)
    assert g["checks"][0]["claim"] == "the trial ran exactly the 26 required classes" and g["checks"][0]["status"] == gates.PASS
    assert g["checks"][1]["status"] == gates.NOT_EVALUATED and g["checks"][1]["observed"] == ["surgery"]
