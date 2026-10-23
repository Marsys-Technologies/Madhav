"""TRIAL_READY T12 (TR_GAPS B2, SELECT-130) — the doctrine version 1.3.0 is SELECTED on the head, and a selection flipped back to 1.2.0 is refused by the trial harness.

Doctrine: P1-MAPPING-DECISION / AM-13-RATIFIED / VEDHA-SOURCE (OWNER-DOCTRINE-CONFIRMED-20261021): the owner-confirmed rows are P1/P2/P3/P4@1.3.0, and the century
profile selects them (`rule_registry.FINAL_SELECTED_PATH_REFS`); only the eight ND-H classes keep their own 1.2.0 override (ND-H-20261005, `CLASS_SELECTION_OVERRIDES`).
`test_od1_v1_versions` asserts the default selection but never flips it, so a selection that quietly fell back to 1.2.0 would leave it green; these two oracles flip it.

  T12-1 the selection the trial reads (the final profile, and the `p1_form_b` trial flag on the measuring profile) is 1.3.0 for every trial class with no ND-H override
        (revert: `FINAL_SELECTED_PATH_REFS` selects 1.2.0 for P1);
  T12-2 a selection flipped to 1.2.0 is REFUSED by the trial harness — gate G-7's rule-version identity check reads the versions the production selection
        yields, a flipped selection differs from the declared change and reads FAIL, the unflipped selection reads PASS (revert: the gate stops reading rule_versions).

(I) INTERPRETATION recorded with the registry entry: G-2 ("wiring complete") reads the blank-reason census of stored windows and has no selection input at all, so no
unit oracle can make G-2 itself refuse on a flipped selection without a full build; the harness gate that reads the selected version identity is G-7's noninterference
check (`g7_noninterference_checks`, "rule-version identities differ from the baseline only by declared changes"), and that is what this oracle drives.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from services.gochara_kernel import rule_registry as rr

REPO = Path(__file__).resolve().parents[5]
HARNESS = REPO / "00_ARCHITECTURE" / "briefs" / "kalayantra" / "fleet" / "trial_harness"
DOC = "1.3.0"
ND_H = "1.2.0"
PATHS = ("P1", "P2", "P3", "P4")


def _gates():
    """The harness's gate module, loaded from its directory (it imports its sibling `g5_cpu`)."""
    if str(HARNESS) not in sys.path:
        sys.path.insert(0, str(HARNESS))
    spec = importlib.util.spec_from_file_location("tr_select_130_gates", HARNESS / "gates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _doc_classes(gates) -> list[str]:
    """The trial classes the ND-H override does not touch (they run P1..P4 under the default selection)."""
    overridden = {cls for (cls, _pid) in rr.CLASS_SELECTION_OVERRIDES}
    return sorted(c for c in gates.TRIAL_CLASSES_12 if c not in overridden)


def _selection(classes, **profile) -> dict:
    with rr.rule_profile(**profile):
        return {c: rr.selected_versions_for(c) for c in classes}


def test_t12_1_the_selection_the_trial_reads_is_1_3_0_for_every_class_without_an_nd_h_override():
    """Planted reversion: `FINAL_SELECTED_PATH_REFS` selects P1@1.2.0 (the doctrine row is registered but not selected)."""
    classes = _doc_classes(_gates())
    assert classes, "the 12 trial classes include no class outside the ND-H overrides: nothing to read"
    final = _selection(classes, final_rules=True)
    for cls in classes:
        assert {pid: final[cls][pid] for pid in PATHS} == {pid: DOC for pid in PATHS}, cls
    flagged = _selection(classes, final_rules=False, p1_form_b=True)            # the measuring profile + the trial flag: P1 only, at 1.3.0
    for cls in classes:
        assert flagged[cls]["P1"] == DOC, cls
    unflagged = _selection(classes, final_rules=False)
    assert all(unflagged[cls]["P1"] == "1.0.0" for cls in classes)                # the flag, not the default, is what moves it


def _snapshot(versions: dict) -> dict:
    """A natural-key snapshot with identical keys on both sides, so that only the rule-version identities can differ."""
    kinds = {k: {"groups": {"g": {"sha256": "ab", "count": 1}}, "sha256": "ab" * 32, "count": 1} for k in ("windows", "supports", "contacts", "membership")}
    return {"geometry_config": "cfg", "kinds": kinds, "rule_versions": versions}


def _versions(selection: dict) -> dict:
    return {pid: sorted({sel[pid] for sel in selection.values()}) for pid in PATHS}


def _identity_check(gates, trial_selection, base_selection, declared_to) -> dict:
    table = json.loads((HARNESS / "g3_decision_table.json").read_text())
    table = copy.deepcopy(table)
    table["noninterference"]["declared_rule_version_changes"] = [{"path": pid, "from": "1.0.0", "to": declared_to} for pid in PATHS]
    table = gates.load_decision_table(table)
    checks = gates.g7_noninterference_checks({"noninterference": _snapshot(_versions(trial_selection))},
                                             {"noninterference": _snapshot(_versions(base_selection))}, table)
    (hit,) = [c for c in checks if c["claim"].startswith("rule-version identities")]
    return hit


def test_t12_2_a_selection_flipped_to_1_2_0_is_refused_by_the_harness_and_the_real_selection_is_accepted(monkeypatch):
    """Planted reversion: the gate no longer reads `rule_versions` (the identity check passes whatever the trial selected)."""
    gates = _gates()
    classes = _doc_classes(gates)
    baseline = _selection(classes, final_rules=False)                              # the all-null baseline is made on the 1.0.0 selection
    real = _selection(classes, final_rules=True)
    assert _identity_check(gates, real, baseline, DOC)["status"] == gates.PASS      # the declared 1.0.0 -> 1.3.0 change is exactly what was selected

    monkeypatch.setattr(rr, "FINAL_SELECTED_PATH_REFS", tuple((pid, ND_H if pid == "P1" else v) for pid, v in rr.FINAL_SELECTED_PATH_REFS))
    flipped = _selection(classes, final_rules=True)
    assert all(flipped[c]["P1"] == ND_H for c in classes), "the flip did not reach the production selection"
    refused = _identity_check(gates, flipped, baseline, DOC)
    assert refused["status"] == gates.FAIL and "P1" in refused["observed"], refused
