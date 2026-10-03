"""test_e6_5_registry_check.py: E6.5, `asset_census.py --registry-check` (registry-only coverage report, SS N-97(1)).

Offline (psql is made to raise). Every detector below is proven able to FAIL by a mutation of the registry, the N/A rules, the
revision or the report bytes: a green here is not "it usually holds". The committed-report test is the CI drift guard."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

REPO = HERE.parents[3]
COMMITTED = REPO / ac.REGISTRY_COVERAGE_REPORT_REL
SHA_A, SHA_B = "a" * 40, "b" * 40
D2 = "Carr.D2"


def _report(**kw):
    return ac.registry_coverage_report(**kw)


def _text(rep, sha=SHA_A):
    return ac.registry_report_text({**rep, "inspector_commit": sha})


@pytest.fixture(autouse=True)
def _no_database(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("--registry-check must never touch the database")
    monkeypatch.setattr(ac, "psql", boom)
    monkeypatch.setattr(ac, "scalar", boom)


# ───────────────────────── shape, counts, determinism ─────────────────────────

def test_schema_and_tracker_keys():
    r = _report()
    for k in ("registry_revision", "inspector_commit", "covered_cells", "uncovered_required_criteria", "per_asset_pending",
              "na_rules", "registry_fingerprint", "expected_cells"):
        assert k in r
    assert r["registry_revision"] == ac.REGISTRY_REVISION and r["registry_fingerprint"] == ac.registry_fingerprint()
    assert isinstance(r["covered_cells"], int) and r["covered_cells"] > 0
    assert r["expected_cells"] == 54


def test_three_candidate_counts_side_by_side():
    cc = _report()["candidate_cell_counts"]
    assert cc["gate_x_layer"]["total"] == 54 and cc["gate_x_layer"]["pinned"] is True
    assert cc["core_criterion_x_layer"]["total"] == 150 and cc["core_criterion_x_layer"]["pinned"] is False
    assert cc["gate_x_asset"]["total"] is None and "offline" in cc["gate_x_asset"]["omitted_reason"]
    assert cc["core_criterion_x_layer"]["auto_measured"] + cc["core_criterion_x_layer"]["detector_none"] == 150


def test_today_uncovered_are_the_three_detector_none_core_criteria():
    r = _report()
    assert r["uncovered_required_criteria"] == [D2, "Carr.D3", "Earn.service_state"]
    assert r["per_asset_pending"] == []
    assert r["non_core_detector_none"] == ["Completeness.depth.dasha_link"]      # information, never a core cell
    assert r["covered_cells"] == 42      # Carr x6 and Earn x6 each hold one uncovered criterion


def test_deterministic_and_no_timestamps():
    a, b = _text(_report()), _text(_report())
    assert a == b and a.endswith("\n")
    low = a.lower()
    assert "timestamp" not in low and "generated_at" not in low
    assert json.loads(a)["cells"] == _report()["cells"]


def test_na_rules_listed_with_decisions_and_undeclared_reported():
    r = _report()
    assert [x["rule_id"] for x in r["na_rules"]] == sorted(ac.NA_RULE_DECISIONS)
    assert all(x["decision"] == ac.NA_RULE_DECISIONS[x["rule_id"]] for x in r["na_rules"])
    assert "Vocab.alias#columns_any" in r["undeclared_na_pattern_ids"] and len(r["undeclared_na_pattern_ids"]) == 4
    assert not set(r["undeclared_na_causes"]) & set(ac.NA_RULE_DECISIONS)


# ───────────────────────── mutation: each detector can fail ─────────────────────────

def test_detector_none_without_rule_is_uncovered(monkeypatch):
    base = _report()
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Idem.zz_probe",
                        dict(ac.CRITERION_REGISTRY["Idem.pattern"], check="zz_probe", detector="NONE"))
    r = _report()
    assert "Idem.zz_probe" in r["uncovered_required_criteria"]
    assert r["covered_cells"] == base["covered_cells"] - 6      # the Idem cell of every layer loses coverage
    assert r["candidate_cell_counts"]["core_criterion_x_layer"]["total"] == 156


def test_a_measured_detector_removes_the_uncovered_entry(monkeypatch):
    monkeypatch.setitem(ac.CRITERION_REGISTRY, D2, dict(ac.CRITERION_REGISTRY[D2], detector="asset_census.py:measure()"))
    r = _report()
    assert D2 not in r["uncovered_required_criteria"] and r["covered_cells"] == 42      # Carr.D3 still holds every Carr cell open
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Carr.D3", dict(ac.CRITERION_REGISTRY["Carr.D3"], detector="asset_census.py:measure()"))
    assert _report()["covered_cells"] == 48


def test_layer_narrowing_changes_required_and_cells(monkeypatch):
    monkeypatch.setitem(ac.CRITERION_REGISTRY, D2, dict(ac.CRITERION_REGISTRY[D2], layers=("L1",)))
    cc = _report()["candidate_cell_counts"]["core_criterion_x_layer"]
    assert cc["total"] == 145


def test_declared_na_rule_does_not_cover_a_detector_none_criterion():
    r = _report()
    assert f"{D2}#measured:not-the-declared-carriage" in ac.NA_RULE_DECISIONS      # a rule exists for Carr.D2 ...
    assert D2 in r["uncovered_required_criteria"]                                   # ... and it is still uncovered
    cell = next(c for c in r["cells"] if c["gate"] == "Carr" and c["layer"] == "L2")
    assert f"{D2}#measured:not-the-declared-carriage" in cell["declared_na_rules"] and D2 in cell["uncovered"]


def test_removing_an_na_rule_changes_the_report(monkeypatch):
    base = _report()
    rid = "Narr.lint#measured:no-prose"
    monkeypatch.delitem(ac.NA_RULE_DECISIONS, rid)
    r = _report()
    assert rid not in [x["rule_id"] for x in r["na_rules"]] and rid in r["undeclared_na_causes"]
    assert r["registry_fingerprint"] != base["registry_fingerprint"]
    assert _text(r) != _text(base)


def test_fingerprint_and_revision_change_change_the_report(monkeypatch):
    base = _report()
    monkeypatch.setattr(ac, "REGISTRY_REVISION", ac.REGISTRY_REVISION + 1)
    bumped = _report()
    assert bumped["registry_revision"] == base["registry_revision"] + 1 and _text(bumped) != _text(base)
    monkeypatch.setitem(ac.CRITERION_REGISTRY, "Build.dag", dict(ac.CRITERION_REGISTRY["Build.dag"], revision=99))
    assert _report()["registry_fingerprint"] != base["registry_fingerprint"]


def test_per_asset_pending_hook_moves_a_criterion_out_of_uncovered():
    r = _report(pending={D2: "SS-decision-x", "Carr.D3": "SS-decision-x"})
    assert r["per_asset_pending"] == [D2, "Carr.D3"] and r["uncovered_required_criteria"] == ["Earn.service_state"]
    assert r["covered_cells"] == 48         # the six Carr cells are covered once D2 and D3 are declared pending


def test_pending_hook_refuses_a_measured_unknown_or_undecided_entry():
    for bad in ({"Build.dag": "x"}, {"No.such": "x"}, {D2: ""}, {"Completeness.depth.dasha_link": "x"}):
        with pytest.raises(ValueError):
            _report(pending=bad)


# ───────────────────────── gating (SS N-97(1)) ─────────────────────────

def test_gate_fails_on_uncovered_and_passes_when_all_pending():
    assert any("Carr.D2" in p for p in ac.registry_report_problems(_report()))
    allp = _report(pending={c: "SS-decision-x" for c in (D2, "Carr.D3", "Earn.service_state")})
    assert ac.registry_report_problems(allp) == []


def test_gate_fails_when_cell_count_is_not_54(monkeypatch):
    monkeypatch.setattr(ac, "CELL_GATES", ac.CELL_GATES[:-1])
    r = _report(pending={})
    assert r["candidate_cell_counts"]["gate_x_layer"]["total"] == 48
    assert any("48" in p and "54" in p for p in ac.registry_report_problems(r))


def test_cli_exit_codes_and_no_database(tmp_path, monkeypatch):
    out = tmp_path / "r.json"
    assert ac.registry_check_main(str(out), False) == ac.EXIT_REG_UNCOVERED      # uncovered today: written, exit 3
    assert out.exists()
    assert ac.registry_check_main(str(out), True) == ac.EXIT_REG_UNCOVERED      # matches a fresh regeneration; gate still red
    out.write_text(out.read_text().replace('"covered_cells": 42', '"covered_cells": 54'), encoding="utf-8")
    assert ac.registry_check_main(str(out), True) == ac.EXIT_REG_DRIFT
    assert ac.registry_check_main(str(tmp_path / "missing.json"), True) == ac.EXIT_REG_DRIFT
    monkeypatch.setattr(ac, "PER_ASSET_PENDING", {c: "SS-decision-x" for c in (D2, "Carr.D3", "Earn.service_state")})
    assert ac.registry_check_main(str(out), False) == 0
    assert ac.registry_check_main(str(out), True) == 0


def test_cli_check_requires_registry_check():
    p = subprocess.run([sys.executable, str(HERE.parent / "asset_census.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 2 and "--registry-check" in p.stderr


# ───────────────────────── drift: committed report == fresh regeneration ─────────────────────────

def test_drift_detector_can_fail_and_only_normalises_inspector_commit():
    t = _text(_report(), SHA_A)
    assert ac.registry_report_drift(t, _text(_report(), SHA_B)) is None             # another commit sha: not drift
    assert ac.registry_report_drift(t.replace('"covered_cells": 42', '"covered_cells": 43'), t)
    assert ac.registry_report_drift(t.replace('"expected_cells": 54', '"expected_cells": 150'), t)
    assert ac.registry_report_drift(t.replace("\n ", "\n  ", 1), t)                  # formatting is part of the bytes
    assert ac.registry_report_drift(t + "\n", t)
    assert ac.registry_report_drift(t.replace(SHA_A, "abc123"), t)                   # abbreviated sha refused
    assert ac.registry_report_drift(t.replace(f'"{SHA_A}"', "null"), t)


def test_committed_report_equals_fresh_regeneration():
    assert COMMITTED.exists(), "00_ARCHITECTURE/control/registry_coverage_report.json must be committed"
    rep = _report()
    rep["inspector_commit"] = SHA_A
    assert ac.registry_report_drift(COMMITTED.read_text(encoding="utf-8"), ac.registry_report_text(rep)) is None
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed["registry_fingerprint"] == ac.registry_fingerprint()
    assert committed["registry_revision"] == ac.REGISTRY_REVISION and committed["expected_cells"] == 54
